from trade_service_agents.scoring.payment_currency import score_payment_currency


def test_lc_terms_score_low(clean_invoice):
    result = score_payment_currency(clean_invoice)
    assert result["score"] == 5


def test_missing_payment_term_flagged(clean_invoice):
    clean_invoice.payment_term = None
    result = score_payment_currency(clean_invoice)
    assert result["score"] >= 15


def test_advance_payment_flagged(risky_invoice):
    result = score_payment_currency(risky_invoice)
    assert result["score"] >= 20
    assert any("high-risk" in finding.lower() for finding in result["findings"])
