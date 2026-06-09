from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_id: int = Field(alias="API_ID")
    api_hash: str = Field(alias="API_HASH")
    bot_token: str = Field(alias="BOT_TOKEN")
    mongodb_uri: str = Field(alias="MONGODB_URI")
    database_name: str = Field(default="telegram_dating_bot", alias="DATABASE_NAME")
    admin_ids: set[int] = Field(default_factory=set, alias="ADMIN_IDS")
    default_language: str = Field(default="en", alias="DEFAULT_LANGUAGE")
    geocoder_base_url: str = Field(
        default="https://nominatim.openstreetmap.org", alias="GEOCODER_BASE_URL"
    )
    owner_link: str | None = Field(
        default=None, validation_alias=AliasChoices("OWNER_LINK", "OWNER_URL")
    )
    support_link: str | None = Field(
        default=None, validation_alias=AliasChoices("SUPPORT_LINK", "SUPPORT_URL", "GROUP_LINK", "GROUP_URL")
    )
    updates_link: str | None = Field(
        default=None, validation_alias=AliasChoices("UPDATES_LINK", "UPDATES_URL")
    )
    start_image: str | None = Field(
        default=None, validation_alias=AliasChoices("START_IMAGE", "START_IMAGE_URL")
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: object) -> set[int]:
        if value is None or value == "":
            return set()
        if isinstance(value, set):
            return value
        if isinstance(value, list):
            return {int(item) for item in value}
        return {int(item.strip()) for item in str(value).split(",") if item.strip()}

    @field_validator("default_language")
    @classmethod
    def validate_default_language(cls, value: str) -> str:
        return value if value in {"en", "my"} else "en"

    @field_validator("owner_link", "support_link", "updates_link", "start_image", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
