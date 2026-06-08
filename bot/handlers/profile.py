from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bot.context import AppContext
from bot.i18n import t
from bot.keyboards import gender_keyboard, interested_in_keyboard, profile_start_keyboard
from bot.models import display_place, profile_is_complete
from bot.profile_setup import next_missing_step, next_step_after


async def prompt_profile_step(
    ctx: AppContext,
    message: Message,
    user_id: int,
    language: str | None,
    step: str | None,
    edit: bool = False,
) -> None:
    if not step:
        await ctx.users.set_profile_setup_step(user_id, None)
        if edit:
            await message.edit_text(t(language, "profile_complete"))
        else:
            await message.reply_text(t(language, "profile_complete"))
        return

    await ctx.users.set_profile_setup_step(user_id, step)
    if step == "gender":
        text = t(language, "profile_step_gender")
        markup = gender_keyboard()
    elif step == "interested_in":
        text = t(language, "profile_step_interested_in")
        markup = interested_in_keyboard()
    else:
        text = t(language, f"profile_step_{step}")
        markup = None

    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.reply_text(text, reply_markup=markup)


async def continue_profile_setup(
    ctx: AppContext,
    message: Message,
    user_id: int,
    language: str | None,
    profile: dict,
    completed_step: str,
    edit: bool = False,
) -> None:
    if profile_is_complete(profile):
        await ctx.users.set_profile_setup_step(user_id, None)
        if edit:
            await message.edit_text(t(language, "profile_complete"))
        else:
            await message.reply_text(t(language, "profile_complete"))
        return
    await prompt_profile_step(
        ctx, message, user_id, language, next_step_after(profile, completed_step), edit=edit
    )


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("profile") & filters.private)
    async def profile_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        profile = await ctx.profiles.get(message.from_user.id)
        if profile_is_complete(profile):
            await message.reply_text(
                t(user.get("language"), "profile_complete"),
                reply_markup=profile_start_keyboard(complete=True),
            )
        else:
            await message.reply_text(
                t(user.get("language"), "profile_help"),
                reply_markup=profile_start_keyboard(complete=False),
            )

    @app.on_callback_query(filters.regex(r"^profile:start$"))
    async def profile_start_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        profile = await ctx.profiles.get(query.from_user.id)
        await query.answer()
        await prompt_profile_step(
            ctx,
            query.message,
            query.from_user.id,
            user.get("language"),
            next_missing_step(profile) or "display_name",
            edit=True,
        )

    @app.on_callback_query(filters.regex(r"^profile:(gender|interested_in):(female|male|other|any)$"))
    async def profile_choice_callback(_: Client, query: CallbackQuery) -> None:
        field, value = query.data.split(":")[1:]
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        language = user.get("language")
        expected_step = user.get("profile_setup_step")
        if expected_step != field:
            await query.answer()
            await prompt_profile_step(
                ctx, query.message, query.from_user.id, language, expected_step, edit=True
            )
            return
        profile = await ctx.profiles.update_fields(query.from_user.id, {field: value})
        await query.answer()
        await continue_profile_setup(
            ctx, query.message, query.from_user.id, language, profile, field, edit=True
        )

    @app.on_message(filters.photo & filters.private)
    async def photo_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        language = user.get("language")
        if user.get("profile_setup_step") not in {None, "photo"}:
            await prompt_profile_step(
                ctx, message, message.from_user.id, language, user["profile_setup_step"]
            )
            return
        photo = message.photo.file_id
        profile = await ctx.profiles.update_fields(message.from_user.id, {"photo_file_id": photo})
        await continue_profile_setup(ctx, message, message.from_user.id, language, profile, "photo")

    @app.on_message(filters.location & filters.private)
    async def location_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        language = user.get("language")
        if user.get("profile_setup_step") not in {None, "location"}:
            await prompt_profile_step(
                ctx, message, message.from_user.id, language, user["profile_setup_step"]
            )
            return
        status_message = await message.reply_text(t(language, "location_processing"))
        resolved = await ctx.locations.resolve(message.location.latitude, message.location.longitude)
        if not resolved or not resolved.is_myanmar:
            await status_message.edit_text(t(language, "location_rejected"))
            return
        profile = await ctx.profiles.update_fields(
            message.from_user.id, {"location": resolved.to_profile_location()}
        )
        place = display_place(profile.get("location"))
        if profile_is_complete(profile):
            await ctx.users.set_profile_setup_step(message.from_user.id, None)
            await status_message.edit_text(t(language, "profile_complete_with_location", place=place))
        else:
            await status_message.edit_text(t(language, "location_saved", place=place))
            await continue_profile_setup(
                ctx, message, message.from_user.id, language, profile, "location"
            )

    @app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "settings", "browse", "matches", "admin", "reports", "ban", "unban"]))
    async def profile_text_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        language = user.get("language")
        step = user.get("profile_setup_step")
        if not step:
            return
        text = (message.text or "").strip()
        fields: dict[str, object] = {}
        if step == "display_name":
            if not text:
                await message.reply_text(t(language, "profile_step_display_name"))
                return
            fields["display_name"] = text[:80]
        elif step == "age":
            try:
                age = int(text)
            except ValueError:
                await message.reply_text(t(language, "profile_invalid_age"))
                return
            if not 1 <= age <= 120:
                await message.reply_text(t(language, "profile_invalid_age"))
                return
            fields["age"] = age
        elif step == "bio":
            if len(text) < 10:
                await message.reply_text(t(language, "profile_invalid_bio"))
                return
            fields["bio"] = text[:500]
        else:
            await prompt_profile_step(ctx, message, message.from_user.id, language, step)
            return

        profile = await ctx.profiles.update_fields(message.from_user.id, fields)
        await continue_profile_setup(ctx, message, message.from_user.id, language, profile, step)
