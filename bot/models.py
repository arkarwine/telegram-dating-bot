from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from bot.constants import PROFILE_FIELDS


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ResolvedLocation:
    latitude: float
    longitude: float
    country_code: str
    country: str
    region: str | None
    city: str | None
    town: str | None
    township: str | None
    display_name: str

    @property
    def is_myanmar(self) -> bool:
        return self.country_code.lower() == "mm" or self.country.lower() in {"myanmar", "burma"}

    def to_profile_location(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country_code": self.country_code,
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "town": self.town,
            "township": self.township,
            "display_name": self.display_name,
        }


def profile_is_complete(profile: dict[str, Any] | None) -> bool:
    if not profile:
        return False
    return all(profile.get(field) for field in PROFILE_FIELDS)


def display_place(location: dict[str, Any] | None) -> str:
    if not location:
        return "Myanmar"
    parts = [
        location.get("township"),
        location.get("town"),
        location.get("city"),
        location.get("region"),
    ]
    return ", ".join(str(part) for part in parts if part) or location.get("display_name") or "Myanmar"

