"""Orchestrates the full risk assessment: invoice data in, decision-ready response out."""

from typing import Any

from trade_service_agents.agents.crew import RiskAssessmentCrew
from trade_service_agents.models.invoice import ProformaInvoice
from trade_service_agents.scoring.aggregation import invoice_anomaly_index

_HIGH_RISK_FINDING_THRESHOLD = 20
_UNVALIDATED_CATEGORY_FINDING = (
    "This category's automated score could not be validated and requires manual review."
)
_AGGREGATION_UNVALIDATED_SUMMARY = (
    "Automated risk aggregation could not be validated for this invoice; manual compliance "
    "review is required."
)


async def analyze_proforma(invoice: ProformaInvoice) -> dict[str, Any]:
    """Run the risk-assessment crew for a single proforma invoice and shape the response.

    An agent occasionally fails to produce a tool-grounded, schema-valid answer even after a
    guardrail retry — a real failure mode of LLM tool use, not a bug to paper over. Rather than
    crash or silently drop that category, an unvalidated result is surfaced as an explicit
    finding so a human reviewer sees it, keeping the platform's audit trail honest.
    """
    invoice_json = invoice.model_dump_json(by_alias=True)
    result = await RiskAssessmentCrew().crew().kickoff_async(inputs={"invoice_json": invoice_json})

    category_outputs = result.tasks_output[:-2]
    aggregation_output = result.tasks_output[-2]
    summary_text = result.tasks_output[-1].raw.strip()

    insights: list[str] = []
    recommendations: list[str] = []
    for output in category_outputs:
        if output.pydantic is None:
            insights.append(_UNVALIDATED_CATEGORY_FINDING)
            recommendations.append(_UNVALIDATED_CATEGORY_FINDING)
            continue
        insights.extend(output.pydantic.findings)
        if output.pydantic.score >= _HIGH_RISK_FINDING_THRESHOLD:
            recommendations.extend(output.pydantic.findings)

    if aggregation_output.pydantic is None:
        return {
            "summary": _AGGREGATION_UNVALIDATED_SUMMARY,
            "risk": {
                "finalRiskScore": None,
                "riskCategory": "Unknown",
                "decision": "Manual review required",
                "categoryBreakdown": {},
            },
            "insights": insights,
            "recommendations": [*recommendations, _AGGREGATION_UNVALIDATED_SUMMARY],
            "invoiceAnomalyIndex": None,
        }

    aggregation = aggregation_output.pydantic
    return {
        "summary": summary_text,
        "risk": aggregation.model_dump(),
        "insights": insights,
        "recommendations": recommendations,
        "invoiceAnomalyIndex": invoice_anomaly_index(aggregation.categoryBreakdown),
    }
