"""Agent 9 — Purpose Validation: alignment between stated purpose, goods, and quantities."""

from trade_service_agents.models.invoice import ProformaInvoice
from trade_service_agents.scoring._helpers import contains_any

MINIMUM_EXPECTED_QUANTITY = 5


def score_purpose_validation(data: ProformaInvoice) -> dict:
    score = 0
    findings: list[str] = []

    if (
        data.purpose
        and data.client_name
        and data.item_description
        and not contains_any(data.item_description, data.purpose.split())
    ):
        score += 25
        findings.append("Stated purpose does not clearly correspond to the described goods.")

    if data.quantity is not None and data.quantity < MINIMUM_EXPECTED_QUANTITY:
        score += 10
        findings.append(f"Quantity ({data.quantity}) is unusually low for the stated purpose.")

    if not findings:
        findings.append("Stated purpose, goods, and quantities are consistent.")

    return {"score": min(100, score), "findings": findings}
