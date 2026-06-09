from __future__ import annotations

from typing import Any

from bot.models import profile_is_complete
from bot.repositories import ActionsRepo, ProfilesRepo


def gender_compatible(viewer: dict[str, Any], candidate: dict[str, Any]) -> bool:
    viewer_interest = viewer.get("interested_in", "any")
    candidate_interest = candidate.get("interested_in", "any")
    viewer_gender = viewer.get("gender")
    candidate_gender = candidate.get("gender")
    viewer_likes_candidate = viewer_interest == "any" or viewer_interest == candidate_gender
    candidate_likes_viewer = candidate_interest == "any" or candidate_interest == viewer_gender
    return bool(viewer_likes_candidate and candidate_likes_viewer)


def age_in_range(viewer: dict[str, Any], candidate: dict[str, Any], tolerance: int = 5) -> bool:
    viewer_age = int(viewer.get("age") or 0)
    candidate_age = int(candidate.get("age") or 0)
    if not viewer_age or not candidate_age:
        return True
    return abs(viewer_age - candidate_age) <= tolerance


def same_location_level(viewer: dict[str, Any], candidate: dict[str, Any], field: str) -> bool:
    viewer_location = viewer.get("location") or {}
    candidate_location = candidate.get("location") or {}
    return bool(viewer_location.get(field) and viewer_location.get(field) == candidate_location.get(field))


async def next_candidate(
    viewer_id: int,
    profiles: ProfilesRepo,
    actions: ActionsRepo,
) -> dict[str, Any] | None:
    viewer = await profiles.get(viewer_id)
    excluded = await actions.target_ids_for_actor(viewer_id, ["heart", "like", "pass", "block", "report"])
    base_query = {
        "user_id": {"$ne": viewer_id, "$nin": excluded},
        "complete": True,
        "visible": True,
        "banned": {"$ne": True},
        "location.country_code": "mm",
    }
    candidates = await profiles.find_candidates(base_query, limit=50)
    if not viewer or not profile_is_complete(viewer):
        return candidates[0] if candidates else None

    compatible = [candidate for candidate in candidates if gender_compatible(viewer, candidate)]
    for field in ("township", "town", "city", "region"):
        local = [
            candidate
            for candidate in compatible
            if same_location_level(viewer, candidate, field) and age_in_range(viewer, candidate)
        ]
        if local:
            return local[0]

    relaxed_location = [candidate for candidate in compatible if age_in_range(viewer, candidate)]
    if relaxed_location:
        return relaxed_location[0]

    relaxed_age = [candidate for candidate in compatible if age_in_range(viewer, candidate, tolerance=10)]
    return relaxed_age[0] if relaxed_age else None
