from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime

# --- API Input Schemas ---

class LocationInput(BaseModel):
    """User-provided location string."""
    text: str

class IdeaInput(BaseModel):
    """The main input model for the /validate-idea endpoint."""
    idea: str = Field(..., min_length=10, description="A detailed description of the startup idea.")
    location: Optional[LocationInput] = None

# --- Agent Output Schemas ---

class LocationAnalysisResult(BaseModel):
    normalized_name: str
    coordinates: Dict[str, float]
    country_code: str
    region: Optional[str] = None
    city: Optional[str] = None
    viability_score: float = Field(..., ge=0, le=100)
    market_readiness: float = Field(..., ge=0, le=10)
    key_opportunities: List[str]
    critical_risks: List[str]
    recommendations: List[str]
    evidence: List[Dict[str, str]]

class MarketResearchResult(BaseModel):
    market_size: str
    competitors: List[Dict[str, Any]]
    target_audience: str
    market_trends: List[str]
    sources: List[HttpUrl]

class UserPersonaResult(BaseModel):
    name: str
    age: int
    occupation: str
    story: str
    pain_points: List[str]

class TechnicalFeasibilityResult(BaseModel):
    key_challenges: List[str]
    suggested_stack: Dict[str, Any]
    development_timeline: Dict[str, Any]
    team_requirements: List[str]
    feasibility: Literal["feasible", "feasible_with_research", "high_risk"]

class FinanceResult(BaseModel):
    initial_development: Dict[str, Any]
    monthly_operations: Dict[str, Any]
    revenue_projections_year_1: Dict[str, Any]
    key_financial_ratios: Dict[str, Any]
    assumptions: List[str]
    data_sources: List[str]

class RiskResult(BaseModel):
    summary: str
    overall_risk_score: float = Field(..., ge=0, le=100)
    risk_level: Literal["low", "medium", "high"]
    risks: List[Dict[str, Any]]
    recommendations: List[str]

class CriticResult(BaseModel):
    critique: str
    blind_spots: List[str]
    contradictory_findings: List[str]
    validation_questions: List[str]

class TechnicalStack(BaseModel):
    frontend: List[str]
    backend: List[str]
    database: List[str]
    infrastructure: List[str]
    third_party_services: List[str]

class DevelopmentTimeline(BaseModel):
    research_phase: int
    design_phase: int
    development_phase: int
    testing_phase: int
    deployment_phase: int

class UserPersonaDetail(BaseModel):
    name: str
    age: int
    occupation: str
    income: Optional[float]
    income_currency: Optional[str]
    location: Optional[str]
    goals: List[str]
    pain_points: List[str]
    tech_savviness: Optional[int]

# --- Final, All-Encompassing Report Schema ---

class FullFeasibilityReport(BaseModel):
    """
    The final, comprehensive report that nests all individual agent analyses.
    This is the definitive output of the API.
    """
    title: str
    executive_summary: str
    final_verdict: str
    user_persona: Optional[UserPersonaResult] = None
    location_analysis: Optional[LocationAnalysisResult] = None
    market_analysis: Optional[MarketResearchResult] = None
    technical_feasibility: Optional[TechnicalFeasibilityResult] = None
    financial_outlook: Optional[FinanceResult] = None
    risk_assessment: Optional[RiskResult] = None
    critical_assessment: Optional[CriticResult] = None
    metadata: Dict[str, Any]
    generated_at: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "Startup Feasibility Report: AI Personal Trainer",
                "executive_summary": "Localized analysis for Pune indicates ...",
                "final_verdict": "Go with conditions",
                "metadata": {"version": "2.0"},
                "generated_at": "2025-08-25T12:00:00Z"
            }
        }