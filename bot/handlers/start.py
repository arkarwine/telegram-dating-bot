from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bot.context import AppContext
from bot.i18n import t
from bot.keyboards import language_keyboard


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("start") & filters.private)
    async def start_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text(t(user.get("language"), "welcome"), reply_markup=language_keyboard())

    @app.on_message(filters.command("help") & filters.private)
    async def help_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text(t(user.get("language"), "help"))

    @app.on_message(filters.command("settings") & filters.private)
    async def settings_handler(_: Client, message: Message) -> None:
        await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text("Language / ဘာသာစကား", reply_markup=language_keyboard())

    @app.on_callback_query(filters.regex(r"^lang:(en|my)$"))
    async def language_callback(_: Client, query: CallbackQuery) -> None:
        language = query.data.split(":", 1)[1]
        await ctx.users.set_language(query.from_user.id, language)
        await query.answer()
        await query.message.reply_text(t(language, "language_saved"))

