"""Calendar drafts and RFC 5545 downloads; event times are Eastern."""

from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")


def calendar_entry(event, occurrence):
    o = event["occurrences"][occurrence]
    start_date = date.fromisoformat(o["start_date"])
    end_date = date.fromisoformat(o["end_date"])
    all_day = not o.get("start_time")
    notes = [
        event.get("description", ""),
        f"Listed dates: {o['start_date']} to {o['end_date']}. Times are Eastern.",
    ]
    if not event.get("verified"):
        notes.append("Unverified event: confirm details with the original source.")
    if all_day:
        start = start_date.strftime("%Y%m%d")
        end = (end_date + timedelta(days=1)).strftime("%Y%m%d")
        start_iso, end_iso = (
            start_date.isoformat(),
            (end_date + timedelta(days=1)).isoformat(),
        )
        notes.append(
            "Time to be announced. Saved as an all-day reminder, not confirmed operating hours."
        )
    else:

        def utc(day, clock):
            return (
                datetime.fromisoformat(f"{day}T{clock}")
                .replace(tzinfo=EASTERN)
                .astimezone(timezone.utc)
            )

        dt = utc(o["start_date"], o["start_time"])
        finish = utc(o["end_date"], o["end_time"]) if o.get("end_time") else None
        start, end = (
            dt.strftime("%Y%m%dT%H%M%SZ"),
            finish.strftime("%Y%m%dT%H%M%SZ") if finish else None,
        )
        start_iso, end_iso = dt.isoformat(), finish.isoformat() if finish else None
        if not finish:
            notes.append(
                "End time has not been announced. Check the source before attending."
            )
    if start_date != end_date:
        notes.append(
            "Date range: check the source for individual operating days and hours."
        )
    notes.extend(
        filter(
            None,
            [
                event.get("schedule_notes"),
                event.get("price_details"),
                event.get("source_url"),
            ],
        )
    )
    notes.append(
        "This is a saved copy, not a subscription. Later changes will not sync automatically."
    )
    venue = event.get("venue") or {}
    location = ", ".join(
        filter(None, [venue.get("name"), venue.get("address"), event.get("city")])
    )
    description = "\n\n".join(filter(None, notes))
    title = event["name"]
    if event.get("status") != "scheduled":
        title = f"[{event['status'].upper()}] {title}"
    google = "https://calendar.google.com/calendar/render?" + urlencode(
        {
            "action": "TEMPLATE",
            "text": title,
            "dates": f"{start}/{end or start}",
            "ctz": "America/New_York",
            "details": description,
            "location": location,
        }
    )
    outlook = {
        "subject": title,
        "startdt": start_iso,
        "body": description,
        "location": location,
        "allday": str(all_day).lower(),
    }
    if end_iso:
        outlook["enddt"] = end_iso
    return dict(
        start=start,
        end=end,
        all_day=all_day,
        title=title,
        description=description,
        location=location,
        google=google,
        outlook="https://outlook.live.com/calendar/0/deeplink/compose?"
        + urlencode(outlook),
        office="https://outlook.office.com/calendar/0/deeplink/compose?"
        + urlencode(outlook),
    )


def escape(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def fold(line):
    chunks, current = [], ""
    for char in line:
        if len((current + char).encode("utf-8")) > 75:
            chunks.append(current)
            current = " "
        current += char
    return "\r\n".join([*chunks, current])


def calendar_file(event, occurrence=None):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//North Georgia Holiday Events//Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    indexes = range(len(event["occurrences"])) if occurrence is None else [occurrence]
    for index in indexes:
        item = calendar_entry(event, index)
        o = event["occurrences"][index]
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{event['id']}-{o['start_date']}-{o.get('start_time') or 'all-day'}-{index}@christmas.decorteindustries.com",
                "DTSTAMP:" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                "SUMMARY:" + escape(item["title"]),
                "DESCRIPTION:" + escape(item["description"]),
                "LOCATION:" + escape(item["location"]),
            ]
        )
        suffix = ";VALUE=DATE" if item["all_day"] else ""
        lines.append(f"DTSTART{suffix}:{item['start']}")
        if item["end"]:
            lines.append(f"DTEND{suffix}:{item['end']}")
        if event.get("source_url"):
            lines.append("URL:" + escape(event["source_url"]))
        lines.append(
            "STATUS:"
            + (
                "CANCELLED"
                if event.get("status") == "cancelled"
                else "CONFIRMED"
                if event.get("verified") and event.get("status") == "scheduled"
                else "TENTATIVE"
            )
        )
        lines.append("END:VEVENT")
    return "\r\n".join(map(fold, [*lines, "END:VCALENDAR"])) + "\r\n"
