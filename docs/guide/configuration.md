# Configuration (.env)

La configuration se fait dans un fichier `.env` à la racine (copie de `.env.example`).
**Priorité** : ligne de commande > variables d'environnement > `.env` > préréglage du mode.

!!! question "Pourquoi un `.env` et pas un `config.py` ?"
    Le `.env` contient ce qui change d'une machine à l'autre (source, GPU, chemins, URL de caméra
    avec mot de passe) et **n'est pas commité**. Il se transmet aussi tel quel à Docker (`env_file`).
    Ce qui relève du code, comme le catalogue des classes et leurs dimensions, reste en Python
    (`projets/distance_vitesse/classes.py`).

## Source et mode

| Variable | Défaut | Description |
|---|---|---|
| `SOURCE` | `0` | Fichier vidéo/image, URL `rtsp://` / `http://`, ou index de webcam |
| `MODE` | `fast` | `fast` (temps réel) ou `accurate` (vidéo enregistrée) — voir [Modes](../fonctionnalites/modeles.md) |

## Modèle et inférence

| Variable | Défaut | Description |
|---|---|---|
| `MODEL` | *(préréglage)* | Poids : `yolo26m.pt`, `models/best.engine`, `.onnx`, dossier OpenVINO… |
| `MODELS_DIR` | `models` | Dossier où les poids sont téléchargés |
| `IMGSZ` | 640 / 1280 | Taille d'entrée du réseau |
| `CONF` | `0.35` | Seuil de confiance |
| `DEVICE` | auto | `cpu`, `0`, `1`… |
| `HALF` | auto | FP16 (activé automatiquement sur GPU) |
| `TRACKER` | préréglage | `bytetrack.yaml` ou `botsort.yaml` |
| `OPEN_VOCAB_CLASSES` | — | Active YOLOE : `"person:1.7,child:1.2,dog:0.55,stroller"` |

## Mesures

| Variable | Défaut | Description |
|---|---|---|
| `CAMERA_HFOV_DEG` | `70` | Champ de vision horizontal de la caméra |
| `FOCAL_LENGTH_PX` | — | Focale en pixels (prioritaire sur le FOV) |
| `CALIBRATION_FILE` | — | Homographie du sol pour une vitesse fiable |
| `SPEED_WINDOW_S` | `1.0` | Fenêtre de lissage de la vitesse (s) |

## Plaques

| Variable | Défaut | Description |
|---|---|---|
| `PLATES_ENABLED` | `true` | Active la lecture des plaques |
| `PLATE_DETECTOR_MODEL` | `yolo-v9-t-384-license-plate-end2end` | Détecteur de plaques (`-t-256` … `-s-608`) |
| `PLATE_OCR_MODEL` | `cct-s-v2-global-model` | OCR (`cct-xs-v2-global-model` : plus rapide) |
| `PLATE_COUNTRIES` | `France` | Formats essayés quand l'OCR ne reconnaît pas le pays |
| `PLATE_DEVICE` | `cpu` | `cpu` ou `cuda` |
| `PLATE_EVERY` | 15 / 3 | Une tentative toutes les N images par véhicule |
| `PLATE_MIN_VEHICLE_PX` | `80` | Hauteur minimale du véhicule pour tenter une lecture |

## Zones, affichage et sorties

| Variable | Défaut | Description |
|---|---|---|
| `ZONES_FILE` | — | Fichier JSON de zones/lignes |
| `VIEW` | `window` | `window`, `web` (MJPEG sur `WEB_PORT`) ou `none` |
| `LABELS` | `auto` | `full`, `compact`, ou `auto` (compact au-delà de 20 objets) |
| `WEB_HOST` / `WEB_PORT` | `0.0.0.0` / `8080` | Serveur du flux annoté |
| `OUTPUT_DIR` | `output` | Dossier des résultats |
| `SAVE_VIDEO` | non / oui | Enregistrer la vidéo annotée (préréglage `fast` / `accurate`) |
| `DROP_FRAMES` | oui / non | Flux live : ne traiter que l'image la plus récente |

## Exemple : caméra RTSP de parking

```dotenv
SOURCE=rtsp://admin:secret@192.168.1.20:554/Streaming/Channels/101
MODE=fast
CAMERA_HFOV_DEG=100
ZONES_FILE=zones/parking.json
VIEW=web
PLATE_COUNTRIES=France
```
