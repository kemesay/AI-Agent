"""Agent 10 — Risk Aggregation & Decision: weighted scoring and final decision logic."""

CATEGORY_WEIGHTS = {
    "invoiceIntegrity": 0.15,
    "currencyAndPaymentTerms": 0.15,
    "supplierLegitimacy": 0.20,
    "bankDetails": 0.10,  # placeholder category; not yet extracted from source documents
    "productAndHsCode": 0.15,
    "logisticsAndIncoterms": 0.15,
    "purposeMatch": 0.10,
}


def _risk_category(score: float) -> str:
    if score <= 20:
        return "Very Low"
    if score <= 40:
        return "Low-Medium"
    if score <= 65:
        return "Medium-High"
    if score <= 85:
        return "High"
    return "Critical"


def _decision(score: float) -> str:
    if score <= 20:
        return "Auto-approve"
    if score <= 40:
        return "Normal approval workflow"
    if score <= 65:
        return "Request Clarification"
    if score <= 85:
        return "Management-level approval"
    return "Reject or escalate"


def aggregate_risk(category_scores: dict[str, int]) -> dict:
    """Combine per-category scores into a final weighted risk score and decision."""
    final_score = sum(category_scores.get(key, 0) * weight for key, weight in CATEGORY_WEIGHTS.items())

    return {
        "finalRiskScore": round(final_score, 2),
        "riskCategory": _risk_category(final_score),
        "decision": _decision(final_score),
        "categoryBreakdown": category_scores,
    }


def invoice_anomaly_index(category_scores: dict[str, int]) -> float:
    """Secondary anomaly signal derived from logistics and payment risk."""
    return round(
        category_scores.get("logisticsAndIncoterms", 0) * 0.5
        + category_scores.get("currencyAndPaymentTerms", 0) * 0.5,
        2,
    )
