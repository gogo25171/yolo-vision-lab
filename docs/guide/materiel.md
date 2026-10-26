# Matériel

## Calcul (PC / serveur)

| Usage | Minimum | Recommandé |
|---|---|---|
| Test sur une image ou une courte vidéo | CPU 4 cœurs, 8 Go RAM | — |
| 1 caméra temps réel (`fast`) | GPU NVIDIA 4 Go (GTX 1650) | RTX 3060 / 4060 (8 Go) |
| Vidéos enregistrées (`accurate`) | GPU NVIDIA 6 Go | RTX 4070 et plus (12 Go+) |
| Plusieurs caméras simultanées | — | RTX 4080/4090 ou GPU serveur (L4, A10) + export TensorRT |
| Embarqué / bord de route | Jetson Orin Nano | Jetson Orin NX / AGX + TensorRT |
| Intel sans GPU NVIDIA | CPU Core i5 récent | Export OpenVINO (iGPU / NPU Intel) |

- **RAM** : 16 Go conseillés (8 Go suffisent en `fast`).
- **Disque** : ~6 Go pour PyTorch + CUDA, ~200 Mo de modèles, et l'espace pour les vidéos annotées
  (une vidéo 1080p de 30 s fait ~70 Mo en `mp4v`).
- **Pilote NVIDIA** récent (compatible CUDA 12.8). Le toolkit CUDA n'est pas nécessaire : les wheels
  PyTorch l'embarquent.

### Performances mesurées

Mesures sur **RTX 4060 (8 Go)**, vidéos 1080p, pipeline complet (suivi + mesures + rendu) :

| Scène | Mode | Modèle / taille | FPS |
|---|---|---|---|
| Rue (~10 objets) | `fast` | yolo26s / 640 | ~37 (32 avec plaques) |
| Rond-point (drone) | `fast` | yolo26s / 640 | ~31 |
| Rond-point (drone) | `accurate` | yolo26x / 1280 | ~17 |
| Parking (~45 véhicules + plaques) | `accurate` | yolo26x / 1280 | ~11 |

Ordre de grandeur publié par Ultralytics (inférence seule, 640 px) : yolo26n ≈ 39 ms/image sur CPU (ONNX),
1,7 ms sur T4 (TensorRT) ; yolo26x ≈ 526 ms sur CPU, 11,8 ms sur T4.

!!! tip "Gagner des FPS"
    1. Exporter en TensorRT : `yolo export model=models/yolo26s.pt format=engine half=True` puis
       `MODEL=models/yolo26s.engine` (×2 à ×3 sur GPU NVIDIA).
    2. Réduire `IMGSZ` (480) ou passer à `yolo26n`.
    3. Augmenter `PLATE_EVERY`, ou désactiver les plaques si elles sont inutiles.

## Caméras

Les mesures dépendent davantage de la caméra que du modèle.

| Critère | Recommandation | Pourquoi |
|---|---|---|
| Résolution | 1080p minimum, 4 MP pour les plaques | Une plaque doit faire **≥ 100 px de large** (idéalement 130-150) pour être lue de façon fiable |
| Images/s | 15-25 | Suffisant pour la vitesse ; au-delà, peu de gain |
| Obturation | Rapide (≤ 1/500 s) pour les plaques | Évite le flou de mouvement |
| Infrarouge | Caméra IR / « LPR » la nuit | Les plaques sont rétroréfléchissantes |
| Compression | H.264/H.265 à débit élevé | Les artefacts détruisent les caractères |
| Position | Fixe, 3-6 m de haut, angle < 30° par rapport à l'axe de la route | Moins d'occlusions ; plaques lisibles ; calibration valable |
| Objectif | Connaître le champ de vision horizontal (HFOV) | Nécessaire pour la distance (`CAMERA_HFOV_DEG`) |

**Champ de vision typique** (HFOV, capteur 1/2,8") :

| Focale | HFOV approx. | Usage |
|---|---|---|
| 2,8 mm | 100-110° | Vue large (parking, cour) |
| 4 mm | 80-90° | Polyvalent |
| 6 mm | 50-55° | Rue, entrée |
| 8-12 mm | 25-40° | Lecture de plaques à distance |
| Webcam | 60-78° | Bureau |

!!! note "Caméra dédiée à la lecture de plaques"
    En pratique, on sépare souvent une caméra **vue d'ensemble** (comptage, vitesse) et une caméra
    **LPR** zoomée sur une voie. Les deux peuvent tourner dans deux instances de Traffic Vision.

## Réseau

- Flux RTSP : 4-8 Mbit/s par caméra 1080p (H.264).
- En mode `fast`, l'image la plus récente est toujours traitée : un réseau lent fait baisser les FPS
  mais n'accumule pas de retard.
