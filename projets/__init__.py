"""Projets du laboratoire. Chaque projet est un dossier autonome (README, prérequis, code).

Pour ajouter un projet : créer ``projets/<nom>/`` avec un module ``cli.py`` exposant
``main(argv) -> int``, puis l'enregistrer ci-dessous (voir docs/projet/nouveau-projet.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectInfo:
    name: str
    title: str
    module: str                                   # module exposant main(argv)
    summary: str
    imports: tuple[str, ...] = ()                 # paquets Python requis (vérifiés par « doctor »)
    tools: tuple[str, ...] = ()                   # logiciels externes requis
    optional: dict[str, str] = field(default_factory=dict)  # paquet -> fonctionnalité


PROJECTS: dict[str, ProjectInfo] = {
    "distance_vitesse": ProjectInfo(
        name="distance_vitesse",
        title="Distance & vitesse",
        module="projets.distance_vitesse.cli",
        summary="Distance et vitesse des objets, objets statiques, plaques d'immatriculation, zones de comptage.",
        imports=("torch", "ultralytics", "cv2", "numpy", "dotenv", "lap"),
        optional={"fast_alpr": "plaques d'immatriculation", "clip": "vocabulaire ouvert (YOLOE)"},
    ),
    "solutions": ProjectInfo(
        name="solutions",
        title="Solutions Ultralytics",
        module="projets.solutions.cli",
        summary="Les solutions officielles Ultralytics : comptage, heatmap, file d'attente, parking, sport, floutage…",
        imports=("torch", "ultralytics", "cv2", "numpy", "dotenv"),
        optional={"shapely": "régions (comptage, file d'attente)"},
    ),
    "football": ProjectInfo(
        name="football",
        title="Football (Soccer AI)",
        module="projets.football.cli",
        summary="Joueurs, ballon, arbitres, équipes et vue radar du terrain (d'après roboflow/sports).",
        imports=("torch", "ultralytics", "cv2", "numpy", "supervision", "transformers", "umap", "sklearn"),
        optional={"gdown": "téléchargement des modèles et vidéos d'exemple"},
    ),
}
