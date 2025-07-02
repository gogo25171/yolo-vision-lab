# 🎯 YOLO Distance Calculator

Un calculateur de distance intelligent utilisant YOLOv11 pour détecter et mesurer la distance des objets en temps réel à partir de vidéos, images ou flux CCTV.

## ✨ Fonctionnalités

- 🔍 **Détection multi-objets** : Détecte personnes, voitures, motos, vélos, bus, camions, etc.
- 📏 **Calcul de distance** : Calcule automatiquement la distance des objets détectés
- 🎨 **Couleurs personnalisables** : Chaque type d'objet a sa propre couleur
- 📹 **Sources multiples** : Supporte vidéos, images et flux CCTV/webcam
- ⚙️ **Configuration flexible** : Personnalisation facile via le fichier config.py
- 🚀 **Interface interactive** : Sélection simple de la source d'entrée

## 🚀 Installation

### Prérequis

- Python (testé avec Python 3.12)
- pip

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Modèle YOLO

Merci de spécifier l'emplacement du modèle YOLO dans le fichier `config.py` en définissant la variable `YOLO_MODEL_PATH`. Par exemple :

```python
YOLO_MODEL_PATH = "chemin/vers/votre/yolovX.pt"
```

Assurez-vous que le chemin pointe vers le fichier du modèle YOLOvX que vous souhaitez utiliser.

## 🎮 Utilisation

### Lancement du programme

```bash
python yolo_distance.py
```

### Menu interactif

Le programme vous propose 3 options :

1. **URL CCTV/Webcam** - Pour les flux en direct
2. **Fichier image** - Pour analyser une image
3. **Fichier vidéo** - Pour analyser une vidéo (Testé avec des vidéos locales)

### Contrôles

- **Images** : Appuyez sur n'importe quelle touche pour fermer
- **Vidéos/CCTV** : Appuyez sur 'q' pour quitter

## ⚙️ Configuration

### Fichier `config.py`

#### Sources d'entrée

```python
CCTV_URL = "votre_url_cctv"
IMAGE_FILE = "chemin/vers/votre/image.jpg"
VIDEO_FILE = "chemin/vers/votre/video.mp4"
```

#### Classes détectées

```python
CLASS_INFO = {
    0: ("Person", 0.4),        # Personne - 0.4m de largeur moyenne
    2: ("Car", 1.8),           # Voiture - 1.8m de largeur moyenne
    3: ("Motorcycle", 0.8),    # Moto - 0.8m de largeur moyenne
    # ... autres classes
}
```

#### Couleurs personnalisées (format BGR)

```python
CLASS_COLORS = {
    0: (0, 255, 0),      # Vert pour les personnes
    2: (0, 0, 255),      # Rouge pour les voitures
    3: (255, 255, 0),    # Cyan pour les motos
    # ... autres couleurs
}
```

## 🎯 Classes détectées par défaut

| Objet | ID | Couleur | Largeur moyenne |
|-------|----|---------|-----------------|
| 👤 Person | 0 | Vert | 0.4m |
| 🚴 Bicycle | 1 | Bleu | 0.6m |
| 🚗 Car | 2 | Rouge | 1.8m |
| 🏍️ Motorcycle | 3 | Cyan | 0.8m |
| ✈️ Airplane | 4 | Violet | 35.0m |
| 🚌 Bus | 5 | Magenta | 2.5m |
| 🚂 Train | 6 | Orange | 3.0m |
| 🚛 Truck | 7 | Jaune | 2.4m |
| 🛥️ Boat | 8 | Bleu clair | 3.0m |
| 🖥️ Monitor | 62 | Blanc | 0.5m |

## 🔧 Personnalisation

### Ajouter une nouvelle classe

```python
# Dans config.py
CLASS_INFO[15] = ("Cat", 0.3)  # Chat avec largeur 0.3m
CLASS_COLORS[15] = (0, 100, 200)  # Couleur orange
```

### Modifier une classe existante

```python
# Changer la largeur des voitures
CLASS_INFO[2] = ("Car", 2.0)  # Nouvelle largeur 2.0m

# Changer la couleur des voitures
CLASS_COLORS[2] = (255, 100, 0)  # Nouvelle couleur
```

## 📁 Structure du projet

```
yolov8_distance_calculator/
├── yolo_distance.py           # Script principal
├── distance_calculator.py     # Logique de calcul de distance
├── config.py                  # Configuration
├── requirements.txt           # Dépendances
└── README.md                 # Documentation
```

## 🛠️ Fonctionnement technique

### Calcul de distance

La distance est calculée en utilisant la formule :

```
Distance = (Largeur_réelle × Distance_focale) / Largeur_perçue_en_pixels
```

### Distance focale

Calculée automatiquement ou utilise une valeur par défaut si aucune source CCTV n'est disponible.

## 🎨 Couleurs BGR

Format utilisé par OpenCV (Bleu, Vert, Rouge) :

- Rouge : `(0, 0, 255)`
- Vert : `(0, 255, 0)`
- Bleu : `(255, 0, 0)`
- Cyan : `(255, 255, 0)`
- Magenta : `(255, 0, 255)`
- Jaune : `(0, 255, 255)`

## 🚀 Exemples d'utilisation

### Analyse d'une image

```bash
python yolo_distance.py
# Choisir option 2
# Entrer le chemin de votre image
```

### Flux webcam

```bash
python yolo_distance.py
# Choisir option 1
# Entrer 0 pour la webcam par défaut
```

### Vidéo locale

```bash
python yolo_distance.py
# Choisir option 3
# Entrer le chemin de votre vidéo
```

## 🔍 Dépannage

### Problèmes courants

## 📋 Dépendances

- `opencv-python` - Traitement d'images et vidéos
- `ultralytics` - Modèles YOLO
- `numpy` - Calculs numériques

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

- Signaler des bugs
- Proposer de nouvelles fonctionnalités
- Améliorer la documentation
- Ajouter de nouvelles classes d'objets

## 🙏 Remerciements

- [Ultralytics](https://ultralytics.com/) pour YOLO
- [OpenCV](https://opencv.org/) pour le traitement d'images
- Merci à [omukesh](https://github.com/omukesh/yolov8_distance_calculator), auteur du projet original dont ce dépôt est un fork.

## PS

- Ce projet a été réalisé en grande partie avec l'aide de GitHub Copilot dans Visual Studio Code en mode agent et avec le model Claude Sonnet 4, une intelligence artificielle d'assistance à la génération de code.

- Je n'ai pas encore vérifié la logique de calcul de distance du projet d'origine dont j'ai réalisé le fork.
