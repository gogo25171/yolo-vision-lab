"""Réglages du projet trafic (le .env est partagé avec les autres projets).

Priorité : arguments CLI > variables d'environnement > fichier .env > préréglage du mode.
Affichage, enregistrement, diffusion et intégrations : voir ``vision_lab.config``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from vision_lab.config import env, env_bool, env_float, env_int, env_list, resolve_model_path

# Préréglages : "fast" pour le temps réel (CCTV, webcam), "accurate" pour le
# traitement hors ligne de vidéos enregistrées (on prend le temps qu'il faut).
PRESETS = {
    "fast": {
        "model": "yolo26s.pt",       # remplacé par yolo26n.pt sans GPU
        "model_cpu": "yolo26n.pt",
        "open_vocab_model": "yoloe-26s-seg.pt",
        "imgsz": 640,
        "tracker": "bytetrack.yaml",
        "plate_every": 15,           # tentative de lecture de plaque toutes les N images par objet
        "drop_frames": True,         # flux live : on traite toujours l'image la plus récente
        "save_video": False,
    },
    "accurate": {
        "model": "yolo26x.pt",
        "model_cpu": "yolo26x.pt",
        "open_vocab_model": "yoloe-26l-seg.pt",
        "imgsz": 1280,
        "tracker": "botsort.yaml",
        "plate_every": 3,
        "drop_frames": False,        # chaque image est traitée
        "save_video": True,
    },
}


@dataclass
class Settings:
    mode: str = "fast"
    source: str = "0"

    # Modèle / inférence
    model: str | None = None              # None = préréglage du mode
    imgsz: int | None = None
    conf: float = 0.35
    device: str | None = None             # None = auto (GPU si dispo)
    half: bool | None = None              # None = auto (FP16 si GPU)
    tracker: str | None = None
    open_vocab_classes: str | None = None  # active YOLOE (vocabulaire ouvert)

    # Mesures
    camera_hfov_deg: float = 70.0
    focal_length_px: float | None = None
    calibration_file: Path | None = None  # homographie sol -> mètres (vitesse précise)
    speed_window_s: float = 1.0

    # Plaques
    plates_enabled: bool = True
    plate_detector_model: str = "yolo-v9-t-384-license-plate-end2end"
    plate_ocr_model: str = "cct-s-v2-global-model"
    plate_every: int | None = None
    plate_min_vehicle_px: int = 80        # hauteur mini du véhicule pour tenter une lecture
    plate_device: str = "cpu"             # cpu | cuda (onnxruntime-gpu requis)
    plate_countries: list[str] | None = None  # formats testés si l'OCR ne prédit pas de pays

    # Zones et objets statiques
    zones_file: Path | None = None
    static_objects_file: Path | None = None

    # Rendu
    labels: str = "auto"                  # auto | full | compact
    save_video: bool | None = None
    drop_frames: bool | None = None

    # --- valeurs résolues -------------------------------------------------
    def preset(self) -> dict:
        return PRESETS[self.mode]

    def resolved_model(self, has_gpu: bool) -> str:
        preset = self.preset()
        if self.model:
            name = self.model
        elif self.open_vocab_classes:
            name = preset["open_vocab_model"]
        else:
            name = preset["model"] if has_gpu else preset["model_cpu"]
        return resolve_model_path(name)

    def resolved(self, key: str):
        value = getattr(self, key)
        return self.preset()[key] if value is None else value


def load_settings(**overrides) -> Settings:
    """Lit les variables (le .env doit déjà être chargé : ``core.config.load_env``)."""
    mode = (overrides.get("mode") or env("MODE", "fast") or "fast").lower()
    if mode not in PRESETS:
        raise ValueError(f"MODE invalide : {mode!r} (attendu : {', '.join(PRESETS)})")

    calibration = env("CALIBRATION_FILE")
    zones = env("ZONES_FILE")
    settings = Settings(
        mode=mode,
        source=env("SOURCE", "0"),
        model=env("MODEL"),
        imgsz=env_int("IMGSZ", None),
        conf=env_float("CONF", 0.35),
        device=env("DEVICE"),
        half=env_bool("HALF", None),
        tracker=env("TRACKER"),
        open_vocab_classes=env("OPEN_VOCAB_CLASSES"),
        camera_hfov_deg=env_float("CAMERA_HFOV_DEG", 70.0),
        focal_length_px=env_float("FOCAL_LENGTH_PX", None),
        calibration_file=Path(calibration) if calibration else None,
        speed_window_s=env_float("SPEED_WINDOW_S", 1.0),
        plates_enabled=env_bool("PLATES_ENABLED", True),
        plate_detector_model=env("PLATE_DETECTOR_MODEL", "yolo-v9-t-384-license-plate-end2end"),
        plate_ocr_model=env("PLATE_OCR_MODEL", "cct-s-v2-global-model"),
        plate_every=env_int("PLATE_EVERY", None),
        plate_min_vehicle_px=env_int("PLATE_MIN_VEHICLE_PX", 80),
        plate_device=(env("PLATE_DEVICE", "cpu") or "cpu").lower(),
        plate_countries=env_list("PLATE_COUNTRIES", "France"),
        zones_file=Path(zones) if zones else None,
        static_objects_file=Path(static) if (static := env("STATIC_OBJECTS_FILE")) else None,
        labels=(env("LABELS", "auto") or "auto").lower(),
        save_video=env_bool("SAVE_VIDEO", None),
        drop_frames=env_bool("DROP_FRAMES", None),
    )
    overrides["mode"] = mode
    return replace(settings, **{key: value for key, value in overrides.items() if value is not None})
