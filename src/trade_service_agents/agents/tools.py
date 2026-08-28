"""CrewAI tools exposing the deterministic scoring engine to the risk-assessment agents.

Every risk number in the platform's final output is computed by these pure functions,
never by the language model itself — the agents call the tool, then explain the result.
This keeps the risk assessment auditable and reproducible.
"""

import json

from crewai.tools import tool

from trade_service_agents.models.invoice import ProformaInvoice
from trade_service_agents.scoring.aggregation import aggregate_risk
from trade_service_agents.scoring.invoice_integrity import score_invoice_integrity
from trade_service_agents.scoring.logistics_incoterms import score_logistics_incoterms
from trade_service_agents.scoring.payment_currency import score_payment_currency
from trade_service_agents.scoring.product_hs_code import score_product_hs_code
from trade_service_agents.scoring.purpose_validation import score_purpose_validation
from trade_service_agents.scoring.supplier_legitimacy import score_supplier_legitimacy


@tool("Score Invoice Integrity")
def score_invoice_integrity_tool(invoice_json: str) -> str:
    """Deterministically scores invoice arithmetic, date, and metadata integrity risk (0-100)
    from a JSON-encoded proforma invoice. Returns JSON: {"score": int, "findings": [str]}."""
    data = ProformaInvoice.model_validate_json(invoice_json)
    return json.dumps(score_invoice_integrity(data))


@tool("Score Supplier Legitimacy")
def score_supplier_legitimacy_tool(invoice_json: str) -> str:
    """Deterministically scores supplier name/address/origin legitimacy risk (0-100)
    from a JSON-encoded proforma invoice. Returns JSON: {"score": int, "findings": [str]}."""
    data = ProformaInvoice.model_validate_json(invoice_json)
    return json.dumps(score_supplier_legitimacy(data))


@tool("Score Payment and Currency Risk")
def score_payment_currency_tool(invoice_json: str) -> str:
    """Deterministically scores currency/payment-term mismatch and settlement risk (0-100)
    from a JSON-encoded proforma invoice. Returns JSON: {"score": int, "findings": [str]}."""
    data = ProformaInvoice.model_validate_json(invoice_json)
    return json.dumps(score_payment_currency(data))


@tool("Score Product and HS Code Compliance")
def score_product_hs_code_tool(invoice_json: str) -> str:
    """Deterministically scores HS code alignment and pricing anomaly risk (0-100)
    from a JSON-encoded proforma invoice. Returns JSON: {"score": int, "findings": [str]}."""
    data = ProformaInvoice.model_validate_json(invoice_json)
    return json.dumps(score_product_hs_code(data))


@tool("Score Logistics and Incoterms")
def score_logistics_incoterms_tool(invoice_json: str) -> str:
    """Deterministically scores incoterm/transport-mode alignment risk (0-100)
    from a JSON-encoded proforma invoice. Returns JSON: {"score": int, "findings": [str]}."""
    data = ProformaInvoice.model_validate_json(invoice_json)
    return json.dumps(score_logistics_incoterms(data))


@tool("Score Purpose Validation")
def score_purpose_validation_tool(invoice_json: str) -> str:
    """Deterministically scores alignment between stated purpose, goods, and quantities (0-100)
    from a JSON-encoded proforma invoice. Returns JSON: {"score": int, "findings": [str]}."""
    data = ProformaInvoice.model_validate_json(invoice_json)
    return json.dumps(score_purpose_validation(data))


@tool("Aggregate Risk Score")
def aggregate_risk_tool(category_scores_json: str) -> str:
    """Deterministically combines per-category risk scores into a final weighted risk score,
    risk category, and decision. Input is a JSON object mapping category name to score (0-100),
    e.g. {"invoiceIntegrity": 10, "supplierLegitimacy": 25, ...}. Returns JSON with
    finalRiskScore, riskCategory, decision, and categoryBreakdown."""
    category_scores = json.loads(category_scores_json)
    return json.dumps(aggregate_risk(category_scores))
