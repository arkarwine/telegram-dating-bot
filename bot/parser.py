from __future__ import annotations

from bot.constants import GENDERS, INTERESTS


def parse_profile_text(text: str) -> dict[str, object]:
    fields: dict[str, object] = {}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if not value:
            continue
        if key in {"name", "display_name"}:
            fields["display_name"] = value[:80]
        elif key == "age":
            try:
                age = int(value)
            except ValueError:
                continue
            if 1 <= age <= 120:
                fields["age"] = age
        elif key == "gender" and value.lower() in GENDERS:
            fields["gender"] = value.lower()
        elif key in {"interested", "interested_in"} and value.lower() in INTERESTS:
            fields["interested_in"] = value.lower()
        elif key == "bio":
            fields["bio"] = value[:500]
    return fields

