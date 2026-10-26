# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; versions selon
[SemVer](https://semver.org/lang/fr/).

## [Non publié] — 0.3.0 (en cours, branche `refonte/vision-lab`)

Le projet devient **YOLO Vision Lab**, un laboratoire de projets.

### Ajouté

- Socle commun `vision_lab/` : sources, affichage, enregistrement, **diffusion RTMP (YouTube/Twitch)**,
  **API REST + WebSocket + MJPEG** (FastAPI), **webhooks**, **MQTT**, bus d'événements.
- `python -m vision_lab` : liste et lance les projets ; `doctor` vérifie l'installation ; `zones` (éditeur commun).
- Projets dans `projets/` : `distance_vitesse` (ex-Traffic Vision), `solutions` (Solutions Ultralytics),
  `football` (d'après roboflow/sports, en cours).
- Objets statiques : sélection à la souris et distance en continu (`--select-static`, `--static`).
- Événements `zone_exit` (avec anti-rebond) et `plate` ; fichier `events.jsonl`.
- Workflows GitHub : CI multi-OS (Python 3.10 et 3.14), CodeQL, Docker → GHCR, release, liens, Dependabot.
- Python 3.14 comme version de référence.

### Corrigé

- Franchissement de ligne perdu quand l'objet tombait exactement sur la ligne.
- Python 3.14 + antivirus Avast (`SSLKEYLOGFILE`) : plantage OpenSSL sur toute connexion HTTPS.
- `opencv-python-headless` (tiré par fast-alpr) supprimait les fenêtres OpenCV : détecté par `doctor`.

## [0.2.0] — 2026-10-26

Refonte complète : le projet devient **Traffic Vision**.

### Ajouté

- YOLO26 (Ultralytics 8.4) avec deux modes : `fast` (temps réel) et `accurate` (vidéo enregistrée).
- Suivi multi-objets (ByteTrack / BoT-SORT) avec identifiant stable.
- Estimation de la vitesse, avec calibration optionnelle du sol (homographie).
- Lecture des plaques d'immatriculation multi-pays (fast-alpr) ; formats France SIV et FNI, Belgique,
  Espagne, Italie, Royaume-Uni, Monaco.
- Zones (occupation, entrées) et lignes de comptage orientées ; éditeur de zones interactif.
- Regroupement personne + vélo/moto en « Cycliste » / « Motard ».
- Classes animales COCO ; vocabulaire ouvert avec YOLOE-26.
- Configuration par `.env` ; ligne de commande `python -m traffic_vision`.
- Affichage en fenêtre, dans le navigateur (MJPEG) ou sans affichage.
- Rapports : vidéo annotée, `tracks.csv`, `events.csv`, `summary.json`.
- Dockerfile et `docker-compose.yml` (GPU NVIDIA).
- Script de téléchargement d'échantillons libres de droits ; stockage Git LFS.
- Documentation MkDocs Material, tests unitaires, CI GitHub Actions.

### Modifié

- Distance calculée à partir de la **hauteur** réelle des objets et du champ de vision de la caméra
  (au lieu d'une largeur et d'une focale fixe de 1000 px).
- Licence : AGPL-3.0-or-later (compatibilité avec Ultralytics).

### Supprimé

- `config.py`, `distance_calculator.py`, `yolo_distance.py` (remplacés par le paquet `traffic_vision`).

### Corrigé

- La focale était recalculée, et le flux CCTV rouvert, pour **chaque objet de chaque image**.
- Les valeurs factices de `config.py` (`"your_cctv_url"`) empêchaient la saisie manuelle de la source.
- L'index de webcam saisi (`"0"`) était passé comme une chaîne à OpenCV.

## [0.1.0] — 2025

- Version initiale (fork de `omukesh/yolov8_distance_calculator`) : détection YOLO et distance par la largeur.
