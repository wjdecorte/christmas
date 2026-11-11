import csv
import io
import json
import os
import secrets
import sqlite3
import time
from collections import Counter
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from fastapi import Depends, FastAPI, HTTPException, Request, Response, Query
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError
from .db import connect, initialize, event_rows, save_event, save_venue, import_dataset
from .models import Event, EventRead, Venue, Dataset, CATEGORIES
from .security import (
    admin,
    session,
    same_origin,
    token_hash,
    configure_password,
    password_hasher,
)
from .geocoding import geocode
from .public_config import validate_config, check_request, public_mode, secure_cookie
from .review_api import router as review_router
from .discovery import start_worker


@asynccontextmanager
async def lifespan(app):
    validate_config()
    app.state.password_hash = configure_password()
    initialize()
    # A server restart or password rotation revokes old administrator sessions.
    with connect() as db:
        db.execute("DELETE FROM sessions")
    worker = (
        start_worker()
        if os.environ.get("DISCOVERY_ENABLED", "true").lower() == "true"
        else None
    )
    try:
        yield
    finally:
        if worker:
            worker[0].set()
            import asyncio

            await asyncio.to_thread(worker[1].join, 5)


app = FastAPI(
    title="North Georgia Holiday Events",
    version="1.0.0",
    description="Public read-only event calendar. Administrator access: POST /api/auth/login with the configured password; retain its holiday_session cookie. Send the returned csrf value in X-CSRF-Token for administrative writes and logout. Data uses Eastern Time; unknown values are explicit. Imports are atomic upserts.",
    lifespan=lifespan,
    docs_url=None,
    openapi_url="/api/openapi.json",
    redoc_url=None,
)


app.include_router(review_router)


@app.middleware("http")
async def headers(request, call_next):
    try:
        check_request(request)
    except HTTPException as exc:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    # Read bounded bodies before the JSON parser, including chunked requests.
    if request.method in ("POST", "PUT", "PATCH"):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 5_000_000:
                return JSONResponse(
                    {"detail": "Request exceeds 5 MB limit"}, status_code=413
                )
        request._body = bytes(body)
    response = await call_next(request)
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if public_mode():
        response.headers["Strict-Transport-Security"] = "max-age=15552000"
        if os.environ.get("PUBLIC_INDEXABLE", "false").lower() != "true":
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://tile.openstreetmap.org; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache"
    if request.url.path.startswith("/api/admin") or request.url.path.startswith(
        "/api/auth"
    ):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(sqlite3.IntegrityError)
def integrity_error(request, exc):
    return JSONResponse(
        {
            "detail": "Referenced venue is missing, an ID already exists, or the record is still in use."
        },
        status_code=409,
    )


@app.get("/api/health")
def health():
    with connect() as db:
        db.execute("SELECT 1 FROM events LIMIT 1")
    return {"status": "ok"}


class Login(BaseModel):
    password: str = Field(max_length=1024)


@app.post("/api/auth/login")
def login(payload: Login, request: Request, response: Response):
    same_origin(request)
    ip = request.client.host if request.client else "unknown"
    stamp = int(time.time())
    with connect() as db:
        db.execute("DELETE FROM login_attempts WHERE attempted_at<?", (stamp - 900,))
        count = db.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE ip=?", (ip,)
        ).fetchone()[0]
        if count >= 5:
            raise HTTPException(429, "Too many sign-in attempts. Wait 15 minutes.")
        db.execute("INSERT INTO login_attempts VALUES (?,?)", (ip, stamp))
    if not password_hasher.verify(payload.password, app.state.password_hash):
        raise HTTPException(401, "Incorrect administrator password")
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    with connect() as db:
        db.execute("DELETE FROM sessions WHERE expires_at<?", (stamp,))
        db.execute(
            "INSERT INTO sessions VALUES (?,?,?)",
            (token_hash(token), csrf, stamp + 8 * 3600),
        )
        db.execute("DELETE FROM login_attempts WHERE ip=?", (ip,))
    response.set_cookie(
        "holiday_session",
        token,
        max_age=8 * 3600,
        httponly=True,
        secure=secure_cookie(),
        samesite="strict",
        path="/",
    )
    return {"csrf": csrf}


@app.get("/api/auth/session")
def current_session(auth=Depends(session)):
    return {"csrf": auth["csrf"]}


@app.post("/api/auth/logout", dependencies=[Depends(admin)])
def logout(request: Request, response: Response):
    with connect() as db:
        db.execute(
            "DELETE FROM sessions WHERE token_hash=?",
            (token_hash(request.cookies.get("holiday_session", "")),),
        )
    response.delete_cookie("holiday_session", path="/")
    return {"ok": True}


@app.get("/api/categories")
def categories():
    return CATEGORIES


@app.get("/api/meta")
def metadata():
    with connect() as db:
        return {
            "years": [
                r[0]
                for r in db.execute(
                    "SELECT DISTINCT season FROM events ORDER BY season"
                )
            ],
            "cities": [
                r[0]
                for r in db.execute("SELECT DISTINCT city FROM events ORDER BY city")
            ],
            "today": datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
            "timezone": "America/New_York",
        }


def filtered_events(
    q="",
    city="",
    category="",
    year=None,
    start=None,
    end=None,
    verified=None,
    price="",
    sort="date",
):
    if start and end and end < start:
        raise HTTPException(422, "End date must follow start date")
    with connect() as db:
        events = event_rows(db)
    result = []
    for e in events:
        if year is not None and e["season"] != year:
            continue
        if city and e["city"] != city:
            continue
        if category and e["category"] != category:
            continue
        if verified is not None and e["verified"] != verified:
            continue
        if price and e["price_type"] != price:
            continue
        if (
            q
            and q.casefold()
            not in " ".join(
                [
                    e["name"],
                    e["city"],
                    e["description"],
                    (e["venue"] or {}).get("name", ""),
                ]
            ).casefold()
        ):
            continue
        if (start or end) and not any(
            (not start or o["end_date"] >= start.isoformat())
            and (not end or o["start_date"] <= end.isoformat())
            for o in e["occurrences"]
        ):
            continue
        result.append(e)
    if sort == "name":
        result.sort(key=lambda e: e["name"].casefold())
    elif sort == "city":
        result.sort(key=lambda e: (e["city"], e["name"]))
    else:
        result.sort(
            key=lambda e: (
                next(
                    (
                        o["start_date"]
                        for o in e["occurrences"]
                        if not start or o["end_date"] >= start.isoformat()
                    ),
                    "9999",
                ),
                e["name"],
            )
        )
    return result


def filters(
    q: str = Query("", max_length=200),
    city: str = "",
    category: str = "",
    year: int | None = Query(None, ge=2000, le=2200),
    start: date | None = None,
    end: date | None = None,
    verified: bool | None = None,
    price: str = "",
    sort: str = Query("date", pattern="^(date|name|city)$"),
):
    return filtered_events(q, city, category, year, start, end, verified, price, sort)


@app.get("/api/events", response_model=list[EventRead])
def list_events(events=Depends(filters)):
    return events


@app.get("/api/events/{event_id}", response_model=EventRead)
def event_detail(event_id: str):
    with connect() as db:
        event = next((e for e in event_rows(db) if e["id"] == event_id), None)
    if not event:
        raise HTTPException(404, "Event not found")
    return event


@app.get("/api/venues", response_model=list[Venue])
def venues():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM venues ORDER BY city,name")]


@app.get("/api/markers")
def markers(events=Depends(filters)):
    mapped = [e for e in events if e["venue"] and e["venue"]["latitude"] is not None]
    return {"events": mapped, "unmapped_count": len(events) - len(mapped)}


@app.get("/api/dashboard")
def dashboard(events=Depends(filters)):
    today = datetime.now(ZoneInfo("America/New_York")).date()
    saturday = (
        today + timedelta(days=(5 - today.weekday()) % 7)
        if today.weekday() != 6
        else today - timedelta(days=1)
    )
    sunday = saturday + timedelta(days=1)
    eligible = [e for e in events if e["status"] == "scheduled"]
    return {
        "total": len(events),
        "by_city": dict(Counter(e["city"] for e in events)),
        "by_category": dict(Counter(e["category"] for e in events)),
        "upcoming": [
            e["id"]
            for e in eligible
            if any(o["end_date"] >= today.isoformat() for o in e["occurrences"])
        ],
        "concerts": [
            e["id"] for e in eligible if e["category"] == "concert" and e["featured"]
        ],
        "weekend": [
            e["id"]
            for e in eligible
            if any(
                o["start_date"] <= sunday.isoformat()
                and o["end_date"] >= saturday.isoformat()
                for o in e["occurrences"]
            )
        ],
        "free": [e["id"] for e in eligible if e["price_type"] == "free"],
        "weekend_start": saturday.isoformat(),
        "weekend_end": sunday.isoformat(),
    }


@app.post("/api/admin/events", dependencies=[Depends(admin)], status_code=201)
def add_event(event: Event):
    with connect() as db:
        if db.execute("SELECT 1 FROM events WHERE id=?", (event.id,)).fetchone():
            raise HTTPException(409, "Event ID already exists")
        save_event(db, event)
    return {"id": event.id}


@app.put("/api/admin/events/{event_id}", dependencies=[Depends(admin)])
def edit_event(event_id: str, event: Event):
    if event.id != event_id:
        raise HTTPException(422, "Event ID cannot change")
    with connect() as db:
        if not db.execute("SELECT 1 FROM events WHERE id=?", (event_id,)).fetchone():
            raise HTTPException(404, "Event not found")
        save_event(db, event)
    return {"id": event.id}


@app.delete("/api/admin/events/{event_id}", dependencies=[Depends(admin)])
def delete_event(event_id: str):
    with connect() as db:
        if not db.execute("DELETE FROM events WHERE id=?", (event_id,)).rowcount:
            raise HTTPException(404, "Event not found")
    return {"ok": True}


@app.post("/api/admin/venues", dependencies=[Depends(admin)], status_code=201)
def add_venue(venue: Venue):
    with connect() as db:
        if db.execute("SELECT 1 FROM venues WHERE id=?", (venue.id,)).fetchone():
            raise HTTPException(409, "Venue ID already exists")
        save_venue(db, venue)
    return {"id": venue.id}


@app.put("/api/admin/venues/{venue_id}", dependencies=[Depends(admin)])
def edit_venue(venue_id: str, venue: Venue):
    if venue.id != venue_id:
        raise HTTPException(422, "Venue ID cannot change")
    with connect() as db:
        if not db.execute("SELECT 1 FROM venues WHERE id=?", (venue_id,)).fetchone():
            raise HTTPException(404, "Venue not found")
        save_venue(db, venue)
    return {"id": venue.id}


@app.delete("/api/admin/venues/{venue_id}", dependencies=[Depends(admin)])
def delete_venue(venue_id: str):
    with connect() as db:
        if not db.execute("DELETE FROM venues WHERE id=?", (venue_id,)).rowcount:
            raise HTTPException(404, "Venue not found")
    return {"ok": True}


@app.post("/api/admin/venues/{venue_id}/geocode", dependencies=[Depends(admin)])
def geocode_venue(venue_id: str):
    with connect() as db:
        row = db.execute("SELECT * FROM venues WHERE id=?", (venue_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Venue not found")
    if row["latitude"] is not None:
        return dict(row)
    if not row["address"].strip():
        raise HTTPException(422, "Enter a verified street address before geocoding")
    result = geocode(f"{row['address']}, {row['city']}, Georgia, USA")
    if result["latitude"] is None:
        raise HTTPException(
            404,
            "No geocoding result. Correct the address or enter sourced coordinates.",
        )
    venue = Venue(
        **{
            **dict(row),
            "latitude": result["latitude"],
            "longitude": result["longitude"],
            "coordinate_source": f"OpenStreetMap Nominatim: {result['display_name']}",
            "geocoded_at": result["fetched_at"],
        }
    )
    with connect() as db:
        save_venue(db, venue)
    return venue


CSV_FIELDS = list(Event.model_fields)


@app.get("/api/admin/export", dependencies=[Depends(admin)])
def export_data(format: str = Query("json", pattern="^(json|csv)$")):
    with connect() as db:
        data = {
            "venues": [dict(r) for r in db.execute("SELECT * FROM venues")],
            "events": [
                {k: v for k, v in e.items() if k in Event.model_fields}
                for e in event_rows(db)
            ],
        }
    if format == "json":
        return Response(
            json.dumps(data, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": 'attachment; filename="holiday-events.json"'
            },
        )
    stream = io.StringIO()
    # Venue JSON on each event row makes CSV independently portable.
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS + ["venue_json"])
    writer.writeheader()
    venue_map = {v["id"]: v for v in data["venues"]}
    for e in data["events"]:
        row = {
            **e,
            "occurrences": json.dumps(e["occurrences"]),
            "venue_json": json.dumps(venue_map.get(e["venue_id"])),
        }
        for key, value in row.items():
            if isinstance(value, str) and value.lstrip().startswith(
                ("=", "+", "-", "@", "\t", "\r")
            ):
                row[key] = "'" + value
        writer.writerow(row)
    return Response(
        stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="holiday-events.csv"'},
    )


class ImportBody(BaseModel):
    format: str = Field(pattern="^(json|csv)$")
    content: str = Field(max_length=4_500_000)


@app.post("/api/admin/import", dependencies=[Depends(admin)])
def import_data(payload: ImportBody):
    try:
        if payload.format == "json":
            data = Dataset.model_validate_json(payload.content)
        else:
            rows = list(csv.DictReader(io.StringIO(payload.content)))
            if len(rows) > 2000:
                raise ValueError("Import limited to 2,000 events")
            events, venues = {}, {}
            for row in rows:
                row = {
                    k: (
                        v[1:]
                        if v
                        and v.startswith("'")
                        and v[1:].lstrip().startswith(("=", "+", "-", "@", "\t", "\r"))
                        else v
                    )
                    for k, v in row.items()
                    if k is not None
                }
                venue = json.loads(row.pop("venue_json", "null") or "null")
                if venue:
                    venues[venue["id"]] = venue
                row["occurrences"] = json.loads(row.get("occurrences") or "[]")
                for field in ("last_verified", "last_checked", "venue_id"):
                    row[field] = row.get(field) or None
                if row["id"] in events:
                    raise ValueError("Duplicate event IDs in CSV")
                events[row["id"]] = row
            data = Dataset.model_validate(
                {"venues": list(venues.values()), "events": list(events.values())}
            )
        if len({e.id for e in data.events}) != len(data.events) or len(
            {v.id for v in data.venues}
        ) != len(data.venues):
            raise ValueError("Duplicate IDs in import")
    except (
        ValidationError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        csv.Error,
    ) as exc:
        raise HTTPException(422, f"Import rejected: {str(exc)[:1000]}")
    with connect() as db:
        import_dataset(db, data)
    return {"events": len(data.events), "venues": len(data.venues)}


DIST = Path(
    os.environ.get(
        "FRONTEND_DIST", str(Path(__file__).resolve().parents[2] / "frontend" / "dist")
    )
)


@app.get("/api/docs", include_in_schema=False, response_class=HTMLResponse)
def docs():
    return '<!doctype html><html><head><title>Holiday Events API</title><link rel="stylesheet" href="/api-docs/swagger-ui.css"></head><body><div id="swagger-ui"></div><script src="/api-docs/swagger-ui-bundle.js"></script><script src="/api-docs/init.js"></script></body></html>'


@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    icon = DIST / "favicon.svg"
    if not icon.is_file():
        raise HTTPException(404, "Icon is available after the frontend build")
    return FileResponse(
        icon,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )


if DIST.exists():
    app.mount("/api-docs", StaticFiles(directory=DIST / "api-docs"), name="api-docs")
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/") or path == "api":
            raise HTTPException(404, "Endpoint not found")
        return FileResponse(DIST / "index.html")
