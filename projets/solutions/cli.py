"""Solutions Ultralytics : ``python -m vision_lab solutions <solution> <source> [options]``.

Chaque solution officielle (comptage, heatmap, file d'attente, parking, sport…) est
branchée sur les sorties communes du laboratoire : fenêtre/web, enregistrement,
diffusion YouTube, API, webhooks et MQTT. Les zones se dessinent avec
``python -m vision_lab zones`` (même format pour tous les projets).

Exemples ::

    python -m vision_lab solutions count samples/videos/roundabout.mp4 --zones zones/roundabout.json
    python -m vision_lab solutions heatmap samples/videos/crosswalk_toronto.mp4
    python -m vision_lab solutions workout 0 --arg kpts=6,8,10
    python -m vision_lab solutions blur samples/videos/street_ljubljana.mp4 --classes 0
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from vision_lab.config import add_output_arguments, load_output_settings, pop_output_overrides, resolve_model_path
from vision_lab.events import EventBus
from vision_lab.outputs import Outputs
from vision_lab.sources import VideoSource

# nom -> (classe Ultralytics, modèle par défaut, type de région attendu, description)
SOLUTIONS = {
    "count": ("ObjectCounter", "yolo26n.pt", "line_or_zone", "comptage par ligne ou zone (entrées/sorties)"),
    "region": ("RegionCounter", "yolo26n.pt", "zones", "comptage dans plusieurs zones"),
    "heatmap": ("Heatmap", "yolo26n.pt", "optional", "carte de chaleur des passages"),
    "speed": ("SpeedEstimator", "yolo26n.pt", "none", "vitesse (meter_per_pixel à régler)"),
    "queue": ("QueueManager", "yolo26n.pt", "zone", "longueur de file d'attente"),
    "parking": ("ParkingManagement", "yolo26n.pt", "none", "places libres/occupées (json_file requis)"),
    "trackzone": ("TrackZone", "yolo26n.pt", "zone", "suivi limité à une zone"),
    "workout": ("AIGym", "yolo26n-pose.pt", "none", "répétitions d'exercices (pose)"),
    "blur": ("ObjectBlurrer", "yolo26n.pt", "none", "floutage des objets (RGPD)"),
    "crop": ("ObjectCropper", "yolo26n.pt", "none", "extraction des objets détectés"),
    "isegment": ("InstanceSegmentation", "yolo26n-seg.pt", "none", "segmentation d'instances"),
    "visioneye": ("VisionEye", "yolo26n.pt", "none", "lignes de visée depuis un point"),
    "analytics": ("Analytics", "yolo26n.pt", "none", "graphiques (line, bar, pie, area)"),
    "security": ("SecurityAlarm", "yolo26n.pt", "none", "alarme par e-mail au-delà d'un seuil"),
    "distance": ("DistanceCalculation", "yolo26n.pt", "none", "distance entre deux objets (clic)"),
}
# Champs de SolutionResults transformés en événements quand ils changent.
EVENT_FIELDS = ("in_count", "out_count", "queue_count", "filled_slots", "available_slots", "email_sent")


def _parse_value(text: str):
    for cast in (int, float):
        try:
            return cast(text)
        except ValueError:
            pass
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if "," in text:
        return [_parse_value(part) for part in text.split(",")]
    return text


def _regions(path: Path | None, kind: str, width: int, height: int):
    if path is None or kind == "none":
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    def pixels(points):
        return [(int(x * width), int(y * height)) if x <= 1 and y <= 1 else (int(x), int(y)) for x, y in points]

    if kind == "zones":
        return {zone["name"]: pixels(zone["polygon"]) for zone in data.get("zones", [])}
    if kind in {"line_or_zone", "optional"} and data.get("lines"):
        return pixels(data["lines"][0]["points"])
    if data.get("zones"):
        return pixels(data["zones"][0]["polygon"])
    return None


def _stats(results) -> dict:
    stats = {}
    for key, value in vars(results).items():
        if key in {"plot_im", "speed"} or value is None or value in ([], {}):
            continue
        if isinstance(value, (int, float, str, bool, list, dict)):
            stats[key] = value
    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vision_lab solutions", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("solution", choices=sorted(SOLUTIONS), help="solution Ultralytics à lancer")
    parser.add_argument("source", help="fichier vidéo, URL RTSP/HTTP ou index webcam")
    parser.add_argument("--model", help="poids (défaut selon la solution, ex. yolo26n.pt / yolo26n-pose.pt)")
    parser.add_argument("--zones", type=Path, help="zones/lignes (python -m vision_lab zones)")
    parser.add_argument("--classes", help="identifiants COCO à garder, ex. 0,2 (personnes, voitures)")
    parser.add_argument("--arg", action="append", default=[], metavar="CLÉ=VALEUR",
                        help="paramètre de la solution, ex. meter_per_pixel=0.04, kpts=6,8,10, json_file=…")
    parser.add_argument("--save", action="store_true", help="enregistre la vidéo annotée")
    add_output_arguments(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    from ultralytics import solutions

    args = vars(build_parser().parse_args(argv))
    output_settings = load_output_settings(**pop_output_overrides(args))
    name = args["solution"]
    class_name, default_model, region_kind, _ = SOLUTIONS[name]

    capture = VideoSource(args["source"], drop_frames=True)
    kwargs = {"model": resolve_model_path(args["model"] or default_model), "show": False, "verbose": False}
    if args["classes"]:
        kwargs["classes"] = [int(c) for c in args["classes"].split(",")]
    region = _regions(args["zones"], region_kind, capture.width, capture.height)
    if region:
        kwargs["region"] = region
    for item in args["arg"]:
        key, _, value = item.partition("=")
        kwargs[key.strip()] = _parse_value(value.strip())
    if name == "workout":
        kwargs.setdefault("kpts", [6, 8, 10])

    solution = getattr(solutions, class_name)(**kwargs)
    bus = EventBus(f"solutions/{name}", output_settings)
    out_dir = output_settings.output_dir / f"{name}_{datetime.now():%Y%m%d_%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = Outputs(output_settings, bus, record_path=out_dir / "annotated.mp4" if args["save"] else None,
                      fps=capture.fps, live=capture.live, title=f"Vision Lab - {name}")

    previous: dict = {}
    last_log = time.monotonic()
    try:
        for index, (frame, timestamp) in enumerate(capture):
            results = solution(frame)
            stats = _stats(results)
            for key in EVENT_FIELDS:
                if key in stats and previous.get(key) not in (None, stats[key]):
                    bus.publish(key, timestamp, old=previous[key], new=stats[key])
            previous = stats
            bus.update_stats(stats, timestamp)
            if not outputs.write(results.plot_im):
                break
            if output_settings.view == "none" and time.monotonic() - last_log > 2:
                print(f"image {index + 1} - {stats}")
                last_log = time.monotonic()
    except KeyboardInterrupt:
        print("Arrêt demandé.")
    finally:
        capture.release()
        outputs.close()
        bus.update_stats(previous, force=True)
        (out_dir / "summary.json").write_text(
            json.dumps({"solution": name, "source": args["source"], **previous}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        bus.close()
    print(f"Résultats : {out_dir}")
    return 0
