"""Shared FastAPI dependencies."""

from google import genai

from trade_service_agents.extraction.vision import get_client

__all__ = ["get_client", "genai"]
