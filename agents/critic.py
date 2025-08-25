from .base_agent import BaseAgent
from core.clients import generate_text_with_fallback, enhanced_web_search
from models.schemas import CriticResult
from pydantic import ValidationError
import json
from typing import Dict, Any, List, Optional

class CriticAgent(BaseAgent):
    """
    An advanced, evidence-based agent that provides a deep critical analysis by
    identifying blind spots, contradictions, and validation requirements.
    """
    def run(self, idea: str, finance_data: Dict, risk_data: Dict, tech_data: Dict, 
            market_data: Dict, location_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Executes the full critical analysis pipeline.
        """
        print(f"🎯 CriticAgent: Starting critical analysis for '{idea}'")
        
        try:
            # 1. Perform targeted research based on the initial analysis
            failure_evidence = self._research_common_failures(idea, risk_data)
            
            # 2. Synthesize all information into a critical analysis
            critique_json = self._synthesize_critique(
                idea=idea,
                finance_data=finance_data,
                risk_data=risk_data,
                tech_data=tech_data,
                market_data=market_data,
                location_data=location_data,
                failure_evidence=failure_evidence
            )
            if isinstance(critique_json, dict) and "error" in critique_json:
                fallback = CriticResult(
                    critique="Critic unavailable due to synthesis error.",
                    blind_spots=[],
                    contradictory_findings=[],
                    validation_questions=[]
                )
                return fallback.model_dump()

            # 3. Validate and structure the final output
            validated_critique = CriticResult.model_validate(critique_json)
            print("   ✅ Critic analysis completed and validated.")
            return validated_critique.model_dump()

        except ValidationError as e:
            error_msg = f"Critic agent output failed Pydantic validation: {e}"
            print(f"   ❌ {error_msg}")
            fallback = CriticResult(
                critique="Could not generate critic report due to validation error.",
                blind_spots=[],
                contradictory_findings=[],
                validation_questions=[]
            )
            return fallback.model_dump()
        except Exception as e:
            error_msg = f"An unexpected error occurred in CriticAgent: {e}"
            print(f"   ❌ {error_msg}")
            fallback = CriticResult(
                critique=f"Critic generation failed: {str(e)}",
                blind_spots=[],
                contradictory_findings=[],
                validation_questions=[]
            )
            return fallback.model_dump()

    def _research_common_failures(self, idea: str, risk_data: dict) -> str:
        """
        Performs targeted web searches for failure modes related to the identified risks.
        """
        top_risk_titles = [r.get('title', '') for r in risk_data.get('risks', [])[:2]]
        if not top_risk_titles:
            return "No specific risks were provided to research."

        print(f"   -> Researching failure modes related to risks: {top_risk_titles}")
        queries = [f"why startups fail due to '{risk_title}' for '{idea}'" for risk_title in top_risk_titles]
        
        evidence = []
        for query in queries:
            results = enhanced_web_search(query, max_results=2)
            evidence.extend(results)
        
        return json.dumps(evidence, indent=2)

    def _synthesize_critique(self, **kwargs) -> dict:
        """
        Uses an LLM to generate the final critical analysis based on all available data.
        """
        # Unpack all context for the prompt
        idea = kwargs.get('idea')
        finance_data = kwargs.get('finance_data')
        risk_data = kwargs.get('risk_data')
        tech_data = kwargs.get('tech_data')
        market_data = kwargs.get('market_data')
        location_data = kwargs.get('location_data')
        failure_evidence = kwargs.get('failure_evidence')

        prompt = f"""
        You are a Principal at a Venture Capital firm with a 'Red Team' mindset. Your job is to be brutally honest and find the fatal flaws in a startup plan before investment.

        **ANALYST REPORTS (INPUT):**
        ---
        **Idea:** {idea}
        **Location Analysis:** {json.dumps(location_data, indent=2, default=str)}
        **Market Analysis:** {json.dumps(market_data, indent=2, default=str)}
        **Technical Feasibility:** {json.dumps(tech_data, indent=2, default=str)}
        **Financial Outlook:** {json.dumps(finance_data, indent=2, default=str)}
        **Risk Assessment:** {json.dumps(risk_data, indent=2, default=str)}
        ---

        **FAILURE MODE RESEARCH (ADDITIONAL EVIDENCE):**
        ---
        {failure_evidence[:4000]}
        ---

        **YOUR TASK:**
        Synthesize ALL the information above to produce a final critical assessment.
        1.  **Critique:** Write a sharp, concise paragraph identifying the single most critical flaw.
        2.  **Blind Spots:** List 2-3 unstated assumptions or overlooked areas.
        3.  **Contradictory Findings:** Find contradictions between the reports (e.g., 'Tech report shows high complexity, but Finance report shows low dev costs').
        4.  **Validation Questions:** List the top 3-4 tough questions the founders MUST answer.
        5.  **Confidence Score:** Provide your confidence (0-100) in this critical assessment.

        Return ONLY a JSON object that strictly adheres to the 'CriticResult' schema.
        """
        
        try:
            response = generate_text_with_fallback(prompt, is_json=True)
            return json.loads(response.text)
        except Exception as e:
            return {"error": f"LLM synthesis failed in CriticAgent: {e}"}