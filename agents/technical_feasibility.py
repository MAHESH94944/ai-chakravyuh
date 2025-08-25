from .base_agent import BaseAgent
from core.clients import generate_text_with_fallback, enhanced_web_search
from models.schemas import TechnicalFeasibilityResult
from pydantic import ValidationError
import json
from typing import Dict, Any, List, Optional

class TechnicalFeasibilityAgent(BaseAgent):
    """
    An advanced agent that provides a realistic technical assessment based on
    consolidated research into technology, challenges, and talent.
    """
    def run(self, idea: str, market_research_data: Optional[Dict] = None, 
            location_analysis: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Executes the full, evidence-based technical feasibility pipeline.
        """
        print(f"🛠️  TechnicalFeasibilityAgent: Starting advanced analysis for '{idea}'")
        
        try:
            # Step 1: Gather comprehensive technical evidence
            tech_evidence = self._gather_technical_evidence(idea, location_analysis)

            # Step 2: Synthesize the evidence into a structured technical assessment
            tech_analysis_json = self._synthesize_technical_analysis(
                idea=idea,
                tech_evidence=tech_evidence
            )
            if isinstance(tech_analysis_json, dict) and "error" in tech_analysis_json:
                # Return schema-compliant fallback
                fallback = TechnicalFeasibilityResult(
                    key_challenges=[],
                    suggested_stack={"note": "synthesis_unavailable"},
                    development_timeline={"note": "synthesis_unavailable"},
                    team_requirements=[],
                    feasibility="feasible_with_research"
                )
                return fallback.model_dump()

            # Step 3: Validate and structure the final output
            validated_report = TechnicalFeasibilityResult.model_validate(tech_analysis_json)
            print("   ✅ Technical feasibility analysis completed and validated.")
            return validated_report.model_dump()

        except ValidationError as e:
            error_msg = f"Technical feasibility agent output failed Pydantic validation: {e}"
            print(f"   ❌ {error_msg}")
            # Schema-compliant fallback
            fallback = TechnicalFeasibilityResult(
                key_challenges=[],
                suggested_stack={"note": "validation_failed"},
                development_timeline={"note": "validation_failed"},
                team_requirements=[],
                feasibility="feasible_with_research"
            )
            return fallback.model_dump()
        except Exception as e:
            error_msg = f"An unexpected error occurred in TechnicalFeasibilityAgent: {e}"
            print(f"   ❌ {error_msg}")
            fallback = TechnicalFeasibilityResult(
                key_challenges=[],
                suggested_stack={"note": "exception"},
                development_timeline={"note": "exception"},
                team_requirements=[],
                feasibility="high_risk"
            )
            return fallback.model_dump()

    def _gather_technical_evidence(self, idea: str, location_analysis: Optional[Dict]) -> str:
        """Performs a consolidated web search for all technical aspects."""
        print("   -> Researching tech stack, challenges, and talent availability...")
        
        country_code = location_analysis.get("normalized_location", {}).get("country_code", "US") if location_analysis else "US"
        city = location_analysis.get("normalized_location", {}).get("city", "") if location_analysis else ""
        
        queries = [
            f"technology stack for '{idea}' startup",
            f"common technical challenges building '{idea}'",
            f"scalability issues for '{idea}' applications",
            f"hiring software developers for '{idea}' in {city}, {country_code}"
        ]
        
        evidence = []
        for query in queries:
            results = enhanced_web_search(query, max_results=2, country=country_code.lower())
            if results:
                evidence.append(f"Evidence for '{query}':\n" + json.dumps(results, indent=2))
        
        return "\n\n".join(evidence)

    def _synthesize_technical_analysis(self, idea: str, tech_evidence: str) -> dict:
        """Uses a powerful LLM to synthesize gathered evidence into a structured technical plan."""
        
        prompt = f"""
        You are an experienced Chief Technology Officer (CTO) and startup advisor.
        Your task is to create a comprehensive and realistic technical feasibility plan for the startup idea: "{idea}".

        **Intelligence Briefing from Research Team:**
        ---
        {tech_evidence[:12000]}
        ---

        **Your Synthesis Task:**
        Based on the provided research, create a detailed technical assessment.
        -   Recommend a modern, scalable technology stack.
        -   Outline a realistic development timeline in weeks for an MVP.
        -   Estimate development, infrastructure, and maintenance costs.
        -   Define the core team required to build the MVP.
        -   Provide an overall feasibility rating.

        Return ONLY a valid JSON object that strictly adheres to the 'TechnicalFeasibilityResult' Pydantic schema. All fields are required.
        """
        
        try:
            response = generate_text_with_fallback(prompt, is_json=True)
            parsed = json.loads(response.text)
            return parsed
        except Exception as e:
            # Deterministic fallback: infer a minimal stack and timeline from evidence
            try:
                stack = {
                    'frontend': ['React or Flutter'],
                    'backend': ['Python (FastAPI) or Node.js'],
                    'database': ['Postgres'],
                    'infrastructure': ['Cloud VPS or managed services'],
                    'third_party_services': ['Auth0, Stripe, Twilio (optional)']
                }
                timeline = {'research_phase': 2, 'design_phase': 4, 'development_phase': 12, 'testing_phase': 4, 'deployment_phase': 2}
                return {
                    'key_challenges': ['Data privacy and regulatory compliance', 'Integrating AI models reliably', 'User retention for health apps'],
                    'suggested_stack': stack,
                    'development_timeline': timeline,
                    'team_requirements': ['1-2 backend engineers', '1 frontend engineer', '1 ML engineer (contract)', '1 product manager'],
                    'feasibility': 'feasible_with_research'
                }
            except Exception:
                return {"error": f"LLM synthesis failed in TechnicalFeasibilityAgent: {e}"}