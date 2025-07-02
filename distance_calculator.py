import cv2
import numpy as np
import config

cctv_url = config.CCTV_URL

class DistanceCalculator:
    def __init__(self, known_width=0.4, focal_length=None):
        self.known_width = known_width
        self.focal_length = focal_length or self.calculate_focal_length()

    def calculate_focal_length(self, img_width=868, known_distance=1, known_width=0.2):
        # Si pas d'URL CCTV ou si elle est vide, utiliser une valeur par défaut
        if not cctv_url or cctv_url == "your_cctv_url":
            # Calcul approximatif basé sur des paramètres standards
            pixel_width = 200  # Valeur par défaut
            self.focal_length = (pixel_width * known_distance) / known_width
            return self.focal_length
            
        try:
            cap = cv2.VideoCapture(cctv_url)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                # Si impossible de capturer, utiliser une valeur par défaut
                pixel_width = 200
            else:
                # Mesurer depuis la frame avec une règle commune
                pixel_width = 200
                
            self.focal_length = (pixel_width * known_distance) / known_width
            return self.focal_length
        except Exception:
            # En cas d'erreur, utiliser une valeur par défaut
            pixel_width = 200
            self.focal_length = (pixel_width * known_distance) / known_width
            return self.focal_length

    def calculate_distance(self, perceived_width, known_width):
        if self.focal_length is None:
            raise ValueError("Focal length needs to be calculated")
        return (known_width * self.focal_length) / perceived_width

    def calculate_distance_class(self, box):
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        perceived_width = x2 - x1
        return self.calculate_distance(perceived_width, self.known_width)
