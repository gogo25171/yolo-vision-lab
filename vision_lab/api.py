"""API REST + WebSocket + MJPEG pour récupérer en direct ce que voit un projet.

| Route | Description |
|---|---|
| ``GET /`` | Page de visualisation (flux + statistiques + derniers événements) |
| ``GET /api/status`` | Projet, état, nombre d'événements |
| ``GET /api/stats`` | Dernières statistiques (compteurs, zones…) |
| ``GET /api/events?type=line_*&limit=50`` | Derniers événements |
| ``WS  /ws`` | Événements et statistiques poussés en temps réel (JSON) |
| ``GET /stream.mjpg`` | Flux vidéo annoté (MJPEG, lisible par VLC, Home Assistant, ``<img>``) |
| ``GET /snapshot.jpg`` | Dernière image annotée |

Documentation interactive : ``/docs`` (Swagger). Si ``API_TOKEN`` est défini, chaque
requête doit fournir ``Authorization: Bearer <token>`` (ou ``?token=`` pour le flux et le WebSocket).
"""

from __future__ import annotations

import asyncio
import fnmatch
import threading
import time

# Import au niveau du module : FastAPI résout les annotations (Request, WebSocket…) dans les
# globales du module ; importés dans une fonction, ils seraient pris pour des paramètres.
try:
    from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, Response, StreamingResponse
except ImportError as exc:  # le module n'est importé que si API_ENABLED
    raise RuntimeError("L'API nécessite FastAPI : pip install fastapi uvicorn") from exc

from .config import OutputSettings
from .events import EventBus

_PAGE = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Vision Lab</title>
<style>
body{margin:0;font-family:system-ui,sans-serif;background:#111;color:#eee}
main{display:grid;grid-template-columns:minmax(0,3fr) minmax(260px,1fr);gap:12px;padding:12px}
@media(max-width:800px){main{grid-template-columns:1fr}}
img{width:100%;border-radius:6px;background:#000}
pre{background:#1d1d1d;padding:8px;border-radius:6px;overflow:auto;max-height:40vh;font-size:12px}
h2{font-size:14px;margin:8px 0}
</style></head><body><main>
<div><img src="stream.mjpg{token}" alt="flux annoté"></div>
<div><h2>Statistiques</h2><pre id="stats">…</pre><h2>Événements</h2><pre id="events"></pre></div>
</main><script>
const ws = new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws{token}');
const events=[];
ws.onmessage = (m) => { const e = JSON.parse(m.data);
  if (e.type === 'stats') { document.getElementById('stats').textContent = JSON.stringify(e.data, null, 2); return; }
  events.unshift(e.t + 's  ' + e.type + '  ' + JSON.stringify(e.data)); events.length = Math.min(events.length, 50);
  document.getElementById('events').textContent = events.join('\\n'); };
</script></body></html>"""


class ApiServer:
    def __init__(self, server, thread):
        self._server = server
        self._thread = thread

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5)


def create_app(settings: OutputSettings, hub, bus: EventBus | None):
    app = FastAPI(title="YOLO Vision Lab", description="Événements, statistiques et flux vidéo en direct.")
    started = time.time()
    websockets: set = set()
    loop_holder: dict = {}

    def check_token(request: Request, token: str | None = Query(default=None)) -> None:
        if not settings.api_token:
            return
        header = request.headers.get("authorization", "")
        if header == f"Bearer {settings.api_token}" or token == settings.api_token:
            return
        raise HTTPException(status_code=401, detail="Jeton manquant ou invalide")

    auth = [Depends(check_token)]
    token_qs = f"?token={settings.api_token}" if settings.api_token else ""

    @app.get("/", response_class=HTMLResponse, dependencies=auth)
    def index():
        return _PAGE.replace("{token}", token_qs)

    @app.get("/api/status", dependencies=auth)
    def status():
        return {
            "project": bus.project if bus else None,
            "uptime_s": round(time.time() - started),
            "events": len(bus.recent) if bus else 0,
            "dropped_events": bus.dropped if bus else 0,
        }

    @app.get("/api/stats", dependencies=auth)
    def stats():
        return bus.stats if bus else {}

    @app.get("/api/events", dependencies=auth)
    def events(type: str = "*", limit: int = Query(default=100, le=500)):  # noqa: A002 - nom public de l'API
        items = [e for e in (bus.recent if bus else []) if fnmatch.fnmatch(e["type"], type)]
        return items[-limit:]

    @app.get("/snapshot.jpg", dependencies=auth)
    def snapshot():
        jpeg = hub.latest()
        if jpeg is None:
            raise HTTPException(status_code=503, detail="Pas encore d'image")
        return Response(jpeg, media_type="image/jpeg")

    @app.get("/stream.mjpg", dependencies=auth)
    def stream():
        def frames():
            while True:
                jpeg = hub.wait(timeout=5)
                if jpeg:
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"

        return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket, token: str | None = None):
        if settings.api_token and token != settings.api_token:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        loop_holder["loop"] = asyncio.get_running_loop()
        websockets.add(websocket)
        try:
            if bus and bus.stats:
                await websocket.send_json({"type": "stats", "data": bus.stats, "t": None})
            while True:
                await websocket.receive_text()   # garde la connexion ouverte
        except WebSocketDisconnect:
            pass
        finally:
            websockets.discard(websocket)

    def broadcast(event: dict) -> None:
        loop = loop_holder.get("loop")
        if loop is None:
            return
        for websocket in list(websockets):
            asyncio.run_coroutine_threadsafe(websocket.send_json(event), loop)

    if bus is not None:
        bus.add_listener(broadcast)
    return app


def start_api(settings: OutputSettings, hub, bus: EventBus | None) -> ApiServer:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("L'API nécessite uvicorn : pip install fastapi uvicorn") from exc
    app = create_app(settings, hub, bus)
    config = uvicorn.Config(app, host=settings.api_host, port=settings.api_port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    print(f"API : http://localhost:{settings.api_port}  (documentation : /docs)")
    return ApiServer(server, thread)
