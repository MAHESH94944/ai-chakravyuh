from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Optional, Any


class IdeaInput(BaseModel):
    """Shape of the input JSON for the validation request."""
    idea: str = Field(..., min_length=1, description="A short description of the startup idea")


class TaskResponse(BaseModel):
    """Initial response after a task is submitted (async task pattern)."""
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    message: str


# --- Agent output schemas ---


class MarketResearchMetadata(BaseModel):
    search_queries_attempted: int = 0
    search_results_analyzed: int = 0
    search_success_rate: str = "0%"
    synthesis_timestamp: Optional[str]


class MarketResearchResult(BaseModel):
    competitors: List[str] = Field(default_factory=list)
    market_size: Any = Field(default_factory=dict)
    target_audience: Any = Field(default_factory=dict)
    market_trends: List[str] = Field(default_factory=list)
    growth_rate: Any = Field(default_factory=dict)
    key_risks: List[str] = Field(default_factory=list)
    success_factors: List[str] = Field(default_factory=list)
    data_quality: str = "unknown"
    research_metadata: Optional[MarketResearchMetadata]


class UserPersonaResult(BaseModel):
    persona_story: str


class TechnicalFeasibilityResult(BaseModel):
    key_challenges: List[str] = Field(default_factory=list)
    suggested_stack: Dict[str, Any] = Field(default_factory=dict)


class FinanceResult(BaseModel):
    estimated_costs: Dict[str, str] = Field(default_factory=dict)
    potential_revenue_streams: List[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    id: Optional[str]
    title: str
    description: str
    likelihood: Literal["low", "medium", "high"]
    impact: Literal["low", "medium", "high"]
    mitigation: Optional[str]


class RiskResult(BaseModel):
    summary: Optional[str]
    overall_risk_score: Optional[int]
    risks: List[RiskItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class CriticResult(BaseModel):
    critique: str


# Final synthesized report returned to frontend
class FinalReport(BaseModel):
    report: str = Field(..., description="Final synthesized report in Markdown format")


__all__ = [
    "IdeaInput",
    "TaskResponse",
    "MarketResearchResult",
    "MarketResearchMetadata",
    "UserPersonaResult",
    "TechnicalFeasibilityResult",
    "FinanceResult",
    "RiskResult",
    "RiskItem",
    "CriticResult",
    "FinalReport",
]

