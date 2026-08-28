from trade_service_agents.scoring.supplier_legitimacy import score_supplier_legitimacy


def test_clean_invoice_scores_low(clean_invoice):
    result = score_supplier_legitimacy(clean_invoice)
    assert result["score"] == 0


def test_residential_address_flagged(risky_invoice):
    result = score_supplier_legitimacy(risky_invoice)
    assert result["score"] >= 25
    assert any("non-commercial" in finding.lower() for finding in result["findings"])


def test_missing_supplier_name_flagged(risky_invoice):
    result = score_supplier_legitimacy(risky_invoice)
    assert any("supplier name" in finding.lower() for finding in result["findings"])


def test_non_standard_origin_flagged(risky_invoice):
    result = score_supplier_legitimacy(risky_invoice)
    assert any("origin" in finding.lower() for finding in result["findings"])
