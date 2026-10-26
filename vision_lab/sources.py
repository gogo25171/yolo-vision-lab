"""Ouverture des sources : webcam, flux réseau (RTSP/HTTP), fichier vidéo ou image."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def is_image(source: str) -> bool:
    return Path(source).suffix.lower() in IMAGE_EXTENSIONS


def is_live(source: str) -> bool:
    return source.isdigit() or source.lower().startswith(("rtsp://", "rtmp://", "http://", "https://", "udp://"))


class VideoSource:
    """Itère sur ``(image, horodatage_en_secondes)``.

    - Fichier : chaque image, horodatage = index / FPS (indépendant de la vitesse de calcul).
    - Live + ``drop_frames`` : un thread lit en continu et on ne garde que la dernière
      image, pour ne jamais accumuler de retard sur un flux CCTV.
    """

    def __init__(self, source: str, drop_frames: bool):
        self.source = source
        self.live = is_live(source)
        self._cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
        if not self._cap.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la source : {source}")
        self.fps = self._cap.get(cv2.CAP_PROP_FPS) or 25.0
        if not 1 <= self.fps <= 240:
            self.fps = 25.0
        self.frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT)) if not self.live else 0
        self.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self._threaded = self.live and drop_frames
        self._latest: tuple[np.ndarray, float] | None = None
        self._lock = threading.Lock()
        self._new_frame = threading.Event()
        self._stopped = False
        self._start = time.monotonic()
        if self._threaded:
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        while not self._stopped:
            ok, frame = self._cap.read()
            if not ok:
                self._stopped = True
                self._new_frame.set()
                break
            with self._lock:
                self._latest = (frame, time.monotonic() - self._start)
            self._new_frame.set()

    def __iter__(self):
        if self._threaded:
            while True:
                self._new_frame.wait(timeout=5)
                self._new_frame.clear()
                with self._lock:
                    item, self._latest = self._latest, None
                if item is None:
                    if self._stopped:
                        return
                    continue
                yield item
        else:
            index = 0
            while True:
                ok, frame = self._cap.read()
                if not ok:
                    return
                timestamp = time.monotonic() - self._start if self.live else index / self.fps
                index += 1
                yield frame, timestamp

    def release(self) -> None:
        self._stopped = True
        self._cap.release()
