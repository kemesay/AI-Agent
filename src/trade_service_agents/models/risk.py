"""Typed outputs produced by the risk-scoring engine and the risk-assessment crew."""

from pydantic import BaseModel


class CategoryScoreOutput(BaseModel):
    """Deterministic score (0-100) and human-readable findings for one risk dimension."""

    score: int
    findings: list[str] = []


class RiskAggregationOutput(BaseModel):
    """Final weighted risk score and decision produced by the aggregation agent."""

    finalRiskScore: float
    riskCategory: str
    decision: str
    categoryBreakdown: dict[str, int]
