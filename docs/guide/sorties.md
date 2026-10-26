# Sorties et rapports

Chaque exécution crée `output/<source>_<AAAAMMJJ_HHMMSS>/`.

| Fichier | Quand | Contenu |
|---|---|---|
| `annotated.mp4` | `SAVE_VIDEO` (par défaut en `accurate`) | Vidéo avec boîtes, mesures, plaques et zones |
| `annotated.jpg` | Image en entrée | Image annotée |
| `detections.csv` | Image en entrée | Une ligne par objet |
| `tracks.csv` | Vidéo/flux | Une ligne par objet suivi (au moins 3 images) |
| `events.csv` | Zones définies | Entrées dans les zones, franchissements de lignes |
| `summary.json` | Vidéo/flux | Totaux par classe, comptages des zones et lignes |

## `tracks.csv`

| Colonne | Description |
|---|---|
| `track_id` | Identifiant de suivi |
| `label` | Classe majoritaire (ex. `Cycliste`) |
| `debut_s`, `fin_s` | Première et dernière apparition (secondes) |
| `images` | Nombre d'images où l'objet est vu |
| `vitesse_moy_kmh`, `vitesse_max_kmh` | Moyenne et 95e centile (robuste aux pics) |
| `distance_min_m` | Plus courte distance estimée à la caméra |
| `plaque`, `region` | Meilleure lecture (vote pondéré) et pays prédit |

## `events.csv`

```csv
t,type,name,track_id,label
3.4,zone_enter,Parking,12,Voiture
5.1,line_in,Entrée,12,Voiture
```

## `summary.json`

```json
{
  "source": "samples/videos/roundabout.mp4",
  "mode": "accurate",
  "model": "yolo26x.pt",
  "objets": {"Voiture": 35, "Camion": 1},
  "zones": {"Anneau": {"total": {"Voiture": 20}, "occupation_finale": {"Voiture": 2}}},
  "lines": {"Branche nord-ouest": {"in": {"Voiture": 9}, "out": {"Voiture": 1}}}
}
```

!!! note "Flux live"
    Pour une caméra, les rapports sont écrits à l'arrêt (touche ++q++ ou ++ctrl+c++).
    Un export périodique et une base de données sont prévus dans la [feuille de route](../projet/feuille-de-route.md).
