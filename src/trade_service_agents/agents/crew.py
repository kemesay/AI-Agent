"""The risk-assessment crew: agents 4-11 of the multi-agent architecture.

Agents 4-9 (the six risk-dimension analysts) run concurrently, agent 10
(risk aggregation) waits for all six, and agent 11 (executive summary)
waits for the aggregation result. Agents 1-3 (ingestion, normalization,
multimodal extraction) run ahead of this crew as ordinary pipeline stages.
"""

from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.task_output import TaskOutput

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
from trade_service_agents.core.config import get_settings
from trade_service_agents.models.risk import CategoryScoreOutput, RiskAggregationOutput


def _require_tool_usage_guardrail(tool_name: str):
    """Build a guardrail rejecting a task's answer if its agent never called `tool_name`.

    Agents occasionally "helpfully" answer from their own reasoning instead of calling their
    assigned deterministic tool. Since `Task.used_tools` is only known once the task object
    exists, the guardrail closes over a mutable holder that gets filled in right after the
    `Task` it belongs to is constructed — by the time CrewAI actually calls the guardrail
    (after the agent's first attempt), the holder is already populated.
    """
    holder: dict[str, Task] = {}

    def guardrail(output: TaskOutput) -> tuple[bool, Any]:
        task = holder.get("task")
        if task is not None and task.used_tools == 0:
            return False, (
                f"You did not call the {tool_name} tool. You must call it with the exact "
                "invoice JSON provided in the task and return its raw output — never compute "
                "or estimate the score yourself."
            )
        return True, output

    return holder, guardrail


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
        holder, guardrail = _require_tool_usage_guardrail("Score Invoice Integrity")
        task = Task(
            config=self.tasks_config["invoice_integrity_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
            guardrail=guardrail,
            guardrail_max_retries=1,
        )
        holder["task"] = task
        return task

    @task
    def supplier_legitimacy_task(self) -> Task:
        holder, guardrail = _require_tool_usage_guardrail("Score Supplier Legitimacy")
        task = Task(
            config=self.tasks_config["supplier_legitimacy_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
            guardrail=guardrail,
            guardrail_max_retries=1,
        )
        holder["task"] = task
        return task

    @task
    def payment_currency_task(self) -> Task:
        holder, guardrail = _require_tool_usage_guardrail("Score Payment and Currency Risk")
        task = Task(
            config=self.tasks_config["payment_currency_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
            guardrail=guardrail,
            guardrail_max_retries=1,
        )
        holder["task"] = task
        return task

    @task
    def product_hs_code_task(self) -> Task:
        holder, guardrail = _require_tool_usage_guardrail("Score Product and HS Code Compliance")
        task = Task(
            config=self.tasks_config["product_hs_code_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
            guardrail=guardrail,
            guardrail_max_retries=1,
        )
        holder["task"] = task
        return task

    @task
    def logistics_incoterms_task(self) -> Task:
        holder, guardrail = _require_tool_usage_guardrail("Score Logistics and Incoterms")
        task = Task(
            config=self.tasks_config["logistics_incoterms_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
            guardrail=guardrail,
            guardrail_max_retries=1,
        )
        holder["task"] = task
        return task

    @task
    def purpose_validation_task(self) -> Task:
        holder, guardrail = _require_tool_usage_guardrail("Score Purpose Validation")
        task = Task(
            config=self.tasks_config["purpose_validation_task"],
            output_pydantic=CategoryScoreOutput,
            async_execution=True,
            guardrail=guardrail,
            guardrail_max_retries=1,
        )
        holder["task"] = task
        return task

    # -- Tasks (10-11): aggregation waits on all six, summary waits on 10 -

    @task
    def risk_aggregation_task(self) -> Task:
        holder, guardrail = _require_tool_usage_guardrail("Aggregate Risk Score")
        task = Task(
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
            guardrail=guardrail,
            guardrail_max_retries=1,
        )
        holder["task"] = task
        return task

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
            max_rpm=get_settings().gemini_max_rpm,
        )
