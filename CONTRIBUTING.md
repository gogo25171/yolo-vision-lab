# Contribuer

Merci de votre intérêt ! Les contributions sont les bienvenues : bugs, idées, formats de plaques, documentation…

## Mettre en place l'environnement

```bash
git clone https://github.com/gogo25171/yolo-vision-lab.git
cd yolo-vision-lab
git lfs install && git lfs pull          # échantillons vidéo
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt -r projets/distance_vitesse/requirements.txt -r requirements-docs.txt pytest ruff
```

## Avant d'ouvrir une pull request

```bash
ruff check vision_lab projets scripts tests     # style et erreurs courantes
python -m pytest                             # tests (sans GPU)
mkdocs build --strict                        # documentation
```

- Une PR = un sujet. Décrivez le **pourquoi** et la manière de tester.
- Ajoutez un test pour toute logique pure (formats de plaques, zones, mesures…).
- Mettez à jour la documentation (`docs/`) et `CHANGELOG.md` (section « Non publié »).
- Le code et la documentation sont en français ; les noms de variables restent en anglais.

## Ajouter un format de plaque

1. Ajoutez une entrée dans `FORMATS` (`projets/distance_vitesse/plate_formats.py`), la clé étant le nom du pays tel
   que renvoyé par l'OCR.
2. Ajoutez des cas dans `tests/test_core.py::test_plate_normalize`.
3. Complétez le tableau de `docs/fonctionnalites/plaques.md`.

## Signaler un bug

Ouvrez une *issue* avec : commande lancée, contenu du `.env` (sans mots de passe), matériel (GPU, OS),
message d'erreur complet, et si possible une image de la scène.

## Licence

En contribuant, vous acceptez que votre contribution soit publiée sous licence AGPL-3.0-or-later.
