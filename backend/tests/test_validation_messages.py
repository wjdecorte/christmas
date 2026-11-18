import pytest
from pydantic import ValidationError
from app.models import Event


def test_verified_event_explains_only_missing_requirements():
    event = {
        "id": "test-event",
        "name": "Test event",
        "category": "concert",
        "city": "Canton",
        "season": 2026,
        "source_url": "https://example.com/event",
        "occurrences": [{"start_date": "2026-12-01", "end_date": "2026-12-01"}],
        "verified": True,
    }
    with pytest.raises(ValidationError) as result:
        Event.model_validate(event)
    message = result.value.errors()[0]["msg"]
    assert "add a last verification date" in message
    assert "official source URL" not in message
    assert "uncheck Verified" in message
    event["verified"] = False
    assert Event.model_validate(event).last_verified is None
    event.update(verified=True, last_verified="2026-11-18")
    assert Event.model_validate(event).verified


def test_verified_event_lists_all_missing_requirements():
    with pytest.raises(ValidationError) as result:
        Event.model_validate({
            "id": "test-event", "name": "Test event", "category": "concert",
            "city": "Canton", "season": 2026, "verified": True,
        })
    message = result.value.errors()[0]["msg"]
    assert "last verification date" in message
    assert "official source URL" in message
    assert "at least one event date" in message
