from pyrogram import Client

from bot.context import AppContext
from bot.handlers import admin, browsing, profile, start


def register_handlers(app: Client, ctx: AppContext) -> None:
    start.register(app, ctx)
    profile.register(app, ctx)
    browsing.register(app, ctx)
    admin.register(app, ctx)

