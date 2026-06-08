from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from bot.config import Settings


def create_client(settings: Settings) -> AsyncIOMotorClient:
    return AsyncIOMotorClient(settings.mongodb_uri)


def get_database(client: AsyncIOMotorClient, settings: Settings) -> AsyncIOMotorDatabase:
    return client[settings.database_name]


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("telegram_id", unique=True)
    await db.profiles.create_index("user_id", unique=True)
    await db.profiles.create_index([("visible", 1), ("complete", 1), ("banned", 1)])
    await db.actions.create_index([("actor_id", 1), ("target_id", 1), ("type", 1)], unique=True)
    await db.actions.create_index([("target_id", 1), ("type", 1), ("created_at", -1)])
    await db.matches.create_index([("user_ids", 1)], unique=True)
    await db.location_cache.create_index("key", unique=True)
    await db.admin_events.create_index("created_at")

