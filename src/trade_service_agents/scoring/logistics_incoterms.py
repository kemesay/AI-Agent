"""Agent 8 — Logistics & Incoterms: incoterm/transport-mode alignment and shipping anomalies."""

from trade_service_agents.models.invoice import ProformaInvoice
from trade_service_agents.scoring._helpers import contains_any

BULK_GOODS_KEYWORDS = ["steel", "bulky", "pot"]
AIR_TRANSPORT_KEYWORDS = ["air", "flight"]


def score_logistics_incoterms(data: ProformaInvoice) -> dict:
    score = 0
    findings: list[str] = []

    if data.incoterm and data.transport_mode:
        incoterm = data.incoterm.lower()
        mode = data.transport_mode.lower()
        if ("cfr" in incoterm or "fob" in incoterm) and "air" in mode:
            score += 30
            findings.append(f"Incoterm '{data.incoterm}' is inconsistent with air transport mode.")

    if contains_any(data.transport_mode, AIR_TRANSPORT_KEYWORDS) and contains_any(
        data.item_description, BULK_GOODS_KEYWORDS
    ):
        score += 20
        findings.append("Air transport is unusual for the described bulky/heavy goods.")

    if not data.port_of_loading:
        score += 5
        findings.append("Port of loading is missing.")

    if not findings:
        findings.append("Incoterms, transport mode, and logistics details are consistent.")

    return {"score": min(100, score), "findings": findings}
