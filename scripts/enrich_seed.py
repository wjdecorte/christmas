"""Apply checked official-source findings to the supplied-list transcription."""

import json
from pathlib import Path

p = Path("data/seed.json")
data = json.loads(p.read_text())
venues = {v["id"]: v for v in data["venues"]}
events = {e["id"]: e for e in data["events"]}
venues["falany"]["address"] = "199 Fine Arts Drive, Waleska, GA 30183"
venues["woodstock-city-center"]["address"] = "101 Arnold Mill Rd, Woodstock, GA 30188"
for id, name, city, address in [
    (
        "woodstock-arts",
        "Woodstock Arts Theatre",
        "Woodstock",
        "8534 Main St, Woodstock, GA 30188",
    ),
    (
        "depot-park",
        "Depot Park",
        "Kennesaw",
        "2828 Cherokee Street NW, Kennesaw, GA 30144",
    ),
    (
        "marietta-pac",
        "Marietta Performing Arts Center",
        "Marietta",
        "1171 Whitlock Ave NW, Marietta, GA 30064",
    ),
]:
    venues.setdefault(id, dict(id=id, name=name, city=city, address=address))


def confirm(
    id, url, notes, occurrences=None, venue=None, price=None, price_details=None
):
    e = events[id]
    e.update(
        verified=True,
        last_checked="2026-11-10",
        last_verified="2026-11-10",
        source_url=url,
        verification_notes=notes,
        schedule_notes=notes,
    )
    if occurrences is not None:
        e["occurrences"] = occurrences
    if venue:
        e["venue_id"] = venue
    if price:
        e["price_type"] = price
    if price_details:
        e["price_details"] = price_details


def occurrence(day, start=None, end=None, end_date=None):
    return dict(
        start_date="2026-" + day,
        end_date=end_date or "2026-" + day,
        start_time=start,
        end_time=end,
    )


confirm(
    "atlanta-pops",
    "https://atlantapops.org/concerts-events/",
    "Orchestra calendar confirms two November 30 performances at the Falany. End times and prices not stated.",
    [occurrence("11-30", "15:00"), occurrence("11-30", "19:30")],
    venue="falany",
)
confirm(
    "christmas-carol-musical",
    "https://woodstockarts.org/events/a-christmas-carol-2026/",
    "Producer lists individual performances. December 10 is not available online; contact the theatre. End times not assumed.",
    [
        occurrence("12-" + d, t)
        for d, t in [
            ("04", "19:30"),
            ("05", "19:30"),
            ("06", "14:30"),
            ("10", "10:00"),
            ("11", "19:30"),
            ("12", "19:30"),
            ("13", "14:30"),
            ("18", "19:30"),
            ("19", "19:30"),
            ("20", "14:30"),
            ("23", "14:30"),
            ("24", "14:30"),
        ]
    ],
    venue="woodstock-arts",
    price="paid",
    price_details="Online $21–22; at the door $23–25. Check producer for current fees and availability.",
)
confirm(
    "georgia-symphony-pops",
    "https://www.georgiasymphony.org/event/holiday-pops-4/",
    "Orchestra confirms both concerts. Sunday source: https://www.georgiasymphony.org/event/holiday-pops-5/",
    [occurrence("12-05", "19:30", "21:30"), occurrence("12-06", "15:00", "17:00")],
    venue="marietta-pac",
    price="paid",
    price_details="Saturday $20–65; Sunday $15–49.50, as listed by the orchestra. Fees and availability may vary.",
)
confirm(
    "kennesaw-tree-lighting",
    "https://www.kennesaw-ga.gov/kennesaw-event/annual-tree-lighting-ceremony-2/",
    "City calendar confirms ceremony hours at Depot Park; lighting at 7 pm.",
    [occurrence("12-02", "18:00", "19:30")],
    venue="depot-park",
)
confirm(
    "glimmer-and-glee",
    "https://www.kennesaw-ga.gov/kennesaw-event/glimmer-glee-drone-show/",
    "City calendar confirms evening program 6–8 pm and drone display at 7:30 pm.",
    [occurrence("12-13", "18:00", "20:00")],
    venue="depot-park",
)
confirm(
    "kennesaw-extravaganza",
    "https://www.kennesaw-ga.gov/kennesaw-celebrates-the-holiday-season-with-annual-holly-days-events/",
    "City confirms November 29 through January 10, 2027 at Depot Park. Daily access hours not stated.",
    [occurrence("11-29", end_date="2027-01-10")],
    venue="depot-park",
)
e = events["nashville-noel"]
e.update(
    source_url="https://thefalany.showare.com/eventperformances.asp?evt=9",
    last_checked="2026-11-10",
    verification_notes="Official ticketing page confirms show and venue; date loads dynamically and was not confirmed. Supplied date retained as unverified.",
)
e = events["kennesaw-santa-parade"]
e.update(
    source_url="https://www.kennesaw-ga.gov/city-notifications/",
    last_checked="2026-11-10",
    verification_notes="City confirms parade December 5 at 6 pm; full combined Day with Santa schedule remains unverified.",
)
data["venues"] = list(venues.values())
data["events"] = list(events.values())
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(
    "Confirmed", sum(e["verified"] for e in data["events"]), "of", len(data["events"])
)
