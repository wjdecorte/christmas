"""Extract source-stated facts only. Discovery drafts never imply verification."""

import hashlib
import json
import re
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")


def canonical(url):
    p = urlsplit(url)
    return urlunsplit(
        (
            p.scheme.lower(),
            p.netloc.lower(),
            p.path.rstrip("/") or "/",
            urlencode(
                [
                    (k, v)
                    for k, v in parse_qsl(p.query)
                    if not k.lower().startswith("utm_")
                ]
            ),
            "",
        )
    )


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts = []
        self.links = []
        self.parts = []
        self.script = None
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            self.script = (
                [] if attrs.get("type", "").lower() == "application/ld+json" else None
            )
        if tag in ("script", "style", "nav", "footer", "header"):
            self.hidden += 1
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            self.scripts.append("".join(self.script))
            self.script = None
        if tag in ("script", "style", "nav", "footer", "header"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, text):
        if self.script is not None:
            self.script.append(text)
        elif not self.hidden:
            self.parts.append(text)

    @property
    def text(self):
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()[:12000]


def plain(value, limit=4000):
    if not isinstance(value, str):
        return ""
    p = Page()
    p.feed(value)
    return p.text[:limit]


def nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from nodes(item)
    elif isinstance(value, dict):
        yield value
        for item in value.values():
            if isinstance(item, (dict, list)):
                yield from nodes(item)


def local_stamp(value):
    if isinstance(value, datetime):
        d = value.astimezone(EASTERN) if value.tzinfo else value
        return d.date().isoformat(), d.time().replace(tzinfo=None).isoformat()
    if isinstance(value, date):
        return value.isoformat(), None
    if not isinstance(value, str):
        raise ValueError("A dated event is required")
    if len(value) == 10:
        return date.fromisoformat(value).isoformat(), None
    return local_stamp(datetime.fromisoformat(value.replace("Z", "+00:00")))


def category(name):
    name = name.casefold()
    for term, kind in [
        ("concert", "concert"),
        ("symphony", "concert"),
        ("pops", "concert"),
        ("parade", "parade"),
        ("market", "market"),
        ("nutcracker", "theatre"),
        ("musical", "theatre"),
        ("tree lighting", "tree-lighting"),
        ("ice", "ice-skating"),
        ("lights", "lights"),
    ]:
        if term in name:
            return kind
    return "festival"


def jsonld_records(body, url):
    page = Page()
    page.feed(body)
    documents = []
    for script in page.scripts:
        try:
            documents.extend(nodes(json.loads(script)))
        except (ValueError, RecursionError):
            continue
    # Direct JSON-LD feeds are supported as well as script elements.
    if not documents and body.lstrip().startswith(("{", "[")):
        try:
            documents = list(nodes(json.loads(body)))
        except (ValueError, RecursionError):
            pass
    refs = {x["@id"]: x for x in documents if isinstance(x.get("@id"), str)}
    records = []
    for item in documents:
        kinds = item.get("@type", [])
        kinds = [kinds] if isinstance(kinds, str) else kinds
        if not any(
            k
            in (
                "Event",
                "MusicEvent",
                "TheaterEvent",
                "Festival",
                "DanceEvent",
                "SocialEvent",
                "ChildrensEvent",
                "VisualArtsEvent",
            )
            for k in kinds
        ):
            continue
        name = plain(item.get("name"), 250)
        try:
            start, stime = local_stamp(item.get("startDate"))
            end, etime = local_stamp(item.get("endDate", item["startDate"]))
            if not item.get("endDate"):
                etime = None
        except (ValueError, TypeError, KeyError):
            continue
        if not name or end < start:
            continue
        link = urljoin(
            url, item.get("url") if isinstance(item.get("url"), str) else url
        )
        loc = item.get("location", {})
        loc = loc[0] if isinstance(loc, list) and loc else loc
        if isinstance(loc, dict) and loc.get("@id") in refs:
            loc = refs[loc["@id"]]
        address = loc.get("address", {}) if isinstance(loc, dict) else {}
        fields = {
            "name": name,
            "source_url": link,
            "occurrences": [
                dict(start_date=start, end_date=end, start_time=stime, end_time=etime)
            ],
        }
        if item.get("description"):
            fields["description"] = plain(item["description"])
        status = item.get("eventStatus", "").rsplit("/", 1)[-1]
        if status == "EventCancelled":
            fields["status"] = "cancelled"
        elif status in ("EventPostponed", "EventRescheduled"):
            fields["status"] = (
                "postponed" if status == "EventPostponed" else "scheduled"
            )
        elif status == "EventScheduled":
            fields["status"] = "scheduled"
        venue = None
        if isinstance(address, dict):
            city = plain(address.get("addressLocality"), 100)
            if city:
                fields["city"] = city
            street = plain(address.get("streetAddress"), 500)
            region = plain(address.get("addressRegion"), 50)
            if street and isinstance(loc, dict):
                venue = {
                    "name": plain(loc.get("name"), 200) or street,
                    "address": ", ".join(x for x in [street, city, region] if x),
                    "city": city,
                }
        elif isinstance(address, str) and isinstance(loc, dict):
            venue = {
                "name": plain(loc.get("name"), 200) or plain(address, 200),
                "address": plain(address, 500),
                "city": "",
            }
        offers = item.get("offers", {})
        offers = offers[0] if isinstance(offers, list) and offers else offers
        if isinstance(offers, dict) and offers.get("price") is not None:
            try:
                price = float(offers["price"])
                if price >= 0:
                    fields["price_type"] = "free" if price == 0 else "paid"
                    fields["price_details"] = (
                        f"{offers['price']} {offers.get('priceCurrency', '')} as listed by source".strip()
                    )
            except (ValueError, TypeError):
                pass
        if item.get("isAccessibleForFree") is True:
            fields["price_type"] = "free"
        external = str(
            item.get("@id")
            or (link if item.get("url") else url + "#" + name.casefold())
        )
        records.append(
            {
                "external_id": external,
                "fields": fields,
                "venue": venue,
                "evidence": page.text[:4000],
            }
        )
        if len(records) >= 100:
            break
    return records, page


def ical_records(body, url):
    from icalendar import Calendar

    calendar = Calendar.from_ical(body)
    records = []
    for item in calendar.walk("VEVENT"):
        # Unexpanded recurring series are never silently presented as complete schedules.
        if item.get("RRULE") or item.get("RDATE") or item.get("RECURRENCE-ID"):
            raise ValueError(
                "Recurring iCalendar rules/overrides require an expanded feed or individual event pages; no partial import performed"
            )
        name = plain(str(item.get("SUMMARY", "")), 250)
        if not name or not item.get("DTSTART"):
            continue
        raw_start = item.decoded("DTSTART")
        raw_end = item.decoded("DTEND") if item.get("DTEND") else raw_start
        start, stime = local_stamp(raw_start)
        end, etime = local_stamp(raw_end)
        if not stime and item.get("DTEND"):
            # RFC 5545 DATE end is exclusive; the application's date ranges are inclusive.
            end = (date.fromisoformat(end) - timedelta(days=1)).isoformat()
        if not item.get("DTEND"):
            etime = None
        if end < start:
            raise ValueError("Invalid iCalendar date range")
        fields = {
            "name": name,
            "source_url": urljoin(url, str(item.get("URL") or url)),
            "occurrences": [
                dict(start_date=start, end_date=end, start_time=stime, end_time=etime)
            ],
        }
        if item.get("DESCRIPTION"):
            fields["description"] = plain(str(item["DESCRIPTION"]))
        status = str(item.get("STATUS", ""))
        if status == "CANCELLED":
            fields["status"] = "cancelled"
        elif status == "CONFIRMED":
            fields["status"] = "scheduled"
        venue = None
        if item.get("LOCATION"):
            venue = {
                "name": plain(str(item["LOCATION"]), 200),
                "address": plain(str(item["LOCATION"]), 500),
                "city": "",
            }
        records.append(
            {
                "external_id": str(
                    item.get("UID") or fields["source_url"] + "#" + name.casefold()
                ),
                "fields": fields,
                "venue": venue,
                "evidence": plain(str(item.get("DESCRIPTION", ""))),
            }
        )
        if len(records) >= 100:
            break
    return records


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
