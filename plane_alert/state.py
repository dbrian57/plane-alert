import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone


class NotificationState:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        with closing(sqlite3.connect(self._db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    entity_id TEXT PRIMARY KEY,
                    last_notified_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def should_notify(self, entity_id: str, cooldown_minutes: int) -> bool:
        with closing(sqlite3.connect(self._db_path)) as conn:
            row = conn.execute(
                "SELECT last_notified_at FROM notifications WHERE entity_id = ?",
                (entity_id,),
            ).fetchone()
        if row is None:
            return True
        last_notified_at = datetime.fromisoformat(row[0])
        return datetime.now(timezone.utc) - last_notified_at > timedelta(minutes=cooldown_minutes)

    def record_notified(self, entity_id: str) -> None:
        with closing(sqlite3.connect(self._db_path)) as conn:
            conn.execute(
                """
                INSERT INTO notifications (entity_id, last_notified_at) VALUES (?, ?)
                ON CONFLICT(entity_id) DO UPDATE SET last_notified_at = excluded.last_notified_at
                """,
                (entity_id, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
