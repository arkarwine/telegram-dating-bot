from pyrogram import Client
from pyrogram.errors import RPCError

from bot.context import AppContext
from bot.i18n import t


async def _display_name(ctx: AppContext, user_id: int) -> str:
    profile = await ctx.profiles.get(user_id) or {}
    user = await ctx.users.get_by_telegram_id(user_id) or {}
    return profile.get("display_name") or user.get("first_name") or "Your match"


async def _notify(
    client: Client,
    ctx: AppContext,
    target_id: int,
    key: str,
    name: str,
) -> None:
    target = await ctx.users.get_by_telegram_id(target_id) or {}
    try:
        await client.send_message(target_id, t(target.get("language"), key, name=name))
    except RPCError:
        pass


async def open_chat_session(
    client: Client,
    ctx: AppContext,
    user_id: int,
    target_id: int,
    target_name: str,
) -> None:
    user = await ctx.users.get_by_telegram_id(user_id) or {}
    current_target = user.get("relay_target_id")
    if current_target == target_id:
        return
    if current_target:
        await close_chat_session(client, ctx, user_id)

    await ctx.users.set_relay_target(user_id, target_id, target_name)
    await _notify(client, ctx, target_id, "chat_session_started_remote", await _display_name(ctx, user_id))


async def close_chat_session(client: Client, ctx: AppContext, user_id: int) -> bool:
    user = await ctx.users.get_by_telegram_id(user_id) or {}
    target_id = user.get("relay_target_id")
    if not target_id:
        return False

    await ctx.users.set_relay_target(user_id, None)
    await _notify(client, ctx, target_id, "chat_session_ended_remote", await _display_name(ctx, user_id))
    return True

