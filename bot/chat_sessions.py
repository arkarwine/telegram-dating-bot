from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.types import ReplyKeyboardRemove

from bot.context import AppContext
from bot.i18n import t
from bot.keyboards import active_chat_keyboard, chat_ended_keyboard


async def display_name(ctx: AppContext, user_id: int) -> str:
    profile = await ctx.profiles.get(user_id) or {}
    user = await ctx.users.get_by_telegram_id(user_id) or {}
    return profile.get("display_name") or user.get("first_name") or "Your match"


async def send_safe(client: Client, user_id: int, text: str, reply_markup=None) -> None:
    try:
        await client.send_message(user_id, text, reply_markup=reply_markup)
    except RPCError:
        pass


async def start_chat_session(
    client: Client,
    ctx: AppContext,
    user_a: int,
    user_b: int,
) -> None:
    name_a = await display_name(ctx, user_a)
    name_b = await display_name(ctx, user_b)
    user_a_doc = await ctx.users.get_by_telegram_id(user_a) or {}
    user_b_doc = await ctx.users.get_by_telegram_id(user_b) or {}

    await ctx.users.set_chat_request(user_b, None)
    await ctx.users.set_relay_target(user_a, user_b, name_b)
    await ctx.users.set_relay_target(user_b, user_a, name_a)

    await send_safe(
        client,
        user_a,
        t(user_a_doc.get("language"), "chat_session_started", name=name_b),
        active_chat_keyboard(name_b),
    )
    await send_safe(
        client,
        user_b,
        t(user_b_doc.get("language"), "chat_session_started", name=name_a),
        active_chat_keyboard(name_a),
    )


async def close_chat_session(
    client: Client, ctx: AppContext, user_id: int, offer_reconnect: bool = True
) -> bool:
    user = await ctx.users.get_by_telegram_id(user_id) or {}
    target_id = user.get("relay_target_id")
    if not target_id:
        return False

    target = await ctx.users.get_by_telegram_id(target_id) or {}
    name = await display_name(ctx, user_id)
    target_name = await display_name(ctx, target_id)

    await ctx.users.set_relay_target(user_id, None)
    await ctx.users.set_relay_target(target_id, None)

    await send_safe(
        client,
        user_id,
        t(user.get("language"), "chat_session_ended", name=target_name),
        ReplyKeyboardRemove(),
    )
    if offer_reconnect:
        await send_safe(
            client,
            user_id,
            t(user.get("language"), "chat_session_after_end"),
            chat_ended_keyboard(target_id),
        )
    await send_safe(
        client,
        target_id,
        t(target.get("language"), "chat_session_ended", name=name),
        ReplyKeyboardRemove(),
    )
    if offer_reconnect:
        await send_safe(
            client,
            target_id,
            t(target.get("language"), "chat_session_after_end"),
            chat_ended_keyboard(user_id),
        )
    return True
