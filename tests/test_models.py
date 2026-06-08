from bot.models import ResolvedLocation, display_place, profile_is_complete


def test_profile_complete_requires_location_and_basics() -> None:
    assert profile_is_complete(
        {
            "photo_file_id": "file",
            "bio": "Hello",
            "age": 17,
            "gender": "female",
            "interested_in": "male",
            "location": {"country_code": "mm"},
        }
    )


def test_myanmar_location_detection() -> None:
    location = ResolvedLocation(
        latitude=16.8,
        longitude=96.1,
        country_code="mm",
        country="Myanmar",
        region="Yangon Region",
        city="Yangon",
        town=None,
        township="Kamayut",
        display_name="Kamayut, Yangon, Myanmar",
    )

    assert location.is_myanmar
    assert display_place(location.to_profile_location()) == "Kamayut, Yangon, Yangon Region"

