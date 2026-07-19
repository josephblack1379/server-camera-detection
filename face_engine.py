import face_recognition
import numpy as np
import cv2
import logging
from database import get_all_authorized_encodings
from config import FACE_RECOGNITION_TOLERANCE

logger = logging.getLogger(__name__)


class FaceEngine:
    def __init__(self):
        self.authorized = []
        self.reload_authorized()

    def reload_authorized(self):
        """بارگذاری مجدد لیست مجاز از دیتابیس (بدون نیاز به ری‌استارت)"""
        self.authorized = get_all_authorized_encodings()
        logger.info(f"Loaded {len(self.authorized)} authorized face(s) from DB.")

    def analyze_frame(self, frame: np.ndarray) -> list[dict]:
        """
        تحلیل یک فریم و بازگشت لیست چهره‌های شناسایی‌شده.
        هر آیتم: {'name': str, 'person_id': int|None, 'location': tuple, 'is_authorized': bool}
        """
        # کوچک کردن تصویر برای سرعت بیشتر
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        if not face_locations:
            return []

        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        results = []
        known_encodings = [p["encoding"] for p in self.authorized]

        for encoding, location in zip(face_encodings, face_locations):
            name = "Unknown"
            person_id = None
            is_authorized = False

            if known_encodings:
                distances = face_recognition.face_distance(known_encodings, encoding)
                best_idx = int(np.argmin(distances))
                if distances[best_idx] <= FACE_RECOGNITION_TOLERANCE:
                    person = self.authorized[best_idx]
                    name = person["name"]
                    person_id = person["id"]
                    is_authorized = True

            # مقیاس مکان به اندازه اصلی برگرداندن
            top, right, bottom, left = location
            scaled_location = (top * 2, right * 2, bottom * 2, left * 2)

            results.append({
                "name": name,
                "person_id": person_id,
                "location": scaled_location,
                "is_authorized": is_authorized
            })

        return results

    @staticmethod
    def get_encoding_from_image_path(image_path: str) -> np.ndarray | None:
        """استخراج face encoding از یک فایل تصویر"""
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            logger.warning(f"No face found in image: {image_path}")
            return None
        if len(encodings) > 1:
            logger.warning(f"Multiple faces in image, using the first one: {image_path}")
        return encodings[0]
