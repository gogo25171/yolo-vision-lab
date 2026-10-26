"""Vérification de l'installation : ``python -m vision_lab doctor [projet]``.

Contrôle la version de Python, le GPU, les paquets Python de chaque projet, les
logiciels externes (ffmpeg, git, git-lfs, docker) et la configuration (.env).
Code de sortie 0 si tout l'essentiel est présent, 1 sinon.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import platform
import shutil
import subprocess
import sys
from pathlib import Path

OK, WARN, FAIL = "OK ", "!! ", "XX "

# nom d'import -> nom du paquet pip (pour afficher la version et la commande d'installation)
PIP_NAMES = {
    "cv2": "opencv-python", "dotenv": "python-dotenv", "sklearn": "scikit-learn", "umap": "umap-learn",
    "fast_alpr": "fast-alpr", "paho": "paho-mqtt", "clip": "clip (git+https://github.com/ultralytics/CLIP.git)",
}
CORE_IMPORTS = ("numpy", "cv2", "dotenv", "torch", "ultralytics")
INTEGRATION_IMPORTS = {"fastapi": "API", "uvicorn": "API", "paho": "MQTT", "truststore": "certificats système"}
TOOLS = {
    "ffmpeg": "diffusion YouTube/RTMP, découpe des échantillons",
    "git": "gestion du dépôt",
    "git-lfs": "vidéos d'exemple (samples/)",
    "docker": "exécution en conteneur",
    "nvidia-smi": "diagnostic GPU NVIDIA",
}
MIN_PYTHON = (3, 10)
RECOMMENDED_PYTHON = (3, 14)


def _version(module: str) -> str | None:
    try:
        importlib.import_module(module)
    except Exception:
        return None
    try:
        return importlib.metadata.version(PIP_NAMES.get(module, module).split(" ")[0])
    except importlib.metadata.PackageNotFoundError:
        return "?"


def _line(status: str, label: str, detail: str = "") -> None:
    print(f"  {status}{label:<22} {detail}")


def check_python() -> bool:
    current = sys.version_info[:3]
    text = ".".join(map(str, current))
    if current[:2] < MIN_PYTHON:
        _line(FAIL, "Python", f"{text} (minimum {'.'.join(map(str, MIN_PYTHON))})")
        return False
    status = OK if current[:2] >= RECOMMENDED_PYTHON else WARN
    hint = "" if status == OK else f"(recommandé : {'.'.join(map(str, RECOMMENDED_PYTHON))})"
    _line(status, "Python", f"{text} {platform.system()} {platform.machine()} {hint}")
    return True


def check_gpu() -> None:
    try:
        import torch
    except ImportError:
        _line(FAIL, "PyTorch", "absent : voir docs/guide/prerequis.md")
        return
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        _line(OK, "GPU CUDA", f"{name} ({memory:.0f} Go), torch {torch.__version__}, CUDA {torch.version.cuda}")
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        _line(OK, "GPU Apple (MPS)", f"torch {torch.__version__}")
    else:
        build = "build CPU" if torch.version.cuda is None else f"CUDA {torch.version.cuda} mais aucun GPU visible"
        _line(WARN, "GPU", f"non disponible ({build}) : modes lents, préférez yolo26n")


def check_opencv_gui() -> None:
    """opencv-python-headless (tiré par fast-alpr) écrase la version graphique : plus de fenêtre."""
    try:
        import cv2
    except ImportError:
        return
    gui = [line.split(":", 1)[1].strip() for line in cv2.getBuildInformation().splitlines()
           if line.strip().startswith("GUI:")]
    if gui and gui[0].upper() != "NONE":
        _line(OK, "OpenCV fenêtres", gui[0])
    else:
        _line(WARN, "OpenCV fenêtres", "absentes (version headless) : VIEW=window impossible -> "
              "pip install --force-reinstall --no-deps opencv-python")


def check_imports(modules, label_for_missing: str) -> bool:
    ok = True
    for module in modules:
        version = _version(module)
        if version is None:
            ok = False
            _line(FAIL, module, f"manquant ({label_for_missing}) : pip install {PIP_NAMES.get(module, module)}")
        else:
            _line(OK, module, version)
    return ok


def check_optional(optional: dict[str, str]) -> None:
    for module, feature in optional.items():
        version = _version(module)
        if version is None:
            _line(WARN, module, f"absent : {feature} indisponible (pip install {PIP_NAMES.get(module, module)})")
        else:
            _line(OK, module, f"{version} ({feature})")


def check_tools() -> None:
    for tool, usage in TOOLS.items():
        path = shutil.which(tool)
        if path is None:
            _line(WARN, tool, f"absent ({usage})")
            continue
        try:
            flag = {"nvidia-smi": "-L", "ffmpeg": "-version"}.get(tool, "--version")
            out = subprocess.run([tool, flag], capture_output=True, text=True, timeout=10).stdout.splitlines()
            _line(OK, tool, (out[0] if out else path)[:70])
        except Exception:
            _line(OK, tool, path)


def check_config() -> None:
    if Path(".env").exists():
        _line(OK, ".env", "présent")
    else:
        _line(WARN, ".env", "absent : cp .env.example .env (valeurs par défaut utilisées)")
    samples = Path("samples/videos")
    count = len(list(samples.glob("*.mp4"))) if samples.exists() else 0
    _line(OK if count else WARN, "échantillons", f"{count} vidéo(s)" if count else
          "aucun : python scripts/download_samples.py (ou git lfs pull)")


def main(argv: list[str] | None = None) -> int:
    from projets import PROJECTS

    argv = argv or []
    selected = [PROJECTS[name] for name in argv if name in PROJECTS] or list(PROJECTS.values())

    print("Système")
    essential = check_python()
    check_gpu()
    print("\nSocle (vision_lab)")
    essential &= check_imports(CORE_IMPORTS, "indispensable")
    check_opencv_gui()
    check_optional(INTEGRATION_IMPORTS)
    for info in selected:
        print(f"\nProjet {info.name} — {info.title}")
        project_ok = check_imports([m for m in info.imports if m not in CORE_IMPORTS], f"requis par {info.name}")
        check_optional(info.optional)
        if argv:
            essential &= project_ok
    print("\nLogiciels")
    check_tools()
    print("\nConfiguration")
    check_config()
    print("\n" + ("Tout l'essentiel est présent." if essential else "Des éléments indispensables manquent (XX)."))
    return 0 if essential else 1
