"""The risk-assessment crew: agents 10-11 of the multi-agent architecture.

Agents 4-9 (the six risk-dimension analysts) are pure Python — see
`services/proforma_analysis_service.py` — for the same reason agents 1-3 (ingestion,
normalization, multimodal extraction) run ahead of this crew: no LLM round-trip is needed
to run a deterministic function, and every one skipped is a call that can't be rate-limited,
mis-scored, or burn a scarce free-tier request. Only the aggregation agent (10, which must
call a tool over six numbers it didn't compute) and the executive summary agent (11, which
genuinely needs to generate prose) remain real CrewAI/LLM agents.
"""

from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.task_output import TaskOutput

from trade_service_agents.agents.llm import build_gemini_llm
from trade_service_agents.agents.tools import aggregate_risk_tool
from trade_service_agents.core.config import get_settings
from trade_service_agents.models.risk import RiskAggregationOutput


def _require_tool_usage_guardrail(tool_name: str):
    """Build a guardrail rejecting a task's answer if its agent never called `tool_name`.

    Agents occasionally "helpfully" answer from their own reasoning instead of calling their
    assigned deterministic tool. Since `Task.used_tools` is only known once the task object
    exists, the guardrail closes over a mutable holder that gets filled in right after the
    `Task` it belongs to is constructed — by the time CrewAI actually calls the guardrail
    (after the agent's first attempt), the holder is already populated.

    On success this must return the raw string (`output.raw`), not the `TaskOutput` object
    itself: CrewAI only re-runs `output_pydantic` conversion when a guardrail's success value
    is a string. Returning the `TaskOutput` unchanged is accepted silently but skips that
    conversion, leaving `.pydantic` permanently `None` even for a perfectly valid answer.
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
        return True, output.raw

    return holder, guardrail


@CrewBase
class RiskAssessmentCrew:
    """Risk aggregation and executive-summary crew (agents 10-11)."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self) -> None:
        self.llm = build_gemini_llm()

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

    @task
    def risk_aggregation_task(self) -> Task:
        holder, guardrail = _require_tool_usage_guardrail("Aggregate Risk Score")
        task = Task(
            config=self.tasks_config["risk_aggregation_task"],
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
