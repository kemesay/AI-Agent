"""Agent 4 — Invoice Integrity: arithmetic, date, and metadata consistency checks."""

from datetime import datetime, timezone

from trade_service_agents.models.invoice import ProformaInvoice


def score_invoice_integrity(data: ProformaInvoice) -> dict:
    score = 0
    findings: list[str] = []

    if data.item_total is not None and data.shipment_cost is not None and data.grand_total is not None:
        expected = data.item_total + data.shipment_cost
        if abs(expected - data.grand_total) > 0.01:
            score += 25
            findings.append("Grand total does not equal item total plus shipment cost.")
    else:
        score += 10
        findings.append("One or more invoice totals (item total, shipment cost, grand total) are missing.")

    if not data.pi_number or not data.pi_date:
        score += 10
        findings.append("Proforma invoice number or date is missing.")
    else:
        try:
            parsed_date = datetime.fromisoformat(str(data.pi_date))
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - parsed_date).days > 90:
                score += 15
                findings.append("Proforma invoice date is older than 90 days.")
        except ValueError:
            score += 10
            findings.append("Proforma invoice date could not be parsed.")

    if not findings:
        findings.append("Invoice totals, number, and date are consistent.")

    return {"score": min(100, score), "findings": findings}
