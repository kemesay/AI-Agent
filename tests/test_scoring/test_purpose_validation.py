from trade_service_agents.scoring.purpose_validation import score_purpose_validation


def test_clean_invoice_scores_low(clean_invoice):
    result = score_purpose_validation(clean_invoice)
    assert result["score"] == 0


def test_mismatched_purpose_flagged(risky_invoice):
    result = score_purpose_validation(risky_invoice)
    assert result["score"] >= 25
    assert any("purpose" in finding.lower() for finding in result["findings"])


def test_low_quantity_flagged(risky_invoice):
    result = score_purpose_validation(risky_invoice)
    assert any("quantity" in finding.lower() for finding in result["findings"])
