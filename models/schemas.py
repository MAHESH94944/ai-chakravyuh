# models/schemas.py
"""Enhanced schemas with more detailed financial and location data."""

from pydantic import BaseModel, Field, validator
from typing import Literal, List, Dict, Optional, Any, Union
from datetime import datetime
import re


class IdeaInput(BaseModel):
    """Shape of the input JSON for the validation request."""
    idea: str = Field(..., min_length=1, description="A short description of the startup idea")
    location: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Location info with text and/or coordinates"
    )


# Enhanced financial schema with detailed breakdowns
class CostBreakdown(BaseModel):
    initial_development: Dict[str, float] = Field(..., description="Breakdown of initial development costs")
    monthly_operations: Dict[str, float] = Field(..., description="Monthly operational costs breakdown")
    one_time_capex: Optional[Dict[str, float]] = Field(None, description="One-time capital expenditures")
    variable_costs: Optional[Dict[str, Any]] = Field(None, description="Variable costs structure")


class RevenueProjection(BaseModel):
    stream_name: str = Field(..., description="Name of revenue stream")
    description: str = Field(..., description="Description of revenue stream")
    estimated_monthly: float = Field(..., description="Estimated monthly revenue")
    growth_rate: Optional[float] = Field(None, description="Expected monthly growth rate")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions behind projection")


class FinancialMetrics(BaseModel):
    cac: Optional[float] = Field(None, description="Customer Acquisition Cost")
    ltv: Optional[float] = Field(None, description="Lifetime Value")
    gross_margin: Optional[float] = Field(None, description="Gross margin percentage")
    break_even_months: Optional[float] = Field(None, description="Months to break even")


class FinanceResult(BaseModel):
    estimated_costs: CostBreakdown = Field(..., description="Detailed cost breakdown")
    revenue_projections: List[RevenueProjection] = Field(..., description="Revenue projections")
    currency: str = Field(..., description="Currency code (USD, INR, EUR, etc.)")
    financial_metrics: Optional[FinancialMetrics] = Field(None, description="Key financial metrics")
    pointwise_summary: List[str] = Field(..., description="User-friendly summary bullets")
    assumptions: List[str] = Field(..., description="Key assumptions")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score 0-100")
    citations: List[Dict[str, str]] = Field(..., description="Data sources and references")
    local_cost_data: Optional[Dict[str, Any]] = Field(None, description="Local cost research data")
    exchange_rate: Optional[float] = Field(None, description="Exchange rate to USD if applicable")


# Enhanced location schema
class DemographicData(BaseModel):
    population: Optional[int] = Field(None, description="Population count")
    median_age: Optional[float] = Field(None, description="Median age")
    median_income: Optional[float] = Field(None, description="Median income in local currency")
    income_currency: Optional[str] = Field(None, description="Currency for income data")


class EconomicIndicators(BaseModel):
    gdp_growth: Optional[float] = Field(None, description="GDP growth rate")
    unemployment_rate: Optional[float] = Field(None, description="Unemployment rate")
    inflation_rate: Optional[float] = Field(None, description="Inflation rate")


class LocationAnalysisResult(BaseModel):
    normalized_name: str = Field(..., description="Standardized location name")
    coordinates: Dict[str, float] = Field(..., description="Latitude and longitude")
    country_code: str = Field(..., description="2-letter country code")
    region: Optional[str] = Field(None, description="State/region/province")
    city: Optional[str] = Field(None, description="City name")
    type: str = Field(..., description="Location type (city, town, etc.)")
    importance: float = Field(..., description="OSM importance score")
    demographics: Optional[DemographicData] = Field(None, description="Demographic data")
    economic_indicators: Optional[EconomicIndicators] = Field(None, description="Economic indicators")
    internet_penetration: Optional[float] = Field(None, description="Internet penetration rate")
    digital_literacy: Optional[float] = Field(None, description="Digital literacy score")
    infrastructure_quality: Optional[float] = Field(None, description="Infrastructure quality score")
    key_industries: List[str] = Field(..., description="Major local industries")
    viability_score: float = Field(..., ge=0, le=100, description="Viability score 0-100")
    market_readiness: float = Field(..., ge=0, le=10, description="Market readiness score 0-10")
    key_opportunities: List[str] = Field(..., description="Key business opportunities")
    critical_risks: List[str] = Field(..., description="Critical location-specific risks")
    recommendations: List[str] = Field(..., description="Location-specific recommendations")
    evidence: List[Dict[str, str]] = Field(..., description="Supporting evidence and sources")


# Enhanced market research schema
class MarketSizeEstimate(BaseModel):
    # Allow partial/optional numeric values since scraping/synthesis may be incomplete
    total_addressable_market: Optional[float] = Field(None, description="Total addressable market in local currency or units")
    serviceable_addressable_market: Optional[float] = Field(None, description="Serviceable addressable market")
    serviceable_obtainable_market: Optional[float] = Field(None, description="Serviceable obtainable market (realistic share)")
    currency: Optional[str] = Field(None, description="Currency for market size (ISO code)")
    growth_rate: Optional[float] = Field(None, description="Market growth rate (percent)")
    year: Optional[int] = Field(None, description="Year of estimate")


class CompetitorItem(BaseModel):
    name: Optional[str] = Field(None, description="Competitor name")
    description: Optional[str] = Field(None, description="Short description of the competitor")
    market_share: Optional[float] = Field(None, description="Estimated market share (percent)")
    url: Optional[str] = Field(None, description="Competitor website or listing URL")


class CompetitorAnalysis(BaseModel):
    competitors: List[CompetitorItem] = Field(default_factory=list, description="List of identified competitors")
    top_competitor_count: Optional[int] = Field(None, description="Number of top competitors identified")
    notes: Optional[str] = Field(None, description="Free-form notes about competitor landscape")


class MarketResearchResult(BaseModel):
    market_size: Optional[MarketSizeEstimate] = Field(None, description="Market sizing estimates")
    competitor_analysis: Optional[CompetitorAnalysis] = Field(None, description="Competitor analysis summary")
    target_audience: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Target audience characteristics")
    market_trends: List[str] = Field(default_factory=list, description="Key market trends")
    growth_rate: Optional[float] = Field(None, description="Overall market growth rate")
    key_risks: List[str] = Field(default_factory=list, description="Market-specific risks")
    success_factors: List[str] = Field(default_factory=list, description="Critical success factors")
    data_quality: Optional[str] = Field(None, description="Assessment of data quality")
    research_metadata: Dict[str, Any] = Field(default_factory=dict, description="Research methodology metadata")
    key_findings: List[str] = Field(default_factory=list, description="Short pointwise findings for the market")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Source citations")

# Enhanced user persona schema
class UserPersonaDetail(BaseModel):
    name: str = Field(..., description="Persona name")
    age: int = Field(..., description="Persona age")
    occupation: str = Field(..., description="Persona occupation")
    income: float = Field(..., description="Annual income")
    income_currency: str = Field(..., description="Currency for income")
    location: str = Field(..., description="Persona location")
    goals: List[str] = Field(..., description="Persona goals")
    pain_points: List[str] = Field(..., description="Persona pain points")
    tech_savviness: int = Field(..., ge=1, le=5, description="Tech savviness 1-5")
    buying_behavior: str = Field(..., description="Buying behavior description")


class UserPersonaResult(BaseModel):
    primary_persona: UserPersonaDetail = Field(..., description="Primary user persona")
    secondary_personas: Optional[List[UserPersonaDetail]] = Field(None, description="Secondary personas")
    demographic_validation: List[Dict[str, str]] = Field(..., description="Demographic validation sources")
    scenario: str = Field(..., description="Usage scenario story")
    validation_methodology: str = Field(..., description="How persona was validated")


# Enhanced technical feasibility schema
class TechnicalStack(BaseModel):
    frontend: List[str] = Field(..., description="Frontend technologies")
    backend: List[str] = Field(..., description="Backend technologies")
    database: List[str] = Field(..., description="Database technologies")
    infrastructure: List[str] = Field(..., description="Infrastructure technologies")
    third_party_services: List[str] = Field(..., description="Third-party services")


class DevelopmentTimeline(BaseModel):
    research_phase: int = Field(..., description="Weeks for research")
    design_phase: int = Field(..., description="Weeks for design")
    development_phase: int = Field(..., description="Weeks for development")
    testing_phase: int = Field(..., description="Weeks for testing")
    deployment_phase: int = Field(..., description="Weeks for deployment")


class TechnicalFeasibilityResult(BaseModel):
    key_challenges: List[str] = Field(..., description="Technical challenges")
    suggested_stack: TechnicalStack = Field(..., description="Recommended tech stack")
    architecture_overview: str = Field(..., description="System architecture description")
    data_pipeline: str = Field(..., description="Data pipeline description")
    development_timeline: DevelopmentTimeline = Field(..., description="Development timeline")
    cost_estimate: Dict[str, Any] = Field(..., description="Development cost estimate")
    team_requirements: List[str] = Field(..., description="Required team roles")
    feasibility: Literal["feasible", "feasible_with_research", "high_risk"] = Field(..., description="Feasibility rating")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score 0-100")
    research_sources: List[Dict[str, str]] = Field(..., description="Technical research sources")


# Enhanced risk schema
class RiskItem(BaseModel):
    id: str = Field(..., description="Risk identifier")
    title: str = Field(..., description="Risk title")
    description: str = Field(..., description="Risk description")
    category: Literal["market", "financial", "technical", "regulatory", "talent", "external"] = Field(..., description="Risk category")
    likelihood: Literal["low", "medium", "high"] = Field(..., description="Likelihood")
    impact: Literal["low", "medium", "high"] = Field(..., description="Impact")
    severity_score: int = Field(..., ge=1, le=9, description="Severity score 1-9")
    mitigation: str = Field(..., description="Mitigation strategy")
    validation_experiment: str = Field(..., description="Validation experiment")


class RiskResult(BaseModel):
    summary: str = Field(..., description="Risk summary")
    overall_risk_score: float = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Overall risk level")
    risk_categories: Dict[str, int] = Field(..., description="Risk counts by category")
    risks: List[RiskItem] = Field(..., description="Detailed risks")
    risk_matrix: List[RiskItem] = Field(..., description="Top risks matrix")
    recommendations: List[str] = Field(..., description="Risk mitigation recommendations")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score 0-100")
    metadata: Dict[str, Any] = Field(..., description="Analysis metadata")


# Enhanced critic schema
class CriticResult(BaseModel):
    critique: str = Field(..., description="Critical assessment")
    blind_spots: List[str] = Field(..., description="Identified blind spots")
    contradictory_findings: List[str] = Field(..., description="Contradictory findings")
    validation_questions: List[str] = Field(..., description="Questions for validation")
    confidence_score: float = Field(..., ge=0, le=100, description="Confidence score 0-100")
    evidence: List[Dict[str, str]] = Field(..., description="Supporting evidence")


# Final report schema
class FinalReport(BaseModel):
    report: str = Field(..., description="Final synthesized report in Markdown format")
    executive_summary: str = Field(..., description="Executive summary")
    key_findings: List[str] = Field(..., description="Key findings")
    recommendations: List[str] = Field(..., description="Final recommendations")
    confidence_score: float = Field(..., ge=0, le=100, description="Overall confidence score")
    generated_at: datetime = Field(..., description="Report generation timestamp")


__all__ = [
    "IdeaInput",
    "FinanceResult",
    "LocationAnalysisResult",
    "MarketResearchResult",
    "UserPersonaResult",
    "TechnicalFeasibilityResult",
    "RiskResult",
    "CriticResult",
    "FinalReport",
]