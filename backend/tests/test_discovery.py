import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import connect, initialize, event_rows
from app.discovery import (
    observe_records,
    observe_page,
    run_due_sources,
    check_source,
    Source,
)
from app.source_parse import jsonld_records, ical_records
from app.source_fetch import validate_url, PublicHTTPS

YEAR = datetime.now(ZoneInfo("America/New_York")).year


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "events.sqlite3"))
    monkeypatch.setenv("DISCOVERY_ENABLED", "false")
    monkeypatch.setenv("PUBLIC_MODE", "false")
    monkeypatch.setenv("ADMIN_PASSWORD", "this-is-a-test-password")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    return {
        "x-csrf-token": client.post(
            "/api/auth/login", json={"password": "this-is-a-test-password"}
        ).json()["csrf"]
    }


@pytest.fixture
def source(client):
    with connect() as db:
        return dict(
            db.execute(
                "SELECT * FROM discovery_sources WHERE id='kennesaw-calendar'"
            ).fetchone()
        )


def record(name="Christmas Test Concert", day="12-12", status="scheduled"):
    return {
        "external_id": "event-1",
        "fields": {
            "name": name,
            "source_url": "https://www.kennesaw-ga.gov/kennesaw-event/test/",
            "status": status,
            "occurrences": [
                dict(
                    start_date=f"{YEAR}-{day}",
                    end_date=f"{YEAR}-{day}",
                    start_time="19:00:00",
                    end_time=None,
                )
            ],
        },
        "venue": {
            "name": "Test Venue",
            "address": "123 Source Street, Kennesaw, GA",
            "city": "Kennesaw",
        },
        "evidence": "Synthetic source fixture",
    }


def pending(client):
    return client.get("/api/admin/review").json()


def test_public_cannot_access_discovery(client):
    for url in ["/api/admin/sources", "/api/admin/review", "/api/admin/review-audit"]:
        assert client.get(url).status_code == 401
    assert client.post("/api/admin/sources/kennesaw-calendar/check").status_code == 401
    assert client.post("/api/admin/review/nope/approve", json={}).status_code == 401


def test_observation_is_private_until_approved_and_duplicate_is_not_requeued(
    client, auth, source
):
    before = client.get("/api/events").json()
    assert observe_records(source, [record()]) == 1
    assert client.get("/api/events").json() == before
    assert observe_records(source, [record()]) == 0
    p = pending(client)[0]
    assert p["kind"] == "new" and not p["proposed"]["verified"]
    r = client.post(
        "/api/admin/review/" + p["id"] + "/approve",
        headers=auth,
        json={"event": p["proposed"], "venue": p["venue"]},
    )
    assert r.status_code == 200, r.text
    assert len(client.get("/api/events").json()) == len(before) + 1
    assert (
        client.get("/api/events/" + p["proposed"]["id"]).json()["venue"]["latitude"]
        is None
    )
    assert (
        client.post(
            "/api/admin/review/" + p["id"] + "/approve",
            headers=auth,
            json={"event": p["proposed"], "venue": p["venue"]},
        ).status_code
        == 409
    )
    assert len(client.get("/api/admin/review-audit").json()) == 1


def test_changed_schedule_and_cancellation_preserve_published_until_approval(
    client, auth, source
):
    observe_records(source, [record()])
    p = pending(client)[0]
    client.post(
        "/api/admin/review/" + p["id"] + "/approve",
        headers=auth,
        json={"event": p["proposed"], "venue": p["venue"]},
    )
    assert observe_records(source, [record(day="12-13", status="cancelled")]) == 1
    p = pending(client)[0]
    assert p["kind"] == "changed"
    assert client.get("/api/events/" + p["event_id"]).json()["status"] == "scheduled"
    assert (
        client.post(
            "/api/admin/review/" + p["id"] + "/approve",
            headers=auth,
            json={"event": p["proposed"], "venue": p["venue"]},
        ).status_code
        == 200
    )
    assert client.get("/api/events/" + p["event_id"]).json()["status"] == "cancelled"


def test_dismissal_and_superseded_proposals(client, auth, source):
    observe_records(source, [record()])
    p = pending(client)[0]
    client.post(
        "/api/admin/review/" + p["id"] + "/dismiss",
        headers=auth,
        json={"note": "Not an area event"},
    )
    assert observe_records(source, [record()]) == 0 and not pending(client)
    observe_records(source, [record(day="12-13")])
    old = pending(client)[0]
    observe_records(source, [record(day="12-14")])
    new = pending(client)[0]
    assert new["id"] != old["id"] and len(pending(client)) == 1
    assert (
        client.post(
            "/api/admin/review/" + old["id"] + "/approve",
            headers=auth,
            json={"event": old["proposed"], "venue": old["venue"]},
        ).status_code
        == 409
    )
    assert len(client.get("/api/events").json()) == 43


def test_concurrent_manual_edit_blocks_approval_and_can_rebase(client, auth, source):
    observe_records(source, [record()])
    p = pending(client)[0]
    client.post(
        "/api/admin/review/" + p["id"] + "/approve",
        headers=auth,
        json={"event": p["proposed"], "venue": p["venue"]},
    )
    observe_records(source, [record(day="12-13")])
    p = pending(client)[0]
    event = client.get("/api/events/" + p["event_id"]).json()
    event["featured"] = True
    client.put("/api/admin/events/" + event["id"], headers=auth, json=event)
    assert (
        client.post(
            "/api/admin/review/" + p["id"] + "/approve",
            headers=auth,
            json={"event": p["proposed"], "venue": p["venue"]},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/admin/review/" + p["id"] + "/rebase", headers=auth
        ).status_code
        == 200
    )
    p = pending(client)[0]
    assert p["proposed"]["featured"] is True
    assert (
        client.post(
            "/api/admin/review/" + p["id"] + "/approve",
            headers=auth,
            json={"event": p["proposed"], "venue": p["venue"]},
        ).status_code
        == 200
    )


def test_failure_does_not_delete_or_modify_events_and_records_error(
    client, monkeypatch
):
    before = client.get("/api/events").json()

    def fail(*args):
        raise ValueError("Source returned HTTP 503")

    monkeypatch.setattr("app.discovery.check_source", fail)
    assert run_due_sources()
    assert client.get("/api/events").json() == before
    with connect() as db:
        row = db.execute(
            "SELECT * FROM discovery_sources WHERE checked_count=1"
        ).fetchone()
        assert (
            "503" in row["last_error"]
            and row["lease_until"] == 0
            and row["next_check"] > time.time()
        )


def test_source_leases_and_manual_check_cooldown(client, auth, monkeypatch):
    monkeypatch.setenv("DISCOVERY_ENABLED", "true")
    with connect() as db:
        db.execute(
            "UPDATE discovery_sources SET lease_until=?", (int(time.time()) + 3600,)
        )
    assert not run_due_sources()
    assert (
        client.post(
            "/api/admin/sources/kennesaw-calendar/check", headers=auth
        ).status_code
        == 409
    )
    with connect() as db:
        db.execute(
            "UPDATE discovery_sources SET lease_until=0,last_checked=?",
            (datetime.now(ZoneInfo("UTC")).isoformat(),),
        )
    assert (
        client.post(
            "/api/admin/sources/kennesaw-calendar/check", headers=auth
        ).status_code
        == 429
    )


def test_plain_page_baseline_change_and_missing_page_are_not_cancellations(
    client, auth, source
):
    with connect() as db:
        event = event_rows(db)[0]
    assert (
        observe_page(
            source, event, 200, "Original schedule", "https://www.kennesaw-ga.gov/test"
        )
        == 0
    )
    assert (
        observe_page(
            source, event, 200, "Changed schedule", "https://www.kennesaw-ga.gov/test"
        )
        == 1
    )
    p = pending(client)[0]
    assert p["kind"] == "page_changed"
    assert observe_page(source, event, 404, "", "https://www.kennesaw-ga.gov/test") == 1
    p = pending(client)[0]
    assert p["kind"] == "source_unavailable" and p["proposed"]["status"] == "scheduled"


def test_jsonld_only_source_facts_timezone_and_html_sanitization():
    body = (
        '<script type="application/ld+json">'
        + json.dumps(
            {
                "@graph": [
                    {
                        "@type": "MusicEvent",
                        "@id": "stable",
                        "name": "Holiday <b>concert</b>",
                        "startDate": f"{YEAR}-12-12T00:30:00Z",
                        "endDate": f"{YEAR}-12-12T02:00:00Z",
                        "eventStatus": "https://schema.org/EventCancelled",
                        "offers": {"price": "0", "priceCurrency": "USD"},
                        "location": {
                            "name": "Town Hall",
                            "address": {
                                "streetAddress": "12 Main St",
                                "addressLocality": "Canton",
                                "addressRegion": "GA",
                            },
                        },
                    }
                ]
            }
        )
        + "</script>"
    )
    records, _ = jsonld_records(body, "https://example.com/events")
    r = records[0]
    assert r["fields"]["name"] == "Holiday concert"
    assert r["fields"]["occurrences"][0]["start_date"] == f"{YEAR}-12-11"
    assert r["fields"]["occurrences"][0]["start_time"] == "19:30:00"
    assert r["fields"]["price_type"] == "free" and r["fields"]["status"] == "cancelled"
    assert "latitude" not in r["venue"]
    assert (
        jsonld_records(
            '<script type="application/ld+json">not-json</script>',
            "https://example.com",
        )[0]
        == []
    )


def test_ical_exclusive_all_day_dates_and_stable_uid():
    body = f"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:one\r\nSUMMARY:Christmas Market\r\nDTSTART;VALUE=DATE:{YEAR}1205\r\nDTEND;VALUE=DATE:{YEAR}1207\r\nSTATUS:CANCELLED\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    first = ical_records(body, "https://example.com/calendar.ics")[0]
    second = ical_records(
        body.replace("1205", "1204"), "https://example.com/calendar.ics"
    )[0]
    assert first["external_id"] == second["external_id"] == "one"
    assert first["fields"]["occurrences"][0]["end_date"] == f"{YEAR}-12-06"
    assert first["fields"]["status"] == "cancelled"
    with pytest.raises(ValueError, match="Recurring"):
        ical_records(
            body.replace("STATUS:CANCELLED", "RRULE:FREQ=DAILY"),
            "https://example.com/calendar.ics",
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://127.0.0.1",
        "https://[::1]",
        "https://169.254.169.254/latest",
        "https://10.0.0.1",
        "https://user:pass@example.com",
        "https://example.com:8443",
        "https://localhost",
    ],
)
def test_unsafe_urls_are_rejected(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_dns_private_address_is_rejected_before_connect(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("10.0.0.1", 443))]
    )
    with pytest.raises(ValueError, match="non-public"):
        PublicHTTPS("example.com").connect()


def test_approved_venue_coordinates_are_not_overwritten_incidentally(
    client, auth, source
):
    observe_records(source, [record()])
    p = pending(client)[0]
    v = dict(p["venue"])
    v.update(latitude=34, longitude=-84, coordinate_source="Synthetic test fixture")
    client.post("/api/admin/venues", headers=auth, json=v)
    assert (
        client.post(
            "/api/admin/review/" + p["id"] + "/approve",
            headers=auth,
            json={"event": p["proposed"], "venue": p["venue"]},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/admin/review/" + p["id"] + "/approve",
            headers=auth,
            json={"event": p["proposed"], "venue": None},
        ).status_code
        == 200
    )


def test_source_settings_are_protected_and_validated(client, auth):
    data = {
        "id": "test-source",
        "name": "Test",
        "url": "https://example.com/events",
        "city": "Canton",
        "kind": "jsonld",
    }
    assert client.post("/api/admin/sources", json=data).status_code == 403
    assert (
        client.post(
            "/api/admin/sources",
            headers=auth,
            json={**data, "url": "https://127.0.0.1"},
        ).status_code
        == 422
    )
    assert client.post("/api/admin/sources", headers=auth, json=data).status_code == 201
    assert (
        client.put(
            "/api/admin/sources/test-source",
            headers=auth,
            json={**data, "enabled": False},
        ).status_code
        == 200
    )
    assert (
        client.put(
            "/api/admin/sources/test-source",
            headers=auth,
            json={**data, "url": "https://other.example/events"},
        ).status_code
        == 409
    )


def test_partial_page_preserves_other_published_performances(client, auth, source):
    observe_records(source, [record()])
    p = pending(client)[0]
    event = p["proposed"]
    event["occurrences"].append(
        {
            **event["occurrences"][0],
            "start_date": f"{YEAR}-12-14",
            "end_date": f"{YEAR}-12-14",
        }
    )
    assert (
        client.post(
            "/api/admin/review/" + p["id"] + "/approve",
            headers=auth,
            json={"event": event, "venue": p["venue"]},
        ).status_code
        == 200
    )
    observe_records(source, [record(day="12-13")])
    p = pending(client)[0]
    assert [o["start_date"] for o in p["proposed"]["occurrences"]] == [
        f"{YEAR}-12-13",
        f"{YEAR}-12-14",
    ]


def test_renamed_event_matches_unique_source_url(client, auth, source):
    observe_records(source, [record()])
    p = pending(client)[0]
    assert (
        client.post(
            "/api/admin/review/" + p["id"] + "/approve",
            headers=auth,
            json={"event": p["proposed"], "venue": p["venue"]},
        ).status_code
        == 200
    )
    changed = record(name="Christmas Concert Renamed")
    changed["external_id"] = "a-new-remote-id"
    observe_records(source, [changed])
    p = pending(client)[0]
    assert p["kind"] == "changed" and p["event_id"] is not None


def test_fetch_caps_response_and_checks_redirect_host(monkeypatch):
    from app.source_fetch import fetch

    class Response:
        status = 302

        def getheader(self, key, default=""):
            return "https://127.0.0.1/private" if key == "Location" else default

    class Connection:
        def __init__(self, *a, **k):
            pass

        def request(self, *a, **k):
            pass

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr("app.source_fetch.PublicHTTPS", Connection)
    with pytest.raises(ValueError, match="not allowed"):
        fetch("https://example.com", "example.com")

    class Large(Response):
        status = 200

        def getheader(self, key, default=""):
            return default

        def read1(self, size):
            return b"x" * size

    Connection.getresponse = lambda self: Large()
    with pytest.raises(ValueError, match="response-size"):
        fetch("https://example.com", "example.com", limit=100)


def test_robots_disallow_is_respected(monkeypatch):
    from app.source_fetch import PoliteReader

    calls = []

    def fake_fetch(url, *args):
        calls.append(url)
        return (
            200,
            "User-agent: *\nDisallow: /private",
            "https://example.com/robots.txt",
        )

    monkeypatch.setattr("app.source_fetch.fetch", fake_fetch)
    with pytest.raises(ValueError, match="robots.txt"):
        PoliteReader("https://example.com/private").get("https://example.com/private")
    assert len(calls) == 1


def test_listing_and_detail_duplicate_records_merge_into_one_proposal(
    client, auth, source
):
    item = {
        "@type": "Event",
        "@id": "listing-id",
        "name": "Christmas Fixture Market",
        "url": "https://www.kennesaw-ga.gov/kennesaw-event/fixture/",
        "startDate": f"{YEAR}-12-15T17:00:00-05:00",
    }
    listing = (
        '<a href="/kennesaw-event/fixture/">Event</a><script type="application/ld+json">'
        + json.dumps(item)
        + "</script>"
    )
    detail = (
        '<script type="application/ld+json">'
        + json.dumps({**item, "@id": "detail-id"})
        + "</script>"
    )

    class Reader:
        def get(self, url):
            return 200, listing if url == source["url"] else detail, url

    source = {**source, "link_prefix": "/kennesaw-event/"}
    check_source(source, reader=Reader())
    assert (
        len(
            [
                p
                for p in pending(client)
                if p["proposed"]["name"] == "Christmas Fixture Market"
            ]
        )
        == 1
    )


def test_new_migration_preserves_existing_records_and_manual_changes(client, auth):
    from app.models import Event
    from app.db import save_event

    with connect() as db:
        db.execute(
            "UPDATE events SET description='manual work to retain' WHERE id='canton-tree-lighting'"
        )
        db.execute("INSERT INTO metadata VALUES ('migration-test','keep')")
    initialize()
    assert (
        client.get("/api/events/canton-tree-lighting").json()["description"]
        == "manual work to retain"
    )
    with connect() as db:
        assert (
            db.execute(
                "SELECT value FROM metadata WHERE key='migration-test'"
            ).fetchone()[0]
            == "keep"
        )
        assert db.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 2
