"""Agent 7 — Product & HS Code Compliance: HS code alignment and pricing anomalies."""

from trade_service_agents.models.invoice import ProformaInvoice

EXPECTED_STEEL_HS_CODE_PREFIX = "7323"
EXPECTED_UNIT_PRICE_LOW = 0.7 * 150
EXPECTED_UNIT_PRICE_HIGH = 1.3 * 180


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

    if data.unit_price is not None and (
        data.unit_price < EXPECTED_UNIT_PRICE_LOW or data.unit_price > EXPECTED_UNIT_PRICE_HIGH
    ):
        score += 20
        findings.append(f"Unit price {data.unit_price} falls outside the expected pricing band.")

    if not data.item_description:
        score += 5
        findings.append("Item description is missing or too vague to validate.")

    if not findings:
        findings.append("HS code, item description, and pricing appear consistent.")

    return {"score": min(100, score), "findings": findings}
