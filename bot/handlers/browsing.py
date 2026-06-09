from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, InputMediaPhoto, Message

from bot.context import AppContext
from bot.formatters import profile_card
from bot.i18n import t
from bot.keyboards import (
    admin_report_keyboard,
    browse_keyboard,
    cancel_relay_keyboard,
    home_keyboard,
    incoming_heart_keyboard,
    match_relay_keyboard,
    matches_keyboard,
)
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
                await message.reply_text(text, reply_markup=home_keyboard(), quote=False)
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
        await message.reply_text(text, reply_markup=markup, quote=False)
        await message.delete()
    elif edit and photo:
        await message.reply_photo(photo, caption=text, reply_markup=markup, quote=False)
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

    async def matches_view(user_id: int, language: str | None) -> tuple[str, object]:
        matches = await ctx.matches.list_for_user(user_id)
        if not matches:
            return t(language, "no_matches"), home_keyboard()
        buttons = []
        for match in matches:
            other_id = next(uid for uid in match["user_ids"] if uid != user_id)
            profile = await ctx.profiles.get(other_id)
            name = profile.get("display_name") if profile else str(other_id)
            buttons.append((other_id, name))
        return t(language, "matches_intro"), matches_keyboard(buttons)

    @app.on_message(filters.command("matches") & filters.private)
    async def matches_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        text, markup = await matches_view(message.from_user.id, user.get("language"))
        await message.reply_text(
            text,
            reply_markup=markup,
            quote=False,
        )

    @app.on_callback_query(filters.regex(r"^matches:show$"))
    async def matches_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        text, markup = await matches_view(query.from_user.id, user.get("language"))
        await query.message.edit_text(
            text,
            reply_markup=markup,
        )

    @app.on_callback_query(filters.regex(r"^match:message:\d+$"))
    async def match_message_callback(_: Client, query: CallbackQuery) -> None:
        target_id = int(query.data.rsplit(":", 1)[1])
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        if not await ctx.matches.get_between(query.from_user.id, target_id):
            await query.answer(t(user.get("language"), "not_a_match"), show_alert=True)
            return
        await ctx.users.set_relay_target(query.from_user.id, target_id)
        await query.answer()
        text = t(user.get("language"), "relay_prompt")
        if getattr(query.message, "photo", None):
            await query.message.reply_text(text, reply_markup=cancel_relay_keyboard(), quote=False)
        else:
            await query.message.edit_text(text, reply_markup=cancel_relay_keyboard())

    @app.on_callback_query(filters.regex(r"^match:message_cancel$"))
    async def match_message_cancel(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await ctx.users.set_relay_target(query.from_user.id, None)
        await query.answer()
        text, markup = await matches_view(query.from_user.id, user.get("language"))
        await query.message.edit_text(text, reply_markup=markup)

    @app.on_message(filters.private & ~filters.command(["start", "help", "settings", "browse", "matches", "profile", "admin", "reports", "ban", "unban"]), group=-1)
    async def relay_message_handler(client: Client, message: Message) -> None:
        user = await ctx.users.get_by_telegram_id(message.from_user.id)
        target_id = user.get("relay_target_id") if user else None
        if not target_id:
            return
        if not await ctx.matches.get_between(message.from_user.id, target_id):
            await ctx.users.set_relay_target(message.from_user.id, None)
            return
        profile = await ctx.profiles.get(message.from_user.id) or {}
        sender_name = profile.get("display_name") or message.from_user.first_name or "Your match"
        target_user = await ctx.users.get_by_telegram_id(target_id) or {}
        try:
            await client.send_message(
                target_id,
                t(target_user.get("language"), "relay_received", name=sender_name),
                reply_markup=match_relay_keyboard(message.from_user.id),
            )
            await client.copy_message(target_id, message.chat.id, message.id)
            await message.reply_text(t(user.get("language"), "relay_sent"), quote=False)
        except RPCError:
            await message.reply_text(t(user.get("language"), "relay_failed"), quote=False)
        finally:
            await ctx.users.set_relay_target(message.from_user.id, None)
        message.stop_propagation()

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
                await query.message.reply_text(t(language, "match", name=target_name), quote=False)
                if target_user.get("username"):
                    await query.message.reply_text(
                        t(language, "contact", username=target_user["username"]),
                        reply_markup=match_relay_keyboard(target_id),
                        quote=False,
                    )
                else:
                    await query.message.reply_text(
                        t(language, "contact_via_bot"),
                        reply_markup=match_relay_keyboard(target_id),
                        quote=False,
                    )
                if target_user:
                    target_lang = target_user.get("language")
                    viewer_name = viewer_profile.get("display_name") if viewer_profile else "Someone"
                    try:
                        await client.send_message(target_id, t(target_lang, "match", name=viewer_name))
                        if viewer_user.get("username"):
                            await client.send_message(
                                target_id,
                                t(target_lang, "contact", username=viewer_user["username"]),
                                reply_markup=match_relay_keyboard(query.from_user.id),
                            )
                        else:
                            await client.send_message(
                                target_id,
                                t(target_lang, "contact_via_bot"),
                                reply_markup=match_relay_keyboard(query.from_user.id),
                            )
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
