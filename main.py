import cv2
import os
import time
import logging
import signal
import sys
from datetime import datetime
from collections import defaultdict

from config import (
    CAMERA_INDEX, CAMERA_RTSP_URL,
    DETECTION_INTERVAL_SECONDS, ALERT_COOLDOWN_SECONDS,
    ALERT_IMAGES_DIR, LOG_FILE
)
from database import init_db, log_event, mark_event_alerted
from face_engine import FaceEngine
from notifier import send_intruder_alert

# --- راه‌اندازی لاگر ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")

# زمان آخرین هشدار برای جلوگیری از spam ایمیل
last_alert_time: dict[str, float] = defaultdict(float)


def save_alert_image(frame, label: str) -> str:
    """ذخیره فریم هشدار در پوشه مخصوص"""
    os.makedirs(ALERT_IMAGES_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ALERT_IMAGES_DIR}/intruder_{timestamp}_{label}.jpg"
    cv2.imwrite(filename, frame)
    return filename


def draw_annotations(frame, faces: list[dict]) -> None:
    """رسم مستطیل و برچسب روی فریم برای نمایش"""
    for face in faces:
        top, right, bottom, left = face["location"]
        color = (0, 200, 0) if face["is_authorized"] else (0, 0, 220)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        label = face["name"]
        cv2.rectangle(frame, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
        cv2.putText(
            frame, label,
            (left + 6, bottom - 8),
            cv2.FONT_HERSHEY_DUPLEX, 0.6,
            (255, 255, 255), 1
        )


def handle_intruder(frame, face: dict):
    """پردازش و اطلاع‌رسانی برای فرد ناشناس"""
    now = time.time()
    cooldown_key = "intruder"  # همه ناشناس‌ها یک cooldown مشترک دارند

    if now - last_alert_time[cooldown_key] < ALERT_COOLDOWN_SECONDS:
        logger.debug("Intruder alert suppressed (cooldown active).")
        return

    last_alert_time[cooldown_key] = now
    image_path = save_alert_image(frame, "unknown")
    event_id = log_event(
        event_type="intruder",
        image_path=image_path,
        person_name="Unknown"
    )

    logger.warning(f"INTRUDER DETECTED. Image saved: {image_path}")

    success = send_intruder_alert(image_path, detected_at=datetime.now())
    if success:
        mark_event_alerted(event_id)


def open_camera() -> cv2.VideoCapture:
    source = CAMERA_RTSP_URL if CAMERA_RTSP_URL else CAMERA_INDEX
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error(f"Cannot open camera source: {source}")
        sys.exit(1)
    logger.info(f"Camera opened: {source}")
    return cap


def main():
    init_db()
    engine = FaceEngine()
    cap = open_camera()

    # برای خروج تمیز با Ctrl+C
    running = True
    def shutdown(sig, frame):
        nonlocal running
        logger.info("Shutting down...")
        running = False
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    last_analysis_time = 0.0
    logger.info("Monitoring started. Press Ctrl+C to stop.")

    while running:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Failed to read frame. Retrying in 5s...")
            time.sleep(5)
            cap.release()
            cap = open_camera()
            continue

        now = time.time()

        # تحلیل هر DETECTION_INTERVAL_SECONDS ثانیه یک‌بار
        if now - last_analysis_time >= DETECTION_INTERVAL_SECONDS:
            last_analysis_time = now

            faces = engine.analyze_frame(frame)

            for face in faces:
                if face["is_authorized"]:
                    logger.info(f"Authorized access: {face['name']}")
                    log_event(
                        event_type="authorized",
                        image_path=None,
                        person_id=face["person_id"],
                        person_name=face["name"]
                    )
                else:
                    handle_intruder(frame, face)

            draw_annotations(frame, faces)

        # نمایش ویدیو (اختیاری - حذف کنید اگر headless اجرا می‌شود)
        cv2.imshow("Server Room Monitor", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    logger.info("Monitor stopped.")


if __name__ == "__main__":
    main()
