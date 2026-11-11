import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.public_config import validate_config


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "public.sqlite3"))
    monkeypatch.setenv("DISCOVERY_ENABLED", "false")
    monkeypatch.setenv("PUBLIC_MODE", "true")
    monkeypatch.setenv("PUBLIC_ORIGIN", "https://holidays.example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "a-strong-test-password-only")
    monkeypatch.delenv("ADMIN_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD_FILE", raising=False)
    return monkeypatch


def test_public_reads_anonymous_but_writes_require_auth_and_expected_origin(setup):
    with TestClient(app, base_url="https://holidays.example.com") as c:
        r = c.get("/api/events")
        assert r.status_code == 200 and len(r.json()) == 43
        assert r.headers["strict-transport-security"] == "max-age=15552000"
        assert r.headers["x-robots-tag"] == "noindex, nofollow"
        assert (
            c.get("/api/events", headers={"host": "evil.example.com"}).status_code
            == 400
        )
        assert (
            c.get("/api/health", headers={"host": "127.0.0.1:8090"}).status_code == 200
        )
        assert (
            c.post(
                "/api/admin/import", json={"format": "json", "content": "{}"}
            ).status_code
            == 401
        )
        assert (
            c.post(
                "/api/auth/login",
                json={"password": "a-strong-test-password-only"},
                headers={"origin": "http://holidays.example.com"},
            ).status_code
            == 403
        )
        r = c.post(
            "/api/auth/login",
            json={"password": "a-strong-test-password-only"},
            headers={"origin": "https://holidays.example.com"},
        )
        assert r.status_code == 200
        from http.cookies import SimpleCookie

        cookie = SimpleCookie(r.headers["set-cookie"])["holiday_session"]
        assert (
            cookie["secure"] and cookie["httponly"] and cookie["samesite"] == "strict"
        )
        csrf = {"x-csrf-token": r.json()["csrf"]}
        assert c.get("/api/admin/sources").status_code == 200
        assert (
            c.post(
                "/api/auth/logout",
                headers={**csrf, "origin": "https://other.example.com"},
            ).status_code
            == 403
        )
        assert (
            c.post(
                "/api/auth/logout",
                headers={**csrf, "origin": "https://holidays.example.com"},
            ).status_code
            == 200
        )
        assert c.get("/api/auth/session").status_code == 401


@pytest.mark.parametrize(
    "origin",
    [
        "",
        "http://holidays.example.com",
        "https://*.example.com",
        "https://holidays.example.com/path",
        "https://user:secret@holidays.example.com",
    ],
)
def test_public_mode_fails_closed_for_invalid_origin(setup, origin):
    setup.setenv("PUBLIC_ORIGIN", origin)
    with pytest.raises(RuntimeError, match="PUBLIC_ORIGIN"):
        validate_config()


def test_public_mode_requires_longer_password(setup):
    setup.setenv("ADMIN_PASSWORD", "twelve-chars!")
    with pytest.raises(RuntimeError, match="16 characters"):
        validate_config()


def test_secret_file_password_length_is_enforced(setup, tmp_path):
    p = tmp_path / "secret"
    p.write_text("short")
    setup.setenv("ADMIN_PASSWORD_FILE", str(p))
    with pytest.raises(RuntimeError):
        with TestClient(app, base_url="https://holidays.example.com"):
            pass


def test_restart_revokes_old_sessions(setup):
    with TestClient(app, base_url="https://holidays.example.com") as c:
        c.post("/api/auth/login", json={"password": "a-strong-test-password-only"})
        cookies = dict(c.cookies)
        assert c.get("/api/auth/session").status_code == 200
    with TestClient(app, base_url="https://holidays.example.com") as c:
        c.cookies.update(cookies)
        assert c.get("/api/auth/session").status_code == 401
