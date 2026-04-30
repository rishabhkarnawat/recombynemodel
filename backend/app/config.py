"""Configuration module for Recombyne backend."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    twitter_bearer_token: str | None = Field(default=None, alias="TWITTER_BEARER_TOKEN")
    reddit_client_id: str | None = Field(default=None, alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str | None = Field(default=None, alias="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = Field(
        default="RecombyneDev/0.1", alias="REDDIT_USER_AGENT"
    )
    huggingface_api_key: str | None = Field(default=None, alias="HUGGINGFACE_API_KEY")
    database_url: str = Field(
        default="postgresql+asyncpg://recombyne:recombyne@localhost:5432/recombyne",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    secret_key: str = Field(default="dev-secret", alias="SECRET_KEY")
    api_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"], alias="API_CORS_ORIGINS"
    )

    def get_available_sources(self) -> list[Literal["twitter", "reddit"]]:
        """Return the sources with enough credentials to operate."""

        sources: list[Literal["twitter", "reddit"]] = []
        if self.twitter_bearer_token:
            sources.append("twitter")
        if self.reddit_client_id and self.reddit_client_secret:
            sources.append("reddit")
        return sources


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache settings."""

    return Settings()


settings = get_settings()
