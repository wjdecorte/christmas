import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect():
    path = Path(os.environ.get("DATABASE_PATH", "data/events.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=15000")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize():
    with connect() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for path in sorted((ROOT / "backend" / "migrations").glob("*.sql")):
            if not db.execute(
                "SELECT 1 FROM schema_migrations WHERE version=?", (path.stem,)
            ).fetchone():
                # Apply all statements and version stamp in the same transaction.
                for statement in path.read_text().split(";"):
                    if statement.strip():
                        db.execute(statement)
                db.execute(
                    "INSERT INTO schema_migrations VALUES (?,?)", (path.stem, now())
                )
        if not db.execute("SELECT 1 FROM metadata WHERE key='seed_loaded'").fetchone():
            from .models import Dataset

            seed = Path(os.environ.get("SEED_PATH", str(ROOT / "data" / "seed.json")))
            if seed.exists():
                data = Dataset.model_validate_json(seed.read_text())
                import_dataset(db, data)
            db.execute("INSERT INTO metadata VALUES ('seed_loaded',?)", (now(),))


def save_venue(db, venue):
    values = venue.model_dump()
    keys = list(values)
    db.execute(
        f"INSERT INTO venues ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)}) ON CONFLICT(id) DO UPDATE SET {','.join(k + '=excluded.' + k for k in keys if k != 'id')}",
        list(values.values()),
    )


def save_event(db, event):
    values = event.model_dump(mode="json", exclude={"occurrences"})
    values["updated_at"] = now()
    keys = list(values)
    db.execute(
        f"INSERT INTO events ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)}) ON CONFLICT(id) DO UPDATE SET {','.join(k + '=excluded.' + k for k in keys if k != 'id')}",
        list(values.values()),
    )
    db.execute("DELETE FROM occurrences WHERE event_id=?", (event.id,))
    for occurrence in event.occurrences:
        d = occurrence.model_dump(mode="json")
        db.execute(
            "INSERT INTO occurrences(event_id,start_date,end_date,start_time,end_time) VALUES (?,?,?,?,?)",
            (event.id, *d.values()),
        )


def import_dataset(db, data):
    for venue in data.venues:
        save_venue(db, venue)
    for event in data.events:
        save_event(db, event)


def event_rows(db):
    events = [dict(row) for row in db.execute("SELECT * FROM events")]
    venues = {row["id"]: dict(row) for row in db.execute("SELECT * FROM venues")}
    occurrences = {}
    for row in db.execute(
        "SELECT event_id,start_date,end_date,start_time,end_time FROM occurrences ORDER BY start_date,start_time"
    ):
        d = dict(row)
        occurrences.setdefault(d.pop("event_id"), []).append(d)
    for event in events:
        event["verified"] = bool(event["verified"])
        event["featured"] = bool(event["featured"])
        event["venue"] = venues.get(event["venue_id"])
        event["occurrences"] = occurrences.get(event["id"], [])
    return events
