"""Agent 7 (extension) — Under/Over-Invoicing: declared price vs. customs reference price.

Compares an invoice's declared unit price against a real customs indicative-price reference
table (see `reference_data/customs_prices.py`) instead of one arbitrary global band. Flags a
price suspiciously *below* the reference (under-invoicing — a classic customs-duty-evasion
technique) as well as suspiciously *above* it (over-invoicing — a trade-based money-laundering
/ capital-flight signal). When the reference data isn't configured, or no confident match is
found for this invoice, this check silently contributes nothing — an unconfigured or
inapplicable check must never read as a red flag.
"""

from trade_service_agents.models.invoice import ProformaInvoice
from trade_service_agents.reference_data.customs_prices import (
    find_reference_price,
    get_reference_price_list,
)

# Ratio = declared price / reference price.
SEVERE_UNDER_INVOICE_RATIO = 0.5
UNDER_INVOICE_RATIO = 0.7
OVER_INVOICE_RATIO = 1.5
SEVERE_OVER_INVOICE_RATIO = 2.0


def score_price_deviation(data: ProformaInvoice) -> dict:
    score = 0
    findings: list[str] = []

    if data.unit_price is None:
        return {"score": 0, "findings": findings}

    records = get_reference_price_list()
    if not records:
        return {"score": 0, "findings": findings}

    match = find_reference_price(records, data.hs_code, data.item_description, data.origin)
    if match is None:
        return {"score": 0, "findings": findings}

    reference = match.record
    ratio = data.unit_price / reference.price_usd

    if ratio <= SEVERE_UNDER_INVOICE_RATIO:
        score += 35
        findings.append(
            f"Declared unit price (${data.unit_price:,.2f}) is less than half the customs "
            f"indicative price (${reference.price_usd:,.2f}) for '{reference.description}' "
            f"(HS {reference.hs_code}) — possible under-invoicing."
        )
    elif ratio <= UNDER_INVOICE_RATIO:
        score += 20
        findings.append(
            f"Declared unit price (${data.unit_price:,.2f}) is significantly below the "
            f"customs indicative price (${reference.price_usd:,.2f}) for "
            f"'{reference.description}' (HS {reference.hs_code}) — possible under-invoicing."
        )
    elif ratio >= SEVERE_OVER_INVOICE_RATIO:
        score += 25
        findings.append(
            f"Declared unit price (${data.unit_price:,.2f}) is more than double the customs "
            f"indicative price (${reference.price_usd:,.2f}) for '{reference.description}' "
            f"(HS {reference.hs_code}) — possible over-invoicing."
        )
    elif ratio >= OVER_INVOICE_RATIO:
        score += 15
        findings.append(
            f"Declared unit price (${data.unit_price:,.2f}) is significantly above the "
            f"customs indicative price (${reference.price_usd:,.2f}) for "
            f"'{reference.description}' (HS {reference.hs_code}) — possible over-invoicing."
        )
    else:
        findings.append(
            f"Declared unit price (${data.unit_price:,.2f}) aligns with the customs "
            f"indicative price (${reference.price_usd:,.2f}) for '{reference.description}'."
        )

    return {"score": min(100, score), "findings": findings}
