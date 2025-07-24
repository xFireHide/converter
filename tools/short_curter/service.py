import os
import sqlite3
import string
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "short_curter.db")


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


def shorten_url(original_url):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT code FROM urls WHERE original_url = ?", (original_url,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0]

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
