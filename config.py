CCTV_URL = "your_cctv_url"
IMAGE_FILE = "your_image_file_path"
VIDEO_FILE = "D:\Téléchargements\📡 Columbus Circle - New York - USA - Webcam Live Cam HD.mp4"

# Configuration des classes détectées et leurs propriétés
# Format: class_id: (nom_affiché, largeur_moyenne_en_mètres)
CLASS_INFO = {
    0: ("Person", 0.4),        # Personne
    1: ("Bicycle", 0.6),       # Vélo
    2: ("Car", 1.8),           # Voiture
    3: ("Motorcycle", 0.8),    # Moto
    4: ("Airplane", 35.0),     # Avion
    5: ("Bus", 2.5),           # Bus
    6: ("Train", 3.0),         # Train
    7: ("Truck", 2.4),         # Camion
    8: ("Boat", 3.0),          # Bateau
}

# Configuration des couleurs pour chaque classe (format BGR pour OpenCV)
# Format: class_id: (Blue, Green, Red)
CLASS_COLORS = {
    0: (0, 255, 0),      # Vert pour les personnes
    1: (255, 0, 0),      # Bleu pour les vélos
    2: (0, 0, 255),      # Rouge pour les voitures
    3: (255, 255, 0),    # Cyan pour les motos
    4: (128, 0, 128),    # Violet pour les avions
    5: (255, 0, 255),    # Magenta pour les bus
    6: (0, 128, 255),    # Orange pour les trains
    7: (0, 255, 255),    # Jaune pour les camions
    8: (255, 128, 0),    # Bleu clair pour les bateaux
}

# Couleur par défaut pour les classes non définies
DEFAULT_COLOR = (128, 128, 128)  # Gris