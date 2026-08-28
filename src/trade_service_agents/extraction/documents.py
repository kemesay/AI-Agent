"""Agent 2 — Document Normalization: convert uploaded documents into image pages."""

from io import BytesIO

from fastapi import HTTPException
from pdf2image import convert_from_bytes
from PIL import Image


def load_pages(file_bytes: bytes, content_type: str | None) -> list[Image.Image]:
    """Convert uploaded file bytes into PIL image pages based on content type."""
    if content_type == "application/pdf":
        return convert_from_bytes(file_bytes)
    if content_type and content_type.startswith("image/"):
        return [Image.open(BytesIO(file_bytes))]
    raise HTTPException(status_code=400, detail="Unsupported file type")
