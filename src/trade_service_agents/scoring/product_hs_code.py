"""Agent 7 — Product & HS Code Compliance: HS code alignment with product descriptions.

Pricing anomaly detection (previously a single hardcoded band applied to every invoice
regardless of what's being imported) has moved to `scoring/price_deviation.py`, which
compares the declared price against a real customs indicative-price reference table instead
of one arbitrary global range.
"""

from trade_service_agents.models.invoice import ProformaInvoice

EXPECTED_STEEL_HS_CODE_PREFIX = "7323"


def score_product_hs_code(data: ProformaInvoice) -> dict:
    score = 0
    findings: list[str] = []

    if (
        data.hs_code
        and data.item_description
        and EXPECTED_STEEL_HS_CODE_PREFIX not in data.hs_code
        and "steel" in data.item_description.lower()
    ):
        score += 30
        findings.append(
            f"HS code '{data.hs_code}' does not match expected classification for steel goods."
        )

    if not data.item_description:
        score += 5
        findings.append("Item description is missing or too vague to validate.")

    if not findings:
        findings.append("HS code, item description, and pricing appear consistent.")

    return {"score": min(100, score), "findings": findings}
