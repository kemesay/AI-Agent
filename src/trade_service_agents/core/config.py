"""Application settings sourced from environment variables / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    genai_api_key: str = ""
    gemini_extraction_model: str = "gemini-3.6-flash"
    gemini_agent_model: str = "gemini-3.6-flash"
    # Caps the risk-assessment crew's LLM calls per minute. Google's Gemini API free tier
    # allows only 5 requests/minute per model, and the six risk-dimension agents would
    # otherwise call it concurrently and get rate-limited. Raise this on a paid tier.
    gemini_max_rpm: int = 4

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
