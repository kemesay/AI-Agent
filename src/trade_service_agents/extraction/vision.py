"""Agent 3 — Multimodal Data Extraction: vision-based structured extraction via Gemini."""

import json
from typing import Callable, Dict, List

from fastapi import HTTPException, UploadFile
from google import genai
from PIL import Image

from trade_service_agents.core.config import get_settings
from trade_service_agents.core.logging import get_logger
from trade_service_agents.extraction.documents import load_pages

LOGGER = get_logger(__name__)


def get_client() -> genai.Client:
    """Build a GenAI client using the API key from application settings."""
    settings = get_settings()
    if not settings.genai_api_key:
        raise RuntimeError("Environment variable GENAI_API_KEY is required.")
    return genai.Client(api_key=settings.genai_api_key)


def parse_json_response(response_text: str) -> Dict:
    """Strip code fences and parse model output into JSON; return a helpful error on failure."""
    clean_text = response_text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        LOGGER.warning("Failed to parse JSON from model response")
        return {"error": "Failed to parse JSON", "raw": response_text}


def run_extraction(
    file: UploadFile,
    prompt_builder: Callable[[Image.Image], List],
    client: genai.Client,
) -> Dict:
    """Read an uploaded PDF/image, normalize it to pages, and extract structured JSON."""
    file_bytes = file.file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    pages = load_pages(file_bytes, file.content_type)
    first_page = pages[0]

    settings = get_settings()
    response = client.models.generate_content(
        model=settings.gemini_extraction_model, contents=prompt_builder(first_page)
    )
    return parse_json_response(response.text)
