# ...existing code...
from .base_agent import BaseAgent
from core.clients import gemini_model
from typing import Dict, Any, List
import json
import re

class RiskAgent(BaseAgent):
    """
    RiskAgent analyzes market research + idea context and returns a structured
    risk assessment (risks, likelihood, impact, mitigations, overall score).
    Expects market_research_data produced by MarketResearchAgent.
    """
    def run(self, market_research_data: Dict[str, Any]) -> Dict[str, Any]:
        print("RiskAgent: starting risk assessment")
        try:
            # Build a compact prompt with the provided market research
            mr_json = json.dumps(market_research_data, ensure_ascii=False, indent=2)
            prompt = f"""
You are an experienced startup risk analyst. Given the market research and context below,
produce a structured JSON risk assessment for the startup idea.

Input (market research):
{mr_json}

Output JSON schema:
{{
  "summary": "short overall assessment",
  "overall_risk_score": 0-100,                 // 0 low risk, 100 very high risk
  "risks": [
    {{
      "id": "technical|market|regulatory|financial|operational|other",
      "title": "short title",
      "description": "concise description of the risk",
      "likelihood": "low|medium|high",
      "impact": "low|medium|high",
      "mitigation": "practical mitigation steps"
    }}
  ],
  "recommendations": ["short practical recommendation strings"]
}}

Return ONLY valid JSON following the schema above.
"""
            response = gemini_model.generate_content(prompt)
            text = getattr(response, "text", "") or str(response)
            parsed = self._clean_and_parse_json_text(text)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed response is not a JSON object")
            # sanitize minimal fields
            parsed.setdefault("summary", "")
            parsed.setdefault("overall_risk_score", 50)
            parsed.setdefault("risks", [])
            parsed.setdefault("recommendations", [])
            print("RiskAgent: completed parsing risk assessment")
            return parsed
        except Exception as e:
            print(f"RiskAgent error: {e}")
            return self._create_error_response("runtime_error", str(e))

    def _clean_and_parse_json_text(self, text: str) -> Dict[str, Any]:
        """
        Remove markdown/code fences and try to parse the first JSON object found.
        """
        # remove common code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        # try direct parse
        try:
            return json.loads(cleaned)
        except Exception:
            # try to extract a JSON substring
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                candidate = json_match.group(0)
                try:
                    return json.loads(candidate)
                except Exception:
                    pass
            # last resort: raise to be handled by caller
            raise

    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        return {
            "error": {
                "type": error_type,
                "message": error_message
            },
            "summary": "",
            "overall_risk_score": 100,
            "risks": [],
            "recommendations": []
        }
# ...existing code...