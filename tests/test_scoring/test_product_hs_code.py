from trade_service_agents.scoring.product_hs_code import score_product_hs_code


def test_clean_invoice_scores_low(clean_invoice):
    result = score_product_hs_code(clean_invoice)
    assert result["score"] == 0


def test_mismatched_hs_code_for_steel_flagged(risky_invoice):
    result = score_product_hs_code(risky_invoice)
    assert result["score"] == 30
    assert any("hs code" in finding.lower() for finding in result["findings"])
