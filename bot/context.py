from __future__ import annotations

from dataclasses import dataclass

from bot.config import Settings
from bot.location import LocationResolver
from bot.repositories import ActionsRepo, AdminEventsRepo, MatchesRepo, ProfilesRepo, UsersRepo


@dataclass
class AppContext:
    settings: Settings
    users: UsersRepo
    profiles: ProfilesRepo
    actions: ActionsRepo
    matches: MatchesRepo
    admin_events: AdminEventsRepo
    locations: LocationResolver

