"""Explicit opt-in for deployment behind a public HTTPS gateway; no exposure is provisioned."""

import os
from urllib.parse import urlsplit
from fastapi import HTTPException


def public_mode():
    return os.environ.get("PUBLIC_MODE", "false").lower() == "true"


def public_origin():
    raw = os.environ.get("PUBLIC_ORIGIN", "").rstrip("/")
    p = urlsplit(raw)
    if not p.hostname:
        return raw
    host = p.hostname.encode("idna").decode("ascii").lower()
    if ":" in host:
        host = "[" + host + "]"
    port = f":{p.port}" if p.port and p.port != 443 else ""
    return f"{p.scheme.lower()}://{host}{port}"


def secure_cookie():
    return public_mode() or os.environ.get("COOKIE_SECURE", "false").lower() == "true"


def validate_config():
    if public_mode():
        raw = os.environ.get("PUBLIC_ORIGIN", "").rstrip("/")
        try:
            p = urlsplit(raw)
            _ = p.port  # Validate malformed port values at startup.
        except ValueError as exc:
            raise RuntimeError("PUBLIC_ORIGIN must be a valid HTTPS origin") from exc
        if (
            p.scheme != "https"
            or not p.hostname
            or p.username
            or p.password
            or p.path
            or p.query
            or p.fragment
            or "*" in p.netloc
            or any(c.isspace() for c in raw)
        ):
            raise RuntimeError(
                "PUBLIC_MODE requires PUBLIC_ORIGIN to be one exact HTTPS origin, for example https://holidays.example.com"
            )
        password = os.environ.get("ADMIN_PASSWORD", "")
        if (
            not os.environ.get("ADMIN_PASSWORD_HASH")
            and not os.environ.get("ADMIN_PASSWORD_FILE")
            and len(password) < 16
        ):
            raise RuntimeError(
                "Public mode requires an administrator password of at least 16 characters or an Argon2 hash/password secret file"
            )


def check_request(request):
    if not public_mode():
        return
    host = request.headers.get("host", "").lower()
    expected = urlsplit(public_origin()).netloc.lower()
    if request.url.path == "/api/health" and host in (
        "127.0.0.1:8090",
        "localhost:8090",
    ):
        return
    if host != expected:
        raise HTTPException(400, "Unrecognized host")
