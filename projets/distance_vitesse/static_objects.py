"""Objets statiques : sélectionner un objet fixe (poteau, panneau, véhicule garé, porte…) et
obtenir sa distance à la caméra en continu.

Fichier JSON (``STATIC_OBJECTS_FILE``) ::

    {"objects": [{"name": "Panneau stop", "box": [0.61, 0.32, 0.64, 0.47], "height_m": 2.5}]}

- ``box`` : x1, y1, x2, y2 normalisés (0-1) ou en pixels ;
- ``height_m`` : hauteur réelle de l'objet (ou de la partie encadrée).

Sélection interactive : ``python -m vision_lab distance_vitesse <source> --select-static``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .classes import COCO_CLASSES
from .draw import to_ascii
from .measure import estimate_distance


@dataclass
class StaticObject:
    name: str
    box: list[float]
    height_m: float

    def pixels(self, width: int, height: int) -> tuple[int, int, int, int]:
        box = np.asarray(self.box, dtype=float)
        if np.all(box <= 1.0):
            box = box * [width, height, width, height]
        x1, y1, x2, y2 = box.astype(int)
        return int(x1), int(y1), int(x2), int(y2)

    def distance(self, width: int, height: int, focal_px: float) -> float | None:
        _, y1, _, y2 = self.pixels(width, height)
        return estimate_distance(y2 - y1, self.height_m, focal_px)


def load(path: Path | None) -> list[StaticObject]:
    if path is None or not Path(path).exists():
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [StaticObject(o["name"], o["box"], float(o["height_m"])) for o in data.get("objects", [])]


def save(path: Path, objects: list[StaticObject]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"objects": [{"name": o.name, "box": o.box, "height_m": o.height_m} for o in objects]}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_height(answer: str) -> float | None:
    """Accepte un nombre (« 2,5 ») ou un nom de classe connu (« Voiture » -> 1,5 m)."""
    answer = answer.strip().replace(",", ".")
    try:
        return float(answer)
    except ValueError:
        for info in COCO_CLASSES.values():
            if info.label.lower() == answer.lower() and info.height_m:
                return info.height_m
    return None


def select_interactive(frame: np.ndarray, path: Path) -> list[StaticObject]:
    """Dessiner une ou plusieurs boîtes (Entrée pour valider chaque boîte, Échap pour finir)."""
    height, width = frame.shape[:2]
    objects = load(path)
    window = "Objets statiques : encadrer puis Entree (Echap pour terminer)"
    boxes = cv2.selectROIs(window, frame, showCrosshair=True)
    cv2.destroyWindow(window)
    for index, (x, y, w, h) in enumerate(boxes, start=1):
        name = input(f"Objet {index} - nom : ").strip() or f"Objet {len(objects) + 1}"
        real = None
        while real is None:
            real = _parse_height(input("  hauteur réelle en m (ou classe, ex. Voiture) : "))
        box = [round(x / width, 4), round(y / height, 4), round((x + w) / width, 4), round((y + h) / height, 4)]
        objects.append(StaticObject(name, box, real))
    save(path, objects)
    print(f"{len(objects)} objet(s) statique(s) enregistré(s) dans {path}")
    return objects


def draw(frame: np.ndarray, objects: list[StaticObject], focal_px: float) -> dict[str, float | None]:
    height, width = frame.shape[:2]
    distances = {}
    for obj in objects:
        x1, y1, x2, y2 = obj.pixels(width, height)
        distance = obj.distance(width, height, focal_px)
        distances[obj.name] = None if distance is None else round(distance, 2)
        color = (255, 0, 255)
        for x in range(x1, x2, 12):                      # cadre pointillé : objet statique
            cv2.line(frame, (x, y1), (min(x + 6, x2), y1), color, 2)
            cv2.line(frame, (x, y2), (min(x + 6, x2), y2), color, 2)
        for y in range(y1, y2, 12):
            cv2.line(frame, (x1, y), (x1, min(y + 6, y2)), color, 2)
            cv2.line(frame, (x2, y), (x2, min(y + 6, y2)), color, 2)
        text = to_ascii(f"{obj.name}: {distance:.1f} m" if distance else obj.name)
        cv2.putText(frame, text, (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)
    return distances
