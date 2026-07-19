import sqlite3
import numpy as np
import json
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """ساخت جداول دیتابیس در اولین اجرا"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS authorized_persons (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                role        TEXT,
                encoding    TEXT NOT NULL,   -- JSON array of 128 floats
                enrolled_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS access_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id   INTEGER,         -- NULL اگر غریبه باشد
                person_name TEXT,
                event_type  TEXT NOT NULL,   -- 'authorized' | 'intruder'
                image_path  TEXT,
                detected_at TEXT NOT NULL,
                alerted     INTEGER DEFAULT 0
            )
        """)
        conn.commit()
    logger.info("Database initialized.")


def add_authorized_person(name: str, role: str, encoding: np.ndarray) -> int:
    """افزودن یک فرد مجاز به دیتابیس"""
    encoding_json = json.dumps(encoding.tolist())
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO authorized_persons (name, role, encoding, enrolled_at) VALUES (?, ?, ?, ?)",
            (name, role, encoding_json, datetime.now().isoformat())
        )
        conn.commit()
        logger.info(f"Enrolled authorized person: {name} ({role})")
        return cursor.lastrowid


def get_all_authorized_encodings() -> list[dict]:
    """بازیابی همه encoding های مجاز از دیتابیس"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, role, encoding FROM authorized_persons"
        ).fetchall()

    persons = []
    for row in rows:
        persons.append({
            "id": row[0],
            "name": row[1],
            "role": row[2],
            "encoding": np.array(json.loads(row[3]))
        })
    return persons


def log_event(
    event_type: str,
    image_path: str,
    person_id: int = None,
    person_name: str = "Unknown"
) -> int:
    """ثبت رویداد ورود در دیتابیس"""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO access_events
               (person_id, person_name, event_type, image_path, detected_at, alerted)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (person_id, person_name, event_type, image_path, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid


def mark_event_alerted(event_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE access_events SET alerted = 1 WHERE id = ?", (event_id,)
        )
        conn.commit()
