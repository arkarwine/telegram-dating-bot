from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bot.chat_sessions import close_chat_session
from bot.context import AppContext
from bot.i18n import t
from bot.keyboards import home_keyboard, language_keyboard, welcome_keyboard


INFO_FIELDS = {
    "owner": "owner_link",
    "support": "support_link",
    "updates": "updates_link",
}


def _configured_value(ctx: AppContext, info_type: str) -> str | None:
    field = INFO_FIELDS[info_type]
    return getattr(ctx.settings, field, None)


async def send_start_menu(
    message: Message,
    ctx: AppContext,
    language: str | None,
    edit: bool = False,
    notice: str | None = None,
) -> None:
    welcome_text = t(language, "welcome")
    text = f"{notice}\n\n{welcome_text}" if notice else welcome_text
    markup = welcome_keyboard(ctx.settings)
    if ctx.settings.start_image:
        await message.reply_photo(ctx.settings.start_image, caption=text, reply_markup=markup, quote=False)
        if edit:
            await message.delete()
        return
    if edit and getattr(message, "photo", None):
        await message.reply_text(text, reply_markup=markup, quote=False)
        await message.delete()
    elif edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.reply_text(text, reply_markup=markup)


async def send_config_info(
    message: Message, ctx: AppContext, language: str | None, info_type: str, edit: bool = False
) -> None:
    value = _configured_value(ctx, info_type)
    text = (
        t(language, f"{info_type}_info", value=value)
        if value
        else t(language, f"{info_type}_not_configured")
    )
    if edit and getattr(message, "photo", None):
        await message.reply_text(text, reply_markup=home_keyboard(), quote=False)
        await message.delete()
    elif edit:
        await message.edit_text(text, reply_markup=home_keyboard())
    else:
        await message.reply_text(text, reply_markup=home_keyboard(), quote=False)


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("start") & filters.private)
    async def start_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await send_start_menu(message, ctx, user.get("language"))

    @app.on_callback_query(filters.regex(r"^home:start$"))
    async def home_callback(client: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        if user.get("relay_target_id"):
            await close_chat_session(client, ctx, query.from_user.id)
        await query.answer()
        await send_start_menu(query.message, ctx, user.get("language"), edit=True)

    @app.on_message(filters.command("help") & filters.private)
    async def help_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text(t(user.get("language"), "help"), reply_markup=home_keyboard())

    @app.on_message(filters.command("settings") & filters.private)
    async def settings_handler(_: Client, message: Message) -> None:
        await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text(t(None, "choose_language"), reply_markup=language_keyboard())

    @app.on_message(filters.command(["owner", "support", "updates"]) & filters.private)
    async def info_command_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await send_config_info(message, ctx, user.get("language"), message.command[0])

    @app.on_callback_query(filters.regex(r"^info:(owner|support|updates)$"))
    async def info_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        await send_config_info(
            query.message, ctx, user.get("language"), query.data.rsplit(":", 1)[1], edit=True
        )

    @app.on_callback_query(filters.regex(r"^settings:language$"))
    async def settings_callback(_: Client, query: CallbackQuery) -> None:
        await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        if getattr(query.message, "photo", None):
            await query.message.reply_text(t(None, "choose_language"), reply_markup=language_keyboard(), quote=False)
            await query.message.delete()
        else:
            await query.message.edit_text(t(None, "choose_language"), reply_markup=language_keyboard())

    @app.on_callback_query(filters.regex(r"^lang:(en|my)$"))
    async def language_callback(_: Client, query: CallbackQuery) -> None:
        language = query.data.split(":", 1)[1]
        await ctx.users.set_language(query.from_user.id, language)
        await query.answer()
        await send_start_menu(query.message, ctx, language, edit=True, notice=t(language, "language_saved"))
