from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot.profile_setup import OPTIONAL_PROFILE_FIELDS, PROFILE_STEP_LABELS


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
                InlineKeyboardButton("🇲🇲 မြန်မာ", callback_data="lang:my"),
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
                InlineKeyboardButton("💬 Matches", callback_data="matches:show"),
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data="stats:show"),
                InlineKeyboardButton("🌐 Language", callback_data="settings:language"),
            ],
        ]
    )


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home:start")]])


def no_candidates_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔄 Review seen profiles", callback_data="browse:review_seen")],
            [InlineKeyboardButton("🏠 Home", callback_data="home:start")],
        ]
    )


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
    if step in OPTIONAL_PROFILE_FIELDS:
        rows.append(
            [InlineKeyboardButton("Remove this field", callback_data=f"profile:clear:{step}")]
        )
    if step != "display_name":
        rows.append([InlineKeyboardButton("⬅️ Back", callback_data="profile:back")])
    rows.append([InlineKeyboardButton("🗑 Delete profile", callback_data="profile:delete_confirm")])
    return InlineKeyboardMarkup(rows)


def profile_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🪪 Basics", callback_data="profile:edit_group:basics"),
                InlineKeyboardButton("✍️ About me", callback_data="profile:edit_group:about"),
            ],
            [
                InlineKeyboardButton("🎯 Lifestyle", callback_data="profile:edit_group:lifestyle"),
                InlineKeyboardButton("🔗 Socials", callback_data="profile:edit_group:social"),
            ],
            [InlineKeyboardButton("⬅️ Back to profile", callback_data="profile:dashboard")],
            [InlineKeyboardButton("🗑 Delete profile", callback_data="profile:delete_confirm")],
        ]
    )


def profile_edit_group_keyboard(group: str) -> InlineKeyboardMarkup:
    groups = {
        "basics": ["display_name", "age", "gender", "interested_in", "photo", "location"],
        "about": ["bio", "occupation", "education", "languages", "height", "zodiac"],
        "lifestyle": [
            "hobbies",
            "sports",
            "games",
            "music",
            "favorite_food",
            "weekend_style",
            "relationship_goal",
        ],
        "social": ["socials"],
    }
    rows = [
        [InlineKeyboardButton(f"✏️ {PROFILE_STEP_LABELS[field]}", callback_data=f"profile:edit:{field}")]
        for field in groups[group]
    ]
    rows.append([InlineKeyboardButton("⬅️ Edit menu", callback_data="profile:edit_menu")])
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="home:start")])
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


def matches_keyboard(matches: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"💘 {name}", callback_data=f"match:view:{user_id}")]
        for user_id, name in matches[:20]
    ]
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="home:start")])
    return InlineKeyboardMarkup(rows)


def match_actions_keyboard(user_id: int, username: str | None = None) -> InlineKeyboardMarkup:
    direct_url = f"https://t.me/{username}" if username else None
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💬 Request private chat", callback_data=f"match:message:{user_id}")],
            [
                InlineKeyboardButton("↗️ Direct message", url=direct_url)
                if direct_url
                else InlineKeyboardButton(
                    "↗️ Direct message", callback_data=f"match:direct_unavailable:{user_id}"
                )
            ],
            [InlineKeyboardButton("💔 Unmatch", callback_data=f"match:unmatch_confirm:{user_id}")],
            [InlineKeyboardButton("💘 My matches", callback_data="matches:show")],
            [InlineKeyboardButton("🏠 Home", callback_data="home:start")],
        ]
    )


def active_chat_keyboard(name: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("💘 Matches"), KeyboardButton("✖️ Exit chat")]],
        resize_keyboard=True,
        is_persistent=True,
    )


def chat_request_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"match:request_accept:{user_id}"),
                InlineKeyboardButton("Not now", callback_data=f"match:request_reject:{user_id}"),
            ],
            [InlineKeyboardButton("💔 Unmatch", callback_data=f"match:unmatch_confirm:{user_id}")],
        ]
    )


def chat_ended_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💬 Request another chat", callback_data=f"match:message:{user_id}")],
            [InlineKeyboardButton("💘 My matches", callback_data="matches:show")],
        ]
    )


def unmatch_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Yes, unmatch", callback_data=f"match:unmatch:{user_id}")],
            [InlineKeyboardButton("Keep match", callback_data=f"match:view:{user_id}")],
        ]
    )
