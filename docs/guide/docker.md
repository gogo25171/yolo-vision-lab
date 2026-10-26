# Docker

L'image contient PyTorch (CUDA 12.8), Ultralytics, fast-alpr et le code. Dans un conteneur, il n'y a pas
d'écran : le flux annoté est servi dans le navigateur (`VIEW=web`).

## Prérequis

- Docker Desktop (Windows/macOS) ou Docker Engine (Linux)
- GPU NVIDIA : pilote récent ; sous Linux, le [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
  Sous Windows, Docker Desktop + WSL2 suffit.

## Lancer

```bash
cp .env.example .env              # choisir SOURCE, MODE, ZONES_FILE…
python scripts/download_samples.py
docker compose up --build
```

Ouvrir <http://localhost:8080>. Les résultats arrivent dans `./output`.

Autre source ou autre mode sans toucher au `.env` :

```bash
docker compose run --rm --service-ports vision-lab distance_vitesse \
    samples/videos/parking_cctv.mp4 --mode accurate --zones zones/parking_cctv.json
```

## Volumes

| Hôte | Conteneur | Rôle |
|---|---|---|
| `./samples` | `/app/samples` (lecture seule) | Vidéos d'entrée |
| `./zones` | `/app/zones` | Fichiers de zones |
| `./output` | `/app/output` | Résultats |
| volume `models` | `/app/models` | Poids YOLO (téléchargés une fois) |
| volume `model-cache` | `/root/.cache` | Modèles de plaques |

## Sans GPU

```bash
docker build --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cpu -t traffic-vision:cpu .
docker run --rm -p 8080:8080 -v ./samples:/app/samples:ro -v ./output:/app/output \
    traffic-vision:cpu samples/videos/street_ljubljana.mp4 --model yolo26n.pt
```

Supprimez aussi le bloc `deploy:` de `docker-compose.yml` si vous utilisez Compose sans GPU.

## Caméra IP

Une URL RTSP fonctionne telle quelle (`SOURCE=rtsp://…`). Une webcam USB n'est accessible que sous Linux
(`devices: ["/dev/video0:/dev/video0"]`) ; sous Windows, lancez plutôt le programme hors Docker.

!!! warning "Proxy / antivirus qui inspecte le HTTPS"
    Le téléchargement des modèles peut échouer dans le conteneur. Téléchargez-les une fois sur l'hôte
    (`models/`), puis montez ce dossier (`- ./models:/app/models`) à la place du volume nommé.
