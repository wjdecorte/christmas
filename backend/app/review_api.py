import json
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from .db import connect, now, event_rows, save_event, save_venue
from .models import Event, Venue
from .security import admin
from .discovery import Source, comparable

router = APIRouter(prefix="/api/admin", dependencies=[Depends(admin)])


@router.get("/sources")
def sources():
    with connect() as db:
        return [
            dict(r) for r in db.execute("SELECT * FROM discovery_sources ORDER BY name")
        ]


@router.post("/sources", status_code=201)
def add_source(source: Source):
    with connect() as db:
        if db.execute(
            "SELECT 1 FROM discovery_sources WHERE id=?", (source.id,)
        ).fetchone():
            raise HTTPException(409, "Source ID already exists")
        values = source.model_dump()
        db.execute(
            f"INSERT INTO discovery_sources({','.join(values)}) VALUES ({','.join('?' for _ in values)})",
            list(values.values()),
        )
    return {"id": source.id}


@router.put("/sources/{source_id}")
def edit_source(source_id: str, source: Source):
    if source.id != source_id:
        raise HTTPException(422, "Source ID cannot change")
    with connect() as db:
        row = db.execute(
            "SELECT * FROM discovery_sources WHERE id=?", (source_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Source not found")
        if row["lease_until"] > int(time.time()):
            raise HTTPException(
                409, "Source check is running; try again when it finishes"
            )
        if row["url"] != source.url or row["kind"] != source.kind:
            raise HTTPException(
                409,
                "Create a new source ID when changing its URL or format so observation history remains accurate",
            )
        values = source.model_dump(exclude={"id"})
        db.execute(
            f"UPDATE discovery_sources SET {','.join(k + '=?' for k in values)} WHERE id=?",
            [*values.values(), source_id],
        )
    return {"id": source.id}


@router.post("/sources/{source_id}/check", status_code=202)
def request_check(source_id: str):
    import os

    if os.environ.get("DISCOVERY_ENABLED", "true").lower() != "true":
        raise HTTPException(
            503, "Enable DISCOVERY_ENABLED and restart to run source checks"
        )
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT * FROM discovery_sources WHERE id=?", (source_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Source not found")
        if not row["enabled"]:
            raise HTTPException(409, "Enable this source before checking")
        if row["lease_until"] > int(time.time()):
            raise HTTPException(409, "This source check is already running")
        if (
            row["last_checked"]
            and time.time() - datetime.fromisoformat(row["last_checked"]).timestamp()
            < 60
        ):
            raise HTTPException(429, "Wait one minute between manual source checks")
        db.execute("UPDATE discovery_sources SET next_check=0 WHERE id=?", (source_id,))
    return {
        "status": "queued",
        "message": "The background checker will pick this up shortly. Published events will not change.",
    }


@router.get("/review")
def proposals(
    status: str = Query("pending", pattern="^(pending|approved|dismissed|superseded)$"),
):
    with connect() as db:
        rows = db.execute(
            "SELECT p.*,s.name AS source_name FROM review_proposals p JOIN discovery_sources s ON s.id=p.source_id WHERE p.status=? ORDER BY p.created_at DESC LIMIT 200",
            (status,),
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            for key in ("before_json", "proposed_json", "venue_json"):
                d[key.removesuffix("_json")] = json.loads(d.pop(key) or "null")
            result.append(d)
        return result


class ReviewDecision(BaseModel):
    event: Event
    venue: Venue | None = None
    note: str = Field(default="", max_length=2000)


@router.post("/review/{proposal_id}/approve")
def approve(proposal_id: str, decision: ReviewDecision):
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        p = db.execute(
            "SELECT * FROM review_proposals WHERE id=?", (proposal_id,)
        ).fetchone()
        if not p:
            raise HTTPException(404, "Review item not found")
        if p["status"] != "pending":
            raise HTTPException(
                409, "This item was already reviewed or replaced by a newer observation"
            )
        expected = json.loads(p["proposed_json"])
        if decision.event.id != expected["id"]:
            raise HTTPException(422, "Event ID cannot change during review")
        current = next(
            (e for e in event_rows(db) if e["id"] == decision.event.id), None
        )
        if p["event_id"]:
            if not current or current["updated_at"] != p["base_updated_at"]:
                raise HTTPException(
                    409,
                    "The event changed after this proposal. Refresh its baseline, review the differences again, then approve.",
                )
        elif current:
            raise HTTPException(
                409,
                "That event ID now exists. Dismiss this duplicate and edit the existing event.",
            )
        # Never overwrite a shared venue as an incidental consequence of event approval.
        if decision.venue:
            if decision.venue.id != decision.event.venue_id:
                raise HTTPException(422, "Proposed venue must match the event venue")
            old = db.execute(
                "SELECT * FROM venues WHERE id=?", (decision.venue.id,)
            ).fetchone()
            if old and Venue(**dict(old)).model_dump() != decision.venue.model_dump():
                raise HTTPException(
                    409,
                    "This venue already exists with different details. Select it unchanged or create a new venue ID.",
                )
            save_venue(db, decision.venue)
        if (
            decision.event.venue_id
            and not db.execute(
                "SELECT 1 FROM venues WHERE id=?", (decision.event.venue_id,)
            ).fetchone()
        ):
            raise HTTPException(
                422, "Select an existing venue or include the proposed new venue"
            )
        before = comparable(current) if current else {}
        save_event(db, decision.event)
        db.execute(
            "UPDATE review_proposals SET status='approved',reviewed_at=?,event_id=? WHERE id=?",
            (now(), decision.event.id, proposal_id),
        )
        db.execute(
            "INSERT INTO review_audit(proposal_id,action,event_id,before_json,after_json,reviewed_at) VALUES (?,?,?,?,?,?)",
            (
                proposal_id,
                "approved: " + decision.note,
                decision.event.id,
                json.dumps(before),
                decision.event.model_dump_json(),
                now(),
            ),
        )
    return {"id": decision.event.id, "status": "approved"}


class Dismiss(BaseModel):
    note: str = Field(default="", max_length=2000)


@router.post("/review/{proposal_id}/dismiss")
def dismiss(proposal_id: str, decision: Dismiss):
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        p = db.execute(
            "SELECT * FROM review_proposals WHERE id=?", (proposal_id,)
        ).fetchone()
        if not p:
            raise HTTPException(404, "Review item not found")
        if p["status"] != "pending":
            raise HTTPException(409, "This item is no longer pending")
        db.execute(
            "UPDATE review_proposals SET status='dismissed',reviewed_at=? WHERE id=?",
            (now(), proposal_id),
        )
        db.execute(
            "INSERT INTO review_audit(proposal_id,action,event_id,before_json,after_json,reviewed_at) VALUES (?,?,?,?,?,?)",
            (
                proposal_id,
                "dismissed: " + decision.note,
                p["event_id"],
                p["before_json"],
                "{}",
                now(),
            ),
        )
    return {"status": "dismissed"}


@router.post("/review/{proposal_id}/rebase")
def refresh_baseline(proposal_id: str):
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        p = db.execute(
            "SELECT * FROM review_proposals WHERE id=? AND status='pending'",
            (proposal_id,),
        ).fetchone()
        if not p or not p["event_id"]:
            raise HTTPException(
                409, "Only a pending change to an existing event can be refreshed"
            )
        current = next((e for e in event_rows(db) if e["id"] == p["event_id"]), None)
        if not current:
            raise HTTPException(409, "The event was deleted. Dismiss this proposal.")
        before = json.loads(p["before_json"])
        proposed = json.loads(p["proposed_json"])
        changed = {k: v for k, v in proposed.items() if before.get(k) != v}
        merged = {**comparable(current), **changed}
        Event.model_validate(merged)
        db.execute(
            "UPDATE review_proposals SET before_json=?,proposed_json=?,base_updated_at=? WHERE id=?",
            (
                json.dumps(comparable(current)),
                json.dumps(merged),
                current["updated_at"],
                proposal_id,
            ),
        )
    return {
        "status": "refreshed",
        "message": "Review the refreshed differences before approving.",
    }


@router.get("/review-audit")
def audit():
    with connect() as db:
        return [
            dict(r)
            for r in db.execute("SELECT * FROM review_audit ORDER BY id DESC LIMIT 100")
        ]
