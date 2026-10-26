"""Affichage du résultat : fenêtre OpenCV, page web (MJPEG) ou rien (headless/Docker)."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

_PAGE = b"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Traffic Vision</title>
<style>body{margin:0;background:#111;color:#eee;font-family:system-ui,sans-serif;text-align:center}
img{max-width:100%;height:auto}</style></head>
<body><img src="/stream" alt="flux annote"></body></html>"""


class _MjpegServer:
    def __init__(self, host: str, port: int):
        self._frame: bytes | None = None
        self._condition = threading.Condition()
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # silence
                pass

            def do_GET(self):
                if self.path == "/":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(_PAGE)
                    return
                if self.path != "/stream":
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.end_headers()
                try:
                    while True:
                        with server._condition:
                            server._condition.wait(timeout=5)
                            frame = server._frame
                        if frame is None:
                            continue
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
                except (BrokenPipeError, ConnectionResetError):
                    pass

        self._httpd = ThreadingHTTPServer((host, port), Handler)
        self._httpd.daemon_threads = True
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()

    def push(self, frame: np.ndarray) -> None:
        ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            with self._condition:
                self._frame = jpeg.tobytes()
                self._condition.notify_all()

    def close(self) -> None:
        self._httpd.shutdown()


class Viewer:
    def __init__(self, kind: str, host: str = "0.0.0.0", port: int = 8080, title: str = "Traffic Vision"):
        if kind not in {"window", "web", "none"}:
            raise ValueError(f"VIEW invalide : {kind!r} (window | web | none)")
        self.kind = kind
        self.title = title
        self._server = _MjpegServer(host, port) if kind == "web" else None
        if self._server:
            print(f"Flux annoté : http://localhost:{port}")

    def show(self, frame: np.ndarray, wait_ms: int = 1) -> bool:
        """Affiche l'image ; renvoie False si l'utilisateur demande l'arrêt (touche q / Échap)."""
        if self.kind == "window":
            cv2.imshow(self.title, frame)
            key = cv2.waitKey(wait_ms) & 0xFF
            return key not in (ord("q"), 27)
        if self._server:
            self._server.push(frame)
        return True

    def close(self) -> None:
        if self.kind == "window":
            cv2.destroyAllWindows()
        if self._server:
            self._server.close()
