from __future__ import annotations

from typing import Any

from bot.models import display_place, profile_is_complete


def profile_card(profile: dict[str, Any], anonymous: bool = False) -> str:
    name = profile.get("display_name") or "Someone"
    age = profile.get("age") or "?"
    gender = profile.get("gender") or "?"
    bio = profile.get("bio") or ""
    place = display_place(profile.get("location"))
    prefix = "👀 Preview" if anonymous else "💌 Profile"
    return f"{prefix}: {name}, {age}\n\n🧭 {place}\n✨ {gender}\n\n“{bio}”"


def completion_status(profile: dict[str, Any] | None) -> str:
    if profile_is_complete(profile):
        return "complete"
    return "incomplete"
