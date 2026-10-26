"""Lecture des plaques d'immatriculation (multi-pays) via fast-alpr.

Pipeline : pour chaque véhicule suivi, on recadre sa boîte, fast-alpr y détecte la
plaque (YOLOv9 ONNX) puis la lit (OCR « global » entraîné sur des plaques de
nombreux pays, qui prédit aussi la région/pays). On ne relance pas l'OCR à chaque
image : une tentative toutes les ``every`` images par véhicule, et les lectures
sont fusionnées par vote pondéré par la confiance.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from .plate_formats import normalize


@dataclass
class PlateReading:
    text: str
    confidence: float
    region: str | None = None


@dataclass
class _TrackVotes:
    scores: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    hits: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    regions: dict[str, dict[str, float]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(float)))
    last_attempt: int = -10**9
    failures: int = 0


MIN_PLATE_CHARS = 4
CONFIRMED_HITS = 3   # lectures identiques au-delà desquelles on arrête l'OCR pour ce véhicule


def _mean_conf(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (list, tuple, np.ndarray)):
        return float(np.mean(value)) if len(value) else 0.0
    return float(value)


class PlateReader:
    def __init__(self, detector_model: str, ocr_model: str, every: int, device: str = "cpu",
                 fallback_countries: list[str] | None = None, min_confidence: float = 0.5,
                 min_region_confidence: float = 0.3):
        try:
            from fast_alpr import ALPR
        except ImportError as exc:  # dépendance optionnelle
            raise RuntimeError("fast-alpr n'est pas installé : pip install 'fast-alpr[onnx]'") from exc
        # Les modèles plaques sont minuscules : le CPU suffit et évite les conflits de
        # versions CUDA entre onnxruntime-gpu et PyTorch.
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if device == "cuda" else ["CPUExecutionProvider"]
        self._alpr = ALPR(detector_model=detector_model, detector_providers=providers,
                          ocr_model=ocr_model, ocr_device="cuda" if device == "cuda" else "cpu")
        self.every = max(1, every)
        self.fallback_countries = fallback_countries
        self.min_confidence = min_confidence
        self.min_region_confidence = min_region_confidence
        self.min_hits = 2
        self.confident_score = 0.9
        self._tracks: dict[int, _TrackVotes] = {}

    def read_crop(self, crop: np.ndarray, centered: bool = True) -> PlateReading | None:
        """Lit la plaque d'un recadrage de véhicule.

        ``centered`` : ne garde que les plaques proches du centre horizontal du recadrage,
        pour ignorer celle d'un véhicule voisin qui déborde dans la boîte.
        """
        best: PlateReading | None = None
        crop_width = crop.shape[1]
        for result in self._alpr.predict(crop):
            ocr = getattr(result, "ocr", None)
            if ocr is None or not getattr(ocr, "text", None):
                continue
            if centered:
                bbox = result.detection.bounding_box
                if abs((bbox.x1 + bbox.x2) / 2 - crop_width / 2) > 0.3 * crop_width:
                    continue
            text = "".join(ch for ch in ocr.text.upper() if ch.isalnum())
            confidence = _mean_conf(getattr(ocr, "confidence", None))
            if len(text) < MIN_PLATE_CHARS or confidence < self.min_confidence:
                continue
            region = getattr(ocr, "region", None) or None
            if region == "Unknown" or (getattr(ocr, "region_confidence", None) or 0.0) < self.min_region_confidence:
                region = None
            text, region = normalize(text, region, self.fallback_countries)
            reading = PlateReading(text, confidence, region)
            if best is None or reading.confidence > best.confidence:
                best = reading
        return best

    def update(self, track_id: int, frame_index: int, frame: np.ndarray,
               box: tuple[int, int, int, int]) -> PlateReading | None:
        """Tente une lecture si l'intervalle est écoulé ; renvoie la meilleure plaque connue."""
        votes = self._tracks.setdefault(track_id, _TrackVotes())
        confirmed = votes.hits and max(votes.hits.values()) >= CONFIRMED_HITS
        # Échecs répétés (plaque illisible, véhicule de dos/loin) : on espace les tentatives.
        interval = self.every * (1 + votes.failures // 5)
        if not confirmed and frame_index - votes.last_attempt >= interval:
            votes.last_attempt = frame_index
            reading = self.read_crop(crop_box(frame, box))
            if reading:
                votes.scores[reading.text] += reading.confidence
                votes.hits[reading.text] += 1
                if reading.region:
                    votes.regions[reading.text][reading.region] += reading.confidence
            else:
                votes.failures += 1
        return self.best(track_id)

    def best(self, track_id: int) -> PlateReading | None:
        votes = self._tracks.get(track_id)
        if not votes or not votes.scores:
            return None
        text, score = max(votes.scores.items(), key=lambda item: item[1])
        # Une lecture isolée et peu sûre est souvent un faux positif : on attend une confirmation.
        if votes.hits[text] < self.min_hits and score < self.confident_score:
            return None
        regions = votes.regions.get(text)
        region = max(regions.items(), key=lambda item: item[1])[0] if regions else None
        return PlateReading(text, score, region)


def crop_box(frame: np.ndarray, box: tuple[int, int, int, int], margin: float = 0.08) -> np.ndarray:
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = box
    mx, my = int((x2 - x1) * margin), int((y2 - y1) * margin)
    return frame[max(0, y1 - my):min(height, y2 + my), max(0, x1 - mx):min(width, x2 + mx)]
