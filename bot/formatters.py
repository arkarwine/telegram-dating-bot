from __future__ import annotations

from typing import Any

from bot.models import display_place, profile_is_complete


def profile_card(
    profile: dict[str, Any],
    anonymous: bool = False,
    counts: dict[str, int] | None = None,
) -> str:
    name = profile.get("display_name") or "Someone"
    age = profile.get("age") or "?"
    gender = profile.get("gender") or "?"
    bio = profile.get("bio") or ""
    place = display_place(profile.get("location"))
    prefix = "👀 Preview" if anonymous else "💌 Profile"
    stats = ""
    if counts:
        stats = f"\n\n❤️ {counts.get('hearts', 0)} hearts · 🚪 {counts.get('passes', 0)} passes"
    extras = []
    extra_labels = {
        "occupation": "💼",
        "hobbies": "🎨",
        "games": "🎮",
        "sports": "🏃",
        "zodiac": "♈",
        "height": "📏",
        "relationship_goal": "💞",
        "languages": "🗣",
        "music": "🎵",
        "favorite_food": "🍜",
        "weekend_style": "🌤",
        "socials": "🔗",
        "education": "🎓",
    }
    for field, icon in extra_labels.items():
        if profile.get(field):
            extras.append(f"{icon} {profile[field]}")
    extra_text = f"\n\n" + "\n".join(extras) if extras else ""
    return f"{prefix}: {name}, {age}\n\n🧭 {place}\n✨ {gender}\n\n“{bio}”{extra_text}{stats}"


def completion_status(profile: dict[str, Any] | None) -> str:
    if profile_is_complete(profile):
        return "complete"
    return "incomplete"
