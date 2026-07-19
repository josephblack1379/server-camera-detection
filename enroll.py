"""
ابزار ثبت چهره‌های مجاز در دیتابیس.
استفاده: python enroll.py --name "علی احمدی" --role "مدیر IT" --image path/to/photo.jpg
"""
import argparse
import sys
from database import init_db, add_authorized_person
from face_engine import FaceEngine


def main():
    parser = argparse.ArgumentParser(description="ثبت فرد مجاز در سیستم نظارت")
    parser.add_argument("--name", required=True, help="نام کامل فرد")
    parser.add_argument("--role", default="کارمند", help="نقش/سمت فرد")
    parser.add_argument("--image", required=True, help="مسیر تصویر چهره")
    args = parser.parse_args()

    init_db()

    encoding = FaceEngine.get_encoding_from_image_path(args.image)
    if encoding is None:
        print(f"خطا: چهره‌ای در تصویر '{args.image}' پیدا نشد.")
        sys.exit(1)

    person_id = add_authorized_person(args.name, args.role, encoding)
    print(f"✓ '{args.name}' با شناسه {person_id} در سیستم ثبت شد.")


if __name__ == "__main__":
    main()
