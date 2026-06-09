from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from bot.context import AppContext
from bot.formatters import profile_card
from bot.i18n import t
from bot.keyboards import (
    delete_profile_keyboard,
    profile_edit_keyboard,
    profile_edit_group_keyboard,
    profile_step_keyboard,
    gender_keyboard,
    interested_in_keyboard,
    location_request_keyboard,
    profile_start_keyboard,
)
from bot.models import display_place, profile_is_complete, public_profile_summary
from bot.profile_setup import next_missing_step, next_step_after, previous_step
from bot.handlers.start import send_start_menu


def profile_review_text(language: str | None, profile: dict | None) -> str:
    return t(language, "profile_collected_so_far", summary=public_profile_summary(profile))


async def finish_profile_edit(
    ctx: AppContext,
    message: Message,
    user_id: int,
    language: str | None,
    field: str,
    edit_message: bool = False,
) -> None:
    user = await ctx.users.get_by_telegram_id(user_id) or {}
    group = user.get("profile_edit_group") or "basics"
    await ctx.users.set_profile_setup_step(user_id, None)
    await ctx.users.set_profile_edit_mode(user_id, False)
    text = t(language, "profile_field_updated", field=field.replace("_", " ").title())
    if field == "location":
        cleanup = await message.reply_text(text, reply_markup=ReplyKeyboardRemove(), quote=False)
        await cleanup.delete()
        await message.reply_text(
            t(language, f"profile_edit_group_{group}"),
            reply_markup=profile_edit_group_keyboard(group),
            quote=False,
        )
        return
    if edit_message:
        await message.edit_text(
            f"{text}\n\n{t(language, f'profile_edit_group_{group}')}",
            reply_markup=profile_edit_group_keyboard(group),
        )
    else:
        await message.reply_text(
            f"{text}\n\n{t(language, f'profile_edit_group_{group}')}",
            reply_markup=profile_edit_group_keyboard(group),
            quote=False,
        )


async def replace_with_text(message: Message, text: str, reply_markup=None) -> None:
    if getattr(message, "photo", None):
        await message.reply_text(text, reply_markup=reply_markup, quote=False)
        await message.delete()
    else:
        await message.edit_text(text, reply_markup=reply_markup)


async def show_profile_preview(
    message: Message,
    language: str | None,
    profile: dict,
) -> None:
    caption = f"{t(language, 'profile_preview')}\n\n{profile_card(profile)}"
    reply_markup = profile_start_keyboard(complete=True)
    photo = profile.get("photo_file_id") or profile.get("photo_url")
    if photo:
        await message.reply_photo(photo, caption=caption, reply_markup=reply_markup, quote=False)
    else:
        await message.reply_text(caption, reply_markup=reply_markup, quote=False)


async def return_home(
    ctx: AppContext, message: Message, language: str | None, remove_keyboard: bool = False
) -> None:
    if remove_keyboard:
        cleanup = await message.reply_text(
            t(language, "profile_return_home"), reply_markup=ReplyKeyboardRemove()
        )
        await cleanup.delete()
        await send_start_menu(message, ctx, language)
    else:
        await send_start_menu(message, ctx, language)


async def prompt_profile_step(
    ctx: AppContext,
    message: Message,
    user_id: int,
    language: str | None,
    step: str | None,
    edit: bool = False,
    review: str | None = None,
) -> None:
    if not step:
        await ctx.users.set_profile_setup_step(user_id, None)
        await ctx.users.set_profile_edit_mode(user_id, False)
        profile = await ctx.profiles.get(user_id)
        text = f"{t(language, 'profile_complete')}\n\n{profile_review_text(language, profile)}"
        if edit:
            await message.edit_text(text, reply_markup=profile_start_keyboard(complete=True))
        else:
            await message.reply_text(text, reply_markup=profile_start_keyboard(complete=True))
        await return_home(ctx, message, language)
        return

    await ctx.users.set_profile_setup_step(user_id, step)
    if step == "gender":
        text = t(language, "profile_step_gender")
        markup = gender_keyboard()
    elif step == "interested_in":
        text = t(language, "profile_step_interested_in")
        markup = interested_in_keyboard()
    elif step == "location":
        text = t(language, "profile_step_location")
        markup = location_request_keyboard()
    else:
        text = t(language, f"profile_step_{step}")
        markup = profile_step_keyboard(step)

    if step in {"gender", "interested_in"}:
        step_nav = profile_step_keyboard(step)
        if step_nav:
            markup.inline_keyboard.extend(step_nav.inline_keyboard)

    if review:
        text = f"{review}\n\n{text}"

    if edit:
        if step == "location":
            await message.reply_text(text, reply_markup=markup)
        else:
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
        await ctx.users.set_profile_edit_mode(user_id, False)
        text = f"{t(language, 'profile_saved_review')}\n\n{profile_review_text(language, profile)}"
        if edit:
            await message.edit_text(text, reply_markup=profile_start_keyboard(complete=True))
        else:
            await message.reply_text(text, reply_markup=profile_start_keyboard(complete=True))
        await return_home(ctx, message, language)
        return
    review = f"{t(language, 'profile_saved_review')}\n\n{profile_review_text(language, profile)}"
    await prompt_profile_step(
        ctx,
        message,
        user_id,
        language,
        next_step_after(profile, completed_step),
        edit=edit,
        review=review,
    )


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("profile") & filters.private)
    async def profile_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        profile = await ctx.profiles.get(message.from_user.id)
        language = user.get("language")
        if profile_is_complete(profile):
            await show_profile_preview(message, language, profile)
        else:
            await message.reply_text(
                f"{t(language, 'profile_help')}\n\n{profile_review_text(language, profile)}",
                reply_markup=profile_start_keyboard(complete=False),
            )

    @app.on_callback_query(filters.regex(r"^profile:start$"))
    async def profile_start_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        profile = await ctx.profiles.get(query.from_user.id)
        language = user.get("language")
        await query.answer()
        if profile_is_complete(profile):
            await ctx.users.set_profile_edit_mode(query.from_user.id, False)
            await show_profile_preview(query.message, language, profile)
            await query.message.delete()
            return
        await prompt_profile_step(
            ctx,
            query.message,
            query.from_user.id,
            language,
            next_missing_step(profile) or "display_name",
            edit=True,
        )
        await ctx.users.set_profile_edit_mode(query.from_user.id, False)

    @app.on_callback_query(filters.regex(r"^profile:dashboard$"))
    async def profile_dashboard_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        profile = await ctx.profiles.get(query.from_user.id)
        language = user.get("language")
        await ctx.users.set_profile_edit_mode(query.from_user.id, False)
        await ctx.users.set_profile_setup_step(query.from_user.id, None)
        await query.answer()
        if profile_is_complete(profile):
            await show_profile_preview(query.message, language, profile)
            await query.message.delete()
        else:
            await query.message.edit_text(
                f"{t(language, 'profile_help')}\n\n{profile_review_text(language, profile)}",
                reply_markup=profile_start_keyboard(False),
            )

    @app.on_callback_query(filters.regex(r"^profile:edit_menu$"))
    async def profile_edit_menu_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        profile = await ctx.profiles.get(query.from_user.id)
        language = user.get("language")
        await query.answer()
        await ctx.users.set_profile_setup_step(query.from_user.id, None)
        await ctx.users.set_profile_edit_mode(query.from_user.id, False)
        await ctx.users.set_profile_edit_group(query.from_user.id, None)
        await replace_with_text(
            query.message,
            f"{t(language, 'profile_edit_menu')}\n\n{profile_review_text(language, profile)}",
            reply_markup=profile_edit_keyboard(),
        )

    @app.on_callback_query(filters.regex(r"^profile:edit_group:(basics|about|lifestyle|social)$"))
    async def profile_edit_group_callback(_: Client, query: CallbackQuery) -> None:
        group = query.data.rsplit(":", 1)[1]
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await ctx.users.set_profile_edit_group(query.from_user.id, group)
        await query.answer()
        await query.message.edit_text(
            t(user.get("language"), f"profile_edit_group_{group}"),
            reply_markup=profile_edit_group_keyboard(group),
        )

    @app.on_callback_query(filters.regex(r"^profile:edit:(display_name|age|gender|interested_in|bio|photo|location|socials|games|zodiac|height|hobbies|occupation|sports|education|languages|relationship_goal|music|favorite_food|weekend_style)$"))
    async def profile_edit_field_callback(_: Client, query: CallbackQuery) -> None:
        step = query.data.split(":")[-1]
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        profile = await ctx.profiles.get(query.from_user.id)
        language = user.get("language")
        await ctx.users.set_profile_edit_mode(query.from_user.id, True)
        await query.answer()
        await prompt_profile_step(
            ctx,
            query.message,
            query.from_user.id,
            language,
            step,
            edit=True,
            review=profile_review_text(language, profile),
        )

    @app.on_callback_query(filters.regex(r"^profile:clear:(socials|games|zodiac|height|hobbies|occupation|sports|education|languages|relationship_goal|music|favorite_food|weekend_style)$"))
    async def profile_clear_field_callback(_: Client, query: CallbackQuery) -> None:
        field = query.data.rsplit(":", 1)[1]
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await ctx.profiles.update_fields(query.from_user.id, {field: None})
        await query.answer()
        await finish_profile_edit(
            ctx,
            query.message,
            query.from_user.id,
            user.get("language"),
            field,
            edit_message=True,
        )

    @app.on_callback_query(filters.regex(r"^profile:back$"))
    async def profile_back_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        language = user.get("language")
        await query.answer()
        if user.get("profile_edit_mode"):
            await ctx.users.set_profile_setup_step(query.from_user.id, None)
            group = user.get("profile_edit_group") or "basics"
            await query.message.edit_text(
                t(language, f"profile_edit_group_{group}"),
                reply_markup=profile_edit_group_keyboard(group),
            )
            return
        previous = previous_step(user.get("profile_setup_step"))
        if not previous:
            await query.message.edit_text(t(language, "profile_help"), reply_markup=profile_start_keyboard(False))
            return
        await prompt_profile_step(
            ctx, query.message, query.from_user.id, language, previous, edit=True
        )

    @app.on_callback_query(filters.regex(r"^profile:delete_confirm$"))
    async def profile_delete_confirm_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        await replace_with_text(
            query.message,
            t(user.get("language"), "profile_delete_confirm"),
            reply_markup=delete_profile_keyboard(),
        )

    @app.on_callback_query(filters.regex(r"^profile:delete$"))
    async def profile_delete_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await ctx.profiles.delete(query.from_user.id)
        await ctx.actions.delete_for_user(query.from_user.id)
        await ctx.matches.delete_for_user(query.from_user.id)
        await ctx.users.set_profile_setup_step(query.from_user.id, None)
        await ctx.users.set_profile_edit_mode(query.from_user.id, False)
        await query.answer()
        await replace_with_text(
            query.message,
            t(user.get("language"), "profile_deleted"),
            reply_markup=profile_start_keyboard(False),
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
        if user.get("profile_edit_mode"):
            await finish_profile_edit(
                ctx, query.message, query.from_user.id, language, field, edit_message=True
            )
            return
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
        if user.get("profile_edit_mode"):
            await finish_profile_edit(ctx, message, message.from_user.id, language, "photo")
            return
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
        if user.get("profile_edit_mode"):
            await status_message.delete()
            await finish_profile_edit(ctx, message, message.from_user.id, language, "location")
            return
        if profile_is_complete(profile):
            await ctx.users.set_profile_setup_step(message.from_user.id, None)
            await ctx.users.set_profile_edit_mode(message.from_user.id, False)
            await status_message.edit_text(
                f"{t(language, 'profile_complete_with_location', place=place)}\n\n"
                f"{profile_review_text(language, profile)}",
            )
            await return_home(ctx, message, language, remove_keyboard=True)
        else:
            await status_message.edit_text(t(language, "location_saved", place=place))
            await continue_profile_setup(
                ctx, message, message.from_user.id, language, profile, "location"
            )

    @app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "settings", "browse", "matches", "stats", "owner", "support", "updates", "profile", "admin", "reports", "ban", "unban"]))
    async def profile_text_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        language = user.get("language")
        step = user.get("profile_setup_step")
        if not step:
            return
        text = (message.text or "").strip()
        if text == "⬅️ Back":
            previous = previous_step(step)
            if previous:
                await prompt_profile_step(ctx, message, message.from_user.id, language, previous)
            return
        if text == "🗑 Delete profile":
            await message.reply_text(
                t(language, "profile_delete_confirm"),
                reply_markup=delete_profile_keyboard(),
            )
            return
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
        elif step in {
            "socials",
            "games",
            "zodiac",
            "height",
            "hobbies",
            "occupation",
            "sports",
            "education",
            "languages",
            "relationship_goal",
            "music",
            "favorite_food",
            "weekend_style",
        }:
            fields[step] = text[:300]
        else:
            await prompt_profile_step(ctx, message, message.from_user.id, language, step)
            return

        profile = await ctx.profiles.update_fields(message.from_user.id, fields)
        if user.get("profile_edit_mode"):
            await finish_profile_edit(ctx, message, message.from_user.id, language, step)
            return
        await continue_profile_setup(ctx, message, message.from_user.id, language, profile, step)
