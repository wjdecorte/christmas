"""Scheduled source observations and transactional, human-approved publication."""

import json
import os
import re
import threading
import time
import uuid
from datetime import datetime
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from .db import connect, now, event_rows, save_event, save_venue
from .models import Event, Venue
from .source_fetch import PoliteReader, validate_url
from .source_parse import jsonld_records, ical_records, canonical, fingerprint, category


class Source(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,59}$")
    name: str = Field(min_length=1, max_length=200)
    url: str = Field(max_length=2000)
    kind: str = Field(pattern="^(jsonld|ical|page)$")
    city: str = Field(min_length=1, max_length=100)
    keywords: str = Field(
        default="christmas,holiday,santa,noel,nutcracker", max_length=1000
    )
    link_prefix: str = Field(default="", max_length=200)
    enabled: bool = True
    interval_hours: int = Field(default=12, ge=6, le=168)

    @field_validator("url")
    @classmethod
    def safe_url(cls, value):
        validate_url(value)
        return value

    @field_validator("link_prefix")
    @classmethod
    def path_prefix(cls, value):
        if value and (not value.startswith("/") or value.startswith("//")):
            raise ValueError("Link prefix must be a path beginning with /")
        return value


def comparable(event):
    return {k: v for k, v in event.items() if k in Event.model_fields}


def match_event(db, source_id, external_id, fields, city, season, events):
    prior = db.execute(
        "SELECT event_id FROM review_proposals WHERE source_id=? AND external_id=? AND status='approved' AND event_id IS NOT NULL ORDER BY reviewed_at DESC LIMIT 1",
        (source_id, external_id),
    ).fetchone()
    if prior:
        return next((e for e in events if e["id"] == prior["event_id"]), None)
    url = canonical(fields.get("source_url", ""))
    by_url = [
        e
        for e in events
        if e["source_url"]
        and canonical(e["source_url"]) == url
        and e["season"] == season
    ]
    # A shared calendar/feed URL does not identify an individual event.
    source_url = db.execute(
        "SELECT url FROM discovery_sources WHERE id=?", (source_id,)
    ).fetchone()[0]
    if len(by_url) == 1 and url != canonical(source_url):
        return by_url[0]
    matches = [
        e
        for e in events
        if e["season"] == season
        and e["city"].casefold() == city.casefold()
        and comparable_name(e["name"]) == comparable_name(fields["name"])
    ]
    return matches[0] if len(matches) == 1 else None


def comparable_name(name):
    return re.sub(r"[^\w]+", " ", name.casefold()).strip()


def address_key(value):
    value = re.sub(r"\b\d{5}(?:-\d{4})?\s*$", "", value.casefold())
    words = re.sub(r"[^\w]+", " ", value).split()
    abbreviations = {
        "street": "st",
        "road": "rd",
        "avenue": "ave",
        "parkway": "pkwy",
        "drive": "dr",
        "east": "e",
        "west": "w",
        "north": "n",
        "south": "s",
    }
    return " ".join(abbreviations.get(word, word) for word in words)


def draft_for(source, record, current=None, previous_record=None):
    fields = record["fields"]
    city = fields.get("city") or source["city"]
    first = fields["occurrences"][0]["start_date"]
    year = int(first[:4]) - (first[5:7] == "01")
    base = (
        comparable(current)
        if current
        else Event(
            id="discovered-" + fingerprint([source["id"], record["external_id"]])[:24],
            name=fields["name"],
            city=city,
            category=category(fields["name"]),
            season=year,
        ).model_dump(mode="json")
    )
    base.update(fields)
    if current and len(current["occurrences"]) > len(fields["occurrences"]):
        # One performance page cannot establish that other published dates disappeared.
        incoming = fields["occurrences"]
        previous = (previous_record or {}).get("fields", {}).get("occurrences", [])
        replaced = {(o["start_date"], o.get("start_time")) for o in incoming + previous}
        retained = [
            o
            for o in current["occurrences"]
            if (o["start_date"], o.get("start_time")) not in replaced
        ]
        base["occurrences"] = sorted(
            retained + incoming,
            key=lambda o: (o["start_date"], o.get("start_time") or ""),
        )
    base.update(
        verified=False,
        last_verified=None,
        last_checked=datetime.now(ZoneInfo("America/New_York")).date().isoformat(),
    )
    venue = None
    location = record.get("venue")
    if location:
        location = {**location, "city": location.get("city") or city}
        old = current.get("venue") if current else None
        if (
            old
            and old["name"].casefold() == location["name"].casefold()
            and old["city"].casefold() == location["city"].casefold()
            and address_key(old["address"]) == address_key(location["address"])
        ):
            base["venue_id"] = old["id"]
        else:
            venue = Venue(
                id="source-" + fingerprint(location)[:24], **location
            ).model_dump(mode="json")
            base["venue_id"] = venue["id"]
    base["verification_notes"] = (
        "Source discovery awaiting administrator verification. "
        + (
            "A source-stated cancellation/postponement requires review."
            if fields.get("status") in ("cancelled", "postponed")
            else ""
        )
    )
    return Event.model_validate(base).model_dump(mode="json"), venue


def enqueue(
    db,
    source,
    external_id,
    kind,
    current,
    proposed,
    venue,
    stamp,
    evidence_url,
    evidence_text,
    notes="",
):
    existing = db.execute(
        "SELECT 1 FROM review_proposals WHERE source_id=? AND external_id=? AND fingerprint=?",
        (source["id"], external_id, stamp),
    ).fetchone()
    if existing:
        return 0
    # Retain history, but only the most recent observation is actionable.
    db.execute(
        "UPDATE review_proposals SET status='superseded',reviewed_at=? WHERE source_id=? AND external_id=? AND status='pending'",
        (now(), source["id"], external_id),
    )
    db.execute(
        "INSERT INTO review_proposals(id,source_id,external_id,kind,event_id,fingerprint,before_json,proposed_json,venue_json,evidence_url,evidence_text,notes,created_at,base_updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            uuid.uuid4().hex,
            source["id"],
            external_id,
            kind,
            current["id"] if current else None,
            stamp,
            json.dumps(comparable(current)) if current else "{}",
            json.dumps(proposed),
            json.dumps(venue) if venue else None,
            evidence_url,
            evidence_text[:6000],
            notes,
            now(),
            current["updated_at"] if current else None,
        ),
    )
    return 1


def observe_records(source, records, target=None):
    added = 0
    with connect() as db:
        events = event_rows(db)
        for record in records:
            fields = record["fields"]
            start = fields["occurrences"][0]["start_date"]
            if target is None:
                if re.search(r"\bclosed\b", fields["name"], re.IGNORECASE):
                    continue
                today = datetime.now(ZoneInfo("America/New_York")).date()
                # Limit discovery to this and next holiday season, not historical archives.
                if int(start[:4]) not in (today.year, today.year + 1) or start[
                    5:7
                ] not in (
                    "11",
                    "12",
                    "01",
                ):
                    continue
                terms = [
                    t.strip().casefold()
                    for t in source["keywords"].split(",")
                    if t.strip()
                ]
                if terms and not any(
                    t
                    in (fields["name"] + " " + fields.get("description", "")).casefold()
                    for t in terms
                ):
                    continue
            external = record["external_id"]
            stamp = fingerprint({"fields": fields, "venue": record.get("venue")})
            previous = db.execute(
                "SELECT fingerprint,payload FROM source_observations WHERE source_id=? AND external_id=?",
                (source["id"], external),
            ).fetchone()
            if previous and previous["fingerprint"] == stamp:
                continue
            city = fields.get("city") or source["city"]
            season = int(start[:4]) - (start[5:7] == "01")
            current = target or match_event(
                db, source["id"], external, fields, city, season, events
            )
            proposed, venue = draft_for(
                source,
                record,
                current,
                json.loads(previous["payload"]) if previous else None,
            )
            if target is not None:
                proposed["source_url"] = current["source_url"]
            changes = (
                not current
                or any(
                    proposed[k] != current.get(k)
                    for k in fields
                    if target is None or k != "source_url"
                )
                or bool(venue)
            )
            if changes:
                added += enqueue(
                    db,
                    source,
                    external,
                    "changed" if current else "new",
                    current,
                    proposed,
                    venue,
                    stamp,
                    fields["source_url"],
                    record.get("evidence", ""),
                    "Dates, location, admission and category must be checked before publishing.",
                )
            db.execute(
                "INSERT INTO source_observations VALUES (?,?,?,?,?) ON CONFLICT(source_id,external_id) DO UPDATE SET fingerprint=excluded.fingerprint,payload=excluded.payload,observed_at=excluded.observed_at",
                (source["id"], external, stamp, json.dumps(record), now()),
            )
    return added


def observe_page(source, event, status, text, url, initial_review=False):
    external = "page:" + event["id"]
    stamp = fingerprint([status, text])
    with connect() as db:
        previous = db.execute(
            "SELECT fingerprint,payload FROM source_observations WHERE source_id=? AND external_id=?",
            (source["id"], external),
        ).fetchone()
        added = 0
        if (previous and previous["fingerprint"] != stamp) or (
            not previous and (status in (404, 410) or initial_review)
        ):
            proposed = comparable(event)
            proposed.update(
                verified=False,
                last_verified=None,
                last_checked=datetime.now(ZoneInfo("America/New_York"))
                .date()
                .isoformat(),
            )
            note = (
                "A missing source page is not proof of cancellation."
                if status in (404, 410)
                else "Page excerpt requires review. Check dates, prices and venue manually; no unambiguous structured event facts were extracted."
            )
            before_text = (
                json.loads(previous["payload"]).get("text", "") if previous else ""
            )
            added = enqueue(
                db,
                source,
                external,
                "source_unavailable" if status in (404, 410) else "page_changed",
                event,
                proposed,
                None,
                stamp,
                url,
                text,
                "Previous page excerpt:\n" + before_text[:3000] + "\n\n" + note,
            )
        db.execute(
            "INSERT INTO source_observations VALUES (?,?,?,?,?) ON CONFLICT(source_id,external_id) DO UPDATE SET fingerprint=excluded.fingerprint,payload=excluded.payload,observed_at=excluded.observed_at",
            (source["id"], external, stamp, json.dumps({"text": text}), now()),
        )
    return added


def check_source(source, stop=None, reader=None):
    reader = reader or PoliteReader(source["url"], stop)
    status, body, url = reader.get(source["url"])
    if source.get("target_event_id"):
        with connect() as db:
            target = next(
                (e for e in event_rows(db) if e["id"] == source["target_event_id"]),
                None,
            )
        if target is None:
            raise ValueError("Linked event no longer exists; pause this source")
        records, page = jsonld_records(body, url)
        # A listing with several unrelated events must not all overwrite the linked event.
        if len(records) > 1:
            records = [
                r
                for r in records
                if comparable_name(r["fields"]["name"])
                == comparable_name(target["name"])
            ]
        if len(records) == 1 and status == 200:
            records[0]["external_id"] = "linked:" + target["id"]
            added = observe_records(source, records, target=target)
            return f"Linked event inspected; {added} review items created. Original source retained."
        added = observe_page(
            source, target, status, page.text, url, initial_review=True
        )
        return f"Page excerpt captured; {added} review items created. Check details manually; no unambiguous structured event found."
    if status != 200:
        raise ValueError(f"Calendar source returned HTTP {status}; no events removed")
    if source["kind"] == "ical":
        records = ical_records(body, url)
        added = observe_records(source, records)
        return f"{len(records)} feed records inspected; {added} review items created."
    records, page = jsonld_records(body, url)
    urls = []
    if source["link_prefix"] and source["kind"] == "jsonld":
        for link in page.links:
            link = urljoin(url, link)
            p = urlsplit(link)
            if (
                p.hostname == urlsplit(url).hostname
                and p.path.startswith(source["link_prefix"])
                and canonical(link) not in [canonical(x) for x in urls]
                and canonical(link) != canonical(url)
            ):
                urls.append(link)
            if len(urls) >= 8:
                break
    with connect() as db:
        watched = [
            e
            for e in event_rows(db)
            if e["source_url"]
            and urlsplit(e["source_url"]).hostname == urlsplit(source["url"]).hostname
            and (
                source["kind"] != "page"
                or canonical(e["source_url"]) == canonical(source["url"])
            )
        ]
    # Existing source URLs are monitored even when a listing no longer links to them.
    for e in watched:
        if canonical(e["source_url"]) not in [canonical(x) for x in urls] and canonical(
            e["source_url"]
        ) != canonical(url):
            urls.append(e["source_url"])
        if len(urls) >= 16:
            break
    added = 0
    pages = [(status, body, url, page)]
    for link in urls[:16]:
        if stop and stop.is_set():
            raise ValueError("Source check interrupted")
        state, content, final = reader.get(link)
        found, parsed = jsonld_records(content, final)
        records.extend(found)
        pages.append((state, content, final, parsed))
    # Merge source-declared performances at one event URL into a complete set for this check.
    merged = {}
    for record in records:
        event_url = canonical(record["fields"]["source_url"])
        key = (
            event_url
            if event_url != canonical(source["url"])
            else record["external_id"]
        )
        record["external_id"] = key
        if key in merged:
            for o in record["fields"]["occurrences"]:
                if o not in merged[key]["fields"]["occurrences"]:
                    merged[key]["fields"]["occurrences"].append(o)
            # Prefer the event detail's description/location over a listing excerpt.
            dates = merged[key]["fields"]["occurrences"]
            merged[key] = record
            merged[key]["fields"]["occurrences"] = dates
        else:
            merged[key] = record
    added += observe_records(source, list(merged.values()))
    structured_urls = {canonical(r["fields"]["source_url"]) for r in records}
    for state, _, final, parsed in pages:
        for event in watched:
            if (
                canonical(event["source_url"]) == canonical(final)
                and canonical(final) not in structured_urls
            ):
                added += observe_page(source, event, state, parsed.text, final)
    return f"{len(pages)} pages / {len(merged)} structured records inspected; {added} review items created. Plain-page baselines are retained for later checks."


def run_due_sources(stop=None):
    stamp = int(time.time())
    with connect() as db:
        row = db.execute(
            "SELECT * FROM discovery_sources WHERE enabled=1 AND next_check<=? AND lease_until<=? ORDER BY next_check LIMIT 1",
            (stamp, stamp),
        ).fetchone()
        if not row:
            return False
        source = dict(row)
        if not db.execute(
            "UPDATE discovery_sources SET lease_until=? WHERE id=? AND lease_until<=?",
            (stamp + 1800, source["id"], stamp),
        ).rowcount:
            return False
    try:
        result = check_source(source, stop)
        error = ""
    except Exception as exc:
        result = "No published events changed."
        error = f"{type(exc).__name__}: {str(exc)[:400]}"
    with connect() as db:
        db.execute(
            "UPDATE discovery_sources SET last_checked=?,next_check=?,last_error=?,last_result=?,lease_until=0,checked_count=checked_count+1 WHERE id=?",
            (
                now(),
                int(time.time()) + source["interval_hours"] * 3600,
                error,
                result,
                source["id"],
            ),
        )
    return True


def start_worker():
    stop = threading.Event()

    def loop():
        if stop.wait(15):
            return
        while not stop.is_set():
            try:
                active = run_due_sources(stop)
            except Exception:
                import logging

                logging.exception("Discovery worker failed; next poll will retry")
                active = False
            if stop.wait(1 if active else 10):
                return

    thread = threading.Thread(target=loop, name="source-discovery", daemon=True)
    thread.start()
    return stop, thread
