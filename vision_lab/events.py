"""Bus d'événements : ce que voit un projet est publié vers l'API, des webhooks et MQTT.

Un événement ::

    {"project": "traffic", "type": "line_in", "t": 12.4, "ts": "2026-10-26T22:41:03+00:00",
     "data": {"name": "Entrée", "track_id": 12, "label": "Voiture"}}

- ``t`` : temps dans la vidéo (s) ; ``ts`` : horodatage réel (UTC).
- Les statistiques (compteurs courants) sont publiées à part, périodiquement (type ``stats``).

Les envois réseau se font dans un thread dédié : une API lente ou injoignable ne
ralentit jamais l'analyse vidéo (au pire, des événements sont abandonnés et comptés).
"""

from __future__ import annotations

import json
import queue
import threading
import time
import urllib.request
from collections import deque
from datetime import datetime, timezone
from typing import Protocol

from .config import OutputSettings


class Sink(Protocol):
    def send(self, event: dict) -> None: ...
    def close(self) -> None: ...


def make_event(project: str, event_type: str, t: float | None = None, **data) -> dict:
    return {
        "project": project,
        "type": event_type,
        "t": None if t is None else round(float(t), 3),
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data": data,
    }


def _matches(event_type: str, patterns: list[str]) -> bool:
    return any(p == "*" or p == event_type or (p.endswith("*") and event_type.startswith(p[:-1])) for p in patterns)


class WebhookSink:
    """POST JSON vers une ou plusieurs URL (n8n, Node-RED, Zapier, Home Assistant, Discord…)."""

    def __init__(self, urls: list[str], patterns: list[str], token: str | None = None, timeout: float = 5.0):
        self.urls = urls
        self.patterns = patterns or ["*"]
        self.token = token
        self.timeout = timeout

    def send(self, event: dict) -> None:
        if not _matches(event["type"], self.patterns):
            return
        body = json.dumps(event, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json", "User-Agent": "vision-lab"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        for url in self.urls:
            request = urllib.request.Request(url, data=body, headers=headers, method="POST")
            try:
                urllib.request.urlopen(request, timeout=self.timeout).close()
            except Exception as exc:  # un webhook en panne ne doit rien casser
                print(f"[webhook] {url} : {exc}")

    def close(self) -> None:
        pass  # pas de connexion persistante


class MqttSink:
    """Publie ``<prefixe>/<projet>/events/<type>`` et ``<prefixe>/<projet>/stats`` (retenu)."""

    def __init__(self, settings: OutputSettings):
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError("MQTT nécessite paho-mqtt : pip install paho-mqtt") from exc
        self.prefix = settings.mqtt_topic.rstrip("/")
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"vision-lab-{int(time.time())}")
        if settings.mqtt_user:
            self.client.username_pw_set(settings.mqtt_user, settings.mqtt_password)
        if settings.mqtt_tls:
            self.client.tls_set()
        self.client.connect_async(settings.mqtt_host, settings.mqtt_port)
        self.client.loop_start()

    def send(self, event: dict) -> None:
        base = f"{self.prefix}/{event['project']}"
        payload = json.dumps(event, ensure_ascii=False)
        if event["type"] == "stats":
            self.client.publish(f"{base}/stats", payload, qos=0, retain=True)
        else:
            self.client.publish(f"{base}/events/{event['type']}", payload, qos=1)

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()


class EventBus:
    def __init__(self, project: str, settings: OutputSettings | None = None, history: int = 500):
        self.project = project
        self.sinks: list[Sink] = []
        self.recent: deque[dict] = deque(maxlen=history)
        self.stats: dict = {}
        self.dropped = 0
        self._listeners: list = []            # callbacks locaux (API WebSocket)
        self._queue: queue.Queue = queue.Queue(maxsize=1000)
        self._last_stats_push = 0.0
        self._stats_interval = settings.stats_interval_s if settings else 5.0
        if settings:
            if settings.webhook_urls:
                self.sinks.append(WebhookSink(settings.webhook_urls, settings.webhook_events, settings.webhook_token))
            if settings.mqtt_host:
                self.sinks.append(MqttSink(settings))
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def add_listener(self, callback) -> None:
        self._listeners.append(callback)

    def publish(self, event_type: str, t: float | None = None, **data) -> dict:
        event = make_event(self.project, event_type, t, **data)
        self.recent.append(event)
        for callback in self._listeners:
            callback(event)
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            self.dropped += 1
        return event

    def update_stats(self, stats: dict, t: float | None = None, force: bool = False) -> None:
        """Met à jour l'état courant ; le publie au plus toutes les ``stats_interval_s`` secondes."""
        self.stats = stats
        now = time.monotonic()
        if force or now - self._last_stats_push >= self._stats_interval:
            self._last_stats_push = now
            event = make_event(self.project, "stats", t, **stats)
            for callback in self._listeners:
                callback(event)
            try:
                self._queue.put_nowait(event)
            except queue.Full:
                self.dropped += 1

    def _run(self) -> None:
        while True:
            event = self._queue.get()
            if event is None:
                return
            for sink in self.sinks:
                try:
                    sink.send(event)
                except Exception as exc:
                    print(f"[événements] {type(sink).__name__} : {exc}")

    def close(self, timeout: float = 5.0) -> None:
        self._queue.put(None)
        self._worker.join(timeout)
        for sink in self.sinks:
            sink.close()
