from .base_agent import BaseAgent
from core.clients import (
    generate_text_with_fallback, 
    enhanced_web_search, 
    get_proxy_company_financials
)
from models.schemas import FinanceResult
from pydantic import ValidationError
import json
from typing import Dict, Any, List, Optional

class FinanceAgent(BaseAgent):
    """
    A highly advanced agent that builds a financial model grounded in the
    real-world financial performance of comparable public companies ("proxies")
    and localized cost data.
    """
    def run(self, idea: str, market_research_data: dict, location_analysis: Optional[dict] = None) -> Dict[str, Any]:
        """
        Executes the full, evidence-based financial analysis pipeline.
        """
        print(f"💰 FinanceAgent: Starting advanced proxy-based financial analysis for '{idea}'")
        
        try:
            country_code = location_analysis.get("country_code") if location_analysis and isinstance(location_analysis, dict) else (location_analysis.get("normalized_location", {}).get("country_code", "US") if location_analysis else "US")
            city = location_analysis.get("city", "") if location_analysis and isinstance(location_analysis, dict) else (location_analysis.get("normalized_location", {}).get("city", "") if location_analysis else "")
            currency = "INR" if (country_code or "").upper() == "IN" else "USD"

            # 1. Identify and gather financial data from proxy companies
            proxy_financials = self._get_proxy_financial_evidence(idea)
            if not proxy_financials:
                # If no proxy data, return a minimal, schema-compliant fallback with heuristics
                # Heuristic estimates for an early-stage fitness app (seed MVP)
                # If India, scale estimates to INR heuristic levels
                if currency == 'INR':
                    initial_dev = {"estimate": 2000000, "currency": currency, "notes": "MVP dev + basic integration (INR heuristic)"}
                    monthly_ops = {"estimate": 120000, "currency": currency, "notes": "hosting, basic support, marketing (INR heuristic)"}
                else:
                    initial_dev = {"estimate": 25000, "currency": currency, "notes": "MVP dev + basic integration"}
                    monthly_ops = {"estimate": 3000, "currency": currency, "notes": "hosting, basic support, marketing"}
                revenue_proj = {"y1": {"month_12_revenue": 5000, "notes": "conservative early revenue"}}
                concise = f"Heuristic estimates: initial_dev={initial_dev['estimate']} {initial_dev['currency']}, monthly_ops~{monthly_ops['estimate']} {monthly_ops['currency']}"
                fallback = FinanceResult(
                    initial_development=initial_dev,
                    monthly_operations=monthly_ops,
                    revenue_projections_year_1=revenue_proj,
                    key_financial_ratios={"gross_margin_pct": "unknown", "burn_rate_months": "unknown"},
                    assumptions=["Estimates are heuristics; replace with real quotes and local costs"],
                    data_sources=[]
                )
                out = fallback.model_dump()
                out['concise_summary'] = concise
                return out

            # 2. Gather localized cost evidence via web search
            local_cost_evidence = self._gather_local_cost_evidence(idea, city, country_code)

            # 3. Synthesize all evidence into a financial model
            financial_model_json = self._synthesize_financial_model(
                idea=idea,
                currency=currency,
                proxy_financials=proxy_financials,
                local_cost_evidence=local_cost_evidence
            )
            if "error" in financial_model_json:
                # Create schema-compliant fallback using available partial evidence
                fallback = FinanceResult(
                    initial_development={"note": "synthesis_error"},
                    monthly_operations={"note": "synthesis_error"},
                    revenue_projections_year_1={"note": "synthesis_error"},
                    key_financial_ratios={"note": "synthesis_error"},
                    assumptions=[str(financial_model_json.get("error"))],
                    data_sources=[]
                )
                return fallback.model_dump()

            # 4. Validate and structure the final output
            validated_model = FinanceResult.model_validate(financial_model_json)
            print("   ✅ Financial model completed and validated.")
            return validated_model.model_dump()

        except ValidationError as e:
            error_msg = f"Finance agent output failed Pydantic validation: {e}"
            print(f"   ❌ {error_msg}")
            fallback = FinanceResult(
                initial_development={"note": "validation_failed"},
                monthly_operations={"note": "validation_failed"},
                revenue_projections_year_1={"note": "validation_failed"},
                key_financial_ratios={"note": "validation_failed"},
                assumptions=[error_msg],
                data_sources=[]
            )
            return fallback.model_dump()
        except Exception as e:
            error_msg = f"An unexpected error occurred in FinanceAgent: {e}"
            print(f"   ❌ {error_msg}")
            fallback = FinanceResult(
                initial_development={"note": "exception"},
                monthly_operations={"note": "exception"},
                revenue_projections_year_1={"note": "exception"},
                key_financial_ratios={"note": "exception"},
                assumptions=[error_msg],
                data_sources=[]
            )
            return fallback.model_dump()

    def _get_proxy_financial_evidence(self, idea: str) -> List[Dict[str, Any]]:
        """Finds and fetches financial data for comparable public companies."""
        print(f"   -> Finding proxy companies for: '{idea}'")
        
        # Use an LLM to find tickers from a targeted web search
        query = f"publicly traded competitors of '{idea}' stock tickers"
        search_results = enhanced_web_search(query, max_results=5)
        search_content = " ".join([r.get('content', '') for r in search_results])

        prompt = f"""
        From the following text, extract up to 3 relevant stock ticker symbols (e.g., 'PYPL', 'SQ', 'ADBE').
        Return ONLY a JSON object with a single key "tickers" which is a list of strings.
        Text: {search_content[:4000]}
        """
        try:
            response = generate_text_with_fallback(prompt, is_json=True)
            tickers = json.loads(response.text).get("tickers", [])
        except Exception:
            tickers = []

        if not tickers:
            print("   -> No proxy tickers found.")
            return []

        print(f"   -> Found tickers: {tickers}. Fetching their financial data.")
        financial_evidence = []
        for ticker in tickers:
            data = get_proxy_company_financials(ticker)
            if data:
                financial_evidence.append(data)
        return financial_evidence

    def _gather_local_cost_evidence(self, idea: str, city: str, country_code: str) -> str:
        """Performs targeted web searches to find evidence for local operational costs."""
        if not city:
            return "No specific city provided for local cost research."

        print(f"   -> Researching local costs in {city}, {country_code}")
        queries = [
            f"average software developer salary {city}",
            f"commercial office rent per square foot {city}",
            f"startup legal costs in {country_code}"
        ]
        evidence = []
        for query in queries:
            results = enhanced_web_search(query, max_results=2, country=country_code.lower())
            if results:
                evidence.append(f"Evidence for '{query}':\n" + json.dumps(results, indent=2))
        
        return "\n\n".join(evidence)

    def _synthesize_financial_model(self, idea: str, currency: str, proxy_financials: List[Dict], local_cost_evidence: str) -> dict:
        """Uses an LLM to generate the final financial model based on all gathered evidence."""
        
        prompt = f"""
        You are a Partner at a top-tier venture capital firm. Your task is to create a realistic, bottom-up financial model for a new startup.
        You MUST use the provided financial data from comparable public companies ("proxies") as your primary benchmark for ratios, and the local cost evidence to ground the absolute numbers.

        **Startup Idea:** "{idea}"
        **Target Currency for all estimates:** {currency}

        **Financial Evidence from Public Proxy Companies:**
        ---
        {json.dumps(proxy_financials, indent=2)}
        ---

        **Local Cost Evidence (Salaries, Rent, etc.):**
        ---
        {local_cost_evidence[:4000]}
        ---

        **Your Task:**
        1.  **Analyze Proxy Ratios:** Calculate the average Gross Margin (%) from the proxies.
        2.  **Build a Seed-Stage Model:** Create a financial model for the new startup. Assume it's a small, early-stage company. Its revenue will be a tiny fraction of the proxies', but its cost structure (like gross margin) should be similar.
        3.  **Localize Absolute Costs:** Use the local cost evidence to make realistic estimates for salaries, rent, and other operational costs.
        4.  **Structure the Output:** Return a single, clean JSON object that strictly adheres to the 'FinanceResult' schema. Your assumptions are critical.

        Return ONLY a valid JSON object.
        """
        
        try:
            response = generate_text_with_fallback(prompt, is_json=True)
            return json.loads(response.text)
        except Exception as e:
            return {"error": f"LLM synthesis failed in FinanceAgent: {e}"}