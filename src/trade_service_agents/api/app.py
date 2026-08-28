"""FastAPI application factory for the invoice risk assessment platform."""

from dotenv import load_dotenv
from fastapi import FastAPI

from trade_service_agents.api.routes import analysis, extraction, health
from trade_service_agents.core.logging import configure_logging

load_dotenv()
configure_logging()

app = FastAPI(
    title="Enterprise Multi-Agent Invoice Risk Assessment Platform",
    description=(
        "Multimodal AI extraction, deterministic risk scoring, and CrewAI-orchestrated "
        "compliance analysis for proforma invoices."
    ),
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(extraction.router)
app.include_router(analysis.router)
