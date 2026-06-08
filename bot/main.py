import logging

from pyrogram import Client, idle

from bot.config import get_settings
from bot.context import AppContext
from bot.database import create_client, ensure_indexes, get_database
from bot.handlers import register_handlers
from bot.location import LocationResolver
from bot.repositories import ActionsRepo, AdminEventsRepo, MatchesRepo, ProfilesRepo, UsersRepo


async def build_context() -> AppContext:
    settings = get_settings()
    mongo_client = create_client(settings)
    db = get_database(mongo_client, settings)
    await ensure_indexes(db)
    return AppContext(
        settings=settings,
        users=UsersRepo(db),
        profiles=ProfilesRepo(db),
        actions=ActionsRepo(db),
        matches=MatchesRepo(db),
        admin_events=AdminEventsRepo(db),
        locations=LocationResolver(db, settings.geocoder_base_url),
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ctx = await build_context()
    app = Client(
        "telegram_dating_bot",
        api_id=ctx.settings.api_id,
        api_hash=ctx.settings.api_hash,
        bot_token=ctx.settings.bot_token,
        in_memory=True,
    )
    register_handlers(app, ctx)
    await app.start()
    logging.info("Telegram dating bot started.")
    await idle()
    await app.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
