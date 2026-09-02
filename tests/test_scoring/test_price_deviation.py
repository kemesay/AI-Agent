from unittest.mock import patch

from trade_service_agents.reference_data.customs_prices import ReferencePriceRecord
from trade_service_agents.scoring.price_deviation import score_price_deviation

_REFERENCE_RECORDS = [
    ReferencePriceRecord(
        hs_code=7301, description="ANGLE IRON (EQUAL ANGLE)", unit="MT", origin="CN", price_usd=505.0
    ),
]


def _invoice(unit_price, hs_code="7301", item_description="ANGLE IRON (EQUAL ANGLE)", origin="CN"):
    from trade_service_agents.models.invoice import ProformaInvoice

    return ProformaInvoice(
        hsCode=hs_code, itemDescription=item_description, unitPrice=unit_price, origin=origin
    )


def test_no_reference_data_configured_is_a_silent_no_op(clean_invoice):
    with patch(
        "trade_service_agents.scoring.price_deviation.get_reference_price_list", return_value=[]
    ):
        result = score_price_deviation(clean_invoice)
    assert result == {"score": 0, "findings": []}


def test_no_unit_price_is_a_silent_no_op(clean_invoice):
    clean_invoice.unit_price = None
    with patch(
        "trade_service_agents.scoring.price_deviation.get_reference_price_list",
        return_value=_REFERENCE_RECORDS,
    ):
        result = score_price_deviation(clean_invoice)
    assert result == {"score": 0, "findings": []}


def test_no_confident_match_is_a_silent_no_op():
    invoice = _invoice(unit_price=100, hs_code="9999", item_description="unrelated widget")
    with patch(
        "trade_service_agents.scoring.price_deviation.get_reference_price_list",
        return_value=_REFERENCE_RECORDS,
    ):
        result = score_price_deviation(invoice)
    assert result == {"score": 0, "findings": []}


def test_severe_under_invoicing_flagged():
    invoice = _invoice(unit_price=200)  # 200 / 505 ≈ 0.40, below SEVERE_UNDER_INVOICE_RATIO
    with patch(
        "trade_service_agents.scoring.price_deviation.get_reference_price_list",
        return_value=_REFERENCE_RECORDS,
    ):
        result = score_price_deviation(invoice)
    assert result["score"] == 35
    assert any("under-invoicing" in finding.lower() for finding in result["findings"])


def test_moderate_under_invoicing_flagged():
    invoice = _invoice(unit_price=320)  # 320 / 505 ≈ 0.63, between the two under thresholds
    with patch(
        "trade_service_agents.scoring.price_deviation.get_reference_price_list",
        return_value=_REFERENCE_RECORDS,
    ):
        result = score_price_deviation(invoice)
    assert result["score"] == 20
    assert any("under-invoicing" in finding.lower() for finding in result["findings"])


def test_severe_over_invoicing_flagged():
    invoice = _invoice(unit_price=1200)  # 1200 / 505 ≈ 2.38, above SEVERE_OVER_INVOICE_RATIO
    with patch(
        "trade_service_agents.scoring.price_deviation.get_reference_price_list",
        return_value=_REFERENCE_RECORDS,
    ):
        result = score_price_deviation(invoice)
    assert result["score"] == 25
    assert any("over-invoicing" in finding.lower() for finding in result["findings"])


def test_moderate_over_invoicing_flagged():
    invoice = _invoice(unit_price=850)  # 850 / 505 ≈ 1.68, between the two over thresholds
    with patch(
        "trade_service_agents.scoring.price_deviation.get_reference_price_list",
        return_value=_REFERENCE_RECORDS,
    ):
        result = score_price_deviation(invoice)
    assert result["score"] == 15
    assert any("over-invoicing" in finding.lower() for finding in result["findings"])


def test_aligned_price_not_flagged():
    invoice = _invoice(unit_price=500)  # 500 / 505 ≈ 0.99, within the normal band
    with patch(
        "trade_service_agents.scoring.price_deviation.get_reference_price_list",
        return_value=_REFERENCE_RECORDS,
    ):
        result = score_price_deviation(invoice)
    assert result["score"] == 0
    assert any("aligns with" in finding.lower() for finding in result["findings"])
