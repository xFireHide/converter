import re
import sqlite3
import string
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "short_curter.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            original_url TEXT,
            click_count INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


VALID_CODE_PATTERN = re.compile(r"^[A-Za-z0-9-_]{3,64}$")


def validate_custom_code(value: str) -> str:
    code = (value or "").strip()
    if not code:
        raise ValueError("Informe um identificador personalizado.")
    if not VALID_CODE_PATTERN.match(code):
        raise ValueError("Use apenas letras, números, hífen ou underline (3 a 64 caracteres).")
    return code


def shorten_url(original_url: str, desired_code: str | None = None) -> str:
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT code FROM urls WHERE original_url = ?", (original_url,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0]

    if desired_code:
        code = desired_code
        cursor.execute("SELECT id FROM urls WHERE code = ?", (code,))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Esse identificador já está em uso. Escolha outro.")
    else:
        while True:
            code = generate_code()
            cursor.execute("SELECT id FROM urls WHERE code = ?", (code,))
            if not cursor.fetchone():
                break

    cursor.execute(
        "INSERT INTO urls (code, original_url, click_count) VALUES (?, ?, 0)",
        (code, original_url),
    )
    conn.commit()
    conn.close()
    return code


def get_original_url(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT original_url FROM urls WHERE code = ?", (code,))
    row = cursor.fetchone()
    if row:
        cursor.execute(
            "UPDATE urls SET click_count = click_count + 1 WHERE code = ?",
            (code,),
        )
        conn.commit()
        conn.close()
        return row[0]
    conn.close()
    return None


def get_click_count(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT click_count FROM urls WHERE code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return 0


def get_url_details(code: str) -> dict | None:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT code, original_url, click_count FROM urls WHERE code = ?",
        (code,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"code": row[0], "original_url": row[1], "click_count": row[2]}
    return None
