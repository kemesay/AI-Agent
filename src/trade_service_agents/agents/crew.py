"""The risk-assessment crew: agents 4-11 of the multi-agent architecture.

Agents 4-9 (the six risk-dimension analysts) run concurrently, agent 10
(risk aggregation) waits for all six, and agent 11 (executive summary)
waits for the aggregation result. Agents 1-3 (ingestion, normalization,
multimodal extraction) run ahead of this crew as ordinary pipeline stages.
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from trade_service_agents.agents.llm import build_gemini_llm
from trade_service_agents.agents.tools import (
    aggregate_risk_tool,
    score_invoice_integrity_tool,
    score_logistics_incoterms_tool,
    score_payment_currency_tool,
    score_product_hs_code_tool,
    score_purpose_validation_tool,
    score_supplier_legitimacy_tool,
)
from trade_service_agents.models.risk import CategoryScoreOutput, RiskAggregationOutput


@CrewBase
class RiskAssessmentCrew:
    """Multi-agent proforma invoice risk assessment crew."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        self.llm = build_gemini_llm()

    # -- Agents (4-9): independent risk-dimension analysts --------------

    @agent
    def invoice_integrity_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["invoice_integrity_agent"],
            tools=[score_invoice_integrity_tool],
            llm=self.llm,
        )

    @agent
    def supplier_legitimacy_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["supplier_legitimacy_agent"],
            tools=[score_supplier_legitimacy_tool],
            llm=self.llm,
        )

    @agent
    def payment_currency_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["payment_currency_agent"],
            tools=[score_payment_currency_tool],
            llm=self.llm,
        )

    @agent
    def product_hs_code_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["product_hs_code_agent"],
            tools=[score_product_hs_code_tool],
            llm=self.llm,
        )

    @agent
    def logistics_incoterms_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["logistics_incoterms_agent"],
            tools=[score_logistics_incoterms_tool],
            llm=self.llm,
        )

    @agent
    def purpose_validation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["purpose_validation_agent"],
            tools=[score_purpose_validation_tool],
            llm=self.llm,
        )

    # -- Agents (10-11): aggregation and summary -------------------------

    @agent
    def risk_aggregation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_aggregation_agent"],
            tools=[aggregate_risk_tool],
            llm=self.llm,
        )

    @agent
    def executive_summary_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["executive_summary_agent"],
            llm=self.llm,
        )

    # -- Tasks (4-9): run concurrently ------------------------------------

    @task
    def invoice_integrity_task(self) -> Task:
        return Task(
            config=self.tasks_config["invoice_integrity_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
        )

    @task
    def supplier_legitimacy_task(self) -> Task:
        return Task(
            config=self.tasks_config["supplier_legitimacy_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
        )

    @task
    def payment_currency_task(self) -> Task:
        return Task(
            config=self.tasks_config["payment_currency_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
        )

    @task
    def product_hs_code_task(self) -> Task:
        return Task(
            config=self.tasks_config["product_hs_code_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
        )

    @task
    def logistics_incoterms_task(self) -> Task:
        return Task(
            config=self.tasks_config["logistics_incoterms_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
        )

    @task
    def purpose_validation_task(self) -> Task:
        return Task(
            config=self.tasks_config["purpose_validation_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
        )

    # -- Tasks (10-11): aggregation waits on all six, summary waits on 10 -

    @task
    def risk_aggregation_task(self) -> Task:
        return Task(
            config=self.tasks_config["risk_aggregation_task"],
            context=[
                self.invoice_integrity_task(),
                self.supplier_legitimacy_task(),
                self.payment_currency_task(),
                self.product_hs_code_task(),
                self.logistics_incoterms_task(),
                self.purpose_validation_task(),
            ],
            output_pydantic=RiskAggregationOutput,
        )

    @task
    def executive_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config["executive_summary_task"],
            context=[self.risk_aggregation_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
