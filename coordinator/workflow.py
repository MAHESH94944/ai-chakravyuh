import json
from typing import Optional
from agents.market_research import MarketResearchAgent
from agents.user_persona import UserPersonaAgent
from agents.technical_feasibility import TechnicalFeasibilityAgent
from agents.finance import FinanceAgent
from agents.risk import RiskAgent
from agents.critic import CriticAgent
from core.clients import gemini_model

def run_full_analysis(idea: str, location: Optional[dict] = None) -> dict:
    """
    Orchestrates the entire multi-agent workflow to gather all analyses.
    """
    print("--- Starting Full Analysis Workflow ---")
    
    # --- Step 0: Location analysis (optional) ---
    location_data = None
    if location and location.get("text"):
        try:
            from agents.location_analysis import LocationAnalysisAgent
            location_agent = LocationAnalysisAgent()
            location_data = location_agent.run(idea=idea, location_text=location.get("text"))
            print("--- Location analysis completed ---")
        except Exception as e:
            print(f"Location analysis failed: {e}")
            location_data = {"error": str(e)}
    # --- Step 1: Run initial, parallelizable agents ---
    market_agent = MarketResearchAgent()
    # Pass location context if available (agents can optionally accept it)
    try:
        market_data = market_agent.run(idea=idea, location=location_data)  # MarketResearchAgent may ignore location if not implemented
    except TypeError:
        market_data = market_agent.run(idea=idea)
    if "error" in market_data: return market_data

    tech_agent = TechnicalFeasibilityAgent()
    try:
        tech_data = tech_agent.run(idea=idea, location=location_data)
    except TypeError:
        tech_data = tech_agent.run(idea=idea)
    if "error" in tech_data: return tech_data
    
    persona_agent = UserPersonaAgent()
    try:
        persona_data = persona_agent.run(idea=idea, location=location_data)
    except TypeError:
        persona_data = persona_agent.run(idea=idea)
    if "error" in persona_data: return persona_data

    # --- Step 2: Run agents that depend on initial results ---
    finance_agent = FinanceAgent()
    try:
        finance_data = finance_agent.run(idea=idea, market_research_data=market_data, location=location_data)
    except TypeError:
        finance_data = finance_agent.run(idea=idea, market_research_data=market_data)
    if "error" in finance_data: return finance_data

    risk_agent = RiskAgent()
    try:
        risk_data = risk_agent.run(idea=idea, market_research_data=market_data, location=location_data)
    except TypeError:
        risk_data = risk_agent.run(idea=idea, market_research_data=market_data)
    if "error" in risk_data: return risk_data
    
    # --- Step 3: Run the final critic agent ---
    critic_agent = CriticAgent()
    try:
        critique_data = critic_agent.run(
            idea=idea,
            finance_data=finance_data,
            risk_data=risk_data,
            tech_data=tech_data,
            location=location_data,
        )
    except TypeError:
        critique_data = critic_agent.run(
            idea=idea,
            finance_data=finance_data,
            risk_data=risk_data,
            tech_data=tech_data,
        )
    if "error" in critique_data: return critique_data

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
        response = gemini_model.generate_content(prompt)
        # Clean up the response to ensure it's pure markdown
        final_report = response.text.strip()
        return final_report
    except Exception as e:
        print(f"An error occurred during final synthesis: {e}")
        return f"Error: Failed to generate the final report. Details: {e}"