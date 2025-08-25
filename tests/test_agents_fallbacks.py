import sys
import asyncio
sys.path.append(r'D:/All Year/Kurukshetra hackathon (MIT Alandi)/startup-validator-backend')

from agents.market_research import MarketResearchAgent
from agents.technical_feasibility import TechnicalFeasibilityAgent
from agents.risk import RiskAgent
from models.schemas import MarketResearchResult, TechnicalFeasibilityResult, RiskResult


def test_market_research_fallback():
    agent = MarketResearchAgent()
    # Simulate no evidence / no LLM by passing no location and expecting the fallback to be schema-valid
    result = agent.run('A fitness tracking app that uses AI to create personalized workout and diet plans', None)
    # Validate using Pydantic schema
    validated = MarketResearchResult.model_validate(result)
    assert isinstance(validated, MarketResearchResult)
    assert validated.market_size is not None


def test_technical_feasibility_fallback():
    agent = TechnicalFeasibilityAgent()
    result = agent.run('A fitness tracking app that uses AI to create personalized workout and diet plans', None, None)
    validated = TechnicalFeasibilityResult.model_validate(result)
    assert isinstance(validated, TechnicalFeasibilityResult)
    assert 'suggested_stack' in result


def test_risk_agent_fallback():
    agent = RiskAgent()
    result = agent.run('A fitness tracking app that uses AI to create personalized workout and diet plans', {}, None)
    validated = RiskResult.model_validate(result)
    assert isinstance(validated, RiskResult)
    assert validated.overall_risk_score >= 0
