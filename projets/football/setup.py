"""Téléchargement des modèles et vidéos d'exemple : ``python -m vision_lab football setup [--videos]``.

Les modèles (YOLOv8 entraînés par Roboflow sur les données DFL Bundesliga) et les vidéos
sont hébergés sur Google Drive par le projet roboflow/sports.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from vision_lab.config import env

MODELS = {
    "football-player-detection.pt": "17PXFNlx-jI7VjVo_vQnB1sONjRyvoB-q",
    "football-ball-detection.pt": "1isw4wx-MK9h9LMr36VvIWlJD6ppUvw7V",
    "football-pitch-detection.pt": "1Ma5Kt86tgpdjCTKfum79YMgNnSjcoOyf",
}
# Extraits du « DFL - Bundesliga Data Shootout » (Kaggle) : usage de test uniquement, ne pas redistribuer.
VIDEOS = {
    "0bfacc_0.mp4": "12TqauVZ9tLAv8kWxTTBFWtgt2hNQ4_ZF",
    "2e57b9_0.mp4": "19PGw55V8aA6GZu5-Aac5_9mCy3fNxmEf",
    "08fd33_0.mp4": "1OG8K6wqUw9t7lp9ms1M48DxRhwTYciK-",
    "573e61_0.mp4": "1yYPKuXbHsCxqjA9G-S6aeR2Kcnos8RPU",
    "121364_0.mp4": "1vVwjW1dE1drIdd4ZSILfbCGPD4weoNiu",
}


def models_dir() -> Path:
    return Path(env("MODELS_DIR", "models")) / "football"


def videos_dir() -> Path:
    return Path("samples") / "football"


def _download(files: dict[str, str], folder: Path, force: bool) -> None:
    try:
        import gdown
    except ImportError as exc:
        raise SystemExit("gdown est requis : pip install gdown") from exc
    folder.mkdir(parents=True, exist_ok=True)
    for name, file_id in files.items():
        target = folder / name
        if target.exists() and not force:
            print(f"  déjà présent : {target}")
            continue
        gdown.download(id=file_id, output=str(target), quiet=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vision_lab football setup", description=__doc__)
    parser.add_argument("--videos", action="store_true", help="télécharge aussi les 5 vidéos d'exemple (~200 Mo)")
    parser.add_argument("--force", action="store_true", help="retélécharge les fichiers existants")
    args = parser.parse_args(argv)
    print(f"Modèles -> {models_dir()}")
    _download(MODELS, models_dir(), args.force)
    if args.videos:
        print(f"Vidéos -> {videos_dir()}")
        _download(VIDEOS, videos_dir(), args.force)
    return 0
