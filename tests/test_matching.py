import pytest

from bot.matching import gender_compatible, next_candidate


class FakeProfiles:
    def __init__(self, viewer, candidates):
        self.viewer = viewer
        self.candidates = candidates

    async def get(self, user_id):
        if user_id == self.viewer["user_id"]:
            return self.viewer
        return next((candidate for candidate in self.candidates if candidate["user_id"] == user_id), None)

    async def find_candidates(self, query, limit=20):
        excluded = set(query["user_id"].get("$nin", []))
        return [candidate for candidate in self.candidates if candidate["user_id"] not in excluded]


class FakeActions:
    def __init__(self, excluded=None):
        self.excluded = excluded or []

    async def target_ids_for_actor(self, actor_id, types):
        return self.excluded


def complete_profile(user_id, gender="female", interested_in="male", age=24, township="Kamayut"):
    return {
        "user_id": user_id,
        "photo_file_id": "file",
        "bio": "Hello",
        "age": age,
        "gender": gender,
        "interested_in": interested_in,
        "location": {
            "country_code": "mm",
            "region": "Yangon Region",
            "city": "Yangon",
            "township": township,
        },
        "complete": True,
        "visible": True,
    }


def test_gender_compatible() -> None:
    viewer = complete_profile(1, gender="female", interested_in="male")
    candidate = complete_profile(2, gender="male", interested_in="female")

    assert gender_compatible(viewer, candidate)


@pytest.mark.asyncio
async def test_next_candidate_prefers_same_township() -> None:
    viewer = complete_profile(1, township="Kamayut")
    far = complete_profile(2, gender="male", interested_in="female", township="Bahan")
    near = complete_profile(3, gender="male", interested_in="female", township="Kamayut")

    candidate = await next_candidate(1, FakeProfiles(viewer, [far, near]), FakeActions())

    assert candidate["user_id"] == 3


@pytest.mark.asyncio
async def test_next_candidate_excludes_prior_actions() -> None:
    viewer = complete_profile(1)
    skipped = complete_profile(2, gender="male", interested_in="female")
    available = complete_profile(3, gender="male", interested_in="female")

    candidate = await next_candidate(1, FakeProfiles(viewer, [skipped, available]), FakeActions([2]))

    assert candidate["user_id"] == 3

