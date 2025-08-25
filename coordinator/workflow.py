import json
import asyncio
from typing import Optional, Dict, Any

# Import all of your advanced agent classes
from agents.location_analysis import LocationAnalysisAgent
from agents.market_research import MarketResearchAgent
from agents.user_persona import UserPersonaAgent
from agents.technical_feasibility import TechnicalFeasibilityAgent
from agents.finance import FinanceAgent
from agents.risk import RiskAgent
from agents.critic import CriticAgent
from core.clients import generate_text_with_fallback

async def _run_agent_async(agent_instance, timeout: int, **kwargs) -> Dict[str, Any]:
    """
    Runs an agent's run method asynchronously with a timeout.
    """
    agent_name = agent_instance.__class__.__name__
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(agent_instance.run, **kwargs),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        print(f"   ❌ {agent_name} timed out after {timeout}s")
        return {"error": f"{agent_name} timed out."}
    except Exception as e:
        print(f"   ❌ {agent_name} failed with an exception: {e}")
        return {"error": f"{agent_name} failed: {str(e)}"}

async def run_full_analysis(idea: str, location: Optional[dict] = None) -> dict:
    """
    Orchestrates the full, asynchronous multi-agent workflow.
    """
    print("--- 🚀 Starting Full Analysis with Advanced Agents ---")
    
    # --- Phase 1: Run Location first to provide hyper-local context, then run Market, Tech, and Persona ---
    print("--- Phase 1: Running Location analysis first to gather local context ---")
    if location:
        location_data = await _run_agent_async(LocationAnalysisAgent(), timeout=30, idea=idea, location_text=location['text'])
    else:
        location_data = None

    print("--- Phase 1b: Running Market, Tech, and Persona analyses with available location context ---")
    tasks_phase1b = [
        _run_agent_async(MarketResearchAgent(), timeout=40, idea=idea, location_analysis=location_data),
        _run_agent_async(TechnicalFeasibilityAgent(), timeout=30, idea=idea, location_analysis=location_data),
        _run_agent_async(UserPersonaAgent(), timeout=25, idea=idea, location=location_data)
    ]
    market_data, tech_data, persona_data = await asyncio.gather(*tasks_phase1b)
    
    print("--- ✅ Phase 1 Complete ---")

    # --- Phase 2: Run dependent agents sequentially with the necessary context ---
    print("--- Phase 2: Running Finance and Risk analysis ---")
    finance_data = await _run_agent_async(
        FinanceAgent(), timeout=30, idea=idea, market_research_data=market_data, location_analysis=location_data
    )
    risk_data = await _run_agent_async(
        RiskAgent(), timeout=30, idea=idea, market_research_data=market_data, location_analysis=location_data
    )
    print("--- ✅ Phase 2 Complete ---")

    # --- Phase 3: Run the final critic with all available context ---
    print("--- Phase 3: Running final critical assessment ---")
    critique_data = await _run_agent_async(
        CriticAgent(), timeout=30, idea=idea, finance_data=finance_data, risk_data=risk_data, 
        tech_data=tech_data, market_data=market_data, location_data=location_data
    )
    print("--- ✅ Phase 3 Complete ---")

    # --- Step 4: Compile all results into a single context object ---
    return {
        "idea": idea,
        "location_input": location['text'] if location else "Global",
        "analysis": {
            "location_analysis": location_data, "market_analysis": market_data,
            "user_persona": persona_data, "technical_feasibility": tech_data,
            "financial_outlook": finance_data, "risk_assessment": risk_data,
            "critical_assessment": critique_data
        }
    }

def synthesize_final_report(analysis_context: dict) -> dict:
    """
    Synthesizes the final structured report from all advanced agent outputs.
    """
    print("--- ✍️ Synthesizing Final Investment Memo ---")
    prompt = f"""
    You are a Senior Partner at a top-tier Venture Capital firm. Your team of expert AI analysts has submitted their findings.
    Your task is to synthesize all their reports into a final, top-level investment memo in a structured JSON format.

    **Full Data Context from Your Analyst Team:**
    ---
    {json.dumps(analysis_context, indent=2, default=str)[:14000]}
    ---

    **Your Task:**
    Write a professional, structured investment memo. Weave the key findings into a cohesive narrative for each section. Interpret the data, don't just copy it.
    The final verdict must be a clear "Go", "No-Go", or "Go with conditions".

    Return ONLY a valid JSON object matching the 'FullFeasibilityReport' schema.
    """
    try:
        response = generate_text_with_fallback(prompt, is_json=True)
        # In a production app, you would validate this against the FullFeasibilityReport schema
        # For the hackathon, we'll directly parse and return it.
        parsed = json.loads(response.text)
        # If the LLM returned an error fallback, provide a conservative structured report
        if isinstance(parsed, dict) and parsed.get("error"):
            # Build deterministic fallback using available analysis pieces
            fallback = {
                "title": f"Feasibility report (degraded) for: {analysis_context.get('idea')}",
                "executive_summary": "Detailed LLM analysis unavailable. Returning a conservative, evidence-based summary from collected agent outputs.",
                "final_verdict": "Go with conditions",
                "user_persona": analysis_context.get('analysis', {}).get('user_persona'),
                "location_analysis": analysis_context.get('analysis', {}).get('location_analysis'),
                "market_analysis": analysis_context.get('analysis', {}).get('market_analysis'),
                "technical_feasibility": analysis_context.get('analysis', {}).get('technical_feasibility'),
                "financial_outlook": analysis_context.get('analysis', {}).get('financial_outlook'),
                "risk_assessment": analysis_context.get('analysis', {}).get('risk_assessment'),
                "critical_assessment": analysis_context.get('analysis', {}).get('critical_assessment'),
                "metadata": {"fallback": True},
                "generated_at": None
            }
            return fallback

        return parsed
    except Exception as e:
        print(f"   ❌ Final synthesis failed: {e}")
        return {"error": "Failed to generate the final investment memo."}