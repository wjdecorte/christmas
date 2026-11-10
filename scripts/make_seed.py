"""Reproducible supplied-list transcription. Not run at application startup."""

import json
from pathlib import Path

data = {"venues": [], "events": []}


def venue(id, name, city, address=""):
    data["venues"].append(dict(id=id, name=name, city=city, address=address))
    return id


cannon = venue(
    "cannon-park", "Cannon Park", "Canton", "130 E Main St, Canton, GA 30114"
)
town = venue(
    "alpharetta-town-green",
    "Village Green / Downtown Alpharetta",
    "Alpharetta",
    "2 Park Plaza, Alpharetta, GA 30009",
)
avalon = venue(
    "avalon", "Avalon", "Alpharetta", "400 Avalon Blvd, Alpharetta, GA 30009"
)
mill = venue(
    "mill-on-etowah",
    "The Mill on Etowah",
    "Canton",
    "225 Reformation Parkway, Canton, GA 30114",
)
woodpark = venue("woodstock-city-center", "The Park at City Center", "Woodstock")
falany = venue("falany", "Falany Performing Arts Center", "Waleska")
dixie = venue("dixie-speedway", "Dixie Speedway", "Woodstock")
veterans = venue("cherokee-veterans-park", "Cherokee Veterans Park", "Canton")
fbc = venue("first-baptist-woodstock", "First Baptist Woodstock", "Woodstock")


def add(
    id, name, city, category, start=None, end=None, venue_id=None, dates=None, notes=""
):
    occurrences = []
    for d in dates or ([start] if start else []):
        occurrences.append(
            dict(
                start_date="2026-" + d,
                end_date="2026-" + (end or d),
                start_time=None,
                end_time=None,
            )
        )
    data["events"].append(
        dict(
            id=id,
            name=name,
            city=city,
            category=category,
            season=2026,
            venue_id=venue_id,
            description=f"{name} in {city}. See the official source for current event information.",
            price_type="unknown",
            price_details="",
            source_url="",
            verified=False,
            last_verified=None,
            last_checked=None,
            verification_notes="Imported from the supplied planning list. Official 2026 confirmation is still needed.",
            featured=category == "concert",
            schedule_notes=notes
            or (
                "Date range from supplied list; individual operating days and performance times are unconfirmed."
                if end
                else "Time to be announced."
            ),
            occurrences=occurrences,
        )
    )


add(
    "canton-tree-lighting",
    "Canton Tree Lighting and Drone Show",
    "Canton",
    "tree-lighting",
    "11-18",
    venue_id=cannon,
)
add(
    "hamilton-tree-lighting",
    "Hamilton Hotel Christmas Tree Lighting",
    "Alpharetta",
    "tree-lighting",
    "11-20",
)
add(
    "roswell-christkindlmarket",
    "Roswell Christkindlmarket",
    "Roswell",
    "market",
    "11-20",
    "12-23",
)
add(
    "season-of-celebration",
    "Alpharetta Season of Celebration",
    "Alpharetta",
    "tree-lighting",
    "11-21",
    venue_id=town,
)
add(
    "cumming-tree-lighting",
    "Cumming Christmas Tree Lighting",
    "Cumming",
    "tree-lighting",
    "11-21",
)
add(
    "ball-ground-light-up",
    "Ball Ground Light Up the Night",
    "Ball Ground",
    "festival",
    "11-21",
)
add(
    "lighting-of-avalon",
    "Lighting of Avalon",
    "Alpharetta",
    "tree-lighting",
    "11-22",
    venue_id=avalon,
)
add(
    "ball-ground-tree-lighting",
    "Ball Ground Hometown Tree Lighting",
    "Ball Ground",
    "tree-lighting",
    "11-28",
)
add(
    "alpharetta-holiday-symphony",
    "An Alpharetta Holiday — Alpharetta Symphony",
    "Alpharetta",
    "concert",
    "11-28",
)
add(
    "kennesaw-extravaganza",
    "Kennesaw Holiday Extravaganza",
    "Kennesaw",
    "festival",
    "11-29",
    notes="Supplied list says November 29 onward; closing date and operating schedule unknown.",
)
add(
    "atlanta-pops",
    "Atlanta Pops Orchestra Christmas",
    "Waleska",
    "concert",
    "11-30",
    venue_id=falany,
)
add("hickory-flat-market", "Hickory Flat Christmas Market", "Canton", "market", "12-01")
add(
    "kennesaw-tree-lighting",
    "Kennesaw Tree Lighting",
    "Kennesaw",
    "tree-lighting",
    "12-02",
)
add(
    "marietta-tree-lighting",
    "Marietta Square Tree Lighting",
    "Marietta",
    "tree-lighting",
    "12-03",
)
add(
    "mistletoe-on-main",
    "Mistletoe on Main",
    "Canton",
    "festival",
    dates=["12-03", "12-10", "12-17"],
)
add(
    "christmas-at-reinhardt",
    "Christmas at Reinhardt",
    "Waleska",
    "concert",
    "12-03",
    "12-06",
    venue_id=falany,
)
add(
    "march-of-toys",
    "March of the Toys Christmas Parade",
    "Ball Ground",
    "parade",
    "12-04",
)
add(
    "roswell-tree-lighting",
    "Roswell Christmas Tree Lighting",
    "Roswell",
    "tree-lighting",
    "12-04",
)
add(
    "christmas-carol-musical",
    "A Christmas Carol: The Musical",
    "Woodstock",
    "theatre",
    "12-04",
    "12-24",
)
add(
    "dickens-christmas-carol",
    "A Dickens’ Christmas Carol",
    "Canton",
    "theatre",
    "12-04",
    "12-13",
)
add(
    "ball-ground-market",
    "Ball Ground Christmas Market",
    "Ball Ground",
    "market",
    "12-05",
    "12-06",
)
add(
    "kennesaw-santa-parade",
    "A Day with Santa and Illuminate Holly Days Parade",
    "Kennesaw",
    "parade",
    "12-05",
)
add("snow-day", "Snow Day at Cumming City Center", "Cumming", "festival", "12-05")
add(
    "georgia-symphony-pops",
    "Georgia Symphony Holiday Pops",
    "Marietta",
    "concert",
    "12-05",
    "12-06",
)
add(
    "woodstock-jubilee",
    "Woodstock Christmas Jubilee and Parade of Lights",
    "Woodstock",
    "parade",
    "12-06",
    venue_id=woodpark,
)
add("nashville-noel", "Nashville Noel", "Waleska", "concert", "12-07", venue_id=falany)
add(
    "christmas-with-elvis",
    "Christmas with Elvis",
    "Woodstock",
    "concert",
    "12-09",
    "12-10",
)
add("nutcracker", "The Nutcracker", "Roswell", "theatre", "12-11", "12-13")
add(
    "canton-merry-market",
    "Canton Merry Market and Christmas Parade",
    "Canton",
    "market",
    "12-12",
)
add(
    "holly-springs-parade",
    "Holly Springs Holly Jolly Christmas Parade",
    "Holly Springs",
    "parade",
    "12-12",
)
add("cumming-parade", "Cumming Christmas Parade", "Cumming", "parade", "12-12")
add(
    "alpharetta-winter-parade",
    "Alpharetta Winter Parade",
    "Alpharetta",
    "parade",
    "12-12",
)
add(
    "sounds-of-season",
    "Sounds of the Season — First Baptist Woodstock",
    "Woodstock",
    "concert",
    "12-12",
    "12-13",
    venue_id=fbc,
)
add(
    "glimmer-and-glee",
    "Kennesaw Glimmer and Glee Drone Show",
    "Kennesaw",
    "lights",
    "12-13",
)
add(
    "celtic-angels",
    "Celtic Angels Christmas",
    "Waleska",
    "concert",
    "12-17",
    venue_id=falany,
)
add("grinchmas", "Grinchmas at The Mill", "Canton", "festival", "12-18", venue_id=mill)
add(
    "polar-express",
    "Polar Express Winter Wonderland Festival",
    "Canton",
    "festival",
    "12-19",
)
add("big-band-jazz", "Big Band Holiday Jazz", "Woodstock", "concert", "12-20")
add(
    "woodstock-lights",
    "Holiday Lights of Woodstock",
    "Woodstock",
    "lights",
    venue_id=dixie,
    notes="2026 opening and closing dates and daily hours await confirmation.",
)
add(
    "canton-lights",
    "Holiday Lights of Canton",
    "Canton",
    "lights",
    venue_id=veterans,
    notes="2026 opening and closing dates and daily hours await confirmation.",
)
add(
    "rink-on-river",
    "Rink on the River",
    "Canton",
    "ice-skating",
    venue_id=mill,
    notes="2026 operating dates, session times and ticket prices await confirmation.",
)
add(
    "avalon-ice",
    "Avalon on Ice",
    "Alpharetta",
    "ice-skating",
    venue_id=avalon,
    notes="2026 operating dates, session times and ticket prices await confirmation.",
)
add(
    "lights-loop",
    "Lights on the Loop",
    "Alpharetta",
    "lights",
    notes="December 2026; precise dates, access points and hours await confirmation.",
)

confirmed = {
    "canton-tree-lighting": (
        "https://explorecantonga.com/events/city-of-canton-tree-lighting-and-drone-show/",
        "18:30",
        "20:30",
        "Official tourism event page confirms date, time and Cannon Park address. Admission price not stated.",
    ),
    "season-of-celebration": (
        "https://www.awesomealpharetta.com/christmas-tree-lighting/",
        "17:00",
        "20:00",
        "Official tourism source confirms 2026 date and hours. Explore Georgia confirms Village Green at 2 Park Plaza and free admission.",
    ),
    "lighting-of-avalon": (
        "https://www.awesomealpharetta.com/event/the-lighting-of-avalon/",
        "14:00",
        "19:30",
        "Official tourism calendar confirms 2026 date, hours and Avalon venue. Individual activities may cost extra.",
    ),
    "woodstock-jubilee": (
        "https://woodstock.recdesk.com/Community/Program/Detail?programId=2646",
        "14:00",
        None,
        "City Parks and Recreation confirms December 6: festival 2–5 pm at The Park at City Center; parade begins at 5:30 pm. Parade end time not stated.",
    ),
}
for e in data["events"]:
    if e["id"] in confirmed:
        url, start, end, note = confirmed[e["id"]]
        e.update(
            source_url=url,
            verified=True,
            last_verified="2026-11-10",
            last_checked="2026-11-10",
            verification_notes=note,
            schedule_notes=note,
        )
        e["occurrences"][0].update(start_time=start, end_time=end)
        if e["id"] == "season-of-celebration":
            e["price_type"] = "free"
    if e["id"] in ["avalon-ice", "lights-loop"]:
        e["source_url"] = "https://www.awesomealpharetta.com/events/dont-miss-events/"
        e["last_checked"] = "2026-11-10"
        e["verification_notes"] = (
            "Official annual calendar mentions the 2026 attraction. Detailed schedule not fully verified."
        )
Path("data/seed.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(f"Seed: {len(data['events'])} events, {len(data['venues'])} venues")
