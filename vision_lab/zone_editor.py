"""Éditeur de zones : ``python -m vision_lab zones <vidéo|image> [-o zones/ma_scene.json]``.

Commandes (fenêtre OpenCV) :

- clic gauche : ajouter un point          - z : annuler le dernier point
- n : terminer le polygone (zone)         - l : terminer une ligne (2 points)
- s : enregistrer                         - q / Échap : quitter

Les coordonnées sont enregistrées normalisées (0-1) : le fichier reste valable si
la résolution du flux change. Format commun à tous les projets du laboratoire.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from vision_lab.sources import is_image


def _first_frame(source: str):
    if is_image(source):
        return cv2.imread(source)
    capture = cv2.VideoCapture(int(source) if source.isdigit() else source)
    ok, frame = capture.read()
    capture.release()
    return frame if ok else None


class _Editor:
    def __init__(self, frame, output: Path):
        self.frame = frame
        self.height, self.width = frame.shape[:2]
        self.output = output
        self.data = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"zones": [], "lines": []}
        self.current: list[tuple[int, int]] = []

    def on_click(self, event, x, y, *_):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current.append((x, y))

    def normalized(self, points):
        return [[round(x / self.width, 4), round(y / self.height, 4)] for x, y in points]

    def to_pixels(self, points):
        return [(int(x * self.width), int(y * self.height)) for x, y in points]

    def render(self):
        canvas = self.frame.copy()
        for zone in self.data["zones"]:
            pts = self.to_pixels(zone["polygon"])
            cv2.polylines(canvas, [np.array(pts, dtype=np.int32)], True, (255, 200, 0), 2)
            cv2.putText(canvas, zone["name"], pts[0], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
        for line in self.data["lines"]:
            p1, p2 = self.to_pixels(line["points"])
            cv2.line(canvas, p1, p2, (0, 165, 255), 3)
            cv2.putText(canvas, line["name"], p1, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        for i, point in enumerate(self.current):
            cv2.circle(canvas, point, 5, (0, 0, 255), -1)
            if i:
                cv2.line(canvas, self.current[i - 1], point, (0, 0, 255), 2)
        return canvas

    def handle_key(self, key: int) -> bool:
        """Renvoie False pour quitter."""
        if key in (ord("q"), 27):
            return False
        if key == ord("z") and self.current:
            self.current.pop()
        elif key == ord("n") and len(self.current) >= 3:
            self.data["zones"].append({"name": f"Zone {len(self.data['zones']) + 1}",
                                       "polygon": self.normalized(self.current)})
            self.current.clear()
        elif key == ord("l") and len(self.current) == 2:
            self.data["lines"].append({"name": f"Ligne {len(self.data['lines']) + 1}",
                                       "points": self.normalized(self.current)})
            self.current.clear()
        elif key == ord("s"):
            self.output.parent.mkdir(parents=True, exist_ok=True)
            self.output.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Enregistré : {self.output} (renommez les zones dans le JSON si besoin)")
        return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vision_lab zones", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source")
    parser.add_argument("-o", "--output", type=Path, default=Path("zones/zones.json"))
    args = parser.parse_args(argv)

    frame = _first_frame(args.source)
    if frame is None:
        raise SystemExit(f"Impossible de lire : {args.source}")
    editor = _Editor(frame, args.output)
    window = "Editeur de zones (n=zone, l=ligne, z=annuler, s=sauver, q=quitter)"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window, editor.on_click)
    while True:
        cv2.imshow(window, editor.render())
        if not editor.handle_key(cv2.waitKey(30) & 0xFF):
            break
    cv2.destroyAllWindows()
    return 0
