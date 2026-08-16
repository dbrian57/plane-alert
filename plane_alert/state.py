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
                    icao24 TEXT PRIMARY KEY,
                    last_notified_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def should_notify(self, icao24: str, cooldown_minutes: int) -> bool:
        with closing(sqlite3.connect(self._db_path)) as conn:
            row = conn.execute(
                "SELECT last_notified_at FROM notifications WHERE icao24 = ?",
                (icao24,),
            ).fetchone()
        if row is None:
            return True
        last_notified_at = datetime.fromisoformat(row[0])
        return datetime.now(timezone.utc) - last_notified_at > timedelta(minutes=cooldown_minutes)

    def record_notified(self, icao24: str) -> None:
        with closing(sqlite3.connect(self._db_path)) as conn:
            conn.execute(
                """
                INSERT INTO notifications (icao24, last_notified_at) VALUES (?, ?)
                ON CONFLICT(icao24) DO UPDATE SET last_notified_at = excluded.last_notified_at
                """,
                (icao24, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
