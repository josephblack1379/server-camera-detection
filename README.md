# server-camera-detection
Face recognition-based server room access monitor. Enrolls authorized personnel in SQLite, analyzes live camera feed, detects unknown faces, saves snapshots, and sends email alerts. Built with Python, OpenCV, and face\_recognition library.
نحوه راه‌اندازی
۱. ثبت افراد مجاز:
export MONITOR_EMAIL_PASSWORD="your_email_app_password"
python enroll.py --name "علی احمدی" --role "مدیر IT" --image ali.jpg
python enroll.py --name "سارا رضایی" --role "ادمین شبکه" --image sara.jpg
۲. اجرای سیستم:
python main.py
۳. برای IP Camera:

در config.py تنظیم کنید:
CAMERA_RTSP_URL = "rtsp://admin:password@192.168.1.100:554/stream"
۴. اجرا به صورت سرویس در لینوکس:
# /etc/systemd/system/server-monitor.service
[Unit]
Description=Server Room Monitor
After=network.target

[Service]
WorkingDirectory=/opt/server_room_monitor
ExecStart=/usr/bin/python3 main.py
Environment=MONITOR_EMAIL_PASSWORD=your_password
Restart=always

[Install]
WantedBy=multi-user.target
