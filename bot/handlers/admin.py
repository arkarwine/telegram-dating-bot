from pyrogram import Client, filters
from pyrogram.types import Message

from bot.context import AppContext
from bot.i18n import t


def _is_admin(ctx: AppContext, user_id: int) -> bool:
    return user_id in ctx.settings.admin_ids


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("admin") & filters.private)
    async def admin_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        if not _is_admin(ctx, message.from_user.id):
            await message.reply_text(t(user.get("language"), "not_admin"))
            return
        await message.reply_text(t(user.get("language"), "admin_help"))

    @app.on_message(filters.command("reports") & filters.private)
    async def reports_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        if not _is_admin(ctx, message.from_user.id):
            await message.reply_text(t(user.get("language"), "not_admin"))
            return
        reports = await ctx.actions.latest_reports()
        if not reports:
            await message.reply_text(t(user.get("language"), "no_reports"))
            return
        lines = [
            f"Reporter {report['actor_id']} -> User {report['target_id']} at {report.get('created_at')}"
            for report in reports
        ]
        await message.reply_text("\n".join(lines))

    @app.on_message(filters.command("ban") & filters.private)
    async def ban_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        if not _is_admin(ctx, message.from_user.id):
            await message.reply_text(t(user.get("language"), "not_admin"))
            return
        if len(message.command) < 2:
            await message.reply_text("/ban <telegram_id>")
            return
        target_id = int(message.command[1])
        await ctx.users.set_status(target_id, "banned")
        await ctx.profiles.mark_banned(target_id, True)
        await ctx.admin_events.add(message.from_user.id, "ban", target_id)
        await message.reply_text(t(user.get("language"), "banned"))

    @app.on_message(filters.command("unban") & filters.private)
    async def unban_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        if not _is_admin(ctx, message.from_user.id):
            await message.reply_text(t(user.get("language"), "not_admin"))
            return
        if len(message.command) < 2:
            await message.reply_text("/unban <telegram_id>")
            return
        target_id = int(message.command[1])
        await ctx.users.set_status(target_id, "active")
        await ctx.profiles.mark_banned(target_id, False)
        await ctx.admin_events.add(message.from_user.id, "unban", target_id)
        await message.reply_text(t(user.get("language"), "unbanned"))

