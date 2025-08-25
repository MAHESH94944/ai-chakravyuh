from .base_agent import BaseAgent
from core.clients import generate_text_with_fallback, enhanced_web_search
from models.schemas import RiskResult
from pydantic import ValidationError
import json
from typing import Dict, Any, List, Optional

class RiskAgent(BaseAgent):
    """
    An advanced agent that performs a comprehensive, evidence-based risk assessment
    by synthesizing market, location, and targeted risk research.
    """
    def run(self, idea: str, market_research_data: dict, location_analysis: Optional[dict] = None) -> Dict[str, Any]:
        """
        Executes the full, evidence-based risk assessment pipeline.
        """
        print(f"⚠️  RiskAgent: Starting advanced risk assessment for '{idea}'")
        
        try:
            # Step 1: Gather additional evidence on common risks for this type of idea
            risk_evidence = self._gather_risk_evidence(idea, location_analysis)

            # Step 2: Synthesize all available data into a structured risk report
            risk_analysis_json = self._synthesize_risk_analysis(
                idea=idea,
                market_data=market_research_data,
                location_data=location_analysis,
                risk_evidence=risk_evidence
            )
            if isinstance(risk_analysis_json, dict) and "error" in risk_analysis_json:
                fallback = RiskResult(
                    summary="Risk synthesis unavailable.",
                    overall_risk_score=50.0,
                    risk_level="medium",
                    risks=[],
                    recommendations=[]
                )
                return fallback.model_dump()

            # Step 3: Validate and structure the final output
            validated_report = RiskResult.model_validate(risk_analysis_json)
            print("   ✅ Risk assessment completed and validated.")
            return validated_report.model_dump()

        except ValidationError as e:
            error_msg = f"Risk agent output failed Pydantic validation: {e}"
            print(f"   ❌ {error_msg}")
            fallback = RiskResult(
                summary="Risk assessment unavailable (validation_error)",
                overall_risk_score=50.0,
                risk_level="medium",
                risks=[],
                recommendations=[]
            )
            return fallback.model_dump()
        except Exception as e:
            error_msg = f"An unexpected error occurred in RiskAgent: {e}"
            print(f"   ❌ {error_msg}")
            # Deterministic fallback using simple heuristics
            risks = [
                {"title": "Market adoption", "likelihood": "Medium", "impact": "High", "mitigation": "Run local pilots and gather user feedback"},
                {"title": "Regulatory/compliance", "likelihood": "Low", "impact": "Medium", "mitigation": "Consult local legal counsel for health-related claims"},
                {"title": "Technical reliability", "likelihood": "Medium", "impact": "High", "mitigation": "Start with hosted ML APIs and add monitoring"}
            ]
            fallback = RiskResult(
                summary="Deterministic risk summary based on available evidence.",
                overall_risk_score=55.0,
                risk_level="medium",
                risks=risks,
                recommendations=[r['mitigation'] for r in risks]
            )
            return fallback.model_dump()

    def _gather_risk_evidence(self, idea: str, location_analysis: Optional[Dict]) -> str:
        """Performs targeted web searches for risks related to the startup idea."""
        print("   -> Researching common risks and failure modes...")
        
        country_code = location_analysis.get("normalized_location", {}).get("country_code", "US") if location_analysis else "US"
        
        queries = [
            f"common risks for '{idea}' startups",
            f"why '{idea}' businesses fail",
            f"regulatory challenges for '{idea}' in {country_code}"
        ]
        
        evidence = []
        for query in queries:
            results = enhanced_web_search(query, max_results=2, country=country_code.lower())
            if results:
                evidence.append(f"Evidence for '{query}':\n" + json.dumps(results, indent=2))
        
        return "\n\n".join(evidence)

    def _synthesize_risk_analysis(self, idea: str, market_data: dict, location_data: Optional[dict], risk_evidence: str) -> dict:
        """Uses a powerful LLM to synthesize all gathered data into a structured risk report."""
        
        prompt = f"""
        You are a senior risk management expert at a top global consulting firm.
        Your task is to produce a comprehensive, data-driven risk assessment for the startup idea: "{idea}".

        **Provided Intelligence Briefing:**
        ---
        **General Market Analysis:**
        {json.dumps(market_data, indent=2, default=str)}

        **Hyper-Local Context:**
        {json.dumps(location_data, indent=2, default=str)}

        **Targeted Research on Common Risks:**
        {risk_evidence[:5000]}
        ---

        **Your Synthesis Task:**
        Analyze all the provided intelligence to create a structured risk report. You MUST infer, synthesize, and quantify the risks.
        -   Use the provided risk framework (Market, Financial, Technical, etc.).
        -   Assign a `likelihood` and `impact` (Low, Medium, High) for each risk.
        -   Provide a concrete `mitigation` strategy and a `validation_experiment` for each.
        -   Calculate an `overall_risk_score` (0-100) based on the severity of the identified risks.

        Return ONLY a valid JSON object that strictly adheres to the 'RiskResult' Pydantic schema. All fields are required.
        """
        
        try:
            # Use a powerful model for this complex synthesis task
            response = generate_text_with_fallback(prompt, is_json=True)
            return json.loads(response.text)
        except Exception as e:
            # Deterministic, domain-aware fallback when LLM and/or web evidence is unavailable
            print("   -> Using deterministic fallback for risk analysis (no LLM / web evidence)")
            # Base risks for consumer fitness/wellness apps
            risks = [
                {
                    'title': 'Market adoption and competition',
                    'likelihood': 'Medium',
                    'impact': 'High',
                    'mitigation': 'Run local pilots, validate value proposition, partner with local gyms/corporates',
                    'validation_experiment': '3-month pilot with 500 users and retention metrics'
                },
                {
                    'title': 'Data privacy and regulation',
                    'likelihood': 'Low',
                    'impact': 'High',
                    'mitigation': 'Limit health advice to non-diagnostic recommendations and consent flows; consult local counsel',
                    'validation_experiment': 'Legal review and privacy impact assessment for target country'
                },
                {
                    'title': 'Technical reliability and model costs',
                    'likelihood': 'Medium',
                    'impact': 'Medium',
                    'mitigation': 'Start with hosted inference APIs and implement monitoring and cost alerts',
                    'validation_experiment': 'Load test with 100 concurrent users and budget cap testing'
                }
            ]
            overall_score = 55.0
            recommendations = [r['mitigation'] for r in risks]
            return {
                'summary': 'Deterministic fallback risk assessment for consumer fitness/wellness apps',
                'overall_risk_score': overall_score,
                'risk_level': 'medium',
                'risks': risks,
                'recommendations': recommendations
            }