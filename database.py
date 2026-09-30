import sqlite3
import datetime
from config import FREE_DAILY_LIMIT

DB_NAME = "bot_database.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            subscription TEXT DEFAULT 'free',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            selected_style TEXT DEFAULT 'polite'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            module TEXT,
            used_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    conn.commit()
    conn.close()


def add_or_update_user(user_id: int, username: str, full_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, username, full_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name
    """, (user_id, username, full_name))
    conn.commit()
    conn.close()


def get_user(user_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def set_user_style(user_id: int, style: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET selected_style = ? WHERE user_id = ?",
        (style, user_id)
    )
    conn.commit()
    conn.close()


def log_usage(user_id: int, module: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usage_log (user_id, module) VALUES (?, ?)",
        (user_id, module)
    )
    conn.commit()
    conn.close()


def get_today_usage_count(user_id: int, module: str = "shield") -> int:
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM usage_log
        WHERE user_id = ? AND module = ? AND date(used_at) = date(?)
    """, (user_id, module, today))
    count = cursor.fetchone()["cnt"]
    conn.close()
    return count


def check_limit(user_id: int, module: str = "shield") -> bool:
    user = get_user(user_id)
    if not user:
        return False
    if user["subscription"] != "free":
        return True
    count = get_today_usage_count(user_id, module)
    return count < FREE_DAILY_LIMIT


def set_subscription(user_id: int, sub_type: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET subscription = ? WHERE user_id = ?",
        (sub_type, user_id)
    )
    conn.commit()
    conn.close()
