from pyrogram import Client
from pyrogram.types import BotCommand


COMMANDS = [
    BotCommand("start", "Open the welcome screen"),
    BotCommand("profile", "Set up or edit your dating profile"),
    BotCommand("browse", "Browse profile previews"),
    BotCommand("matches", "See your mutual matches"),
    BotCommand("stats", "View your dating stats"),
    BotCommand("owner", "Contact the owner"),
    BotCommand("support", "Get support"),
    BotCommand("updates", "See update channel"),
    BotCommand("settings", "Change language"),
    BotCommand("help", "How the bot works"),
]


async def setup_bot_menu(app: Client) -> None:
    await app.set_bot_commands(COMMANDS)
