"""Projet « Distance & vitesse » : ``python -m vision_lab distance_vitesse [source] [options]``.

Toutes les options ont un équivalent dans le .env (voir .env.example) ; la ligne de
commande a la priorité.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from vision_lab.config import add_output_arguments, load_output_settings, pop_output_overrides
from vision_lab.events import EventBus
from vision_lab.sources import is_image

from .settings import PRESETS, load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vision_lab distance_vitesse", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", nargs="?", help="fichier vidéo/image, URL RTSP/HTTP ou index webcam (0)")
    parser.add_argument("--mode", choices=list(PRESETS), help="fast = temps réel, accurate = vidéo enregistrée")
    parser.add_argument("--model", help="poids YOLO (ex. yolo26m.pt, models/best.engine)")
    parser.add_argument("--zones", type=Path, dest="zones_file", help="fichier JSON de zones/lignes")
    parser.add_argument("--calibration", type=Path, dest="calibration_file", help="homographie sol (vitesse précise)")
    parser.add_argument("--static", type=Path, dest="static_objects_file",
                        help="fichier JSON d'objets statiques dont mesurer la distance")
    parser.add_argument("--select-static", action="store_true",
                        help="sélectionner à la souris des objets statiques sur la première image")
    parser.add_argument("--classes", dest="open_vocab_classes",
                        help='vocabulaire ouvert YOLOE, ex. "child:1.2,adult:1.7,dog:0.55"')
    parser.add_argument("--no-plates", dest="plates_enabled", action="store_false", default=None,
                        help="désactive la lecture des plaques")
    parser.add_argument("--save", dest="save_video", action=argparse.BooleanOptionalAction, default=None,
                        help="enregistre la vidéo annotée")
    add_output_arguments(parser)
    return parser


def _first_frame(source: str):
    if is_image(source):
        return cv2.imread(source)
    capture = cv2.VideoCapture(int(source) if source.isdigit() else source)
    ok, frame = capture.read()
    capture.release()
    return frame if ok else None


def main(argv: list[str] | None = None) -> int:
    args = vars(build_parser().parse_args(argv))
    output_settings = load_output_settings(**pop_output_overrides(args))
    select_static = args.pop("select_static")
    settings = load_settings(**args)

    if select_static:
        from . import static_objects

        path = settings.static_objects_file or Path("zones/objets_statiques.json")
        frame = _first_frame(settings.source)
        if frame is None:
            raise SystemExit(f"Impossible de lire la source : {settings.source}")
        static_objects.select_interactive(frame, path)
        settings.static_objects_file = path

    from .pipeline import Pipeline  # import lourd (torch) après le parsing

    bus = EventBus("distance_vitesse", output_settings)
    pipeline = Pipeline(settings, output_settings, bus)
    print(f"Mode {settings.mode} | modèle {pipeline.model_name} | "
          f"{'GPU' if pipeline.has_gpu else 'CPU'} | source {settings.source}")
    try:
        pipeline.run()
    finally:
        bus.close()
    return 0
