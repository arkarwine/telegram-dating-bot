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


def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💘 Set up profile", callback_data="profile:start")],
            [
                InlineKeyboardButton("👀 Browse", callback_data="browse:start"),
                InlineKeyboardButton("🌐 Language", callback_data="settings:language"),
            ],
        ]
    )


def profile_start_keyboard(complete: bool) -> InlineKeyboardMarkup:
    label = "✨ Edit Profile" if complete else "✨ Set Up Profile"
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data="profile:start")]])


def gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Female", callback_data="profile:gender:female"),
                InlineKeyboardButton("Male", callback_data="profile:gender:male"),
            ],
            [InlineKeyboardButton("Other", callback_data="profile:gender:other")],
        ]
    )


def interested_in_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Women", callback_data="profile:interested_in:female"),
                InlineKeyboardButton("Men", callback_data="profile:interested_in:male"),
            ],
            [
                InlineKeyboardButton("Other", callback_data="profile:interested_in:other"),
                InlineKeyboardButton("Anyone", callback_data="profile:interested_in:any"),
            ],
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
