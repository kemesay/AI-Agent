"""Orchestrates the full risk assessment: invoice data in, decision-ready response out."""

from typing import Any, Dict

from trade_service_agents.agents.crew import RiskAssessmentCrew
from trade_service_agents.models.invoice import ProformaInvoice
from trade_service_agents.scoring.aggregation import invoice_anomaly_index

_HIGH_RISK_FINDING_THRESHOLD = 20


async def analyze_proforma(invoice: ProformaInvoice) -> Dict[str, Any]:
    """Run the risk-assessment crew for a single proforma invoice and shape the response."""
    invoice_json = invoice.model_dump_json(by_alias=True)
    result = RiskAssessmentCrew().crew().kickoff(inputs={"invoice_json": invoice_json})

    category_outputs = result.tasks_output[:-2]
    aggregation = result.tasks_output[-2].pydantic
    summary_text = result.tasks_output[-1].raw.strip()

    insights = [finding for output in category_outputs for finding in output.pydantic.findings]
    recommendations = [
        finding
        for output in category_outputs
        if output.pydantic.score >= _HIGH_RISK_FINDING_THRESHOLD
        for finding in output.pydantic.findings
    ]

    return {
        "summary": summary_text,
        "risk": aggregation.model_dump(),
        "insights": insights,
        "recommendations": recommendations,
        "invoiceAnomalyIndex": invoice_anomaly_index(aggregation.categoryBreakdown),
    }
