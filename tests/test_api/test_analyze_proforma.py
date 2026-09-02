from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

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
        mock_crew_cls.return_value.crew.return_value.kickoff_async = AsyncMock(
            return_value=_stub_crew_result()
        )

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


def test_analyze_proforma_surfaces_unvalidated_category_instead_of_crashing():
    category_outputs = [
        SimpleNamespace(pydantic=None),  # agent never called its tool, guardrail retry exhausted
        _stub_task_output(0, ["Supplier address appears standard."]),
        _stub_task_output(0, ["Currency and payment term align."]),
        _stub_task_output(0, ["HS code and pricing appear consistent."]),
        _stub_task_output(0, ["Logistics details are consistent."]),
        _stub_task_output(0, ["Purpose and goods are consistent."]),
    ]
    aggregation_output = SimpleNamespace(
        pydantic=RiskAggregationOutput(
            finalRiskScore=2.0,
            riskCategory="Very Low",
            decision="Auto-approve",
            categoryBreakdown={"invoiceIntegrity": 0},
        )
    )
    summary_output = SimpleNamespace(raw="Low risk overall.")
    crew_result = SimpleNamespace(tasks_output=[*category_outputs, aggregation_output, summary_output])

    with patch(
        "trade_service_agents.services.proforma_analysis_service.RiskAssessmentCrew"
    ) as mock_crew_cls:
        mock_crew_cls.return_value.crew.return_value.kickoff_async = AsyncMock(
            return_value=crew_result
        )

        response = client.post(
            "/analyze_proforma",
            json={"supplierName": "Acme Ltd", "currency": "USD"},
        )

    assert response.status_code == 200
    body = response.json()
    unvalidated_notice = "requires manual review"
    assert any(unvalidated_notice in finding for finding in body["insights"])
    assert any(unvalidated_notice in finding for finding in body["recommendations"])


def test_analyze_proforma_flags_unvalidated_aggregation_instead_of_crashing():
    category_outputs = [
        _stub_task_output(0, ["Invoice totals are consistent."]) for _ in range(6)
    ]
    aggregation_output = SimpleNamespace(pydantic=None)  # aggregation guardrail retry exhausted
    summary_output = SimpleNamespace(raw="Unused because aggregation was not validated.")
    crew_result = SimpleNamespace(tasks_output=[*category_outputs, aggregation_output, summary_output])

    with patch(
        "trade_service_agents.services.proforma_analysis_service.RiskAssessmentCrew"
    ) as mock_crew_cls:
        mock_crew_cls.return_value.crew.return_value.kickoff_async = AsyncMock(
            return_value=crew_result
        )

        response = client.post(
            "/analyze_proforma",
            json={"supplierName": "Acme Ltd", "currency": "USD"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["risk"]["decision"] == "Manual review required"
    assert body["risk"]["finalRiskScore"] is None
    assert body["invoiceAnomalyIndex"] is None
