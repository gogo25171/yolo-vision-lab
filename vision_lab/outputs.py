"""Sorties vidéo communes : affichage, enregistrement, diffusion en direct (RTMP/YouTube), API.

Un projet n'a qu'à appeler ``outputs.write(image_annotée)`` pour chaque image : tout le
reste (fenêtre, page web, fichier, YouTube, flux MJPEG de l'API) est géré ici.
"""

from __future__ import annotations

import shutil
import subprocess
import threading
import time
from pathlib import Path

import cv2
import numpy as np

from .config import OutputSettings
from .events import EventBus
from .view import Viewer


class FrameHub:
    """Dernière image annotée (JPEG), partagée avec l'API."""

    def __init__(self):
        self._jpeg: bytes | None = None
        self._condition = threading.Condition()

    def push(self, frame: np.ndarray) -> None:
        ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            with self._condition:
                self._jpeg = jpeg.tobytes()
                self._condition.notify_all()

    def latest(self) -> bytes | None:
        return self._jpeg

    def wait(self, timeout: float = 5.0) -> bytes | None:
        with self._condition:
            self._condition.wait(timeout)
            return self._jpeg


class _ConstantRate:
    """Réémet la dernière image reçue à cadence fixe (flux live, YouTube : FPS constant obligatoire)."""

    def __init__(self, fps: float, consumer):
        self.fps = fps
        self._consumer = consumer
        self._frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._stopped = False
        threading.Thread(target=self._run, daemon=True).start()

    def push(self, frame: np.ndarray) -> None:
        with self._lock:
            self._frame = frame

    def _run(self) -> None:
        period = 1.0 / self.fps
        next_tick = time.monotonic()
        while not self._stopped:
            with self._lock:
                frame = self._frame
            if frame is not None:
                self._consumer(frame)
            next_tick += period
            time.sleep(max(0.0, next_tick - time.monotonic()))

    def stop(self) -> None:
        self._stopped = True


class RtmpStreamer:
    """Envoie la vidéo annotée vers un serveur RTMP/SRT via ffmpeg (H.264 + piste audio muette).

    YouTube : ``rtmp://a.rtmp.youtube.com/live2/<clé de flux>`` ; Twitch :
    ``rtmp://live.twitch.tv/app/<clé>`` ; ou un fichier .flv/.mp4 pour tester.
    """

    def __init__(self, url: str, width: int, height: int, fps: float, bitrate: str):
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("La diffusion nécessite ffmpeg dans le PATH")
        fmt = "flv" if url.startswith(("rtmp://", "rtmps://")) or url.endswith(".flv") else None
        gop = str(int(fps * 2))
        cmd = [
            ffmpeg, "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency", "-pix_fmt", "yuv420p",
            "-g", gop, "-b:v", bitrate, "-maxrate", bitrate, "-bufsize", bitrate,
            "-c:a", "aac", "-b:a", "128k", "-shortest",
        ]
        if fmt:
            cmd += ["-f", fmt]
        cmd.append(url)
        self.size = (width, height)
        self._process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self._feeder = _ConstantRate(fps, self._write)

    def _write(self, frame: np.ndarray) -> None:
        if frame.shape[1::-1] != self.size:
            frame = cv2.resize(frame, self.size)
        try:
            self._process.stdin.write(frame.tobytes())
        except OSError:  # BrokenPipeError inclus
            self._feeder.stop()
            print("[diffusion] ffmpeg s'est arrêté (URL ou clé de flux invalide ?)")

    def push(self, frame: np.ndarray) -> None:
        self._feeder.push(frame)

    def close(self) -> None:
        self._feeder.stop()
        time.sleep(1.0 / self._feeder.fps)
        if self._process.stdin:
            self._process.stdin.close()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()


class Recorder:
    """Enregistre la vidéo annotée. Source live : cadence constante (durée réelle respectée)."""

    def __init__(self, path: Path, fps: float, live: bool):
        self.path = path
        self.fps = fps
        self.live = live
        self._writer: cv2.VideoWriter | None = None
        self._feeder = _ConstantRate(fps, self._write) if live else None

    def _write(self, frame: np.ndarray) -> None:
        if self._writer is None:
            height, width = frame.shape[:2]
            self._writer = cv2.VideoWriter(str(self.path), cv2.VideoWriter_fourcc(*"mp4v"), self.fps, (width, height))
        self._writer.write(frame)

    def push(self, frame: np.ndarray) -> None:
        if self._feeder:
            self._feeder.push(frame)
        else:
            self._write(frame)

    def close(self) -> None:
        if self._feeder:
            self._feeder.stop()
            time.sleep(2 / self.fps)  # laisse le thread terminer l'écriture en cours
        if self._writer is not None:
            self._writer.release()


class Outputs:
    """Regroupe toutes les sorties d'un projet ; ``write`` renvoie False si l'utilisateur quitte."""

    def __init__(self, settings: OutputSettings, bus: EventBus | None = None, *,
                 record_path: Path | None = None, fps: float = 25.0, live: bool = False, title: str = "Vision Lab"):
        self.settings = settings
        self.bus = bus
        self.viewer = Viewer(settings.view, settings.web_host, settings.web_port, title=title)
        self.recorder = Recorder(record_path, fps, live) if record_path else None
        self.streamer: RtmpStreamer | None = None
        self.hub = FrameHub() if settings.api_enabled else None
        self.api = None
        if self.hub is not None:
            from .api import start_api

            self.api = start_api(settings, self.hub, bus)

    def write(self, frame: np.ndarray) -> bool:
        if self.settings.stream_url and self.streamer is None:
            height, width = frame.shape[:2]
            self.streamer = RtmpStreamer(self.settings.stream_url, width, height,
                                         self.settings.stream_fps, self.settings.stream_bitrate)
            print("Diffusion en direct démarrée")
        if self.streamer:
            self.streamer.push(frame)
        if self.recorder:
            self.recorder.push(frame)
        if self.hub:
            self.hub.push(frame)
        return self.viewer.show(frame)

    def close(self) -> None:
        if self.streamer:
            self.streamer.close()
        if self.recorder:
            self.recorder.close()
        self.viewer.close()
        if self.api:
            self.api.stop()
