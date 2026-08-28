from trade_service_agents.scoring.aggregation import aggregate_risk, invoice_anomaly_index


def test_all_zero_scores_yield_very_low_auto_approve():
    scores = {key: 0 for key in [
        "invoiceIntegrity", "currencyAndPaymentTerms", "supplierLegitimacy",
        "bankDetails", "productAndHsCode", "logisticsAndIncoterms", "purposeMatch",
    ]}
    result = aggregate_risk(scores)
    assert result["finalRiskScore"] == 0
    assert result["riskCategory"] == "Very Low"
    assert result["decision"] == "Auto-approve"


def test_high_scores_yield_critical_reject():
    scores = {key: 100 for key in [
        "invoiceIntegrity", "currencyAndPaymentTerms", "supplierLegitimacy",
        "bankDetails", "productAndHsCode", "logisticsAndIncoterms", "purposeMatch",
    ]}
    result = aggregate_risk(scores)
    assert result["finalRiskScore"] == 100
    assert result["riskCategory"] == "Critical"
    assert result["decision"] == "Reject or escalate"


def test_weighted_score_uses_category_weights():
    scores = {"supplierLegitimacy": 100}
    result = aggregate_risk(scores)
    assert result["finalRiskScore"] == 20  # 100 * 0.20 weight, all other categories absent (0)


def test_invoice_anomaly_index_averages_logistics_and_payment():
    scores = {"logisticsAndIncoterms": 40, "currencyAndPaymentTerms": 20}
    assert invoice_anomaly_index(scores) == 30
