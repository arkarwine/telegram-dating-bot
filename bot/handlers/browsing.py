from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bot.context import AppContext
from bot.formatters import profile_card
from bot.i18n import t
from bot.keyboards import browse_keyboard
from bot.matching import next_candidate
from bot.models import profile_is_complete


async def send_next_profile(ctx: AppContext, message: Message, user_id: int) -> None:
    user = await ctx.users.get_by_telegram_id(user_id)
    language = user.get("language") if user else ctx.settings.default_language
    viewer_profile = await ctx.profiles.get(user_id)
    candidate = await next_candidate(user_id, ctx.profiles, ctx.actions)
    if not candidate:
        await message.reply_text(t(language, "no_candidates"))
        return
    can_like = profile_is_complete(viewer_profile)
    if not can_like:
        await ctx.users.increment_preview(user_id)
        await message.reply_text(t(language, "anonymous_notice"))
    await message.reply_text(
        profile_card(candidate, anonymous=not can_like),
        reply_markup=browse_keyboard(candidate["user_id"], can_like=can_like),
    )


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("browse") & filters.private)
    async def browse_handler(_: Client, message: Message) -> None:
        await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        await send_next_profile(ctx, message, message.from_user.id)

    @app.on_message(filters.command("matches") & filters.private)
    async def matches_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        matches = await ctx.matches.list_for_user(message.from_user.id)
        if not matches:
            await message.reply_text(t(user.get("language"), "no_candidates"))
            return
        lines = []
        for match in matches:
            other_id = next(uid for uid in match["user_ids"] if uid != message.from_user.id)
            profile = await ctx.profiles.get(other_id)
            other_user = await ctx.users.get_by_telegram_id(other_id)
            name = profile.get("display_name") if profile else str(other_id)
            username = other_user.get("username") if other_user else None
            contact = f"@{username}" if username else t(user.get("language"), "contact_missing")
            lines.append(f"{name}: {contact}")
        await message.reply_text("\n".join(lines))

    @app.on_callback_query(filters.regex(r"^(like|pass|report|block):\d+$"))
    async def browse_callback(client: Client, query: CallbackQuery) -> None:
        action, raw_target = query.data.split(":", 1)
        target_id = int(raw_target)
        user = await ctx.users.upsert_from_telegram(query.from_user, ctx.settings.default_language)
        language = user.get("language")
        viewer_profile = await ctx.profiles.get(query.from_user.id)

        if action == "like" and not profile_is_complete(viewer_profile):
            await query.answer(t(language, "like_requires_profile"), show_alert=True)
            return

        if action == "like":
            await ctx.actions.add(query.from_user.id, target_id, "like")
            if await ctx.actions.has_action(target_id, query.from_user.id, "like"):
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
                    await client.send_message(target_id, t(target_lang, "match", name=viewer_name))
                    if viewer_user.get("username"):
                        await client.send_message(target_id, t(target_lang, "contact", username=viewer_user["username"]))
                    else:
                        await client.send_message(target_id, t(target_lang, "contact_missing"))
            else:
                await query.message.reply_text(t(language, "liked"))
        elif action == "pass":
            await ctx.actions.add(query.from_user.id, target_id, "pass")
            await query.message.reply_text(t(language, "passed"))
        elif action == "report":
            await ctx.actions.add(query.from_user.id, target_id, "report")
            await query.message.reply_text(t(language, "reported"))
        elif action == "block":
            await ctx.actions.add(query.from_user.id, target_id, "block")
            await query.message.reply_text(t(language, "blocked"))

        await query.answer()
        await send_next_profile(ctx, query.message, query.from_user.id)

