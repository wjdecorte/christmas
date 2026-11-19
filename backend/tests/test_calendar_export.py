from urllib.parse import urlparse, parse_qs
from app.calendar_export import calendar_entry, calendar_file


def event(**changes):
    return {
        "id": "holiday",
        "name": "Holiday, fun; 🎄",
        "city": "Canton",
        "description": "First\nSecond",
        "verified": False,
        "status": "scheduled",
        "source_url": "https://example.com/events",
        "occurrences": [
            {
                "start_date": "2026-12-01",
                "end_date": "2026-12-01",
                "start_time": "18:00:00",
                "end_time": "20:00:00",
            }
        ],
        **changes,
    }


def test_timed_links_are_utc_with_eastern_conversion():
    item = calendar_entry(event(), 0)
    assert item["start"] == "20261201T230000Z"
    assert item["end"] == "20261202T010000Z"
    assert parse_qs(urlparse(item["google"]).query)["text"] == [event()["name"]]
    assert parse_qs(urlparse(item["office"]).query)["startdt"] == [
        "2026-12-01T23:00:00+00:00"
    ]
    summer = event(
        occurrences=[
            {
                "start_date": "2027-07-01",
                "end_date": "2027-07-01",
                "start_time": "18:00",
                "end_time": None,
            }
        ]
    )
    assert calendar_entry(summer, 0)["start"] == "20270701T220000Z"
    assert "DTEND" not in calendar_file(summer)
    assert "End time has not been announced" in calendar_entry(summer, 0)["description"]


def test_all_day_range_has_exclusive_end_and_clear_uncertainty():
    e = event(
        occurrences=[
            {"start_date": "2026-12-30", "end_date": "2027-01-02", "start_time": None}
        ]
    )
    text = calendar_file(e)
    assert "DTSTART;VALUE=DATE:20261230\r\n" in text
    assert "DTEND;VALUE=DATE:20270103\r\n" in text
    assert "all-day reminder" in calendar_entry(e, 0)["description"]
    assert "Unverified event" in text


def test_ics_escapes_text_and_folds_utf8_without_injection():
    text = calendar_file(event(name="x\r\nBEGIN:BAD," + "🎄" * 70))
    assert "\r\nBEGIN:BAD" not in text
    assert all(len(line.encode()) <= 75 for line in text.split("\r\n"))
    assert "\\nBEGIN:BAD\\," in text.replace("\r\n ", "")
    assert text.endswith("END:VCALENDAR\r\n")


def test_download_separate_performances_and_stable_uids():
    e = event()
    e["occurrences"].append(
        {"start_date": "2026-12-02", "end_date": "2026-12-02", "start_time": "18:00"}
    )
    assert calendar_file(e).count("BEGIN:VEVENT") == 2
    assert calendar_file(e, 1).count("BEGIN:VEVENT") == 1
    assert "DTSTART:20261202T230000Z" in calendar_file(e, 1)
    uids = [line for line in calendar_file(e).splitlines() if line.startswith("UID:")]
    assert len(set(uids)) == 2
    e["description"] = "Updated information"
    assert uids == [line for line in calendar_file(e).splitlines() if line.startswith("UID:")]
