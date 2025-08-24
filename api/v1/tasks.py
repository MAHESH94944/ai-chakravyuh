from fastapi import APIRouter, HTTPException
from models.schemas import IdeaInput

# Import our new agent
from agents.market_research import MarketResearchAgent

router = APIRouter()

@router.post("/validate-idea")
def validate_idea(idea_input: IdeaInput):
    """
    Accepts a startup idea and returns market research for testing.
    """
    if not idea_input.idea:
        raise HTTPException(status_code=400, detail="Idea text cannot be empty.")

    # Create an instance of the agent and run it
    research_agent = MarketResearchAgent()
    result = research_agent.run(idea=idea_input.idea)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result