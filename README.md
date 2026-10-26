# 🧪 YOLO Vision Lab

> **Refonte en cours (v0.3, branche `refonte/vision-lab`)** : le dépôt devient un *laboratoire* de projets de
> vision, faciles à tester et à brancher sur ses outils. Voir [TODO.md](TODO.md) pour l'état exact.
>
> ```bash
> python -m vision_lab                  # liste des projets
> python -m vision_lab doctor           # vérifie l'installation (GPU, paquets, logiciels)
> python -m vision_lab distance_vitesse samples/videos/street_ljubljana.mp4 --api --stream rtmp://…
> python -m vision_lab solutions heatmap samples/videos/crosswalk_toronto.mp4
> python -m vision_lab football setup --videos && python -m vision_lab football samples/football/0bfacc_0.mp4
> ```
>
> | Projet | Dossier | État |
> |---|---|---|
> | Distance & vitesse (+ plaques, zones, objets statiques) | [`projets/distance_vitesse`](projets/distance_vitesse) | ✅ |
> | Solutions Ultralytics (comptage, heatmap, parking, sport…) | [`projets/solutions`](projets/solutions) | ✅ |
> | Football (d'après roboflow/sports) | [`projets/football`](projets/football) | 🚧 |
>
> Intégrations communes à tous les projets : **API** REST/WebSocket/MJPEG (`--api`), **webhooks** (`--webhook`),
> **MQTT** (`--mqtt`), **diffusion YouTube/RTMP** (`--stream`). Python **3.14** recommandé.

## Projet Distance & vitesse (ex-Traffic Vision)

[![CI](https://github.com/gogo25171/yolo-vision-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/gogo25171/yolo-vision-lab/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://gogo25171.github.io/yolo-vision-lab/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10--3.12-blue)
![YOLO26](https://img.shields.io/badge/YOLO-26-purple)

Analyse vidéo avec **YOLO26** : détection, suivi, **distance**, **vitesse**, **plaques d'immatriculation**
(multi-pays, formats français) et **comptage par zones**, pour une caméra CCTV en temps réel ou une vidéo enregistrée.

![Démonstration](docs/assets/street.jpg)

## ✨ Fonctionnalités

- 🔍 **Détection + suivi** : personnes, véhicules, animaux ; identifiant stable par objet (ByteTrack / BoT-SORT)
- ⚡ **Deux modes** : `fast` (CCTV, webcam, temps réel) et `accurate` (vidéo enregistrée, précision maximale)
- 📏 **Distance** à partir de la hauteur réelle des objets et du champ de vision de la caméra
- 🏎️ **Vitesse** estimée en continu, fiable avec une calibration du sol
- 🔢 **Plaques** : lecture multi-pays (fast-alpr), formats France SIV (`AB-123-CD`) et FNI validés et corrigés
- 🚲 **Cyclistes / motards** : la personne et son vélo comptent pour un seul objet
- 🟦 **Zones et lignes** : occupation, entrées, franchissements par sens ; éditeur de zones
- 🧠 **Vocabulaire ouvert** (YOLOE) : décrire en texte ce qu'il faut détecter
- 🐳 **Docker** (GPU) avec flux annoté dans le navigateur
- 📊 **Rapports** : vidéo annotée, CSV par objet, journal d'événements, résumé JSON

## 🚀 Démarrage rapide

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128   # GPU NVIDIA
pip install -r requirements.txt -r projets/distance_vitesse/requirements.txt
cp .env.example .env
python scripts/download_samples.py                                                 # vidéos de test libres

python -m vision_lab distance_vitesse samples/videos/street_ljubljana.mp4                       # temps réel, fenêtre
python -m vision_lab distance_vitesse samples/videos/parking_cctv.mp4 --mode accurate --zones zones/parking_cctv.json
```

Ou avec Docker : `docker compose up --build` puis <http://localhost:8080>.

## ⚙️ Configuration

Tout se règle dans `.env` (voir [`.env.example`](.env.example)) ou en ligne de commande :

```text
python -m vision_lab distance_vitesse [source] [--mode fast|accurate] [--model POIDS] [--view window|web|none]
                         [--zones ZONES.json] [--calibration CALIB.json] [--classes "a:1.7,b"]
                         [--no-plates] [--save | --no-save]
```

| Mode | Modèle | Entrée | Usage | FPS (RTX 4060, 1080p) |
|---|---|---|---|---|
| `fast` | yolo26s | 640 px | CCTV, webcam, RTSP | ~30-37 |
| `accurate` | yolo26x | 1280 px | Vidéos enregistrées | ~11-17 |

## 📚 Documentation

Documentation complète (MkDocs) : **<https://gogo25171.github.io/yolo-vision-lab/>**, ou en local :

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

| | |
|---|---|
| [Démarrage](docs/guide/demarrage.md) · [Matériel](docs/guide/materiel.md) · [Configuration](docs/guide/configuration.md) · [Docker](docs/guide/docker.md) | Guide |
| [Modèles](docs/fonctionnalites/modeles.md) · [Classes](docs/fonctionnalites/classes.md) · [Distance et vitesse](docs/fonctionnalites/mesures.md) · [Plaques](docs/fonctionnalites/plaques.md) · [Zones](docs/fonctionnalites/zones.md) | Fonctionnalités |
| [Architecture](docs/projet/architecture.md) · [Données de test](docs/projet/donnees-test.md) · [Conformité](docs/projet/conformite.md) · [TODO](TODO.md) | Projet |

## 📁 Structure

```text
├── projets/distance_vitesse/         # paquet principal (python -m vision_lab distance_vitesse)
├── zones/                  # zones de comptage d'exemple
├── samples/                # vidéos de test (Git LFS) + SOURCES.md
├── scripts/                # téléchargement des échantillons
├── tests/                  # tests unitaires (sans GPU)
├── docs/                   # documentation MkDocs
├── Dockerfile, docker-compose.yml
└── .env.example
```

## ⚠️ Avertissements

- Distances et vitesses sont des **estimations**, pas des mesures homologuées.
- Images de personnes et plaques sont des **données personnelles** : voir [Conformité](docs/projet/conformite.md).

## 📄 Licence

[AGPL-3.0-or-later](LICENSE), imposée par la licence d'[Ultralytics](https://ultralytics.com/license).
Les vidéos de test ont leurs propres licences ([`samples/SOURCES.md`](samples/SOURCES.md)).

## 🙏 Remerciements

- [Ultralytics](https://ultralytics.com/) (YOLO26, YOLOE), [fast-alpr](https://github.com/ankandrew/fast-alpr)
  et [fast-plate-ocr](https://github.com/ankandrew/fast-plate-ocr), [OpenCV](https://opencv.org/)
- Projet né au tout départ d'un fork de `omukesh/yolov8_distance_calculator` mais qui c'est transformer en un hub.
- Développé avec l'aide d'assistants IA (GitHub Copilot, Claude).
