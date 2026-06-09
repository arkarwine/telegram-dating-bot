from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, InputMediaPhoto, Message

from bot.context import AppContext
from bot.formatters import profile_card
from bot.i18n import t
from bot.keyboards import admin_report_keyboard, browse_keyboard, home_keyboard, incoming_heart_keyboard
from bot.matching import next_candidate
from bot.models import profile_is_complete


async def send_next_profile(
    ctx: AppContext, message: Message, user_id: int, edit: bool = False
) -> None:
    user = await ctx.users.get_by_telegram_id(user_id)
    language = user.get("language") if user else ctx.settings.default_language
    viewer_profile = await ctx.profiles.get(user_id)
    candidate = await next_candidate(user_id, ctx.profiles, ctx.actions)
    if not candidate:
        text = t(language, "no_candidates")
        if edit:
            if getattr(message, "photo", None):
                await message.reply_text(text, reply_markup=home_keyboard())
                await message.delete()
            else:
                await message.edit_text(text, reply_markup=home_keyboard())
        else:
            await message.reply_text(text, reply_markup=home_keyboard())
        return
    can_like = profile_is_complete(viewer_profile)
    counts = await ctx.actions.counts_for_target(candidate["user_id"])
    text = profile_card(candidate, anonymous=not can_like, counts=counts)
    if not can_like:
        await ctx.users.increment_preview(user_id)
        text = f"{t(language, 'anonymous_notice')}\n\n{text}"
    markup = browse_keyboard(candidate["user_id"], can_like=can_like)
    photo = candidate.get("photo_file_id") or candidate.get("photo_url")
    if edit and getattr(message, "photo", None) and photo:
        await message.edit_media(InputMediaPhoto(photo, caption=text), reply_markup=markup)
    elif edit and getattr(message, "photo", None):
        await message.reply_text(text, reply_markup=markup)
        await message.delete()
    elif edit and photo:
        await message.reply_photo(photo, caption=text, reply_markup=markup)
        await message.delete()
    elif edit:
        await message.edit_text(text, reply_markup=markup)
    elif photo:
        await message.reply_photo(photo, caption=text, reply_markup=markup)
    else:
        await message.reply_text(text, reply_markup=markup)


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("browse") & filters.private)
    async def browse_handler(_: Client, message: Message) -> None:
        await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await send_next_profile(ctx, message, message.from_user.id)

    @app.on_callback_query(filters.regex(r"^browse:start$"))
    async def browse_start_callback(_: Client, query: CallbackQuery) -> None:
        await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        await send_next_profile(ctx, query.message, query.from_user.id, edit=True)

    async def matches_text(user_id: int, language: str | None) -> str:
        matches = await ctx.matches.list_for_user(user_id)
        if not matches:
            return t(language, "no_matches")
        lines = []
        for match in matches:
            other_id = next(uid for uid in match["user_ids"] if uid != user_id)
            profile = await ctx.profiles.get(other_id)
            other_user = await ctx.users.get_by_telegram_id(other_id)
            name = profile.get("display_name") if profile else str(other_id)
            username = other_user.get("username") if other_user else None
            contact = f"@{username}" if username else t(language, "contact_missing")
            lines.append(f"{name}: {contact}")
        return f"{t(language, 'matches_title')}\n\n" + "\n".join(lines)

    @app.on_message(filters.command("matches") & filters.private)
    async def matches_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text(
            await matches_text(message.from_user.id, user.get("language")),
            reply_markup=home_keyboard(),
        )

    @app.on_callback_query(filters.regex(r"^matches:show$"))
    async def matches_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        await query.message.edit_text(
            await matches_text(query.from_user.id, user.get("language")),
            reply_markup=home_keyboard(),
        )

    async def send_hearted_profile(client: Client, target_id: int, actor_id: int) -> None:
        actor_profile = await ctx.profiles.get(actor_id)
        if not actor_profile:
            return
        target_user = await ctx.users.get_by_telegram_id(target_id) or {}
        language = target_user.get("language")
        counts = await ctx.actions.counts_for_target(actor_id)
        text = f"{t(language, 'incoming_heart')}\n\n{profile_card(actor_profile, counts=counts)}"
        try:
            photo = actor_profile.get("photo_file_id") or actor_profile.get("photo_url")
            if photo:
                await client.send_photo(
                    target_id,
                    photo,
                    caption=text,
                    reply_markup=incoming_heart_keyboard(actor_id),
                )
            else:
                await client.send_message(
                    target_id, text, reply_markup=incoming_heart_keyboard(actor_id)
                )
        except RPCError:
            # Seeded profiles and users who blocked the bot are not reachable chats.
            return

    @app.on_callback_query(filters.regex(r"^(heart|like|pass|report|block):\d+$"))
    async def browse_callback(client: Client, query: CallbackQuery) -> None:
        action, raw_target = query.data.split(":", 1)
        if action == "like":
            action = "heart"
        target_id = int(raw_target)
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        language = user.get("language")
        viewer_profile = await ctx.profiles.get(query.from_user.id)
        matched = False

        if action == "heart" and not profile_is_complete(viewer_profile):
            await query.answer(t(language, "like_requires_profile"), show_alert=True)
            return

        if action == "heart":
            await ctx.actions.add(query.from_user.id, target_id, "heart")
            if await ctx.actions.has_any_action(target_id, query.from_user.id, ["heart", "like"]):
                matched = True
                await ctx.matches.create(query.from_user.id, target_id)
                target_profile = await ctx.profiles.get(target_id) or {}
                target_user = await ctx.users.get_by_telegram_id(target_id) or {}
                viewer_user = await ctx.users.get_by_telegram_id(query.from_user.id) or {}
                target_name = target_profile.get("display_name") or "Someone"
                await query.message.reply_text(t(language, "match", name=target_name))
                if target_user.get("username"):
                    await query.message.reply_text(t(language, "contact", username=target_user["username"]))
                else:
                    await query.message.reply_text(t(language, "contact_missing"))
                if target_user:
                    target_lang = target_user.get("language")
                    viewer_name = viewer_profile.get("display_name") if viewer_profile else "Someone"
                    try:
                        await client.send_message(target_id, t(target_lang, "match", name=viewer_name))
                        if viewer_user.get("username"):
                            await client.send_message(target_id, t(target_lang, "contact", username=viewer_user["username"]))
                        else:
                            await client.send_message(target_id, t(target_lang, "contact_missing"))
                    except RPCError:
                        pass
            else:
                await query.answer(t(language, "liked"))
                await send_hearted_profile(client, target_id, query.from_user.id)
        elif action == "pass":
            await ctx.actions.add(query.from_user.id, target_id, "pass")
            await query.answer(t(language, "passed"))
        elif action == "report":
            report = await ctx.actions.add(query.from_user.id, target_id, "report")
            await query.answer(t(language, "reported"), show_alert=True)
            target_profile = await ctx.profiles.get(target_id) or {}
            owner_text = (
                f"{t(None, 'owner_report_received')}\n\n"
                f"Reporter: {query.from_user.id}\nReported user: {target_id}\n\n"
                f"{profile_card(target_profile)}"
            )
            for admin_id in ctx.settings.admin_ids:
                try:
                    await client.send_message(
                        admin_id,
                        owner_text,
                        reply_markup=admin_report_keyboard(str(report["_id"]), target_id),
                    )
                except RPCError:
                    pass
        elif action == "block":
            await ctx.actions.add(query.from_user.id, target_id, "block")
            await query.answer(t(language, "blocked"), show_alert=True)

        if matched:
            await query.answer()
        await send_next_profile(ctx, query.message, query.from_user.id, edit=True)
