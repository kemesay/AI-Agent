"""CrewAI tool exposing the deterministic risk-aggregation engine to the aggregation agent.

The six risk-dimension category scores (agents 4-9) are computed directly in Python by
`services/proforma_analysis_service.py` — no LLM round-trip per category — so the only
tool-backed CrewAI agent left in the pipeline is the aggregation agent (10). This keeps
every risk number auditable and cuts the LLM calls needed per invoice from ~15-17 down to
~3, which matters a great deal against Gemini's free-tier daily request quota.
"""

import json

from crewai.tools import tool

from trade_service_agents.scoring.aggregation import aggregate_risk


@tool("Aggregate Risk Score")
def aggregate_risk_tool(category_scores_json: str) -> str:
    """Deterministically combines per-category risk scores into a final weighted risk score,
    risk category, and decision. Input is a JSON object mapping category name to score (0-100),
    e.g. {"invoiceIntegrity": 10, "supplierLegitimacy": 25, ...}. Returns JSON with
    finalRiskScore, riskCategory, decision, and categoryBreakdown."""
    category_scores = json.loads(category_scores_json)
    return json.dumps(aggregate_risk(category_scores))
