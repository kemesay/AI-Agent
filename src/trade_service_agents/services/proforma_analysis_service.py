"""Orchestrates the full risk assessment: invoice data in, decision-ready response out.

Agents 4-9 (the six risk-dimension analysts) are called here as plain Python functions, not
as CrewAI/LLM agents — see `agents/crew.py` for why. Only the aggregation (10) and executive
summary (11) tasks go through the LLM, which keeps a single analysis to ~3 API calls instead
of ~15-17.
"""

import json
from typing import Any

from trade_service_agents.agents.crew import RiskAssessmentCrew
from trade_service_agents.models.invoice import ProformaInvoice
from trade_service_agents.scoring.aggregation import invoice_anomaly_index
from trade_service_agents.scoring.invoice_integrity import score_invoice_integrity
from trade_service_agents.scoring.logistics_incoterms import score_logistics_incoterms
from trade_service_agents.scoring.payment_currency import score_payment_currency
from trade_service_agents.scoring.price_deviation import score_price_deviation
from trade_service_agents.scoring.product_hs_code import score_product_hs_code
from trade_service_agents.scoring.purpose_validation import score_purpose_validation
from trade_service_agents.scoring.supplier_legitimacy import score_supplier_legitimacy

_HIGH_RISK_FINDING_THRESHOLD = 20
_AGGREGATION_UNVALIDATED_SUMMARY = (
    "Automated risk aggregation could not be validated for this invoice; manual compliance "
    "review is required."
)

# Category key -> deterministic scoring functions (agents 4-9). A category can run more than
# one check (e.g. HS/description consistency and customs reference-price deviation both feed
# `productAndHsCode`) — their scores are summed (capped at 100) and findings concatenated.
# `bankDetails` has no corresponding agent in the 11-agent architecture and is always 0 (see
# aggregation.py).
_CATEGORY_SCORERS = {
    "invoiceIntegrity": [score_invoice_integrity],
    "currencyAndPaymentTerms": [score_payment_currency],
    "supplierLegitimacy": [score_supplier_legitimacy],
    "productAndHsCode": [score_product_hs_code, score_price_deviation],
    "logisticsAndIncoterms": [score_logistics_incoterms],
    "purposeMatch": [score_purpose_validation],
}


def _run_category_scoring(invoice: ProformaInvoice) -> dict[str, dict]:
    """Run agents 4-9 as direct function calls, keyed by their aggregation category name."""
    results: dict[str, dict] = {}
    for name, scorers in _CATEGORY_SCORERS.items():
        sub_results = [scorer(invoice) for scorer in scorers]
        results[name] = {
            "score": min(100, sum(r["score"] for r in sub_results)),
            "findings": [finding for r in sub_results for finding in r["findings"]],
        }
    results["bankDetails"] = {"score": 0, "findings": []}
    return results


async def analyze_proforma(invoice: ProformaInvoice) -> dict[str, Any]:
    """Run the risk-assessment pipeline for a single proforma invoice and shape the response.

    The aggregation agent occasionally fails to produce a tool-grounded, schema-valid answer
    even after a guardrail retry — a real failure mode of LLM tool use, not a bug to paper
    over. Rather than crash or silently return a fabricated number, an unvalidated result is
    surfaced as an explicit "manual review required" decision.
    """
    category_results = _run_category_scoring(invoice)

    insights: list[str] = []
    recommendations: list[str] = []
    category_scores: dict[str, int] = {}
    for name, result in category_results.items():
        category_scores[name] = result["score"]
        insights.extend(result["findings"])
        if result["score"] >= _HIGH_RISK_FINDING_THRESHOLD:
            recommendations.extend(result["findings"])

    recommendations_text = "\n".join(f"- {rec}" for rec in recommendations) or "No specific recommendations."

    result = await RiskAssessmentCrew().crew().kickoff_async(
        inputs={
            "category_scores_json": json.dumps(category_scores),
            "recommendations_text": recommendations_text,
        }
    )

    aggregation_output, summary_output = result.tasks_output

    if aggregation_output.pydantic is None:
        return {
            "summary": _AGGREGATION_UNVALIDATED_SUMMARY,
            "risk": {
                "finalRiskScore": None,
                "riskCategory": "Unknown",
                "decision": "Manual review required",
                "categoryBreakdown": category_scores,
            },
            "insights": insights,
            "recommendations": [*recommendations, _AGGREGATION_UNVALIDATED_SUMMARY],
            "invoiceAnomalyIndex": None,
        }

    aggregation = aggregation_output.pydantic
    return {
        "summary": summary_output.raw.strip(),
        "risk": aggregation.model_dump(),
        "insights": insights,
        "recommendations": recommendations,
        "invoiceAnomalyIndex": invoice_anomaly_index(aggregation.categoryBreakdown),
    }
