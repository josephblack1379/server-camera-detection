import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from config import (
    EMAIL_SENDER, EMAIL_SENDER_PASSWORD,
    EMAIL_RECIPIENT, SMTP_HOST, SMTP_PORT
)

logger = logging.getLogger(__name__)


def send_intruder_alert(image_path: str, detected_at: datetime = None):
    """
    ارسال ایمیل هشدار به مدیر با تصویر ضمیمه.
    پسورد از متغیر محیطی خوانده می‌شود و هرگز در کد نوشته نمی‌شود.
    """
    if not EMAIL_SENDER_PASSWORD:
        logger.error("Email password not set. Export MONITOR_EMAIL_PASSWORD env variable.")
        return False

    timestamp_str = (detected_at or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

    msg = MIMEMultipart("related")
    msg["Subject"] = f"[هشدار امنیتی] ورود فرد غیرمجاز به اتاق سرور - {timestamp_str}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT

    # بدنه HTML ایمیل
    html_body = f"""
    <div dir="rtl" style="font-family: Tahoma, Arial; color: #222;">
        <h2 style="color: #c0392b;">⚠️ هشدار امنیتی</h2>
        <p>
            سیستم نظارت اتاق سرور یک <strong>فرد غیرمجاز</strong> را شناسایی کرده است.
        </p>
        <table style="border-collapse: collapse; width: 400px;">
            <tr>
                <td style="padding: 8px; background: #f5f5f5; font-weight: bold;">زمان تشخیص:</td>
                <td style="padding: 8px;">{timestamp_str}</td>
            </tr>
            <tr>
                <td style="padding: 8px; background: #f5f5f5; font-weight: bold;">وضعیت:</td>
                <td style="padding: 8px; color: #c0392b;">فرد ناشناس شناسایی شد</td>
            </tr>
        </table>
        <br>
        <p>تصویر لحظه تشخیص در ضمیمه ایمیل موجود است:</p>
        <img src="cid:alert_image" style="max-width: 600px; border: 2px solid #c0392b; border-radius: 4px;">
        <br><br>
        <p style="color: #777; font-size: 12px;">
            این پیام به صورت خودکار توسط سیستم نظارت ارسال شده است.
        </p>
    </div>
    """

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # ضمیمه کردن تصویر
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            img = MIMEImage(img_file.read())
            img.add_header("Content-ID", "<alert_image>")
            img.add_header(
                "Content-Disposition", "inline",
                filename=os.path.basename(image_path)
            )
            msg.attach(img)
    else:
        logger.warning(f"Alert image not found: {image_path}")

    # ارسال با TLS
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_SENDER_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_bytes())
        logger.info(f"Alert email sent to {EMAIL_RECIPIENT}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check email credentials.")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
    except OSError as e:
        logger.error(f"Network error while sending email: {e}")
    return False
