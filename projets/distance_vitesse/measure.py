"""Estimation de la distance et de la vitesse.

Deux niveaux de précision :

1. **Sans calibration** (par défaut) : modèle sténopé. La focale en pixels se déduit
   du champ de vision horizontal de la caméra, puis
   ``distance = hauteur_réelle × focale / hauteur_en_pixels``.
   La vitesse découle du déplacement 3D estimé (latéral + profondeur). C'est une
   approximation (±20-30 %), affichée avec un « ~ ».

2. **Avec calibration** (CALIBRATION_FILE) : une homographie relie 4 points de
   l'image à leurs coordonnées au sol en mètres. Le point de contact au sol
   (bas-centre de la boîte) est projeté sur ce plan : la vitesse devient fiable
   pour une caméra fixe (CCTV).
"""

from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np


def focal_length_from_fov(image_width: int, hfov_deg: float) -> float:
    return (image_width / 2) / math.tan(math.radians(hfov_deg) / 2)


class GroundPlane:
    """Homographie image -> sol (mètres), chargée depuis un JSON.

    Format ::

        {"image_points": [[x, y], ... x4], "world_points": [[X, Y], ... x4]}

    Les points image peuvent être en pixels ou normalisés (0-1).
    """

    def __init__(self, image_points: list, world_points: list):
        self._image_points = np.asarray(image_points, dtype=np.float32)
        self._world_points = np.asarray(world_points, dtype=np.float32)
        self._normalized = bool(np.all(self._image_points <= 1.0))
        self._matrix: np.ndarray | None = None
        self._size: tuple[int, int] | None = None

    @classmethod
    def from_file(cls, path: Path) -> GroundPlane:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data["image_points"], data["world_points"])

    def _ensure(self, width: int, height: int) -> np.ndarray:
        if self._matrix is None or self._size != (width, height):
            points = self._image_points.copy()
            if self._normalized:
                points *= np.array([width, height], dtype=np.float32)
            self._matrix, _ = cv2.findHomography(points, self._world_points)
            self._size = (width, height)
        return self._matrix

    def to_world(self, x: float, y: float, width: int, height: int) -> tuple[float, float]:
        matrix = self._ensure(width, height)
        point = cv2.perspectiveTransform(np.array([[[x, y]]], dtype=np.float32), matrix)
        return float(point[0, 0, 0]), float(point[0, 0, 1])


def estimate_distance(box_height_px: float, real_height_m: float | None, focal_px: float) -> float | None:
    if real_height_m is None or box_height_px <= 1:
        return None
    return real_height_m * focal_px / box_height_px


def camera_position(cx: float, image_width: int, distance_m: float, focal_px: float) -> tuple[float, float]:
    """Position (X latéral, Z profondeur) en mètres dans le repère caméra."""
    lateral = (cx - image_width / 2) * distance_m / focal_px
    return lateral, distance_m


@dataclass
class _History:
    samples: deque = field(default_factory=lambda: deque(maxlen=120))  # (t, x, y)
    speed_ms: float | None = None


class SpeedEstimator:
    """Vitesse par objet suivi, lissée sur une fenêtre glissante."""

    def __init__(self, window_s: float = 1.0, min_span_s: float = 0.4, smoothing: float = 0.3):
        self.window_s = window_s
        self.min_span_s = min_span_s
        self.smoothing = smoothing
        self._tracks: dict[int, _History] = {}

    def update(self, track_id: int, t: float, position: tuple[float, float]) -> float | None:
        history = self._tracks.setdefault(track_id, _History())
        history.samples.append((t, *position))
        while history.samples and t - history.samples[0][0] > self.window_s:
            history.samples.popleft()
        t0, x0, y0 = history.samples[0]
        span = t - t0
        if span < self.min_span_s:
            return history.speed_ms
        # Médiane des positions récentes : atténue le bruit de la boîte englobante.
        recent = list(history.samples)[-3:]
        x1 = float(np.median([s[1] for s in recent]))
        y1 = float(np.median([s[2] for s in recent]))
        instant = math.hypot(x1 - x0, y1 - y0) / span
        if history.speed_ms is None:
            history.speed_ms = instant
        else:
            history.speed_ms += self.smoothing * (instant - history.speed_ms)
        return history.speed_ms

    def forget(self, active_ids: set[int]) -> None:
        for track_id in list(self._tracks):
            if track_id not in active_ids:
                del self._tracks[track_id]
