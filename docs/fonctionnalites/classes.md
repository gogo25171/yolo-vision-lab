# Classes détectées

## Catalogue par défaut

Défini dans `projets/distance_vitesse/classes.py` (identifiants COCO). La **hauteur réelle** sert à estimer la distance.

| Catégorie | Classe | Hauteur (m) |
|---|---|---|
| Personne | Personne | 1,70 |
| Véhicules | Vélo 1,05 · Voiture 1,50 · Moto 1,30 · Bus 3,10 · Camion 3,20 · Train 4,00 | |
| | Avion, Bateau | — (pas de distance) |
| Animaux | Oiseau 0,25 · Chat 0,30 · Chien 0,55 · Mouton 0,80 · Ours 1,00 · Vache 1,40 · Zèbre 1,40 · Cheval 1,60 · Éléphant 3,00 · Girafe 4,80 | |

!!! question "Pourquoi la hauteur et pas la largeur ?"
    La largeur dépend de l'angle de vue : une voiture fait 1,8 m de face mais 4,5 m de profil. La hauteur
    reste ~1,5 m quel que soit l'angle, ce qui rend l'estimation bien plus stable.

### Ajouter ou modifier une classe

```python
# projets/distance_vitesse/classes.py
COCO_CLASSES[24] = ClassInfo("Sac à dos", 0.45, (0, 140, 255), "other")
COCO_CLASSES[2] = ClassInfo("Voiture", 1.55, (0, 0, 255), "vehicle")
```

La catégorie `vehicle` active la lecture de plaque. La liste des 80 classes COCO est
[ici](https://docs.ultralytics.com/datasets/detect/coco/).

## Cyclistes et motards

YOLO détecte séparément la **personne** et le **vélo**. Sans traitement, un cycliste compte deux fois.
`projets/distance_vitesse/detections.py` associe chaque personne au vélo ou à la moto qu'elle chevauche :

- recouvrement de la boîte de la personne par celle du véhicule ≥ 25 % ;
- centre de la personne au-dessus du véhicule, à peu près centré ;
- association confirmée après 3 images, puis conservée tant que les deux pistes se chevauchent encore.

Le véhicule devient **Cycliste** ou **Motard**, avec une boîte englobant les deux. La personne est masquée et
n'est plus comptée dans les zones. Le même principe peut s'étendre (personne + cheval, poussette…) :
voir la [feuille de route](../projet/feuille-de-route.md).

## Animaux

Les 10 classes animales de COCO sont actives par défaut. Pour des espèces ou des races plus fines
(« golden retriever », « cat on a car »…), utilisez le [vocabulaire ouvert](modeles.md#vocabulaire-ouvert-yoloe)
ou entraînez un modèle dédié.

## Attributs des personnes

| Attribut | Statut | Méthode |
|---|---|---|
| Enfant / adulte | Possible | Vocabulaire ouvert : `--classes "child:1.2,adult:1.7"` |
| Tranche d'âge fine, genre | Non implémenté par défaut | Voir ci-dessous |
| Corpulence | Écarté | Voir ci-dessous |

!!! danger "Pourquoi le genre et la corpulence ne sont pas intégrés"
    - **Fiabilité** : déduire le genre ou la corpulence d'une silhouette de vidéosurveillance est peu fiable,
      et les erreurs touchent inégalement les groupes de personnes.
    - **Droit** : en Europe, catégoriser des personnes selon ce type de caractéristiques à partir d'images
      relève du RGPD, et l'*AI Act* classe la catégorisation biométrique selon des attributs protégés (sexe,
      âge…) comme système à haut risque. La corpulence touche à la santé, donc à une donnée sensible.

    Le vocabulaire ouvert accepte n'importe quelle invite : la responsabilité de l'usage revient alors à
    l'opérateur. Voir [Conformité](../projet/conformite.md).
