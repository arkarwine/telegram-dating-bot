from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from pymongo import ReturnDocument

from bot.models import profile_is_complete, utcnow


class UsersRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def upsert_from_telegram(self, user: Any, default_language: str) -> dict[str, Any]:
        update = {
            "$set": {
                "telegram_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "updated_at": utcnow(),
            },
            "$setOnInsert": {
                "language": default_language,
                "status": "active",
                "preview_count": 0,
                "created_at": utcnow(),
            },
        }
        return await self.db.users.find_one_and_update(
            {"telegram_id": user.id},
            update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def get_by_telegram_id(self, telegram_id: int) -> dict[str, Any] | None:
        return await self.db.users.find_one({"telegram_id": telegram_id})

    async def set_language(self, telegram_id: int, language: str) -> None:
        await self.db.users.update_one(
            {"telegram_id": telegram_id}, {"$set": {"language": language, "updated_at": utcnow()}}
        )

    async def set_profile_setup_step(self, telegram_id: int, step: str | None) -> None:
        update: dict[str, Any]
        if step:
            update = {"$set": {"profile_setup_step": step, "updated_at": utcnow()}}
        else:
            update = {"$unset": {"profile_setup_step": ""}, "$set": {"updated_at": utcnow()}}
        await self.db.users.update_one({"telegram_id": telegram_id}, update)

    async def set_profile_edit_mode(self, telegram_id: int, editing: bool) -> None:
        await self.db.users.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"profile_edit_mode": editing, "updated_at": utcnow()}},
        )

    async def set_relay_target(self, telegram_id: int, target_id: int | None) -> None:
        if target_id is None:
            update = {"$unset": {"relay_target_id": ""}, "$set": {"updated_at": utcnow()}}
        else:
            update = {"$set": {"relay_target_id": target_id, "updated_at": utcnow()}}
        await self.db.users.update_one({"telegram_id": telegram_id}, update)

    async def increment_preview(self, telegram_id: int) -> int:
        user = await self.db.users.find_one_and_update(
            {"telegram_id": telegram_id},
            {"$inc": {"preview_count": 1}, "$set": {"updated_at": utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return int(user.get("preview_count", 0)) if user else 0

    async def set_status(self, telegram_id: int, status: str) -> None:
        await self.db.users.update_one(
            {"telegram_id": telegram_id}, {"$set": {"status": status, "updated_at": utcnow()}}
        )


class ProfilesRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get(self, user_id: int) -> dict[str, Any] | None:
        return await self.db.profiles.find_one({"user_id": user_id})

    async def delete(self, user_id: int) -> None:
        await self.db.profiles.delete_one({"user_id": user_id})

    async def update_fields(self, user_id: int, fields: dict[str, Any]) -> dict[str, Any]:
        current = await self.get(user_id) or {"user_id": user_id}
        merged = {**current, **fields}
        complete = profile_is_complete(merged)
        update = {
            "$set": {**fields, "complete": complete, "visible": complete, "updated_at": utcnow()},
            "$setOnInsert": {"user_id": user_id, "created_at": utcnow(), "banned": False},
        }
        return await self.db.profiles.find_one_and_update(
            {"user_id": user_id},
            update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def mark_banned(self, user_id: int, banned: bool) -> None:
        await self.db.profiles.update_one(
            {"user_id": user_id},
            {"$set": {"banned": banned, "updated_at": utcnow()}},
            upsert=True,
        )

    async def find_candidates(self, query: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
        cursor = self.db.profiles.find(query).sort("updated_at", -1).limit(limit)
        return [doc async for doc in cursor]


class ActionsRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def add(
        self, actor_id: int, target_id: int, action_type: str, reason: str | None = None
    ) -> dict[str, Any]:
        await self.db.actions.update_one(
            {"actor_id": actor_id, "target_id": target_id, "type": action_type},
            {
                "$set": {"reason": reason, "updated_at": utcnow()},
                "$setOnInsert": {"created_at": utcnow()},
            },
            upsert=True,
        )
        return await self.db.actions.find_one(
            {"actor_id": actor_id, "target_id": target_id, "type": action_type}
        )

    async def has_action(self, actor_id: int, target_id: int, action_type: str) -> bool:
        return bool(
            await self.db.actions.find_one(
                {"actor_id": actor_id, "target_id": target_id, "type": action_type}
            )
        )

    async def has_any_action(self, actor_id: int, target_id: int, action_types: list[str]) -> bool:
        return bool(
            await self.db.actions.find_one(
                {"actor_id": actor_id, "target_id": target_id, "type": {"$in": action_types}}
            )
        )

    async def target_ids_for_actor(self, actor_id: int, types: list[str]) -> list[int]:
        cursor = self.db.actions.find({"actor_id": actor_id, "type": {"$in": types}})
        return [int(doc["target_id"]) async for doc in cursor]

    async def counts_for_target(self, target_id: int) -> dict[str, int]:
        pipeline = [
            {"$match": {"target_id": target_id, "type": {"$in": ["heart", "like", "pass"]}}},
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
        ]
        counts = {"hearts": 0, "passes": 0}
        async for doc in self.db.actions.aggregate(pipeline):
            if doc["_id"] in {"heart", "like"}:
                counts["hearts"] += int(doc["count"])
            elif doc["_id"] == "pass":
                counts["passes"] += int(doc["count"])
        return counts

    async def delete_for_user(self, user_id: int) -> None:
        await self.db.actions.delete_many({"$or": [{"actor_id": user_id}, {"target_id": user_id}]})

    async def latest_reports(self, limit: int = 10) -> list[dict[str, Any]]:
        cursor = self.db.actions.find({"type": "report"}).sort("created_at", -1).limit(limit)
        return [doc async for doc in cursor]

    async def next_report(self, before_id: str | None = None) -> dict[str, Any] | None:
        query: dict[str, Any] = {"type": "report"}
        if before_id:
            query["_id"] = {"$lt": ObjectId(before_id)}
        return await self.db.actions.find_one(query, sort=[("created_at", -1)])


class MatchesRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_between(self, user_a: int, user_b: int) -> dict[str, Any] | None:
        return await self.db.matches.find_one({"user_ids": sorted([user_a, user_b])})

    async def create(self, user_a: int, user_b: int) -> dict[str, Any]:
        user_ids = sorted([user_a, user_b])
        return await self.db.matches.find_one_and_update(
            {"user_ids": user_ids},
            {
                "$setOnInsert": {
                    "user_ids": user_ids,
                    "revealed": True,
                    "created_at": utcnow(),
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def list_for_user(self, user_id: int) -> list[dict[str, Any]]:
        cursor = self.db.matches.find({"user_ids": user_id}).sort("created_at", -1)
        return [doc async for doc in cursor]

    async def delete_for_user(self, user_id: int) -> None:
        await self.db.matches.delete_many({"user_ids": user_id})


class AdminEventsRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def add(self, admin_id: int, action: str, target_id: int) -> None:
        await self.db.admin_events.insert_one(
            {"admin_id": admin_id, "action": action, "target_id": target_id, "created_at": utcnow()}
        )
