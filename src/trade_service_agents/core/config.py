"""Application settings sourced from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The customs indicative-price workbook ships as package data (public customs-commission
# reference pricing, not customer data) so the under/over-invoicing check works out of the
# box after a plain `git clone` / `docker compose up` — no server-side file to place.
_PACKAGE_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_CUSTOMS_PRICE_LIST_PATH = str(_PACKAGE_DIR / "data" / "customs_indicative_prices.xlsx")


class Settings(BaseSettings):
    genai_api_key: str = ""
    gemini_extraction_model: str = "gemini-3.6-flash"
    gemini_agent_model: str = "gemini-3.6-flash"
    # Caps the risk-assessment crew's LLM calls per minute. Google's Gemini API free tier
    # allows only 5 requests/minute per model, and the six risk-dimension agents would
    # otherwise call it concurrently and get rate-limited. Raise this on a paid tier.
    gemini_max_rpm: int = 4

    # Path to the customs indicative-price reference workbook (.xlsx), used by the
    # under/over-invoicing price check (scoring/price_deviation.py). Defaults to the
    # bundled copy; override only to point at an updated/replacement price list without
    # rebuilding the image. The check silently no-ops if the configured file can't be read.
    customs_price_list_path: str = _DEFAULT_CUSTOMS_PRICE_LIST_PATH

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
