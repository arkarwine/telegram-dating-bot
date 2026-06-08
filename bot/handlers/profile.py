from pyrogram import Client, filters
from pyrogram.types import Message

from bot.context import AppContext
from bot.i18n import t
from bot.models import display_place, profile_is_complete
from bot.parser import parse_profile_text


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("profile") & filters.private)
    async def profile_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        profile = await ctx.profiles.get(message.from_user.id)
        if profile_is_complete(profile):
            await message.reply_text(t(user.get("language"), "profile_complete"))
        else:
            await message.reply_text(t(user.get("language"), "profile_help"))

    @app.on_message(filters.photo & filters.private)
    async def photo_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        photo = message.photo.file_id
        profile = await ctx.profiles.update_fields(message.from_user.id, {"photo_file_id": photo})
        key = "profile_complete" if profile_is_complete(profile) else "photo_saved"
        await message.reply_text(t(user.get("language"), key))

    @app.on_message(filters.location & filters.private)
    async def location_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        language = user.get("language")
        await message.reply_text(t(language, "location_processing"))
        resolved = await ctx.locations.resolve(message.location.latitude, message.location.longitude)
        if not resolved or not resolved.is_myanmar:
            await message.reply_text(t(language, "location_rejected"))
            return
        profile = await ctx.profiles.update_fields(
            message.from_user.id, {"location": resolved.to_profile_location()}
        )
        place = display_place(profile.get("location"))
        await message.reply_text(t(language, "location_saved", place=place))
        if profile_is_complete(profile):
            await message.reply_text(t(language, "profile_complete"))

    @app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "settings", "browse", "matches", "admin", "reports", "ban", "unban"]))
    async def profile_text_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        fields = parse_profile_text(message.text or "")
        if not fields:
            return
        profile = await ctx.profiles.update_fields(message.from_user.id, fields)
        key = "profile_complete" if profile_is_complete(profile) else "profile_incomplete"
        await message.reply_text(t(user.get("language"), key))

