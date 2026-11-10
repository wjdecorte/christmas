from datetime import date, time
from typing import Literal
from pydantic import BaseModel, Field, model_validator, field_validator

Category = Literal[
    "concert",
    "parade",
    "market",
    "lights",
    "tree-lighting",
    "theatre",
    "ice-skating",
    "festival",
]
CATEGORIES = [
    "concert",
    "parade",
    "market",
    "lights",
    "tree-lighting",
    "theatre",
    "ice-skating",
    "festival",
]


class Venue(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,99}$")
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(default="", max_length=500)
    city: str = Field(min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    coordinate_source: str = Field(default="", max_length=1000)
    geocoded_at: str | None = None

    @model_validator(mode="after")
    def coordinates(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and longitude must be set together")
        if self.latitude is not None and not self.coordinate_source.strip():
            raise ValueError("Record the source of these coordinates")
        return self


class Occurrence(BaseModel):
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None

    @model_validator(mode="after")
    def order(self):
        if self.end_date < self.start_date:
            raise ValueError("End date must follow start date")
        if (
            self.start_date == self.end_date
            and self.start_time
            and self.end_time
            and self.end_time < self.start_time
        ):
            raise ValueError(
                "End time must follow start time; set the next end date for overnight events"
            )
        return self


class Event(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,99}$")
    name: str = Field(min_length=1, max_length=250)
    category: Category
    venue_id: str | None = None
    city: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=10000)
    price_type: Literal["free", "paid", "unknown"] = "unknown"
    price_details: str = Field(default="", max_length=1000)
    source_url: str = Field(default="", max_length=2000)
    verified: bool = False
    last_verified: date | None = None
    last_checked: date | None = None
    verification_notes: str = Field(default="", max_length=5000)
    featured: bool = False
    season: int = Field(ge=2000, le=2200)
    schedule_notes: str = Field(default="", max_length=5000)
    occurrences: list[Occurrence] = Field(default_factory=list, max_length=500)

    @field_validator("source_url")
    @classmethod
    def valid_url(cls, value):
        from urllib.parse import urlparse

        if value and (
            urlparse(value).scheme not in ("http", "https")
            or not urlparse(value).netloc
        ):
            raise ValueError("Source URL must be an http or https URL")
        return value

    @model_validator(mode="after")
    def confirmation(self):
        if self.verified and (
            not self.last_verified or not self.source_url or not self.occurrences
        ):
            raise ValueError(
                "Verified events require a source URL, verification date and dated occurrence"
            )
        return self


class Dataset(BaseModel):
    venues: list[Venue] = Field(default_factory=list, max_length=1000)
    events: list[Event] = Field(default_factory=list, max_length=2000)


class EventRead(Event):
    venue: Venue | None = None
    updated_at: str
