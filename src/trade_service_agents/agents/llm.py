"""Gemini LLM configuration shared by every risk-assessment agent."""

from crewai import LLM

from trade_service_agents.core.config import get_settings


def build_gemini_llm() -> LLM:
    """Build the CrewAI LLM used by the risk-assessment agents, backed by Gemini."""
    settings = get_settings()
    return LLM(model=f"gemini/{settings.gemini_agent_model}", api_key=settings.genai_api_key)
