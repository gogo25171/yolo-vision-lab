import cv2
from ultralytics import YOLO
from distance_calculator import DistanceCalculator
import config

# Load the YOLOv8 model
model = YOLO(r'D:\Téléchargements\yolo11n-seg.pt')

# Initialize distance calculator with known object dimensions
distance_calculator = DistanceCalculator(
   known_width=0.4   # Average width of specified classes in meters
)

cctv_url = config.CCTV_URL
image_file = config.IMAGE_FILE
video_file = config.VIDEO_FILE

# Importer les configurations des classes et couleurs
class_info = config.CLASS_INFO
class_colors = config.CLASS_COLORS
default_color = config.DEFAULT_COLOR


def select_input_source():
    """Permet à l'utilisateur de sélectionner la source d'entrée"""
    print("Sélectionnez la source d'entrée :")
    print("1. URL CCTV/Webcam")
    print("2. Fichier image")
    print("3. Fichier vidéo")
    
    while True:
        try:
            choice = int(input("Entrez votre choix (1-3) : "))
            if choice in [1, 2, 3]:
                return choice
            else:
                print("Choix invalide. Veuillez entrer 1, 2 ou 3.")
        except ValueError:
            print("Veuillez entrer un nombre valide.")


def get_input_source(choice):
    """Retourne la source d'entrée basée sur le choix de l'utilisateur"""
    if choice == 1:
        if cctv_url:
            return cctv_url
        else:
            url = input("Entrez l'URL de la webcam/CCTV : ")
            return url
    elif choice == 2:
        if image_file:
            return image_file
        else:
            path = input("Entrez le chemin du fichier image : ")
            return path
    elif choice == 3:
        if video_file:
            return video_file
        else:
            path = input("Entrez le chemin du fichier vidéo : ")
            return path


# Sélection de la source d'entrée
choice = select_input_source()
input_source = get_input_source(choice)

# Traitement spécial pour les images
if choice == 2:  # Image file
    # Pour les images, on lit une seule fois
    frame = cv2.imread(input_source)
    if frame is None:
        print("Erreur lors du chargement de l'image")
        exit()
    
    # Run inference on the image
    results = model(frame)
    
    # Visualize and calculate distances
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            
            if class_id in class_info:
                class_name, known_width = class_info[class_id]
                # Créer un calculateur spécifique pour cette classe
                specific_calculator = DistanceCalculator(
                    known_width=known_width)
                distance = specific_calculator.calculate_distance_class(box)
                label = f"{class_name} {distance:.2f}m"
            else:
                continue

            # Extract box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Utiliser la couleur configurée pour cette classe
            color = class_colors.get(class_id, default_color)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    cv2.imshow('YOLOv8 Inference - Image', frame)
    cv2.waitKey(0)  # Attendre une touche pour fermer
    cv2.destroyAllWindows()
    exit()

# Pour les vidéos et webcams
cap = cv2.VideoCapture(input_source)

if not cap.isOpened():
    print("Erreur lors de l'ouverture du flux vidéo ou du fichier")
    exit()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Run inference on the frame
    results = model(frame)

    # Visualize and calculate distances
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            
            if class_id in class_info:
                class_name, known_width = class_info[class_id]
                # Créer un calculateur spécifique pour cette classe
                specific_calculator = DistanceCalculator(
                    known_width=known_width)
                distance = specific_calculator.calculate_distance_class(box)
                label = f"{class_name} {distance:.2f}m"
            else:
                continue

            # Extract box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Utiliser la couleur configurée pour cette classe
            color = class_colors.get(class_id, default_color)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    cv2.imshow('YOLOv8 Inference', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
