"""Agent 5 — Supplier Legitimacy: supplier name, address, and origin red flags."""

from trade_service_agents.models.invoice import ProformaInvoice
from trade_service_agents.scoring._helpers import contains_any

NON_COMMERCIAL_ADDRESS_KEYWORDS = ["village committee", "residential", "group 1"]
LOW_RISK_ORIGINS = {"oecd", "eu", "usa", "uk"}


def score_supplier_legitimacy(data: ProformaInvoice) -> dict:
    score = 0
    findings: list[str] = []

    if contains_any(data.supplier_address, NON_COMMERCIAL_ADDRESS_KEYWORDS):
        score += 25
        findings.append("Supplier address contains non-commercial/residential indicators.")

    if not data.supplier_name:
        score += 10
        findings.append("Supplier name is missing.")

    if data.origin and data.origin.lower() not in LOW_RISK_ORIGINS:
        score += 10
        findings.append(f"Supplier origin '{data.origin}' is outside the standard low-risk origin list.")

    if not findings:
        findings.append("Supplier name, address, and origin appear standard.")

    return {"score": min(100, score), "findings": findings}
