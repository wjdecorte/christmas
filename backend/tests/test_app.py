import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import connect, initialize


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCOVERY_ENABLED", "false")
    monkeypatch.setenv("PUBLIC_MODE", "false")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("ADMIN_PASSWORD", "test-password-long-enough")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    r = client.post("/api/auth/login", json={"password": "test-password-long-enough"})
    assert r.status_code == 200
    return {"x-csrf-token": r.json()["csrf"]}


def sample(id="sample", **kwargs):
    return {
        "id": id,
        "name": "Test holiday concert",
        "city": "Canton",
        "category": "concert",
        "season": 2027,
        "occurrences": [
            {
                "start_date": "2027-12-12",
                "end_date": "2027-12-12",
                "start_time": "19:00",
            }
        ],
        **kwargs,
    }


def test_public_seed_and_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    events = client.get("/api/events").json()
    assert len(events) == 43
    assert any(not e["verified"] for e in events)
    assert (
        len(next(e for e in events if e["id"] == "mistletoe-on-main")["occurrences"])
        == 3
    )
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/api/events/missing").status_code == 404


def test_public_cannot_write_or_export(client):
    for method, url, body in [
        ("post", "/api/admin/events", sample()),
        ("put", "/api/admin/events/sample", sample()),
        ("delete", "/api/admin/events/sample", None),
        ("post", "/api/admin/import", {"format": "json", "content": "{}"}),
        ("post", "/api/admin/venues/x/geocode", None),
    ]:
        assert (
            getattr(client, method)(url, **({"json": body} if body else {})).status_code
            == 401
        )
    assert client.get("/api/admin/export").status_code == 401


def test_csrf_origin_and_revocation(client, auth):
    assert client.post("/api/admin/events", json=sample()).status_code == 403
    assert (
        client.post(
            "/api/admin/events",
            json=sample(),
            headers={**auth, "Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert (
        client.post("/api/admin/events", json=sample(), headers=auth).status_code == 201
    )
    cookie = client.cookies.get("holiday_session")
    assert (
        "HttpOnly"
        in client.post(
            "/api/auth/login", json={"password": "test-password-long-enough"}
        ).headers["set-cookie"]
    )
    # Revoke the current session using its own CSRF token.
    current = client.get("/api/auth/session").json()["csrf"]
    assert (
        client.post("/api/auth/logout", headers={"x-csrf-token": current}).status_code
        == 200
    )
    assert client.get("/api/auth/session").status_code == 401
    assert cookie


def test_rate_limit(client):
    for _ in range(5):
        assert (
            client.post("/api/auth/login", json={"password": "wrong"}).status_code
            == 401
        )
    assert (
        client.post(
            "/api/auth/login", json={"password": "test-password-long-enough"}
        ).status_code
        == 429
    )


def test_crud_future_season(client, auth):
    body = sample()
    assert client.post("/api/admin/events", json=body, headers=auth).status_code == 201
    assert len(client.get("/api/events?year=2027").json()) == 1
    body["name"] = "Updated concert"
    assert (
        client.put("/api/admin/events/sample", json=body, headers=auth).status_code
        == 200
    )
    assert client.get("/api/events/sample").json()["name"] == "Updated concert"
    assert 2027 in client.get("/api/meta").json()["years"]
    assert client.delete("/api/admin/events/sample", headers=auth).status_code == 200
    assert client.get("/api/events/sample").status_code == 404


def test_date_overlap_and_recurrence(client):
    e = client.get("/api/events?start=2026-12-10&end=2026-12-10").json()
    assert "mistletoe-on-main" in [x["id"] for x in e]
    assert "roswell-christkindlmarket" in [x["id"] for x in e]
    e = client.get("/api/events?start=2026-12-11&end=2026-12-11").json()
    assert "mistletoe-on-main" not in [x["id"] for x in e]
    assert client.get("/api/events?start=2026-12-11&end=2026-12-01").status_code == 422
    assert all(
        e["city"] == "Canton" and e["verified"]
        for e in client.get("/api/events?city=Canton&verified=true").json()
    )
    assert client.get("/api/events?q=Elvis").json()[0]["id"] == "christmas-with-elvis"


def test_markers_exclude_unknown_coordinates(client):
    result = client.get("/api/markers?category=concert").json()
    all_count = len(client.get("/api/events?category=concert").json())
    assert len(result["events"]) + result["unmapped_count"] == all_count
    assert all(e["venue"]["latitude"] is not None for e in result["events"])


def test_validation_and_venue_restrictions(client, auth):
    assert (
        client.post(
            "/api/admin/events",
            json=sample(source_url="javascript:alert(1)"),
            headers=auth,
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/admin/events", json=sample(verified=True), headers=auth
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/admin/events",
            json=sample(
                occurrences=[{"start_date": "2027-12-12", "end_date": "2027-12-01"}]
            ),
            headers=auth,
        ).status_code
        == 422
    )
    v = {"id": "test-venue", "name": "Test", "city": "Canton", "latitude": 34}
    assert client.post("/api/admin/venues", json=v, headers=auth).status_code == 422
    v.update(longitude=-84, coordinate_source="Official venue source")
    assert client.post("/api/admin/venues", json=v, headers=auth).status_code == 201
    assert (
        client.post(
            "/api/admin/events", json=sample(venue_id="test-venue"), headers=auth
        ).status_code
        == 201
    )
    assert (
        client.delete("/api/admin/venues/test-venue", headers=auth).status_code == 409
    )


@pytest.mark.parametrize("format", ["json", "csv"])
def test_export_import_round_trip(client, auth, format):
    body = sample(
        name='=HYPERLINK("bad")',
        description="-a description",
        price_details="'a literal quote",
    )
    assert client.post("/api/admin/events", json=body, headers=auth).status_code == 201
    exported = client.get("/api/admin/export?format=" + format)
    assert exported.status_code == 200
    assert client.delete("/api/admin/events/sample", headers=auth).status_code == 200
    result = client.post(
        "/api/admin/import",
        json={"format": format, "content": exported.text},
        headers=auth,
    )
    assert result.status_code == 200, result.text
    restored = client.get("/api/events/sample").json()
    assert restored["name"] == body["name"]
    assert restored["description"] == body["description"]
    assert restored["price_details"] == body["price_details"]
    assert restored["occurrences"][0]["start_time"] == "19:00:00"


def test_atomic_import_rollback(client, auth):
    content = {
        "venues": [{"id": "new-venue", "name": "New", "city": "Canton"}],
        "events": [sample("one"), sample("two", venue_id="missing")],
    }
    r = client.post(
        "/api/admin/import",
        json={"format": "json", "content": json.dumps(content)},
        headers=auth,
    )
    assert r.status_code == 409
    assert client.get("/api/events/one").status_code == 404
    assert not any(v["id"] == "new-venue" for v in client.get("/api/venues").json())


def test_seed_not_reapplied_after_delete(client, auth):
    client.delete("/api/admin/events/canton-tree-lighting", headers=auth)
    initialize()
    assert client.get("/api/events/canton-tree-lighting").status_code == 404


def test_cached_geocoding(client, auth, monkeypatch):
    import app.geocoding as geo

    monkeypatch.setenv("GEOCODER_USER_AGENT", "HolidayEventsTest/1.0")
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {"lat": "34.0", "lon": "-84.0", "display_name": "Test fixture only"}
            ]

    def fake_get(*args, **kwargs):
        calls.append(args)
        return FakeResponse()

    monkeypatch.setattr(geo.httpx, "get", fake_get)
    v = {
        "id": "new",
        "name": "Test",
        "city": "Canton",
        "address": "Test fixture address",
    }
    client.post("/api/admin/venues", json=v, headers=auth)
    assert client.post("/api/admin/venues/new/geocode", headers=auth).status_code == 200
    assert client.post("/api/admin/venues/new/geocode", headers=auth).status_code == 200
    assert len(calls) == 1
    assert geo.geocode("Test fixture address, Canton, Georgia, USA")["latitude"] == 34
    assert len(calls) == 1


def test_body_limit(client):
    assert client.post("/api/auth/login", content="x" * 5_000_001).status_code == 413


def test_invalid_csv_and_duplicate_ids(client, auth):
    for content in [
        "id,venue_json\nx,[]\n",
        "id,name,city,category,season\nx,One,Canton,concert,2027\nx,Two,Canton,concert,2027\n",
    ]:
        assert (
            client.post(
                "/api/admin/import",
                json={"format": "csv", "content": content},
                headers=auth,
            ).status_code
            == 422
        )


def test_backup_restore_revokes_sessions(client, auth, tmp_path, monkeypatch):
    import sys
    from app.manage import main

    backup = tmp_path / "backup.sqlite3"
    monkeypatch.setattr(sys, "argv", ["manage", "backup", str(backup)])
    main()
    assert backup.is_file()
    assert (
        client.post("/api/admin/events", json=sample(), headers=auth).status_code == 201
    )
    monkeypatch.setattr(sys, "argv", ["manage", "restore", str(backup)])
    main()
    assert client.get("/api/events/sample").status_code == 404
    assert client.get("/api/auth/session").status_code == 401


def test_favicon_serves_svg_instead_of_spa_html(client, tmp_path, monkeypatch):
    import app.main as main_module
    from pathlib import Path

    source = Path(__file__).resolve().parents[2] / "frontend/public/favicon.svg"
    (tmp_path / "favicon.svg").write_bytes(source.read_bytes())
    monkeypatch.setattr(main_module, "DIST", tmp_path)
    response = client.get("/favicon.svg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.content == source.read_bytes()
