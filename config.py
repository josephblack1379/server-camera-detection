import os

# --- تنظیمات دوربین ---
CAMERA_INDEX = 0          # اندیس دوربین (0 = دوربین پیش‌فرض)
CAMERA_RTSP_URL = None    # اگر از IP Camera استفاده می‌کنید، مثلاً:
                          # "rtsp://admin:pass@192.168.1.100:554/stream"

# --- تنظیمات تشخیص چهره ---
FACE_RECOGNITION_TOLERANCE = 0.5   # آستانه تشخیص (پایین‌تر = سخت‌گیرانه‌تر)
DETECTION_INTERVAL_SECONDS = 3     # فاصله بین هر بررسی (ثانیه)
ALERT_COOLDOWN_SECONDS = 60        # حداقل فاصله بین دو هشدار برای یک غریبه

# --- تنظیمات ایمیل ---
EMAIL_SENDER = "monitor@yourcompany.com"
EMAIL_SENDER_PASSWORD = os.environ.get("MONITOR_EMAIL_PASSWORD", "")  # از متغیر محیطی
EMAIL_RECIPIENT = "ceo@yourcompany.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# --- مسیرها ---
DB_PATH = "server_room.db"
KNOWN_FACES_DIR = "known_faces"
ALERT_IMAGES_DIR = "alert_images"
LOG_FILE = "monitor.log"
