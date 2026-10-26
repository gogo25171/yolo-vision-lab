# Zones et comptage

![Comptage par zone et par ligne sur un rond-point](../assets/roundabout.jpg)

## Deux outils

| | Zone (polygone) | Ligne |
|---|---|---|
| Question | « Combien d'objets **dans** cette zone ? » | « Combien d'objets **ont franchi** cette ligne, et dans quel sens ? » |
| Compteurs | Occupation courante + total d'objets distincts entrés | Entrées (`+`) et sorties (`-`) par classe |
| Exemples | Places de parking, quai, passage piéton | Entrée de parking, branche de rond-point, porte |

Le **point de référence** d'un objet est le bas-centre de sa boîte, son contact avec le sol. Les cyclistes et
motards comptent pour un seul objet.

## Fichier de zones

```json
{
  "zones": [
    {"name": "Rangee avant", "polygon": [[0.0, 0.74], [1.0, 0.74], [1.0, 1.0], [0.0, 1.0]],
     "classes": ["Voiture", "Camion"]}
  ],
  "lines": [
    {"name": "Entree", "points": [[0.47, 0.70], [0.72, 0.70]], "classes": ["Voiture"]}
  ]
}
```

- Coordonnées **normalisées** (0-1, recommandé : indépendant de la résolution) ou en pixels.
- `classes` (facultatif) : noms affichés (`Voiture`, `Personne`, `Cycliste`…). Sans `classes`, tout est compté.
- Sens d'une ligne : un objet qui passe vers le côté **droit** (en allant du premier au second point, tel
  qu'on voit l'image) compte comme une entrée (`+`), l'inverse comme une sortie (`-`). Inversez les deux
  points pour inverser le sens.

Exemples fournis : `zones/parking_cctv.json`, `zones/roundabout.json`, `zones/crosswalk_toronto.json`.

## Éditeur interactif

```bash
python -m vision_lab zones samples/videos/roundabout.mp4 -o zones/ma_scene.json
```

| Touche | Action |
|---|---|
| Clic gauche | Ajouter un point |
| ++z++ | Annuler le dernier point |
| ++n++ | Fermer le polygone (≥ 3 points) → zone |
| ++l++ | Valider une ligne (2 points) |
| ++s++ | Enregistrer |
| ++q++ / ++esc++ | Quitter |

Renommez ensuite les zones et ajoutez `classes` directement dans le JSON.

## Utilisation

```bash
python -m vision_lab distance_vitesse samples/videos/roundabout.mp4 --mode accurate --zones zones/roundabout.json
```

Les compteurs s'affichent sur la vidéo, et chaque événement est journalisé dans `events.csv`
(voir [Sorties](../guide/sorties.md)).

## Limites

- **Changements d'identifiant** : dans une foule, une occlusion peut faire perdre puis réattribuer un nouvel
  identifiant à un objet, qui est alors recompté dans le « total » d'une zone. Le mode `accurate` (BoT-SORT)
  limite le phénomène ; les franchissements de **ligne** y sont moins sensibles.
- Une zone mal placée (au-dessus du sol) ne capte rien : le point de référence est au sol.
