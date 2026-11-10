import hashlib
import os
import secrets
import time
from pathlib import Path
from urllib.parse import urlparse
from fastapi import HTTPException, Request, Header
from pwdlib import PasswordHash
from .db import connect

password_hasher = PasswordHash.recommended()


def configure_password():
    configured = os.environ.get("ADMIN_PASSWORD_HASH", "")
    if configured:
        return configured
    secret_file = os.environ.get("ADMIN_PASSWORD_FILE")
    password = (
        Path(secret_file).read_text().strip()
        if secret_file
        else os.environ.get("ADMIN_PASSWORD", "")
    )
    if len(password) < 12:
        raise RuntimeError(
            "Set ADMIN_PASSWORD (at least 12 characters), ADMIN_PASSWORD_FILE, or ADMIN_PASSWORD_HASH before starting."
        )
    return password_hasher.hash(password)


def same_origin(request: Request):
    origin = request.headers.get("origin")
    if origin and urlparse(origin).netloc != request.headers.get("host"):
        raise HTTPException(403, "Cross-origin writes are not permitted")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Cross-site writes are not permitted")


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def session(request: Request):
    token = request.cookies.get("holiday_session", "")
    with connect() as db:
        row = db.execute(
            "SELECT * FROM sessions WHERE token_hash=? AND expires_at>?",
            (token_hash(token), int(time.time())),
        ).fetchone()
    if not row:
        raise HTTPException(401, "Sign in to administer events")
    return dict(row)


def admin(request: Request, x_csrf_token: str | None = Header(default=None, description="CSRF token returned by /api/auth/login or /api/auth/session")):
    result = session(request)
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        same_origin(request)
        if not secrets.compare_digest(
            request.headers.get("x-csrf-token", ""), result["csrf"]
        ):
            raise HTTPException(403, "Session check failed. Sign in again.")
    return result
