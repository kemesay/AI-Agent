"""Agent 6 — Payment & Currency Risk: currency/payment-term mismatches and settlement risk."""

from trade_service_agents.models.invoice import ProformaInvoice

HIGH_RISK_TERMS = {"tt", "tt advance", "advance"}
LOWER_RISK_TERMS = {"cad", "lc", "letter of credit"}


def score_payment_currency(data: ProformaInvoice) -> dict:
    score = 0
    findings: list[str] = []

    if data.currency and data.payment_term and data.currency.lower() not in data.payment_term.lower():
        score += 25
        findings.append("Invoice currency and payment term do not clearly align.")

    if not data.payment_term:
        score += 15
        findings.append("Payment term is missing.")
    elif data.payment_term.lower() in HIGH_RISK_TERMS:
        score += 20
        findings.append(f"Payment term '{data.payment_term}' is a high-risk advance settlement method.")
    elif data.payment_term.lower() in LOWER_RISK_TERMS:
        score += 10
        findings.append(f"Payment term '{data.payment_term}' carries moderate settlement risk.")
    else:
        score += 5
        findings.append(f"Payment term '{data.payment_term}' is not a recognized standard term.")

    if not findings:
        findings.append("Currency and payment term align with expected patterns.")

    return {"score": min(100, score), "findings": findings}
