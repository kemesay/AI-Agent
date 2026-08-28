from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from trade_service_agents.api.app import app
from trade_service_agents.models.risk import CategoryScoreOutput, RiskAggregationOutput

client = TestClient(app)


def _stub_task_output(score: int, findings: list[str]):
    return SimpleNamespace(pydantic=CategoryScoreOutput(score=score, findings=findings))


def _stub_crew_result():
    category_outputs = [
        _stub_task_output(0, ["Invoice totals, number, and date are consistent."]),
        _stub_task_output(25, ["Supplier address contains non-commercial/residential indicators."]),
        _stub_task_output(5, ["Payment term 'LC' carries moderate settlement risk."]),
        _stub_task_output(0, ["HS code, item description, and pricing appear consistent."]),
        _stub_task_output(0, ["Incoterms, transport mode, and logistics details are consistent."]),
        _stub_task_output(0, ["Stated purpose, goods, and quantities are consistent."]),
    ]
    aggregation_output = SimpleNamespace(
        pydantic=RiskAggregationOutput(
            finalRiskScore=6.5,
            riskCategory="Very Low",
            decision="Auto-approve",
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
    return SimpleNamespace(tasks_output=[*category_outputs, aggregation_output, summary_output])


def test_analyze_proforma_returns_expected_shape():
    with patch(
        "trade_service_agents.services.proforma_analysis_service.RiskAssessmentCrew"
    ) as mock_crew_cls:
        mock_crew_cls.return_value.crew.return_value.kickoff.return_value = _stub_crew_result()

        response = client.post(
            "/analyze_proforma",
            json={"supplierName": "Acme Ltd", "currency": "USD"},
        )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"summary", "risk", "insights", "recommendations", "invoiceAnomalyIndex"}
    assert body["risk"]["riskCategory"] == "Very Low"
    assert body["risk"]["decision"] == "Auto-approve"
    assert "Supplier address contains non-commercial/residential indicators." in body["recommendations"]
    assert body["invoiceAnomalyIndex"] == 2.5
