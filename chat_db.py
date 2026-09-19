import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "chat.db"

def init_chat_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            user_name TEXT NOT NULL,
            text TEXT NOT NULL,
            color TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_message(room: str, user_name: str, text: str, color: str):
    cleanup_old_messages()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (room, user_name, text, color, created_at) VALUES (?, ?, ?, ?, ?)",
        (room, user_name, text, color, datetime.utcnow())
    )
    conn.commit()
    conn.close()

def get_recent_messages(room: str):
    cleanup_old_messages()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_name, text, color, created_at FROM messages WHERE room = ? ORDER BY created_at ASC",
        (room,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def cleanup_old_messages():
    cutoff = datetime.utcnow() - timedelta(hours=24)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE created_at < ?", (cutoff,))
    conn.commit()
    conn.close()

init_chat_db()