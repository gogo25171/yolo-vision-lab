# Démarrage rapide

## Prérequis

- Python 3.10 à 3.12 (3.12 recommandé)
- Un GPU NVIDIA est conseillé, mais pas obligatoire (voir [Matériel](materiel.md))
- `ffmpeg` (facultatif) pour découper les vidéos de test
- Git LFS si vous clonez le dépôt avec les échantillons

## Installation

=== "Windows (PowerShell)"

    ```powershell
    git clone https://github.com/gogo25171/yolo_distance_calculator.git
    cd yolo_distance_calculator
    py -3.12 -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
    pip install -r requirements.txt
    copy .env.example .env
    ```

=== "Linux / macOS"

    ```bash
    git clone https://github.com/gogo25171/yolo_distance_calculator.git
    cd yolo_distance_calculator
    python3.12 -m venv .venv
    source .venv/bin/activate
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128  # (1)!
    pip install -r requirements.txt
    cp .env.example .env
    ```

    1. Sans GPU NVIDIA (ou sur macOS) : `pip install torch torchvision` suffit.

!!! tip "Projet dans un dossier synchronisé (Google Drive, OneDrive…)"
    Créez l'environnement virtuel **hors** du dossier synchronisé (ex. `~/.venvs/traffic-vision`) :
    des dizaines de milliers de fichiers de bibliothèques seraient sinon synchronisés.

!!! warning "Erreur `CERTIFICATE_VERIFY_FAILED`"
    Un antivirus ou un proxy d'entreprise inspecte le HTTPS. Le programme utilise automatiquement
    les certificats du système via `truststore`. Pour `pip`/`uv`, ajoutez `--use-feature=truststore`
    (pip) ou `--native-tls` (uv).

Les poids YOLO26 (`models/`) et les modèles de plaques (`~/.cache/fast-plate-ocr`) se téléchargent au
premier lancement.

## Échantillons de test

```bash
python scripts/download_samples.py
```

Télécharge cinq vidéos sous licence libre et une image de plaque dans `samples/`
(détails : [Données de test](../projet/donnees-test.md)).

## Premiers lancements

```bash
# Rue : distance, vitesse, plaques (fenêtre OpenCV, touche q pour quitter)
python -m vision_lab distance_vitesse samples/videos/street_ljubljana.mp4

# Vidéo enregistrée, précision maximale, comptage par zones, sans affichage
python -m vision_lab distance_vitesse samples/videos/parking_cctv.mp4 --mode accurate --zones zones/parking_cctv.json --view none

# Webcam
python -m vision_lab distance_vitesse 0

# Caméra IP (RTSP) affichée dans le navigateur (http://localhost:8080)
python -m vision_lab distance_vitesse "rtsp://user:motdepasse@192.168.1.20:554/stream1" --view web

# Image
python -m vision_lab distance_vitesse samples/images/plate_test.png
```

Les résultats sont écrits dans `output/<source>_<date>/` (voir [Sorties](sorties.md)).

## Options de la ligne de commande

```text
python -m vision_lab distance_vitesse [source] [--mode fast|accurate] [--model POIDS] [--view window|web|none]
                         [--zones ZONES.json] [--calibration CALIB.json] [--classes "a:1.7,b"]
                         [--no-plates] [--save | --no-save] [--env FICHIER]
```

Chaque option a un équivalent dans le `.env` : voir [Configuration](configuration.md).

## Définir des zones

```bash
python -m vision_lab zones samples/videos/roundabout.mp4 -o zones/ma_scene.json
```

Voir [Zones et comptage](../fonctionnalites/zones.md).
