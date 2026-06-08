from __future__ import annotations

from typing import Any

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from bot.models import ResolvedLocation, utcnow


def coordinate_key(latitude: float, longitude: float) -> str:
    return f"{latitude:.4f},{longitude:.4f}"


class LocationResolver:
    def __init__(self, db: AsyncIOMotorDatabase, base_url: str):
        self.db = db
        self.base_url = base_url.rstrip("/")

    async def resolve(self, latitude: float, longitude: float) -> ResolvedLocation | None:
        key = coordinate_key(latitude, longitude)
        cached = await self.db.location_cache.find_one({"key": key})
        if cached:
            return ResolvedLocation(**cached["location"])

        location = await self._reverse_geocode(latitude, longitude)
        if location:
            await self.db.location_cache.update_one(
                {"key": key},
                {
                    "$set": {"location": location.__dict__, "updated_at": utcnow()},
                    "$setOnInsert": {"created_at": utcnow()},
                },
                upsert=True,
            )
        return location

    async def _reverse_geocode(self, latitude: float, longitude: float) -> ResolvedLocation | None:
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "telegram-dating-bot/0.1"}) as client:
            response = await client.get(
                f"{self.base_url}/reverse",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "format": "jsonv2",
                    "accept-language": "en",
                    "zoom": 14,
                    "addressdetails": 1,
                },
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()

        address = payload.get("address") or {}
        country_code = str(address.get("country_code") or "").lower()
        country = str(address.get("country") or "")
        return ResolvedLocation(
            latitude=latitude,
            longitude=longitude,
            country_code=country_code,
            country=country,
            region=address.get("state") or address.get("region"),
            city=address.get("city") or address.get("county"),
            town=address.get("town") or address.get("village"),
            township=address.get("city_district") or address.get("suburb") or address.get("municipality"),
            display_name=str(payload.get("display_name") or "Myanmar"),
        )

