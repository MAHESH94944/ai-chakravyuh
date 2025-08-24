from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Optional, Any


class IdeaInput(BaseModel):
    """Shape of the input JSON for the validation request."""
    idea: str = Field(..., min_length=1, description="A short description of the startup idea")
    # Optional free-form location text (e.g. "Alandi, Pune, Maharashtra, India")
    location: Optional[Dict[str, Any]] = Field(default=None, description="Optional location info; e.g. {'text':'Alandi, Pune, India'} or {'lat':..., 'lon':...}")


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


class LocationInput(BaseModel):
    text: Optional[str]
    lat: Optional[float]
    lon: Optional[float]


class LocationAnalysisResult(BaseModel):
    location: Dict[str, Any]
    population: Optional[Dict[str, Any]] = None
    demand_score: float = 0.0
    competitor_density: float = 0.0
    user_interest_trend: Optional[Dict[str, Any]] = None
    payment_preferences: List[str] = Field(default_factory=list)
    infrastructure_score: float = 0.0
    talent_availability: float = 0.0
    regulatory_flags: List[Dict[str, Any]] = Field(default_factory=list)
    local_channels: List[str] = Field(default_factory=list)
    similar_local_startups: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    recommendations: List[str] = Field(default_factory=list)
    raw_evidence: List[Dict[str, Any]] = Field(default_factory=list)


class UserPersonaResult(BaseModel):
    persona_story: str


class TechnicalFeasibilityResult(BaseModel):
    key_challenges: List[str] = Field(default_factory=list)
    suggested_stack: Dict[str, Any] = Field(default_factory=dict)


class FinanceResult(BaseModel):
    # Allow estimated_costs to be a nested object with keys like initial_development, monthly_operations (which may be a dict of line items)
    estimated_costs: Dict[str, Any] = Field(default_factory=dict)
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

