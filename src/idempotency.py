from datetime import datetime, timezone

from src.db import get_connection


def already_processed(event_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_events WHERE event_id = ?", (event_id,)
        ).fetchone()
        return row is not None


def mark_processed(event_id: str, event_type: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_events (event_id, event_type, processed_at) "
            "VALUES (?, ?, ?)",
            (event_id, event_type, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
