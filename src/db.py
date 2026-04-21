import sqlite3

from src.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_events (
                event_id     TEXT PRIMARY KEY,
                event_type   TEXT NOT NULL,
                processed_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
