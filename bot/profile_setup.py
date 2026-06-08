from __future__ import annotations

from typing import Any

from bot.models import profile_is_complete

PROFILE_SETUP_STEPS = [
    "display_name",
    "age",
    "gender",
    "interested_in",
    "bio",
    "photo",
    "location",
]


def next_missing_step(profile: dict[str, Any] | None) -> str | None:
    profile = profile or {}
    if not profile.get("display_name"):
        return "display_name"
    if not profile.get("age"):
        return "age"
    if not profile.get("gender"):
        return "gender"
    if not profile.get("interested_in"):
        return "interested_in"
    if not profile.get("bio"):
        return "bio"
    if not profile.get("photo_file_id"):
        return "photo"
    if not profile.get("location"):
        return "location"
    return None


def next_step_after(profile: dict[str, Any] | None, completed_step: str) -> str | None:
    if profile_is_complete(profile):
        return None
    missing = next_missing_step(profile)
    if missing:
        return missing
    try:
        index = PROFILE_SETUP_STEPS.index(completed_step)
    except ValueError:
        return next_missing_step(profile)
    return PROFILE_SETUP_STEPS[index + 1] if index + 1 < len(PROFILE_SETUP_STEPS) else None

