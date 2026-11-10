"""Offline maintenance: python -m app.manage backup|restore PATH or hash-password."""

import argparse
import getpass
import os
import sqlite3
from pathlib import Path
from .db import connect
from .security import password_hasher


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["backup", "restore", "hash-password"])
    parser.add_argument("path", nargs="?")
    args = parser.parse_args()
    if args.command == "hash-password":
        password = getpass.getpass("Administrator password (12+ characters): ")
        if len(password) < 12:
            parser.error("Password must contain at least 12 characters")
        print(password_hasher.hash(password))
        return
    if not args.path:
        parser.error("A backup path is required")
    path = Path(args.path)
    current = Path(os.environ.get("DATABASE_PATH", "data/events.sqlite3"))
    if path.resolve() == current.resolve():
        parser.error("Backup path must differ from database path")
    if args.command == "backup":
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            parser.error("Backup already exists; use a new filename")
        with connect() as source, sqlite3.connect(path) as destination:
            source.backup(destination)
        os.chmod(path, 0o600)
        print(f"Backup saved: {path}")
    else:
        if not path.is_file():
            parser.error("Backup not found")
        with sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True) as source:
            if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                parser.error("Backup integrity check failed")
            if not source.execute(
                "SELECT 1 FROM sqlite_master WHERE name='events'"
            ).fetchone():
                parser.error("Not an events database")
            with connect() as destination:
                source.backup(destination)
                destination.execute("DELETE FROM sessions")
        print("Restore complete; administrator sessions revoked. Start the app.")


if __name__ == "__main__":
    main()
