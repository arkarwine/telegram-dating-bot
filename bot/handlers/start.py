from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bot.context import AppContext
from bot.i18n import t
from bot.keyboards import home_keyboard, language_keyboard, welcome_keyboard


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("start") & filters.private)
    async def start_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text(t(user.get("language"), "welcome"), reply_markup=welcome_keyboard())

    @app.on_callback_query(filters.regex(r"^home:start$"))
    async def home_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        if getattr(query.message, "photo", None):
            await query.message.reply_text(
                t(user.get("language"), "welcome"), reply_markup=welcome_keyboard(), quote=False
            )
            await query.message.delete()
        else:
            await query.message.edit_text(t(user.get("language"), "welcome"), reply_markup=welcome_keyboard())

    @app.on_message(filters.command("help") & filters.private)
    async def help_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text(t(user.get("language"), "help"), reply_markup=home_keyboard())

    @app.on_message(filters.command("settings") & filters.private)
    async def settings_handler(_: Client, message: Message) -> None:
        await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text(t(None, "choose_language"), reply_markup=language_keyboard())

    @app.on_callback_query(filters.regex(r"^settings:language$"))
    async def settings_callback(_: Client, query: CallbackQuery) -> None:
        await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        await query.message.edit_text(t(None, "choose_language"), reply_markup=language_keyboard())

    @app.on_callback_query(filters.regex(r"^lang:(en|my)$"))
    async def language_callback(_: Client, query: CallbackQuery) -> None:
        language = query.data.split(":", 1)[1]
        await ctx.users.set_language(query.from_user.id, language)
        await query.answer()
        await query.message.edit_text(t(language, "language_saved"), reply_markup=welcome_keyboard())
