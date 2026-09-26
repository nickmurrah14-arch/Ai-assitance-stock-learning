"""SQLite storage for conversations and lead state. One file, no server."""
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    business TEXT NOT NULL,      -- the client's Twilio number
    caller TEXT NOT NULL,        -- the customer's number
    direction TEXT NOT NULL,     -- 'in' or 'out'
    body TEXT NOT NULL,
    ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS messages_thread ON messages (business, caller, ts);
CREATE TABLE IF NOT EXISTS leads (
    business TEXT NOT NULL,
    caller TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    notified_at REAL,
    emergency_notified_at REAL,
    opted_out INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (business, caller)
);
CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY,
    business TEXT NOT NULL,
    caller TEXT NOT NULL,
    texted INTEGER NOT NULL,     -- 1 if the caller got the auto-text (0: opted out or texted recently)
    ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS calls_business ON calls (business, ts);
"""


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._db() as db:
            db.executescript(SCHEMA)

    def _db(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def add_message(self, business: str, caller: str, direction: str, body: str) -> None:
        with self._db() as db:
            db.execute(
                "INSERT INTO messages (business, caller, direction, body, ts) VALUES (?, ?, ?, ?, ?)",
                (business, caller, direction, body, time.time()),
            )
            db.execute("INSERT OR IGNORE INTO leads (business, caller) VALUES (?, ?)", (business, caller))

    def log_call(self, business: str, caller: str, texted: bool) -> None:
        with self._db() as db:
            db.execute(
                "INSERT INTO calls (business, caller, texted, ts) VALUES (?, ?, ?, ?)",
                (business, caller, int(texted), time.time()),
            )

    def thread(self, business: str, caller: str, limit: int = 30) -> list[dict]:
        with self._db() as db:
            rows = db.execute(
                "SELECT direction, body, ts FROM messages WHERE business = ? AND caller = ? "
                "ORDER BY ts DESC, id DESC LIMIT ?",
                (business, caller, limit),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def replies_since(self, business: str, caller: str, since: float) -> int:
        with self._db() as db:
            return db.execute(
                "SELECT COUNT(*) FROM messages WHERE business = ? AND caller = ? AND direction = 'out' AND ts >= ?",
                (business, caller, since),
            ).fetchone()[0]

    def lead(self, business: str, caller: str) -> dict:
        with self._db() as db:
            db.execute("INSERT OR IGNORE INTO leads (business, caller) VALUES (?, ?)", (business, caller))
            return dict(db.execute(
                "SELECT * FROM leads WHERE business = ? AND caller = ?", (business, caller)
            ).fetchone())

    def update_lead(self, business: str, caller: str, **fields) -> None:
        self.lead(business, caller)
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self._db() as db:
            db.execute(
                f"UPDATE leads SET {cols} WHERE business = ? AND caller = ?",
                (*fields.values(), business, caller),
            )
