"""Football : ``python -m vision_lab football [setup | <vidéo> --mode MODE] [options]``.

    python -m vision_lab football setup --videos          modèles + vidéos d'exemple
    python -m vision_lab football samples/football/0bfacc_0.mp4 --mode players

Modes : pitch, players, ball, tracking, teams, radar.
État : version minimale branchée sur les sorties communes (fenêtre, web, YouTube, API).
Les modes tracking/teams/radar attendent le remplacement de ``sv.ByteTrack`` (retiré de
supervision 0.31) : voir TODO.md.
"""

from __future__ import annotations

import argparse
from datetime import datetime

from vision_lab.config import add_output_arguments, load_output_settings, pop_output_overrides
from vision_lab.events import EventBus
from vision_lab.outputs import Outputs

MODES = {
    "pitch": "run_pitch_detection",
    "players": "run_player_detection",
    "ball": "run_ball_detection",
    "tracking": "run_player_tracking",
    "teams": "run_team_classification",
    "radar": "run_radar",
}


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or [])
    if argv and argv[0] == "setup":
        from .setup import main as setup

        return setup(argv[1:])

    parser = argparse.ArgumentParser(prog="vision_lab football", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="vidéo de match (caméra fixe type retransmission)")
    parser.add_argument("--mode", choices=list(MODES), default="players")
    parser.add_argument("--device", default=None, help="cuda, cpu, mps (défaut : auto)")
    parser.add_argument("--save", action="store_true", help="enregistre la vidéo annotée")
    add_output_arguments(parser)
    args = vars(parser.parse_args(argv))
    output_settings = load_output_settings(**pop_output_overrides(args))

    import cv2
    import torch

    from . import _upstream_main as soccer

    device = args["device"] or ("cuda" if torch.cuda.is_available() else "cpu")
    capture = cv2.VideoCapture(args["source"])
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    capture.release()

    bus = EventBus("football", output_settings)
    out_dir = output_settings.output_dir / f"football_{args['mode']}_{datetime.now():%Y%m%d_%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = Outputs(output_settings, bus, record_path=out_dir / "annotated.mp4" if args["save"] else None,
                      fps=fps, title=f"Vision Lab - football {args['mode']}")
    generator = getattr(soccer, MODES[args["mode"]])(source_video_path=args["source"], device=device)
    try:
        for index, frame in enumerate(generator):
            bus.update_stats({"mode": args["mode"], "image": index})
            if not outputs.write(frame):
                break
    except KeyboardInterrupt:
        print("Arrêt demandé.")
    finally:
        outputs.close()
        bus.close()
    print(f"Résultats : {out_dir}")
    return 0
