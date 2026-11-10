import os
import threading
import time
import httpx
from fastapi import HTTPException
from .db import connect, now

lock = threading.Lock()
last_call = 0.0


def geocode(query: str):
    """Admin initiated, cached, serialized, no autocomplete or scheduled bulk requests."""
    global last_call
    with lock:
        with connect() as db:
            row = db.execute(
                "SELECT * FROM geocode_cache WHERE query=?", (query,)
            ).fetchone()
        if row:
            return dict(row)
        agent = os.environ.get("GEOCODER_USER_AGENT", "")
        if not agent or "your-email" in agent:
            raise HTTPException(
                503,
                "Configure GEOCODER_USER_AGENT with an identifying contact before geocoding.",
            )
        time.sleep(max(0, 1.1 - (time.monotonic() - last_call)))
        last_call = time.monotonic()
        try:
            response = httpx.get(
                os.environ.get(
                    "GEOCODER_URL", "https://nominatim.openstreetmap.org/search"
                ),
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": 1,
                    "countrycodes": "us",
                },
                headers={"User-Agent": agent},
                timeout=20,
            )
            response.raise_for_status()
            results = response.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(
                502,
                "Geocoding service unavailable. Try later or enter sourced coordinates manually.",
            )
        result = {
            "query": query,
            "latitude": float(results[0]["lat"]) if results else None,
            "longitude": float(results[0]["lon"]) if results else None,
            "display_name": results[0]["display_name"] if results else "",
            "fetched_at": now(),
        }
        with connect() as db:
            db.execute(
                "INSERT INTO geocode_cache VALUES (?,?,?,?,?)", tuple(result.values())
            )
        return result
