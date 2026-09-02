from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from trade_service_agents.api.app import app
from trade_service_agents.models.risk import RiskAggregationOutput

client = TestClient(app)


def _stub_crew_result(final_score: float, category: str, decision: str):
    aggregation_output = SimpleNamespace(
        pydantic=RiskAggregationOutput(
            finalRiskScore=final_score,
            riskCategory=category,
            decision=decision,
            categoryBreakdown={
                "invoiceIntegrity": 0,
                "currencyAndPaymentTerms": 5,
                "supplierLegitimacy": 25,
                "bankDetails": 0,
                "productAndHsCode": 0,
                "logisticsAndIncoterms": 0,
                "purposeMatch": 0,
            },
        )
    )
    summary_output = SimpleNamespace(raw="This invoice carries very low risk and is recommended for auto-approval.")
    return SimpleNamespace(tasks_output=(aggregation_output, summary_output))


def test_analyze_proforma_returns_expected_shape(risky_invoice):
    """Agents 4-9 run for real here (pure Python); only the aggregation/summary crew is mocked."""
    with patch(
        "trade_service_agents.services.proforma_analysis_service.RiskAssessmentCrew"
    ) as mock_crew_cls:
        mock_crew_cls.return_value.crew.return_value.kickoff_async = AsyncMock(
            return_value=_stub_crew_result(6.5, "Very Low", "Auto-approve")
        )

        response = client.post(
            "/analyze_proforma",
            json=risky_invoice.model_dump(by_alias=True),
        )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"summary", "risk", "insights", "recommendations", "invoiceAnomalyIndex"}
    assert body["risk"]["riskCategory"] == "Very Low"
    assert body["risk"]["decision"] == "Auto-approve"
    assert "Supplier address contains non-commercial/residential indicators." in body["recommendations"]
    assert body["invoiceAnomalyIndex"] == 2.5


def test_analyze_proforma_flags_unvalidated_aggregation_instead_of_crashing(clean_invoice):
    aggregation_output = SimpleNamespace(pydantic=None)  # aggregation guardrail retry exhausted
    summary_output = SimpleNamespace(raw="Unused because aggregation was not validated.")
    crew_result = SimpleNamespace(tasks_output=(aggregation_output, summary_output))

    with patch(
        "trade_service_agents.services.proforma_analysis_service.RiskAssessmentCrew"
    ) as mock_crew_cls:
        mock_crew_cls.return_value.crew.return_value.kickoff_async = AsyncMock(
            return_value=crew_result
        )

        response = client.post(
            "/analyze_proforma",
            json=clean_invoice.model_dump(by_alias=True),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["risk"]["decision"] == "Manual review required"
    assert body["risk"]["finalRiskScore"] is None
    assert body["invoiceAnomalyIndex"] is None
