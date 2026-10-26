"""Dessin des annotations sur l'image."""

from __future__ import annotations

import unicodedata

import cv2
import numpy as np

from .detections import Detection
from .zones import ZoneCounter

FONT = cv2.FONT_HERSHEY_SIMPLEX


def to_ascii(text: str) -> str:
    # Les polices Hershey d'OpenCV ne gèrent que l'ASCII : « Vélo » -> « Velo ».
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _text_block(frame: np.ndarray, lines: list[str], x: int, y: int, color, scale: float = 0.5) -> None:
    """Étiquette sur fond plein, placée au-dessus de (x, y) et gardée dans l'image."""
    lines = [to_ascii(line) for line in lines]
    thickness = 1
    sizes = [cv2.getTextSize(line, FONT, scale, thickness)[0] for line in lines]
    line_h = max(h for _, h in sizes) + 6
    block_w = max(w for w, _ in sizes) + 8
    block_h = line_h * len(lines) + 2
    height, width = frame.shape[:2]
    x = int(min(max(0, x), max(0, width - block_w)))
    top = y - block_h if y - block_h >= 0 else y
    top = int(min(top, max(0, height - block_h)))
    cv2.rectangle(frame, (x, top), (x + block_w, top + block_h), color, -1)
    text_color = (0, 0, 0) if sum(color) > 380 else (255, 255, 255)
    for i, line in enumerate(lines):
        cv2.putText(frame, line, (x + 4, top + line_h * (i + 1) - 4), FONT, scale, text_color, thickness, cv2.LINE_AA)


def _label_lines(det: Detection) -> list[str]:
    title = det.label if det.track_id is None else f"{det.label} #{det.track_id}"
    lines = [title]
    measures = []
    if det.distance_m is not None:
        measures.append(f"{det.distance_m:.1f} m")
    if det.speed_kmh is not None:
        prefix = "" if det.speed_calibrated else "~"
        measures.append(f"{prefix}{det.speed_kmh:.0f} km/h")
    if measures:
        lines.append(" | ".join(measures))
    if det.plate:
        lines.append(det.plate + (f" ({det.plate_region})" if det.plate_region else ""))
    return lines


COMPACT_ABOVE = 20   # mode « auto » : étiquettes compactes au-delà de ce nombre d'objets


def draw_detections(frame: np.ndarray, detections: list[Detection], colors: dict[str, tuple],
                    labels: str = "auto") -> None:
    """``labels`` : ``full`` (tout), ``compact`` (numéro + plaque) ou ``auto``."""
    visible = [d for d in detections if not d.hidden]
    compact = labels == "compact" or (labels == "auto" and len(visible) > COMPACT_ABOVE)
    max_scale = max(0.45, min(1.0, frame.shape[1] / 1600))
    for det in visible:
        color = colors.get(det.label, (128, 128, 128))
        x1, y1, x2, y2 = det.box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        # Petits objets (vue lointaine, drone) : étiquette plus petite pour limiter les chevauchements.
        scale = min(max_scale, max(0.35, det.height_px / 120))
        if compact:
            lines = [f"#{det.track_id}" if det.track_id is not None else det.label[:3]]
            if det.plate:
                lines.append(det.plate)
            scale = min(scale, 0.45)
        else:
            lines = _label_lines(det)
        _text_block(frame, lines, x1, y1, color, scale)


def draw_zones(frame: np.ndarray, counter: ZoneCounter) -> None:
    """Polygones et lignes (sous les détections)."""
    if not counter:
        return
    height, width = frame.shape[:2]
    overlay = frame.copy()
    for zone in counter.zones:
        cv2.fillPoly(overlay, [zone.pixels(width, height)], (255, 200, 0))
    cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)
    for zone in counter.zones:
        cv2.polylines(frame, [zone.pixels(width, height)], True, (255, 200, 0), 2)
    for line in counter.lines:
        (x1, y1), (x2, y2) = line.pixels(width, height).astype(int)
        cv2.line(frame, (x1, y1), (x2, y2), (0, 165, 255), 3)


def draw_zone_counts(frame: np.ndarray, counter: ZoneCounter) -> None:
    """Compteurs des zones et lignes (au-dessus des détections pour rester lisibles)."""
    height, width = frame.shape[:2]
    for zone in counter.zones:
        polygon = zone.pixels(width, height)
        occupancy = zone.occupancy()
        totals = zone.totals()
        lines = [f"{zone.name} : {sum(occupancy.values())} présents / {sum(totals.values())} total"]
        lines += [f"{label}: {occupancy.get(label, 0)} / {count}" for label, count in totals.most_common(4)]
        x, y = polygon.min(axis=0)
        _text_block(frame, lines, int(x), int(y), (255, 200, 0), 0.5)
    for line in counter.lines:
        (x1, y1), (x2, y2) = line.pixels(width, height).astype(int)
        text = f"{line.name} : +{sum(line.count_in.values())} / -{sum(line.count_out.values())}"
        _text_block(frame, [text], min(x1, x2), min(y1, y2), (0, 165, 255), 0.5)


def draw_hud(frame: np.ndarray, lines: list[str]) -> None:
    _text_block(frame, lines, 8, 8 + 22 * len(lines), (40, 40, 40), 0.55)
