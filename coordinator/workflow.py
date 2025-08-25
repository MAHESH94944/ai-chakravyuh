import json
from typing import Optional
import threading
import traceback
import time as _time
from agents.market_research import MarketResearchAgent
from agents.user_persona import UserPersonaAgent
from agents.technical_feasibility import TechnicalFeasibilityAgent
from agents.finance import FinanceAgent
from agents.risk import RiskAgent
from agents.critic import CriticAgent
from core.clients import generate_text

def _run_with_timeout(func, args=(), kwargs=None, timeout=25):
    """Run func in a thread and return result or raise TimeoutError."""
    if kwargs is None:
        kwargs = {}
    result = {}

    def target():
        try:
            result['value'] = func(*args, **kwargs)
        except Exception as e:
            result['error'] = e

    th = threading.Thread(target=target)
    th.daemon = True
    th.start()
    th.join(timeout)
    if th.is_alive():
        raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")
    if 'error' in result:
        raise result['error']
    return result.get('value')


def run_full_analysis(idea: str, location: Optional[dict] = None) -> dict:
    """
    Orchestrates the entire multi-agent workflow to gather all analyses.
    """
    print("--- Starting Full Analysis Workflow ---")
    
    # --- Step 0: Location analysis (optional) ---
    location_data = None
    if location and location.get("text"):
        try:
            # If provided location lacks lat/lon, try to enrich it via central get_location_data
            try:
                # Quick local lookup for commonly tested Indian locations to avoid
                # slow geocoding during development/testing. Fall back to get_location_data.
                known_locations = {
                    "buldhana": {"lat": 20.4333, "lon": 76.1167, "country_code": "IN"}
                }
                lat = location.get('latitude') or location.get('lat')
                lon = location.get('longitude') or location.get('lon')
                if not (lat and lon):
                    text = (location.get('text') or '').lower()
                    for name, info in known_locations.items():
                        if name in text:
                            location.setdefault('latitude', info['lat'])
                            location.setdefault('longitude', info['lon'])
                            location.setdefault('country_code', info['country_code'])
                            location.setdefault('city', location.get('city') or name.title())
                            break
                # If still missing, try the core geocoding helper
                if not (location.get('latitude') and location.get('longitude')):
                    from core.clients import get_location_data
                    remote = get_location_data(location.get('text'))
                    if remote:
                        # populate missing fields
                        location.setdefault('latitude', remote.get('lat'))
                        location.setdefault('longitude', remote.get('lon'))
                        addr = remote.get('address', {})
                        location.setdefault('country_code', (addr.get('country_code') or '').upper())
                        location.setdefault('city', addr.get('city') or addr.get('town') or addr.get('village'))
                        location.setdefault('region', addr.get('state') or addr.get('county'))
            except Exception:
                pass

            from agents.location_analysis import LocationAnalysisAgent
            location_agent = LocationAnalysisAgent()
            # Pass any provided structured location (city, region, country_code, lat/lon)
            location_data = _run_with_timeout(location_agent.run, args=(), kwargs={"idea": idea, "location_text": location.get("text"), "provided_location": location}, timeout=20)
            print("--- Location analysis completed ---")
        except Exception as e:
            print("Location analysis failed:")
            traceback.print_exc()
            location_data = {"error": str(e)}
    # --- Step 1: Run initial, parallelizable agents ---
    market_agent = MarketResearchAgent()
    # Pass location context if available (agents can optionally accept it)
    try:
        market_data = _run_with_timeout(market_agent.run, args=(), kwargs={"idea": idea, "location": location_data}, timeout=30)
    except TypeError:
        try:
            market_data = _run_with_timeout(market_agent.run, args=(idea,), timeout=30)
        except Exception:
            print("MarketResearchAgent failed:")
            traceback.print_exc()
            market_data = {"error": "MarketResearchAgent failed"}
    except Exception:
        print("MarketResearchAgent failed:")
        traceback.print_exc()
        market_data = {"error": "MarketResearchAgent failed"}
    if "error" in market_data:
        print("MarketResearchAgent returned error, embedding into context and continuing")

    tech_agent = TechnicalFeasibilityAgent()
    try:
        tech_data = _run_with_timeout(tech_agent.run, args=(), kwargs={"idea": idea, "location": location_data}, timeout=20)
    except TypeError:
        try:
            tech_data = _run_with_timeout(tech_agent.run, args=(idea,), timeout=20)
        except Exception:
            print("TechnicalFeasibilityAgent failed:")
            traceback.print_exc()
            tech_data = {"error": "TechnicalFeasibilityAgent failed"}
    except Exception:
        print("TechnicalFeasibilityAgent failed:")
        traceback.print_exc()
        tech_data = {"error": "TechnicalFeasibilityAgent failed"}
    if "error" in tech_data:
        print("TechnicalFeasibilityAgent returned error, embedding into context and continuing")
    
    persona_agent = UserPersonaAgent()
    try:
        persona_data = _run_with_timeout(persona_agent.run, args=(), kwargs={"idea": idea, "location": location_data}, timeout=15)
    except TypeError:
        try:
            persona_data = _run_with_timeout(persona_agent.run, args=(idea,), timeout=15)
        except Exception:
            print("UserPersonaAgent failed:")
            traceback.print_exc()
            persona_data = {"error": "UserPersonaAgent failed"}
    except Exception:
        print("UserPersonaAgent failed:")
        traceback.print_exc()
        persona_data = {"error": "UserPersonaAgent failed"}
    if "error" in persona_data:
        print("UserPersonaAgent returned error, embedding into context and continuing")

    # --- Step 2: Run agents that depend on initial results ---
    finance_agent = FinanceAgent()
    try:
        finance_data = _run_with_timeout(finance_agent.run, args=(), kwargs={"idea": idea, "market_research_data": market_data, "location": location_data}, timeout=20)
    except TypeError:
        try:
            finance_data = _run_with_timeout(finance_agent.run, args=(idea, market_data), timeout=20)
        except Exception:
            print("FinanceAgent failed:")
            traceback.print_exc()
            finance_data = {"error": "FinanceAgent failed"}
    except Exception:
        print("FinanceAgent failed:")
        traceback.print_exc()
        finance_data = {"error": "FinanceAgent failed"}
    if "error" in finance_data:
        print("FinanceAgent returned error, embedding into context and continuing")

    risk_agent = RiskAgent()
    try:
        risk_data = _run_with_timeout(risk_agent.run, args=(), kwargs={"idea": idea, "market_research_data": market_data, "location": location_data}, timeout=20)
    except TypeError:
        try:
            risk_data = _run_with_timeout(risk_agent.run, args=(idea, market_data), timeout=20)
        except Exception:
            print("RiskAgent failed:")
            traceback.print_exc()
            risk_data = {"error": "RiskAgent failed"}
    except Exception:
        print("RiskAgent failed:")
        traceback.print_exc()
        risk_data = {"error": "RiskAgent failed"}
    if "error" in risk_data:
        print("RiskAgent returned error, embedding into context and continuing")
    
    # --- Step 3: Run the final critic agent ---
    critic_agent = CriticAgent()
    try:
        critique_data = _run_with_timeout(critic_agent.run, args=(), kwargs={"idea": idea, "finance_data": finance_data, "risk_data": risk_data, "tech_data": tech_data, "location": location_data}, timeout=20)
    except TypeError:
        try:
            critique_data = _run_with_timeout(critic_agent.run, args=(idea, finance_data, risk_data, tech_data), timeout=20)
        except Exception:
            print("CriticAgent failed:")
            traceback.print_exc()
            critique_data = {"error": "CriticAgent failed"}
    except Exception:
        print("CriticAgent failed:")
        traceback.print_exc()
        critique_data = {"error": "CriticAgent failed"}
    if "error" in critique_data:
        print("CriticAgent returned error, embedding into context and continuing")

    print("--- Full Analysis Workflow Finished ---")

    # --- Step 4: Compile all results into a single context object ---
    full_context = {
        "idea": idea,
        "location": location.get("text") if location else None,
        "location_analysis": location_data,
        "market_analysis": market_data,
        "user_persona": persona_data,
        "technical_feasibility": tech_data,
        "financial_outlook": finance_data,
        "risk_analysis": risk_data,
        "final_critique": critique_data,
    }
    
    return full_context

def synthesize_final_report(analysis_context: dict) -> str:
    """
    Takes all the collected data and synthesizes the final Markdown report.
    """
    print("--- Synthesizing Final Report ---")
    
    # Extract the core idea for use in the prompt
    startup_idea = analysis_context['idea']
    
    prompt = f"""
# ROLE & GOAL:
You are a senior business analyst at McKinsey & Company. Your goal is to synthesize the analyses from six specialist AI agents into a single, authoritative, and decisive startup feasibility report for a venture capital partner. The report must be insightful, balanced, and immediately actionable.

# INPUT DATA:
You have been provided with the raw JSON outputs from the following specialist agents:
1.  **Market Research Agent:** Competitive landscape, market size, target audience.
2.  **User Persona Agent:** A detailed profile of the ideal target customer.
3.  **Technical Feasibility Agent:** Key technical challenges and a recommended tech stack.
4.  **Finance Agent:** Estimated costs and potential revenue streams.
5.  **Risk Agent:** A ranked list of business risks with their severity.
6.  **Critic Agent:** A sharp, critical insight identifying the single biggest flaw or blind spot.

**Startup Idea:** "{startup_idea}"
**Full Agent Data:** 
{json.dumps(analysis_context, indent=2)}

# OUTPUT INSTRUCTIONS:
- **FORMAT:** Write the report in clean, professional Markdown.
- **STRUCTURE:** You MUST use the following exact section headers. Weave the information from the agents into a compelling narrative under each section. Do not just list the agent outputs.
- **TONE:** Be direct, analytical, and concise. Avoid fluff and marketing language. The reader is a busy VC.
- **CRITICAL SYNTHESIS:** The most important part is the "Critical Assessment" and "Overall Verdict". The critic's point must be highlighted as the central strategic challenge. The verdict must be a definitive conclusion based on the totality of the evidence.

# REPORT STRUCTURE:

# Startup Feasibility Report: {startup_idea}

## 1. Executive Summary & Target Customer
Begin with a one-paragraph summary of the idea and its potential. Then, introduce the user persona. Tell the story of the target customer, their pain points, and how this idea solves their problem. Make it relatable.

## 2. Market Analysis
Summarize the market opportunity. Who are the key competitors? How large is the market? Is it growing? Is the target audience well-defined and reachable? Synthesize this into a clear picture of the competitive landscape.

## 3. Technical Assessment
What are the most significant technical hurdles? Is the suggested technology stack appropriate and feasible for a startup? Assess the complexity and potential bottlenecks in development.

## 4. Financial Projections
Present the high-level financial outlook. What are the estimated costs to build an MVP and operate monthly? What are the proposed revenue models? Are these estimates realistic given the market and technical challenges?

## 5. Risk Analysis
List the top 3-4 most severe risks, ordered by their "severity" (High, Medium, Low). For each, provide a one-sentence explanation. This should be a quick, scannable list of the biggest dangers.

## 6. Critical Assessment
This is the most important section. Present the critique from the specialist agent. Frame it as the "biggest question" or "most significant hurdle" that must be answered for this venture to succeed. Do not soften the criticism.

## 7. Overall Verdict
Provide a final, one-paragraph verdict. Weigh the market opportunity against the risks and the critical flaw. State clearly whether the idea is **Viable**, **Viable with Significant Risk**, or **Not Viable** based on the preponderance of evidence. Your conclusion must be unambiguous.
"""
    
    try:
        response = generate_text(prompt)
        final_report = response.text.strip()
        return final_report
    except Exception as e:
        print(f"An error occurred during final synthesis: {e}")
        return f"Error: Failed to generate the final report. Details: {e}"