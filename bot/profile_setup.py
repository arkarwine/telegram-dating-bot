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

PROFILE_STEP_LABELS = {
    "display_name": "Display name",
    "age": "Age",
    "gender": "Gender",
    "interested_in": "Looking for",
    "bio": "Bio",
    "photo": "Photo",
    "location": "Location",
}


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


def previous_step(step: str | None) -> str | None:
    if step not in PROFILE_SETUP_STEPS:
        return None
    index = PROFILE_SETUP_STEPS.index(step)
    return PROFILE_SETUP_STEPS[index - 1] if index > 0 else None
