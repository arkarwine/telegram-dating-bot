import pytest

from bot.location import LocationResolver, coordinate_key


class FakeCollection:
    def __init__(self):
        self.docs = {}

    async def find_one(self, query):
        return self.docs.get(query["key"])

    async def update_one(self, query, update, upsert=False):
        self.docs[query["key"]] = {"key": query["key"], **update["$set"]}


class FakeDb:
    def __init__(self):
        self.location_cache = FakeCollection()


async def test_location_cache_key_rounds_coordinates() -> None:
    assert coordinate_key(16.840939, 96.173526) == "16.8409,96.1735"


@pytest.mark.asyncio
async def test_location_resolver_uses_cache() -> None:
    db = FakeDb()
    resolver = LocationResolver(db, "https://example.com")
    db.location_cache.docs["16.8409,96.1735"] = {
        "location": {
            "latitude": 16.8409,
            "longitude": 96.1735,
            "country_code": "mm",
            "country": "Myanmar",
            "region": "Yangon Region",
            "city": "Yangon",
            "town": None,
            "township": "Kamayut",
            "display_name": "Kamayut, Yangon, Myanmar",
        }
    }

    location = await resolver.resolve(16.840939, 96.173526)

    assert location is not None
    assert location.is_myanmar
    assert location.township == "Kamayut"
