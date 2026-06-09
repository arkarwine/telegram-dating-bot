import asyncio
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError

from bot.database import ensure_indexes
from bot.models import utcnow


SEED_PROFILES = [
    {
        "user_id": 990000001,
        "display_name": "Thiri",
        "age": 23,
        "gender": "female",
        "interested_in": "any",
        "bio": "Coffee walks, indie films, and finding the best mohinga in Yangon.",
        "photo_file_id": "https://picsum.photos/seed/thiri-yangon/900/900",
        "location": {"country_code": "mm", "country": "Myanmar", "region": "Yangon Region", "city": "Yangon", "township": "Kamayut", "display_name": "Kamayut, Yangon"},
    },
    {
        "user_id": 990000002,
        "display_name": "Min Khant",
        "age": 26,
        "gender": "male",
        "interested_in": "any",
        "bio": "Weekend photographer, tea shop regular, and a very patient listener.",
        "photo_file_id": "https://picsum.photos/seed/min-khant/900/900",
        "location": {"country_code": "mm", "country": "Myanmar", "region": "Yangon Region", "city": "Yangon", "township": "Bahan", "display_name": "Bahan, Yangon"},
    },
    {
        "user_id": 990000003,
        "display_name": "Su Myat",
        "age": 25,
        "gender": "female",
        "interested_in": "any",
        "bio": "Bookshop explorer, spicy-food fan, and always planning a small adventure.",
        "photo_file_id": "https://picsum.photos/seed/su-myat/900/900",
        "location": {"country_code": "mm", "country": "Myanmar", "region": "Mandalay Region", "city": "Mandalay", "township": "Chanayethazan", "display_name": "Chanayethazan, Mandalay"},
    },
    {
        "user_id": 990000004,
        "display_name": "Ko Zaw",
        "age": 28,
        "gender": "male",
        "interested_in": "any",
        "bio": "I cook, play guitar badly, and know several excellent sunset spots.",
        "photo_file_id": "https://picsum.photos/seed/ko-zaw/900/900",
        "location": {"country_code": "mm", "country": "Myanmar", "region": "Mandalay Region", "city": "Mandalay", "township": "Aungmyaythazan", "display_name": "Aungmyaythazan, Mandalay"},
    },
    {
        "user_id": 990000005,
        "display_name": "Nway",
        "age": 24,
        "gender": "other",
        "interested_in": "any",
        "bio": "Designer, playlist maker, and enthusiastic collector of tiny happy moments.",
        "photo_file_id": "https://picsum.photos/seed/nway/900/900",
        "location": {"country_code": "mm", "country": "Myanmar", "region": "Shan State", "city": "Taunggyi", "township": "Taunggyi", "display_name": "Taunggyi, Shan State"},
    },
]


async def seed() -> None:
    load_dotenv()
    client = AsyncIOMotorClient(
        os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017"),
        serverSelectionTimeoutMS=3000,
    )
    db = client[os.getenv("DATABASE_NAME", "telegram_dating_bot")]
    try:
        await client.admin.command("ping")
    except ServerSelectionTimeoutError as exc:
        client.close()
        raise SystemExit(
            "MongoDB is not reachable. Start MongoDB or set MONGODB_URI, then run python -m bot.seed."
        ) from exc
    await ensure_indexes(db)
    now = utcnow()

    for profile in SEED_PROFILES:
        user_id = profile["user_id"]
        await db.users.update_one(
            {"telegram_id": user_id},
            {
                "$set": {
                    "username": None,
                    "first_name": profile["display_name"],
                    "language": "en",
                    "status": "active",
                    "seeded": True,
                    "updated_at": now,
                },
                "$setOnInsert": {"telegram_id": user_id, "created_at": now, "preview_count": 0},
            },
            upsert=True,
        )
        await db.profiles.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    **profile,
                    "complete": True,
                    "visible": True,
                    "banned": False,
                    "seeded": True,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

        for index in range((user_id % 4) + 1):
            await db.actions.update_one(
                {"actor_id": 980000000 + index, "target_id": user_id, "type": "heart"},
                {"$setOnInsert": {"created_at": now}},
                upsert=True,
            )
        for index in range(user_id % 3):
            await db.actions.update_one(
                {"actor_id": 970000000 + index, "target_id": user_id, "type": "pass"},
                {"$setOnInsert": {"created_at": now}},
                upsert=True,
            )

    client.close()
    print(f"Seeded {len(SEED_PROFILES)} profiles.")


if __name__ == "__main__":
    asyncio.run(seed())
