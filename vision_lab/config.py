"""Réglages communs à tous les projets : affichage, enregistrement, diffusion, intégrations.

Lus depuis le .env (mêmes noms de variables pour tous les projets).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path

from dotenv import load_dotenv


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def env_bool(name: str, default: bool | None) -> bool | None:
    value = env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "oui", "on"}


def env_float(name: str, default: float | None) -> float | None:
    value = env(name)
    return float(value) if value is not None else default


def env_int(name: str, default: int | None) -> int | None:
    value = env(name)
    return int(value) if value is not None else default


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in (env(name, default) or "").split(",") if item.strip()]


def load_env(env_file: str | None = None) -> None:
    load_dotenv(env_file or ".env", override=False)


def resolve_model_path(name: str, models_dir: Path | None = None) -> str:
    """Un nom nu (ex. « yolo26s.pt ») est rangé dans MODELS_DIR ; Ultralytics le télécharge au besoin."""
    models_dir = models_dir or Path(env("MODELS_DIR", "models"))
    path = Path(name)
    if not path.is_absolute() and path.parent == Path("."):
        path = models_dir / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


@dataclass
class OutputSettings:
    # Affichage local
    view: str = "window"                      # window | web | none
    web_host: str = "0.0.0.0"
    web_port: int = 8080
    output_dir: Path = Path("output")

    # Diffusion en direct (YouTube, Twitch, serveur RTMP/SRT…) : URL complète avec la clé
    stream_url: str | None = None
    stream_fps: float = 25.0
    stream_bitrate: str = "4500k"

    # API REST + WebSocket + MJPEG (FastAPI)
    api_enabled: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_token: str | None = None              # si défini : en-tête « Authorization: Bearer <token> »

    # Webhooks : POST JSON de chaque événement
    webhook_urls: list[str] = field(default_factory=list)
    webhook_events: list[str] = field(default_factory=lambda: ["*"])
    webhook_token: str | None = None          # envoyé en « Authorization: Bearer <token> »

    # MQTT (domotique, automates, Node-RED…)
    mqtt_host: str | None = None
    mqtt_port: int = 1883
    mqtt_user: str | None = None
    mqtt_password: str | None = None
    mqtt_topic: str = "vision-lab"
    mqtt_tls: bool = False

    stats_interval_s: float = 5.0              # publication périodique des statistiques


def add_output_arguments(parser) -> None:
    """Options communes à tous les projets (équivalents .env entre parenthèses)."""
    group = parser.add_argument_group("sorties et intégrations (communes à tous les projets)")
    group.add_argument("--view", choices=["window", "web", "none"], help="affichage (VIEW)")
    group.add_argument("--stream", dest="stream_url", metavar="URL",
                       help="diffusion RTMP, ex. rtmp://a.rtmp.youtube.com/live2/<clé> (STREAM_URL)")
    group.add_argument("--api", dest="api_enabled", action="store_true", default=None,
                       help="active l'API REST/WebSocket/MJPEG (API_ENABLED)")
    group.add_argument("--api-port", dest="api_port", type=int, help="port de l'API (API_PORT)")
    group.add_argument("--webhook", dest="webhook_urls", action="append", metavar="URL",
                       help="POST JSON de chaque événement (WEBHOOK_URLS), répétable")
    group.add_argument("--mqtt", dest="mqtt_host", metavar="HÔTE", help="broker MQTT (MQTT_HOST)")
    group.add_argument("--output-dir", dest="output_dir", type=Path, help="dossier des résultats (OUTPUT_DIR)")


OUTPUT_ARGUMENTS = ("view", "stream_url", "api_enabled", "api_port", "webhook_urls", "mqtt_host", "output_dir")


def pop_output_overrides(args: dict) -> dict:
    return {key: args.pop(key) for key in OUTPUT_ARGUMENTS if key in args}


def load_output_settings(**overrides) -> OutputSettings:
    settings = OutputSettings(
        view=(env("VIEW", "window") or "window").lower(),
        web_host=env("WEB_HOST", "0.0.0.0"),
        web_port=env_int("WEB_PORT", 8080),
        output_dir=Path(env("OUTPUT_DIR", "output")),
        stream_url=env("STREAM_URL"),
        stream_fps=env_float("STREAM_FPS", 25.0),
        stream_bitrate=env("STREAM_BITRATE", "4500k"),
        api_enabled=env_bool("API_ENABLED", False),
        api_host=env("API_HOST", "0.0.0.0"),
        api_port=env_int("API_PORT", 8000),
        api_token=env("API_TOKEN"),
        webhook_urls=env_list("WEBHOOK_URLS"),
        webhook_events=env_list("WEBHOOK_EVENTS", "*"),
        webhook_token=env("WEBHOOK_TOKEN"),
        mqtt_host=env("MQTT_HOST"),
        mqtt_port=env_int("MQTT_PORT", 1883),
        mqtt_user=env("MQTT_USER"),
        mqtt_password=env("MQTT_PASSWORD"),
        mqtt_topic=env("MQTT_TOPIC", "vision-lab"),
        mqtt_tls=env_bool("MQTT_TLS", False),
        stats_interval_s=env_float("STATS_INTERVAL_S", 5.0),
    )
    return replace(settings, **{k: v for k, v in overrides.items() if v is not None})
