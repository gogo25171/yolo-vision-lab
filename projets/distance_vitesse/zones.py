"""Zones (polygones) et lignes de comptage.

Fichier JSON (coordonnées en pixels ou normalisées 0-1) ::

    {
      "zones": [
        {"name": "Parking", "polygon": [[0.1, 0.5], [0.6, 0.5], [0.6, 0.9], [0.1, 0.9]],
         "classes": ["Voiture", "Camion"]}
      ],
      "lines": [
        {"name": "Entrée", "points": [[0.0, 0.7], [1.0, 0.7]], "classes": ["Voiture"]}
      ]
    }

``classes`` est optionnel (toutes les classes sinon). Le point de référence d'un
objet est le bas-centre de sa boîte (son contact avec le sol).

Une zone donne l'occupation courante (objets présents) et le total d'objets
distincts entrés. Une ligne compte les passages dans chaque sens.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np


def _scale(points: list, width: int, height: int) -> np.ndarray:
    array = np.asarray(points, dtype=np.float32)
    if np.all(array <= 1.0):
        array = array * np.array([width, height], dtype=np.float32)
    return array


@dataclass
class Zone:
    name: str
    polygon: list
    classes: set[str] | None = None
    inside: dict[int, str] = field(default_factory=dict)        # track_id -> classe (présents, stabilisé)
    entered: dict[int, str] = field(default_factory=dict)       # tous les objets vus dans la zone
    absent: dict[int, int] = field(default_factory=dict)        # track_id -> images consécutives hors zone
    _pixels: np.ndarray | None = None

    def pixels(self, width: int, height: int) -> np.ndarray:
        if self._pixels is None:
            self._pixels = _scale(self.polygon, width, height).astype(np.int32)
        return self._pixels

    def contains(self, point: tuple[float, float], width: int, height: int) -> bool:
        return cv2.pointPolygonTest(self.pixels(width, height), point, False) >= 0

    def occupancy(self) -> Counter:
        return Counter(self.inside.values())

    def totals(self) -> Counter:
        return Counter(self.entered.values())


@dataclass
class Line:
    name: str
    points: list
    classes: set[str] | None = None
    count_in: Counter = field(default_factory=Counter)
    count_out: Counter = field(default_factory=Counter)
    _last_side: dict[int, float] = field(default_factory=dict)
    _pixels: np.ndarray | None = None

    def pixels(self, width: int, height: int) -> np.ndarray:
        if self._pixels is None:
            self._pixels = _scale(self.points, width, height)
        return self._pixels

    def _side(self, point: tuple[float, float], width: int, height: int) -> float:
        (x1, y1), (x2, y2) = self.pixels(width, height)
        return (x2 - x1) * (point[1] - y1) - (y2 - y1) * (point[0] - x1)

    def _within_segment(self, point: tuple[float, float], width: int, height: int) -> bool:
        (x1, y1), (x2, y2) = self.pixels(width, height)
        dx, dy = x2 - x1, y2 - y1
        length2 = dx * dx + dy * dy
        if length2 == 0:
            return False
        t = ((point[0] - x1) * dx + (point[1] - y1) * dy) / length2
        return 0.0 <= t <= 1.0

    def update(self, track_id: int, label: str, point, width: int, height: int) -> str | None:
        side = self._side(point, width, height)
        if side == 0:
            # Pile sur la ligne : on garde le dernier côté connu, le franchissement sera
            # compté à l'image suivante (sinon il serait perdu).
            return None
        previous = self._last_side.get(track_id)
        self._last_side[track_id] = side
        if previous is None or (previous > 0) == (side > 0):
            return None
        if not self._within_segment(point, width, height):
            return None
        direction = "in" if side > 0 else "out"
        (self.count_in if direction == "in" else self.count_out)[label] += 1
        return direction


@dataclass
class _Gone:
    track_id: int
    label: str


class ZoneCounter:
    def __init__(self, zones: list[Zone], lines: list[Line]):
        self.zones = zones
        self.lines = lines
        self.events: list[dict] = []
        self.on_event = None          # callback(event) : publication vers l'API, MQTT, webhooks…
        self.exit_after_frames = 15   # ~0,5 s à 30 images/s

    def _emit(self, timestamp: float, event_type: str, name: str, det) -> None:
        event = {"t": round(timestamp, 2), "type": event_type, "name": name,
                 "track_id": det.track_id, "label": det.label}
        self.events.append(event)
        if self.on_event:
            self.on_event(event)

    @classmethod
    def from_file(cls, path: Path | None) -> ZoneCounter:
        if path is None or not Path(path).exists():
            return cls([], [])
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        zones = [
            Zone(z["name"], z["polygon"], set(z["classes"]) if z.get("classes") else None)
            for z in data.get("zones", [])
        ]
        lines = [
            Line(ln["name"], ln["points"], set(ln["classes"]) if ln.get("classes") else None)
            for ln in data.get("lines", [])
        ]
        return cls(zones, lines)

    def __bool__(self) -> bool:
        return bool(self.zones or self.lines)

    def update(self, detections: list, width: int, height: int, timestamp: float) -> None:
        """``detections`` : objets ayant ``track_id``, ``label`` et ``anchor`` (bas-centre)."""
        tracked = [det for det in detections if det.track_id is not None]
        for zone in self.zones:
            self._update_zone(zone, tracked, width, height, timestamp)
        for line in self.lines:
            for det in tracked:
                if line.classes and det.label not in line.classes:
                    continue
                direction = line.update(det.track_id, det.label, det.anchor, width, height)
                if direction:
                    self._emit(timestamp, f"line_{direction}", line.name, det)

    def _update_zone(self, zone: Zone, detections: list, width: int, height: int, timestamp: float) -> None:
        seen = set()
        for det in detections:
            if zone.classes and det.label not in zone.classes:
                continue
            if zone.contains(det.anchor, width, height):
                seen.add(det.track_id)
                zone.absent.pop(det.track_id, None)
                if det.track_id not in zone.inside:
                    zone.inside[det.track_id] = det.label
                    zone.entered.setdefault(det.track_id, det.label)
                    self._emit(timestamp, "zone_enter", zone.name, det)
        # Sortie confirmée seulement après EXIT_AFTER_FRAMES images d'absence : un objet garé dont
        # la détection clignote ne génère pas de fausses sorties/entrées.
        for track_id, label in list(zone.inside.items()):
            if track_id in seen:
                continue
            zone.absent[track_id] = zone.absent.get(track_id, 0) + 1
            if zone.absent[track_id] >= self.exit_after_frames:
                del zone.inside[track_id]
                del zone.absent[track_id]
                self._emit(timestamp, "zone_exit", zone.name, _Gone(track_id, label))

    def summary(self) -> dict:
        return {
            "zones": {
                z.name: {"total": dict(z.totals()), "occupation_finale": dict(z.occupancy())} for z in self.zones
            },
            "lines": {ln.name: {"in": dict(ln.count_in), "out": dict(ln.count_out)} for ln in self.lines},
        }
