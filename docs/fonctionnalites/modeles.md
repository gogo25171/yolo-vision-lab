# Modes et modèles YOLO

## Les deux modes

| | `fast` — temps réel | `accurate` — vidéo enregistrée |
|---|---|---|
| Usage | CCTV, webcam, flux RTSP | Fichiers à analyser finement |
| Modèle | `yolo26s` (GPU) / `yolo26n` (CPU) | `yolo26x` |
| Taille d'entrée | 640 px | 1280 px (petits objets lointains) |
| Suivi | ByteTrack (rapide) | BoT-SORT (plus robuste aux occlusions) |
| Plaques | 1 tentative / 15 images / véhicule | 1 tentative / 3 images / véhicule |
| Images | La plus récente (pas de retard accumulé) | Toutes, sans exception |
| Vidéo annotée | Non (`--save` pour l'activer) | Oui |

Tout se surcharge individuellement (`MODEL`, `IMGSZ`, `TRACKER`, `PLATE_EVERY`, `SAVE_VIDEO`, `DROP_FRAMES`).

!!! example "Effet de la taille d'entrée"
    Sur le rond-point filmé par drone, une même image contient **3 voitures détectées** en `fast`
    (640 px) contre **13** en `accurate` (1280 px) : à 640 px, une voiture vue de haut ne fait plus
    qu'une dizaine de pixels.

## Famille YOLO26

[YOLO26](https://docs.ultralytics.com/models/yolo26/) (Ultralytics, janvier 2026) est la dernière génération :
architecture *end-to-end* sans NMS, pensée pour l'embarqué. Valeurs publiées sur COCO (640 px) :

| Modèle | mAP50-95 | CPU ONNX (ms) | T4 TensorRT (ms) | Mode |
|---|---|---|---|---|
| `yolo26n` | 40,9 | 38,9 | 1,7 | `fast` sans GPU |
| `yolo26s` | 48,6 | 87,2 | 2,5 | `fast` |
| `yolo26m` | 53,1 | 220,0 | 4,7 | compromis |
| `yolo26l` | 55,0 | 286,2 | 6,2 | — |
| `yolo26x` | 57,5 | 525,8 | 11,8 | `accurate` |

Les poids sont téléchargés automatiquement dans `models/` au premier usage. Tout modèle Ultralytics
(YOLO11, YOLOv8, un modèle entraîné par vos soins) fonctionne aussi via `MODEL=`.

## Export pour la production

```bash
# NVIDIA TensorRT (le plus rapide sur GPU NVIDIA)
yolo export model=models/yolo26s.pt format=engine half=True imgsz=640
# Intel (CPU, iGPU, NPU)
yolo export model=models/yolo26s.pt format=openvino
# Portable
yolo export model=models/yolo26s.pt format=onnx
```

Puis `MODEL=models/yolo26s.engine` (ou `models/yolo26s_openvino_model`). Un modèle exporté a une taille
d'entrée fixe : gardez le même `IMGSZ`.

## Vocabulaire ouvert (YOLOE)

[YOLOE-26](https://docs.ultralytics.com/models/yoloe/) détecte des classes décrites **en texte**, sans
réentraînement :

```bash
pip install git+https://github.com/ultralytics/CLIP.git   # dépendance de YOLOE
python -m vision_lab distance_vitesse samples/videos/dogs_tokyo.mp4 \
    --classes "person:1.7,child:1.2,dog:0.55,stroller:1.0,scooter"
```

- Format : `nom[:hauteur_en_m]`, séparés par des virgules. Sans hauteur, pas de distance pour la classe.
- Les invites en anglais donnent de meilleurs résultats (le modèle texte est entraîné en anglais).
- Modèle utilisé : `yoloe-26s-seg` en `fast`, `yoloe-26l-seg` en `accurate`.
- Plus lent qu'un YOLO26 classique, et moins précis qu'un modèle entraîné sur vos classes : idéal pour
  prototyper avant d'entraîner un modèle dédié.

!!! warning "Statut"
    Le mode YOLOE est implémenté mais n'a pas encore été validé de bout en bout (dépendance CLIP non
    installable via PyPI). Voir la [feuille de route](../projet/feuille-de-route.md).
