from .base_agent import BaseAgent
from core.clients import gemini_model
from models.schemas import FinanceResult
import json
import time
from typing import Dict, Any


def _call_gemini(prompt: str, retries: int = 2, delay: float = 1.0) -> str:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = gemini_model.generate_content(prompt)
            text = getattr(resp, "text", None) or str(resp)
            return text
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(delay * attempt)
            else:
                raise
    raise last_err


class FinanceAgent(BaseAgent):
    """
    Advanced FinanceAgent: produces TAM/SAM/SOM, unit economics (CAC/LTV), 3-year
    revenue projections, cost breakdowns, runway/funding needs, and KPI suggestions.
    """

    def run(self, idea: str, market_research_data: Dict[str, Any]) -> Dict[str, Any]:
        print(f"💰 FinanceAgent: generating financial outlook for '{idea}'")

        prompt = f"""
        You are a senior startup financial analyst and VC. Use the market research data to produce a detailed financial model and practical recommendations.

        INPUT:
        Idea: {idea}
        Market research (JSON):
        {json.dumps(market_research_data, indent=2)[:6000]}

        OUTPUT: Return a strict JSON object containing at least the following keys:
        - estimated_costs: object with initial_development (number or string), monthly_operations (breakdown object), one_time_capex
        - tam_sam_som: object with numeric estimates and short source explanation
        - unit_economics: object with assumed ARPU, CAC, LTV, payback_period
        - revenue_projections: list of objects for years 1..3 with revenue and assumptions
        - funding_needs: suggested funding amount and runway months
        - break_even_month: estimated month (integer) to break even
        - potential_revenue_streams: list of strings
        - kpis: list of key metrics to track
        - sensitivity: short scenarios (best/likely/worst)
        - confidence_score: 0-100 integer

        Be realistic and conservative. When numeric estimates are provided, include units and assumptions. Return valid JSON only.
        """

        try:
            raw = _call_gemini(prompt, retries=2)
            cleaned = raw.strip().replace('```json', '').replace('```', '').strip()
            try:
                parsed = json.loads(cleaned)
            except Exception:
                # ask model to reformat into strict JSON
                repair_prompt = f"""
                The following output needs to be reformatted into strict JSON that matches the required keys.

                INPUT:
                {cleaned[:8000]}

                Return only the JSON.
                """
                repair_raw = _call_gemini(repair_prompt, retries=1)
                repair_text = repair_raw.strip().replace('```json', '').replace('```', '').strip()
                parsed = json.loads(repair_text)

            if not isinstance(parsed, dict):
                return {"error": "Model returned non-object JSON"}

            # Validate using Pydantic model (this will extract the main fields we expect)
            try:
                fr = FinanceResult.parse_obj(parsed)
                out = fr.dict()
                # attach additional fields if present
                for k, v in parsed.items():
                    if k not in out:
                        out[k] = v
                return out
            except Exception as ve:
                # attempt a targeted repair to produce required keys
                repair_prompt = f"""
                Reformat the analysis into strict JSON that contains at minimum: estimated_costs (with initial_development and monthly_operations), potential_revenue_streams (list).

                INPUT:
                {json.dumps(parsed, indent=2)[:8000]}

                Return only the JSON.
                """
                repair_raw = _call_gemini(repair_prompt, retries=1)
                repair_text = repair_raw.strip().replace('```json', '').replace('```', '').strip()
                repaired = json.loads(repair_text)
                fr = FinanceResult.parse_obj(repaired)
                out = fr.dict()
                out["repaired"] = True
                # attach other repaired keys if present
                for k, v in repaired.items():
                    if k not in out:
                        out[k] = v
                return out

        except Exception as e:
            print(f"FinanceAgent failed: {e}")
            return {"error": f"Finance analysis failed: {e}"}
