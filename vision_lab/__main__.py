"""Point d'entrée du laboratoire.

    python -m vision_lab                         liste des projets
    python -m vision_lab doctor [projet]         vérifie l'installation (Python, GPU, paquets, logiciels)
    python -m vision_lab zones <source>          éditeur de zones (commun à tous les projets)
    python -m vision_lab <projet> [options]      lance un projet (--help pour ses options)

Option globale (avant le nom du projet) : ``--env FICHIER`` (défaut : .env).
"""

from __future__ import annotations

import importlib
import sys

from .certs import use_system_certificates
from .config import load_env


def _list_projects() -> None:
    from projets import PROJECTS

    print("Projets disponibles :\n")
    for info in PROJECTS.values():
        print(f"  {info.name:<18} {info.title} — {info.summary}")
    print("\nUsage : python -m vision_lab <projet> --help")
    print("        python -m vision_lab doctor [projet]")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    env_file = None
    if len(argv) >= 2 and argv[0] == "--env":
        env_file, argv = argv[1], argv[2:]
    load_env(env_file)
    use_system_certificates()

    if not argv or argv[0] in {"list", "-h", "--help"}:
        print(__doc__)
        _list_projects()
        return 0

    command, rest = argv[0], argv[1:]
    if command == "doctor":
        from .doctor import main as doctor

        return doctor(rest)
    if command == "zones":
        from .zone_editor import main as zone_editor

        return zone_editor(rest)

    from projets import PROJECTS

    info = PROJECTS.get(command)
    if info is None:
        print(f"Projet inconnu : {command!r}\n")
        _list_projects()
        return 2
    module = importlib.import_module(info.module)
    return module.main(rest)


if __name__ == "__main__":
    sys.exit(main())
