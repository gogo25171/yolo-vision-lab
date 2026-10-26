# Distance et vitesse

!!! warning "Ordres de grandeur, pas des mesures légales"
    Sans calibration, distance et vitesse sont des **estimations** (typiquement ±20-30 %). Elles ne
    remplacent pas un cinémomètre homologué.

## Distance (modèle sténopé)

La focale en pixels se déduit de la largeur de l'image $W$ et du champ de vision horizontal $\theta$ :

$$
f_{px} = \frac{W / 2}{\tan(\theta / 2)}
$$

Puis, avec $H$ la hauteur réelle de l'objet (catalogue) et $h$ sa hauteur en pixels :

$$
d = \frac{H \cdot f_{px}}{h}
$$

- Réglez `CAMERA_HFOV_DEG` selon votre caméra (voir [Matériel](../guide/materiel.md#cameras)), ou
  `FOCAL_LENGTH_PX` si vous l'avez mesurée.
- Un objet coupé par le bord haut ou bas de l'image n'a pas de distance (sa hauteur serait sous-estimée).
- Sources d'erreur : taille réelle variable (enfant/adulte, SUV/citadine), boîte imprécise, caméra très
  plongeante (on voit le toit plutôt que la hauteur).

### Mesurer sa focale

1. Placez un objet de hauteur connue $H$ (ex. une personne de 1,80 m) à une distance connue $d$.
2. Mesurez sa hauteur en pixels $h$ sur l'image.
3. $f_{px} = h \cdot d / H$, à reporter dans `FOCAL_LENGTH_PX`.

## Vitesse

Chaque objet suivi garde l'historique de sa position sur une fenêtre glissante (`SPEED_WINDOW_S`, 1 s par
défaut). La vitesse est le déplacement entre le début de la fenêtre et la médiane des dernières positions,
lissée par une moyenne exponentielle. Elle s'affiche après 0,4 s de suivi.

### Sans calibration (`~ km/h`)

La position est estimée dans le repère de la caméra : profondeur $Z = d$ et décalage latéral
$X = (c_x - W/2) \cdot d / f_{px}$. Cette approche est sensible aux variations de la boîte : un piéton qui
passe devant une voiture garée peut faire apparaître une vitesse de quelques km/h. Les valeurs inférieures
à 2 km/h sont affichées à 0.

### Avec calibration (vitesse fiable)

Pour une caméra **fixe**, une homographie relie le plan du sol de l'image à un plan en mètres. Le point de
contact au sol de chaque objet (bas-centre de la boîte) y est projeté.

1. Repérez sur l'image **4 points au sol** dont vous connaissez les distances réelles : coins d'une place
   de parking (2,5 × 5 m), marquage de passage piéton, bandes de séparation (en France : traits de 3 m
   espacés de 10 m sur route, etc.).
2. Créez `zones/calibration.json` :

    ```json
    {
      "image_points": [[0.32, 0.61], [0.45, 0.61], [0.48, 0.80], [0.27, 0.80]],
      "world_points": [[0, 0], [2.5, 0], [2.5, 5.0], [0, 5.0]]
    }
    ```

    Points image en pixels ou normalisés (0-1), points monde en mètres, **dans le même ordre**.

3. `CALIBRATION_FILE=zones/calibration.json` ou `--calibration zones/calibration.json`.

La vitesse s'affiche alors sans `~`. Plus les 4 points couvrent une grande surface de la zone d'intérêt,
meilleure est la précision.

!!! tip
    Avec `python -m vision_lab zones <source> -o zones/brouillon.json`, cliquez les 4 points,
    appuyez sur ++n++ puis ++s++ : le `polygon` enregistré (coordonnées normalisées) se recopie tel quel
    dans `image_points`.
