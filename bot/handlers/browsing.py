from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, InputMediaPhoto, Message, ReplyKeyboardRemove

from bot.chat_sessions import close_chat_session, display_name, send_safe, start_chat_session
from bot.context import AppContext
from bot.formatters import profile_card
from bot.i18n import t
from bot.keyboards import (
    admin_report_keyboard,
    browse_keyboard,
    home_keyboard,
    incoming_heart_keyboard,
    chat_request_keyboard,
    match_actions_keyboard,
    matches_keyboard,
    no_candidates_keyboard,
    unmatch_confirm_keyboard,
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
                await message.reply_text(text, reply_markup=no_candidates_keyboard(), quote=False)
                await message.delete()
            else:
                await message.edit_text(text, reply_markup=no_candidates_keyboard())
        else:
            await message.reply_text(text, reply_markup=no_candidates_keyboard())
        return
    await ctx.actions.add(user_id, candidate["user_id"], "seen")
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
    async def stats_text(user_id: int, language: str | None) -> str:
        profile = await ctx.profiles.get(user_id)
        received = await ctx.actions.counts_for_target(user_id)
        sent = await ctx.actions.counts_for_actor(user_id)
        matches = await ctx.matches.list_for_user(user_id)
        user = await ctx.users.get_by_telegram_id(user_id) or {}
        return t(
            language,
            "stats",
            completeness=t(language, "stats_complete") if profile_is_complete(profile) else t(language, "stats_incomplete"),
            hearts_received=received["hearts"],
            passes_received=received["passes"],
            hearts_sent=sent["hearts"],
            passes_sent=sent["passes"],
            reports_sent=sent["reports"],
            blocks_sent=sent["blocks"],
            matches=len(matches),
            previews=user.get("preview_count", 0),
        )

    @app.on_message((filters.command("browse") | filters.regex(r"^👀 Browse$")) & filters.private)
    async def browse_handler(_: Client, message: Message) -> None:
        await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await send_next_profile(ctx, message, message.from_user.id)

    @app.on_callback_query(filters.regex(r"^browse:start$"))
    async def browse_start_callback(_: Client, query: CallbackQuery) -> None:
        await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        await send_next_profile(ctx, query.message, query.from_user.id, edit=True)

    @app.on_callback_query(filters.regex(r"^browse:review_seen$"))
    async def browse_review_seen_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await ctx.actions.clear_for_actor(query.from_user.id, ["seen"])
        await query.answer(t(user.get("language"), "browse_cache_cleared"), show_alert=True)
        await send_next_profile(ctx, query.message, query.from_user.id, edit=True)

    @app.on_message((filters.command("stats") | filters.regex(r"^📊 Stats$")) & filters.private)
    async def stats_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await message.reply_text(
            await stats_text(message.from_user.id, user.get("language")),
            reply_markup=home_keyboard(),
            quote=False,
        )

    @app.on_callback_query(filters.regex(r"^stats:show$"))
    async def stats_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        await query.message.edit_text(
            await stats_text(query.from_user.id, user.get("language")),
            reply_markup=home_keyboard(),
        )

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

    @app.on_message((filters.command("matches") | filters.regex(r"^💬 Matches$")) & filters.private)
    async def matches_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        text, markup = await matches_view(message.from_user.id, user.get("language"))
        await message.reply_text(
            text,
            reply_markup=markup,
            quote=False,
        )

    @app.on_callback_query(filters.regex(r"^matches:show$"))
    async def matches_callback(client: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        if user.get("relay_target_id"):
            await close_chat_session(client, ctx, query.from_user.id)
        await query.answer()
        text, markup = await matches_view(query.from_user.id, user.get("language"))
        await query.message.edit_text(
            text,
            reply_markup=markup,
        )

    @app.on_callback_query(filters.regex(r"^match:message:\d+$"))
    async def match_message_callback(client: Client, query: CallbackQuery) -> None:
        target_id = int(query.data.rsplit(":", 1)[1])
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        if not await ctx.matches.get_between(query.from_user.id, target_id):
            await query.answer(t(user.get("language"), "not_a_match"), show_alert=True)
            return
        target_user = await ctx.users.get_by_telegram_id(target_id) or {}
        if user.get("relay_target_id"):
            key = "chat_already_active" if user.get("relay_target_id") == target_id else "chat_request_busy_self"
            await query.answer(t(user.get("language"), key), show_alert=True)
            return
        if target_user.get("relay_target_id"):
            await query.answer(t(user.get("language"), "chat_request_busy"), show_alert=True)
            return
        if target_user.get("chat_request_from_id"):
            await query.answer(t(user.get("language"), "chat_request_pending"), show_alert=True)
            return
        requester_name = await display_name(ctx, query.from_user.id)
        await ctx.users.set_chat_request(target_id, query.from_user.id, requester_name)
        await query.answer(t(user.get("language"), "chat_request_sent"), show_alert=True)
        await send_safe(
            client,
            target_id,
            t(target_user.get("language"), "chat_request_received", name=requester_name),
            chat_request_keyboard(query.from_user.id),
        )

    @app.on_callback_query(filters.regex(r"^match:request_accept:\d+$"))
    async def chat_request_accept(client: Client, query: CallbackQuery) -> None:
        requester_id = int(query.data.rsplit(":", 1)[1])
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        if user.get("chat_request_from_id") != requester_id:
            await query.answer(t(user.get("language"), "chat_request_expired"), show_alert=True)
            return
        if not await ctx.matches.get_between(query.from_user.id, requester_id):
            await ctx.users.set_chat_request(query.from_user.id, None)
            await query.answer(t(user.get("language"), "not_a_match"), show_alert=True)
            return
        requester = await ctx.users.get_by_telegram_id(requester_id) or {}
        if user.get("relay_target_id") or requester.get("relay_target_id"):
            await ctx.users.set_chat_request(query.from_user.id, None)
            await query.answer(t(user.get("language"), "chat_request_busy"), show_alert=True)
            return
        await query.answer()
        await query.message.edit_text(t(user.get("language"), "chat_request_accepted"))
        await start_chat_session(client, ctx, requester_id, query.from_user.id)

    @app.on_callback_query(filters.regex(r"^match:request_reject:\d+$"))
    async def chat_request_reject(client: Client, query: CallbackQuery) -> None:
        requester_id = int(query.data.rsplit(":", 1)[1])
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        if user.get("chat_request_from_id") != requester_id:
            await query.answer(t(user.get("language"), "chat_request_expired"), show_alert=True)
            return
        await ctx.users.set_chat_request(query.from_user.id, None)
        await query.answer(t(user.get("language"), "chat_request_rejected_local"))
        await query.message.edit_text(t(user.get("language"), "chat_request_rejected_local"))
        requester = await ctx.users.get_by_telegram_id(requester_id) or {}
        await send_safe(
            client,
            requester_id,
            t(
                requester.get("language"),
                "chat_request_rejected_remote",
                name=await display_name(ctx, query.from_user.id),
            ),
        )

    @app.on_callback_query(filters.regex(r"^match:unmatch_confirm:\d+$"))
    async def unmatch_confirm_callback(_: Client, query: CallbackQuery) -> None:
        target_id = int(query.data.rsplit(":", 1)[1])
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer()
        await query.message.edit_text(
            t(user.get("language"), "unmatch_confirm"),
            reply_markup=unmatch_confirm_keyboard(target_id),
        )

    @app.on_callback_query(filters.regex(r"^match:unmatch:\d+$"))
    async def unmatch_callback(client: Client, query: CallbackQuery) -> None:
        target_id = int(query.data.rsplit(":", 1)[1])
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        if not await ctx.matches.get_between(query.from_user.id, target_id):
            await query.answer(t(user.get("language"), "not_a_match"), show_alert=True)
            return
        if user.get("relay_target_id") == target_id:
            await close_chat_session(client, ctx, query.from_user.id, offer_reconnect=False)
        await ctx.matches.delete_between(query.from_user.id, target_id)
        await ctx.users.set_chat_request(query.from_user.id, None)
        await ctx.users.set_chat_request(target_id, None)
        target = await ctx.users.get_by_telegram_id(target_id) or {}
        await query.answer()
        await query.message.edit_text(t(user.get("language"), "unmatched"), reply_markup=home_keyboard())
        await send_safe(
            client,
            target_id,
            t(target.get("language"), "unmatched_remote", name=await display_name(ctx, query.from_user.id)),
            home_keyboard(),
        )

    @app.on_callback_query(filters.regex(r"^match:view:\d+$"))
    async def match_view_callback(_: Client, query: CallbackQuery) -> None:
        target_id = int(query.data.rsplit(":", 1)[1])
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        if not await ctx.matches.get_between(query.from_user.id, target_id):
            await query.answer(t(user.get("language"), "not_a_match"), show_alert=True)
            return
        target_user = await ctx.users.get_by_telegram_id(target_id) or {}
        target_profile = await ctx.profiles.get(target_id) or {}
        name = target_profile.get("display_name") or "Your match"
        direct_username = (
            target_user.get("username")
            if user.get("username") and target_user.get("username")
            else None
        )
        await query.answer()
        await query.message.edit_text(
            t(
                user.get("language"),
                "match_details",
                name=name,
                direct=t(user.get("language"), "direct_available")
                if direct_username
                else t(user.get("language"), "direct_not_available"),
            ),
            reply_markup=match_actions_keyboard(target_id, direct_username),
        )

    @app.on_callback_query(filters.regex(r"^match:direct_unavailable:\d+$"))
    async def direct_unavailable_callback(_: Client, query: CallbackQuery) -> None:
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        await query.answer(t(user.get("language"), "direct_unavailable"), show_alert=True)

    @app.on_message(filters.command(["start", "help", "settings", "browse", "matches", "stats", "owner", "support", "updates", "profile", "admin", "reports", "ban", "unban"]) & filters.private, group=-2)
    async def leave_chat_on_command(client: Client, message: Message) -> None:
        user = await ctx.users.get_by_telegram_id(message.from_user.id)
        if user and user.get("relay_target_id"):
            await close_chat_session(client, ctx, message.from_user.id)

    @app.on_message(filters.regex(r"^🏠 Home$") & filters.private, group=-2)
    async def leave_chat_on_home_button(client: Client, message: Message) -> None:
        user = await ctx.users.get_by_telegram_id(message.from_user.id)
        if user and user.get("relay_target_id"):
            await close_chat_session(client, ctx, message.from_user.id)

    @app.on_message(filters.private & filters.regex(r"^(💘 Matches|✖️ Exit chat)$"), group=-2)
    async def chat_navigation(client: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await close_chat_session(client, ctx, message.from_user.id)
        if message.text == "💘 Matches":
            text, markup = await matches_view(message.from_user.id, user.get("language"))
            await message.reply_text(text, reply_markup=markup, quote=False)
        message.stop_propagation()

    @app.on_message(filters.private & ~filters.command(["start", "help", "settings", "browse", "matches", "stats", "owner", "support", "updates", "profile", "admin", "reports", "ban", "unban"]) & ~filters.regex(r"^(💘 Set up profile|👀 Browse|💬 Matches|📊 Stats|🌐 Language|🏠 Home)$"), group=-1)
    async def relay_message_handler(client: Client, message: Message) -> None:
        user = await ctx.users.get_by_telegram_id(message.from_user.id)
        target_id = user.get("relay_target_id") if user else None
        if not target_id:
            return
        if not await ctx.matches.get_between(message.from_user.id, target_id):
            await close_chat_session(client, ctx, message.from_user.id, offer_reconnect=False)
            return
        if await ctx.actions.has_action(message.from_user.id, target_id, "block") or await ctx.actions.has_action(
            target_id, message.from_user.id, "block"
        ):
            await close_chat_session(client, ctx, message.from_user.id, offer_reconnect=False)
            await message.reply_text(
                t(user.get("language"), "chat_blocked"),
                reply_markup=ReplyKeyboardRemove(),
                quote=False,
            )
            message.stop_propagation()
            return
        profile = await ctx.profiles.get(message.from_user.id) or {}
        sender_name = profile.get("display_name") or message.from_user.first_name or "Your match"
        target_user = await ctx.users.get_by_telegram_id(target_id) or {}
        try:
            if target_user.get("relay_target_id") != message.from_user.id:
                await client.send_message(
                    target_id,
                    t(target_user.get("language"), "chat_incoming", name=sender_name),
                    reply_markup=match_actions_keyboard(
                        message.from_user.id,
                        message.from_user.username
                        if message.from_user.username and target_user.get("username")
                        else None,
                    ),
                )
            await client.copy_message(
                target_id,
                message.chat.id,
                message.id,
            )
        except RPCError:
            await message.reply_text(t(user.get("language"), "relay_failed"), quote=False)
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
                if target_user.get("username") and viewer_user.get("username"):
                    await query.message.reply_text(
                        t(language, "contact", username=target_user["username"]),
                        reply_markup=match_actions_keyboard(
                            target_id,
                            target_user["username"] if viewer_user.get("username") else None,
                        ),
                        quote=False,
                    )
                else:
                    await query.message.reply_text(
                        t(language, "contact_via_bot"),
                        reply_markup=match_actions_keyboard(target_id),
                        quote=False,
                    )
                if target_user:
                    target_lang = target_user.get("language")
                    viewer_name = viewer_profile.get("display_name") if viewer_profile else "Someone"
                    try:
                        await client.send_message(target_id, t(target_lang, "match", name=viewer_name))
                        if viewer_user.get("username") and target_user.get("username"):
                            await client.send_message(
                                target_id,
                                t(target_lang, "contact", username=viewer_user["username"]),
                                reply_markup=match_actions_keyboard(
                                    query.from_user.id,
                                    viewer_user["username"] if target_user.get("username") else None,
                                ),
                            )
                        else:
                            await client.send_message(
                                target_id,
                                t(target_lang, "contact_via_bot"),
                                reply_markup=match_actions_keyboard(query.from_user.id),
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
                    photo = target_profile.get("photo_file_id") or target_profile.get("photo_url")
                    if photo:
                        await client.send_photo(
                            admin_id,
                            photo,
                            caption=owner_text,
                            reply_markup=admin_report_keyboard(str(report["_id"]), target_id),
                        )
                    else:
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
