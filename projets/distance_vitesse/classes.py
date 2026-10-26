"""Catalogue des classes suivies et de leurs dimensions réelles.

Ce catalogue reste en Python (et non dans le .env) : c'est de la donnée structurée
qui fait partie du code, alors que le .env ne contient que ce qui change d'une
machine ou d'un déploiement à l'autre.

La distance est estimée à partir de la HAUTEUR réelle de l'objet : contrairement à
la largeur, elle ne dépend presque pas de l'angle de vue (une voiture fait ~1,8 m
de large de face mais ~4,5 m de profil, alors que sa hauteur reste ~1,5 m).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClassInfo:
    label: str                       # nom affiché
    height_m: float | None           # hauteur réelle moyenne (None = pas de distance)
    color: tuple[int, int, int]      # BGR (OpenCV)
    category: str                    # "person" | "vehicle" | "animal" | "other"


# Identifiants COCO (modèles YOLO pré-entraînés standard).
COCO_CLASSES: dict[int, ClassInfo] = {
    0: ClassInfo("Personne", 1.70, (0, 255, 0), "person"),
    1: ClassInfo("Vélo", 1.05, (255, 0, 0), "vehicle"),
    2: ClassInfo("Voiture", 1.50, (0, 0, 255), "vehicle"),
    3: ClassInfo("Moto", 1.30, (255, 255, 0), "vehicle"),
    4: ClassInfo("Avion", None, (128, 0, 128), "vehicle"),
    5: ClassInfo("Bus", 3.10, (255, 0, 255), "vehicle"),
    6: ClassInfo("Train", 4.00, (0, 128, 255), "vehicle"),
    7: ClassInfo("Camion", 3.20, (0, 255, 255), "vehicle"),
    8: ClassInfo("Bateau", None, (255, 128, 0), "vehicle"),
    14: ClassInfo("Oiseau", 0.25, (200, 200, 50), "animal"),
    15: ClassInfo("Chat", 0.30, (180, 105, 255), "animal"),
    16: ClassInfo("Chien", 0.55, (30, 105, 210), "animal"),
    17: ClassInfo("Cheval", 1.60, (19, 69, 139), "animal"),
    18: ClassInfo("Mouton", 0.80, (220, 220, 220), "animal"),
    19: ClassInfo("Vache", 1.40, (60, 60, 60), "animal"),
    20: ClassInfo("Éléphant", 3.00, (130, 130, 130), "animal"),
    21: ClassInfo("Ours", 1.00, (42, 42, 165), "animal"),
    22: ClassInfo("Zèbre", 1.40, (255, 255, 255), "animal"),
    23: ClassInfo("Girafe", 4.80, (0, 200, 255), "animal"),
}

DEFAULT_COLOR = (128, 128, 128)

# Classes sur lesquelles on tente une lecture de plaque.
PLATE_CATEGORIES = {"vehicle"}
PLATE_LABELS_EXCLUDED = {"Vélo", "Avion", "Bateau", "Train"}

# Palette utilisée pour les classes en vocabulaire ouvert (YOLOE).
_OPEN_VOCAB_PALETTE = [
    (0, 255, 0), (0, 0, 255), (255, 0, 0), (0, 255, 255), (255, 0, 255),
    (255, 255, 0), (0, 128, 255), (128, 0, 255), (255, 128, 0), (0, 200, 120),
]


def parse_open_vocab(spec: str) -> dict[int, ClassInfo]:
    """Construit un catalogue à partir de OPEN_VOCAB_CLASSES.

    Format : ``"enfant:1.2, adulte:1.7, poussette:1.0, chien:0.55, trottinette"``.
    La hauteur (en mètres) est optionnelle ; sans elle, pas de distance pour la classe.
    La catégorie est déduite de mots-clés simples (utile pour les plaques).
    """
    catalog: dict[int, ClassInfo] = {}
    for index, raw in enumerate(item.strip() for item in spec.split(",") if item.strip()):
        name, _, height = raw.partition(":")
        name = name.strip()
        catalog[index] = ClassInfo(
            label=name,
            height_m=float(height) if height.strip() else None,
            color=_OPEN_VOCAB_PALETTE[index % len(_OPEN_VOCAB_PALETTE)],
            category=_guess_category(name),
        )
    return catalog


_VEHICLE_WORDS = ("car", "truck", "bus", "van", "motorcycle", "voiture", "camion", "moto", "fourgon", "taxi")


def _guess_category(name: str) -> str:
    lowered = name.lower()
    if any(word in lowered for word in _VEHICLE_WORDS):
        return "vehicle"
    return "other"


def supports_plates(info: ClassInfo) -> bool:
    return info.category in PLATE_CATEGORIES and info.label not in PLATE_LABELS_EXCLUDED
