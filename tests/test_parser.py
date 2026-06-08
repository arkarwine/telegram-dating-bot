from bot.parser import parse_profile_text


def test_parse_profile_text() -> None:
    fields = parse_profile_text(
        "Name: Aye\nAge: 24\nGender: female\nInterested: male\nBio: Coffee and books"
    )

    assert fields == {
        "display_name": "Aye",
        "age": 24,
        "gender": "female",
        "interested_in": "male",
        "bio": "Coffee and books",
    }


def test_parse_profile_text_does_not_enforce_18_plus() -> None:
    fields = parse_profile_text("Age: 16\nGender: female")

    assert fields["age"] == 16

