"""Full risk-assessment endpoint, backed by the CrewAI risk-assessment crew."""

from fastapi import APIRouter

from trade_service_agents.models.invoice import ProformaInvoice
from trade_service_agents.services.proforma_analysis_service import analyze_proforma

router = APIRouter()


@router.post("/analyze_proforma")
async def analyze_proforma_endpoint(payload: ProformaInvoice):
    return await analyze_proforma(payload)
