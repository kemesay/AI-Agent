from trade_service_agents.scoring.logistics_incoterms import score_logistics_incoterms


def test_clean_invoice_scores_low(clean_invoice):
    result = score_logistics_incoterms(clean_invoice)
    assert result["score"] == 0


def test_cfr_with_air_freight_flagged(risky_invoice):
    result = score_logistics_incoterms(risky_invoice)
    assert result["score"] >= 30
    assert any("inconsistent with air" in finding.lower() for finding in result["findings"])


def test_bulky_goods_by_air_flagged(risky_invoice):
    result = score_logistics_incoterms(risky_invoice)
    assert result["score"] >= 50


def test_missing_port_of_loading_flagged(risky_invoice):
    result = score_logistics_incoterms(risky_invoice)
    assert any("port of loading" in finding.lower() for finding in result["findings"])
