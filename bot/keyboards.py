from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.profile_setup import PROFILE_STEP_LABELS, PROFILE_SETUP_STEPS


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("English", callback_data="lang:en"),
                InlineKeyboardButton("မြန်မာ", callback_data="lang:my"),
            ],
            [InlineKeyboardButton("🏠 Home", callback_data="home:start")],
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


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home:start")]])


def profile_start_keyboard(complete: bool) -> InlineKeyboardMarkup:
    if complete:
        return InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✏️ Edit one field", callback_data="profile:edit_menu")],
                [InlineKeyboardButton("🗑 Delete profile", callback_data="profile:delete_confirm")],
                [InlineKeyboardButton("🏠 Home", callback_data="home:start")],
            ]
        )
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✨ Continue setup", callback_data="profile:start")],
            [InlineKeyboardButton("🏠 Home", callback_data="home:start")],
        ]
    )


def profile_step_keyboard(step: str) -> InlineKeyboardMarkup | None:
    rows: list[list[InlineKeyboardButton]] = []
    if step != "display_name":
        rows.append([InlineKeyboardButton("⬅️ Back", callback_data="profile:back")])
    rows.append([InlineKeyboardButton("🗑 Delete profile", callback_data="profile:delete_confirm")])
    return InlineKeyboardMarkup(rows)


def profile_edit_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"✏️ {PROFILE_STEP_LABELS[step]}", callback_data=f"profile:edit:{step}")]
        for step in PROFILE_SETUP_STEPS
    ]
    rows.append([InlineKeyboardButton("⬅️ Back to profile", callback_data="profile:dashboard")])
    rows.append([InlineKeyboardButton("🗑 Delete profile", callback_data="profile:delete_confirm")])
    return InlineKeyboardMarkup(rows)


def delete_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Yes, delete it", callback_data="profile:delete")],
            [InlineKeyboardButton("Keep my profile", callback_data="profile:edit_menu")],
            [InlineKeyboardButton("🏠 Home", callback_data="home:start")],
        ]
    )


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


def location_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📍 Share my location", request_location=True)],
            [KeyboardButton("⬅️ Back"), KeyboardButton("🗑 Delete profile")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def browse_keyboard(target_id: int, can_like: bool) -> InlineKeyboardMarkup:
    first_row = []
    if can_like:
        first_row.append(InlineKeyboardButton("❤️ Heart", callback_data=f"heart:{target_id}"))
    first_row.append(InlineKeyboardButton("Pass", callback_data=f"pass:{target_id}"))
    return InlineKeyboardMarkup(
        [
            first_row,
            [
                InlineKeyboardButton("Report", callback_data=f"report:{target_id}"),
                InlineKeyboardButton("Block", callback_data=f"block:{target_id}"),
            ],
            [InlineKeyboardButton("🏠 Home", callback_data="home:start")],
        ]
    )


def incoming_heart_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❤️ Heart back", callback_data=f"heart:{user_id}"),
                InlineKeyboardButton("Pass", callback_data=f"pass:{user_id}"),
            ],
            [
                InlineKeyboardButton("Report", callback_data=f"report:{user_id}"),
                InlineKeyboardButton("Block", callback_data=f"block:{user_id}"),
            ],
            [InlineKeyboardButton("🏠 Home", callback_data="home:start")],
        ]
    )


def admin_report_keyboard(report_id: str, target_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🛑 Ban reported user", callback_data=f"admin:report_ban:{target_id}"),
                InlineKeyboardButton("Next ➡️", callback_data=f"admin:report_next:{report_id}"),
            ],
            [InlineKeyboardButton("🏠 Home", callback_data="home:start")],
        ]
    )
