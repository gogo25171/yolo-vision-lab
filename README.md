# 🧪 YOLO Vision Lab

[![CI](https://github.com/gogo25171/yolo-vision-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/gogo25171/yolo-vision-lab/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://gogo25171.github.io/yolo-vision-lab/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.14_(3.10+)-blue)
![YOLO26](https://img.shields.io/badge/YOLO-26-purple)

**Un laboratoire de vision par ordinateur** pour comprendre, tester et brancher sur ses propres outils des
projets de vision : ceux des équipes [Ultralytics](https://ultralytics.com/) et [Roboflow](https://roboflow.com/),
les nôtres et ceux de la communauté. Ils sont **mis à jour sur les dernières versions** (Python 3.14, YOLO26)
et utilisables **sur toute plateforme** (Windows, Linux avec ou sans GPU, macOS, Docker).

> 🚧 **Refonte en cours** (v0.3) : l'état exact et les prochaines étapes sont dans [TODO.md](TODO.md).
> Priorité suivante : une interface web pour lancer les projets sans ligne de commande.

## 📦 Projets

| Projet | Ce qu'il fait | État | Utilisation | Documentation technique |
|---|---|---|---|---|
| [**Distance & vitesse**](projets/distance_vitesse) | Distance et vitesse des objets, objets statiques, plaques d'immatriculation (FR + multi-pays), zones de comptage | ✅ | [Démarrage](docs/guide/demarrage.md) · [Zones](docs/fonctionnalites/zones.md) · [Plaques](docs/fonctionnalites/plaques.md) | [Mesures](docs/fonctionnalites/mesures.md) · [Modèles](docs/fonctionnalites/modeles.md) · [Classes](docs/fonctionnalites/classes.md) · [Architecture](docs/projet/architecture.md) |
| [**Solutions Ultralytics**](projets/solutions) | Les 15 solutions officielles : comptage, heatmap, file d'attente, parking, sport, floutage… | ✅ | [`cli.py`](projets/solutions/cli.py) (exemples en tête du fichier) | [Ultralytics Solutions](https://docs.ultralytics.com/solutions/) |
| [**Football**](projets/football) | Joueurs, ballon, arbitres, équipes, vue radar du terrain | 🚧 | [`cli.py`](projets/football/cli.py) | [roboflow/sports](https://github.com/roboflow/sports/tree/main/examples/soccer) (code repris sous licence MIT) |

```bash
python -m vision_lab                      # liste des projets
python -m vision_lab <projet> --help      # options d'un projet
```

## 🔌 Commun à tous les projets

| Fonction | Option | Documentation |
|---|---|---|
| Affichage : fenêtre, page web, sans affichage | `--view window\|web\|none` | [Configuration](docs/guide/configuration.md) |
| API REST + WebSocket + flux vidéo MJPEG | `--api` | [`vision_lab/api.py`](vision_lab/api.py) · `/docs` une fois lancée |
| Webhooks (n8n, Node-RED, Home Assistant…) | `--webhook URL` | [`vision_lab/events.py`](vision_lab/events.py) |
| MQTT (domotique, automates, équipements) | `--mqtt HÔTE` | [`vision_lab/events.py`](vision_lab/events.py) |
| Diffusion en direct (YouTube, Twitch, RTMP) | `--stream rtmp://…` | [`vision_lab/outputs.py`](vision_lab/outputs.py) |
| Éditeur de zones et de lignes | `python -m vision_lab zones <source>` | [Zones](docs/fonctionnalites/zones.md) |
| Vérification de l'installation | `python -m vision_lab doctor [projet]` | [`vision_lab/doctor.py`](vision_lab/doctor.py) |

## 🚀 Installation

```bash
git clone https://github.com/gogo25171/yolo-vision-lab.git && cd yolo-vision-lab
git lfs pull                                             # vidéos d'exemple (ou : python scripts/download_samples.py)

# Python 3.14 recommandé, puis PyTorch selon la machine :
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128   # GPU NVIDIA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu     # sans GPU

pip install -r requirements.txt                          # socle commun
pip install -r projets/<projet>/requirements.txt         # dépendances propres à chaque projet
cp .env.example .env
python -m vision_lab doctor                              # indique ce qui manque (pilote, paquet, logiciel)
```

Avec Docker (GPU NVIDIA) : `docker compose up --build`, puis <http://localhost:8080> et l'API sur <http://localhost:8000/docs>.

## 📚 Documentation générale

| Sujet | Lien |
|---|---|
| Matériel conseillé (GPU, caméras, performances) | [docs/guide/materiel.md](docs/guide/materiel.md) |
| Configuration (`.env`) | [docs/guide/configuration.md](docs/guide/configuration.md) |
| Docker | [docs/guide/docker.md](docs/guide/docker.md) |
| Données de test et licences | [docs/projet/donnees-test.md](docs/projet/donnees-test.md) |
| Conformité (RGPD, AI Act, licences) | [docs/projet/conformite.md](docs/projet/conformite.md) |
| Contribuer, ajouter un projet | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Feuille de route | [TODO.md](TODO.md) · [CHANGELOG.md](CHANGELOG.md) |

Site complet (MkDocs) : <https://gogo25171.github.io/yolo-vision-lab/>, ou en local :
`pip install -r requirements-docs.txt && mkdocs serve`.

## 📁 Organisation du dépôt

```text
├── vision_lab/        # socle commun : sources, affichage, API, webhooks, MQTT, diffusion, doctor
├── projets/           # un dossier par projet (code, requirements.txt)
│   ├── distance_vitesse/
│   ├── solutions/
│   └── football/
├── zones/             # zones de comptage d'exemple
├── samples/           # vidéos de test libres de droits (Git LFS) + SOURCES.md
├── docs/              # documentation MkDocs
├── tests/             # tests unitaires (sans GPU)
└── scripts/           # outils (téléchargement des échantillons…)
```

## ⚠️ Avertissements

- Distances, vitesses et comptages sont des **estimations**, pas des mesures homologuées.
- Images de personnes et plaques d'immatriculation sont des **données personnelles** : voir [Conformité](docs/projet/conformite.md).

## 📄 Licence et remerciements

[AGPL-3.0-or-later](LICENSE), imposée par la licence d'[Ultralytics](https://ultralytics.com/license). Les projets
repris gardent leur licence d'origine (ex. [roboflow/sports](https://github.com/roboflow/sports), MIT) et les
vidéos de test ont la leur ([`samples/SOURCES.md`](samples/SOURCES.md)).

Merci à [Ultralytics](https://ultralytics.com/), [Roboflow](https://roboflow.com/),
[fast-alpr](https://github.com/ankandrew/fast-alpr) et [OpenCV](https://opencv.org/). Projet né d'un fork de
`omukesh/yolov8_distance_calculator`, développé avec l'aide d'assistants IA (GitHub Copilot, Claude).
