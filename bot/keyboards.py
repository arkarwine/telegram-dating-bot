from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("English", callback_data="lang:en"),
                InlineKeyboardButton("မြန်မာ", callback_data="lang:my"),
            ]
        ]
    )


def browse_keyboard(target_id: int, can_like: bool) -> InlineKeyboardMarkup:
    first_row = []
    if can_like:
        first_row.append(InlineKeyboardButton("Like", callback_data=f"like:{target_id}"))
    first_row.append(InlineKeyboardButton("Pass", callback_data=f"pass:{target_id}"))
    return InlineKeyboardMarkup(
        [
            first_row,
            [
                InlineKeyboardButton("Report", callback_data=f"report:{target_id}"),
                InlineKeyboardButton("Block", callback_data=f"block:{target_id}"),
            ],
        ]
    )

