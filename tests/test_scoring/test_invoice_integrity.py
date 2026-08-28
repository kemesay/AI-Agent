from trade_service_agents.scoring.invoice_integrity import score_invoice_integrity


def test_clean_invoice_scores_low(clean_invoice):
    result = score_invoice_integrity(clean_invoice)
    assert result["score"] == 0
    assert result["findings"]


def test_missing_pi_metadata_raises_score(risky_invoice):
    result = score_invoice_integrity(risky_invoice)
    assert result["score"] >= 10
    assert any("missing" in finding.lower() for finding in result["findings"])


def test_mismatched_totals_flagged(clean_invoice):
    clean_invoice.grand_total = 999999
    result = score_invoice_integrity(clean_invoice)
    assert result["score"] >= 25
    assert any("grand total" in finding.lower() for finding in result["findings"])
