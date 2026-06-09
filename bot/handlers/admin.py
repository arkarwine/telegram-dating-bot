from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from bot.context import AppContext
from bot.formatters import profile_card
from bot.i18n import t
from bot.keyboards import admin_report_keyboard, home_keyboard


def _is_admin(ctx: AppContext, user_id: int) -> bool:
    return user_id in ctx.settings.admin_ids


async def _send_report_card(
    message: Message,
    text: str,
    profile: dict,
    *,
    reply_markup,
    edit: bool,
) -> None:
    photo = profile.get("photo_file_id") or profile.get("photo_url")
    if edit and not photo and not getattr(message, "photo", None):
        await message.edit_text(text, reply_markup=reply_markup)
        return
    if photo:
        await message.reply_photo(photo, caption=text, reply_markup=reply_markup, quote=False)
    else:
        await message.reply_text(text, reply_markup=reply_markup, quote=False)
    if edit:
        await message.delete()


async def show_report(ctx: AppContext, message: Message, language: str | None, before_id: str | None = None) -> None:
    report = await ctx.actions.next_report(before_id)
    if not report:
        if getattr(message, "photo", None):
            await message.reply_text(t(language, "no_reports"), reply_markup=home_keyboard(), quote=False)
            await message.delete()
        else:
            await message.edit_text(t(language, "no_reports"), reply_markup=home_keyboard())
        return
    profile = await ctx.profiles.get(report["target_id"]) or {}
    text = (
        f"{t(language, 'report_review')}\n\n"
        f"Reporter: {report['actor_id']}\nReported user: {report['target_id']}\n"
        f"Reported at: {report.get('created_at')}\n\n{profile_card(profile)}"
    )
    markup = admin_report_keyboard(str(report["_id"]), int(report["target_id"]))
    await _send_report_card(message, text, profile, reply_markup=markup, edit=True)


def register(app: Client, ctx: AppContext) -> None:
    @app.on_message(filters.command("admin") & filters.private)
    async def admin_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        if not _is_admin(ctx, message.from_user.id):
            await message.reply_text(t(user.get("language"), "not_admin"))
            return
        await message.reply_text(t(user.get("language"), "admin_help"), reply_markup=home_keyboard())

    @app.on_message(filters.command("reports") & filters.private)
    async def reports_handler(_: Client, message: Message) -> None:
        user = await ctx.users.upsert_from_telegram(message.from_user, ctx.settings.default_language)
        if not _is_admin(ctx, message.from_user.id):
            await message.reply_text(t(user.get("language"), "not_admin"))
            return
        report = await ctx.actions.next_report()
        if not report:
            await message.reply_text(t(user.get("language"), "no_reports"), reply_markup=home_keyboard())
            return
        profile = await ctx.profiles.get(report["target_id"]) or {}
        text = (
            f"{t(user.get('language'), 'report_review')}\n\n"
            f"Reporter: {report['actor_id']}\nReported user: {report['target_id']}\n"
            f"Reported at: {report.get('created_at')}\n\n{profile_card(profile)}"
        )
        markup = admin_report_keyboard(str(report["_id"]), int(report["target_id"]))
        await _send_report_card(message, text, profile, reply_markup=markup, edit=False)

    @app.on_callback_query(filters.regex(r"^admin:report_next:[a-f0-9]{24}$"))
    async def report_next_handler(_: Client, query: CallbackQuery) -> None:
        if not _is_admin(ctx, query.from_user.id):
            await query.answer(t(None, "not_admin"), show_alert=True)
            return
        await query.answer()
        await show_report(ctx, query.message, None, query.data.rsplit(":", 1)[1])

    @app.on_callback_query(filters.regex(r"^admin:report_ban:\d+$"))
    async def report_ban_handler(_: Client, query: CallbackQuery) -> None:
        if not _is_admin(ctx, query.from_user.id):
            await query.answer(t(None, "not_admin"), show_alert=True)
            return
        target_id = int(query.data.rsplit(":", 1)[1])
        await ctx.users.set_status(target_id, "banned")
        await ctx.profiles.mark_banned(target_id, True)
        await ctx.admin_events.add(query.from_user.id, "ban", target_id)
        await query.answer(t(None, "banned"), show_alert=True)

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
