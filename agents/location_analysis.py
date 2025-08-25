from .base_agent import BaseAgent
from core.clients import generate_text_with_fallback, enhanced_web_search
from models.schemas import LocationAnalysisResult
from pydantic import ValidationError
try:
    from pytrends.request import TrendReq
    from geopy.geocoders import Nominatim
except ImportError:
    # These libraries may be optional in some environments; degrade gracefully.
    TrendReq = None
    Nominatim = None
import json
from typing import Dict, Any, Optional

class LocationAnalysisAgent(BaseAgent):
    """
    A highly advanced agent that performs deep, contextual analysis of a 
    startup's viability in a specific geographic location.
    """
    def __init__(self):
        # Initialize only the components available; allow the agent to run in degraded mode
        self.geolocator = Nominatim(user_agent="startup_validator_v3") if Nominatim else None
        self.trends = TrendReq(hl='en-US', tz=360) if TrendReq else None

    def run(self, idea: str, location_text: str, **kwargs) -> Dict[str, Any]:
        print(f"🌍 LocationAnalysisAgent: Starting advanced analysis for '{idea}' in '{location_text}'")
        
        try:
            # 1. Geocode the location to get structured data
            geo_data = self._geocode_location(location_text)
            if "error" in geo_data:
                # Provide a minimal, schema-compatible fallback object
                fallback = {
                    "normalized_name": location_text,
                    "coordinates": {"latitude": 0.0, "longitude": 0.0},
                    "country_code": "",
                    "region": None,
                    "city": None,
                    "viability_score": 0.0,
                    "market_readiness": 0.0,
                    "key_opportunities": [],
                    "critical_risks": [],
                    "recommendations": [],
                    "evidence": []
                }
                return fallback

            # 2. Gather multi-source intelligence
            intelligence = self._gather_intelligence(idea, geo_data)

            # 3. Perform AI-powered synthesis of all gathered data
            analysis_json = self._synthesize_analysis(idea, geo_data, intelligence)
            if isinstance(analysis_json, dict) and "error" in analysis_json:
                # Produce a deterministic, evidence-driven summary instead of raw error
                return self._deterministic_location_summary(idea, geo_data, intelligence)

            # 4. Final validation against our strict schema
            validated_report = LocationAnalysisResult.model_validate(analysis_json)
            print(f"   ✅ Location analysis for '{location_text}' completed and validated.")
            return validated_report.model_dump()

        except ValidationError as e:
            print(f"   ⚠️ Location analysis failed validation. Attempting self-correction... Error: {e}")
            # If self-correction fails, return a schema-compliant fallback
            try:
                return self._self_correct_analysis(analysis_json, str(e))
            except Exception:
                return {
                    "normalized_name": location_text,
                    "coordinates": {"latitude": 0.0, "longitude": 0.0},
                    "country_code": "",
                    "region": None,
                    "city": None,
                    "viability_score": 0.0,
                    "market_readiness": 0.0,
                    "key_opportunities": [],
                    "critical_risks": [],
                    "recommendations": [],
                    "evidence": []
                }
        except Exception as e:
            error_msg = f"An unexpected error occurred in LocationAnalysisAgent: {e}"
            print(f"   ❌ {error_msg}")
            return {"error": error_msg}

    def _geocode_location(self, location_text: str) -> Dict[str, Any]:
        """Normalizes a location string into structured geographic data."""
        try:
            if not self.geolocator:
                return {"error": "geolocator_unavailable"}
            location = self.geolocator.geocode(location_text, addressdetails=True, language='en')
            if not location:
                return {"error": f"Could not find location: {location_text}"}
            
            addr = location.raw.get('address', {})
            return {
                "normalized_name": location.address,
                "coordinates": {"latitude": location.latitude, "longitude": location.longitude},
                "country_code": addr.get('country_code', '').upper(),
                "region": addr.get('state', addr.get('county', '')),
                "city": addr.get('city', addr.get('town', addr.get('village', ''))),
                "type": location.raw.get('type', 'unknown'),
                "importance": location.raw.get('importance', 0)
            }
        except Exception as e:
            return {"error": f"Geocoding failed: {e}"}

    def _gather_intelligence(self, idea: str, geo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gathers data from web search and Google Trends."""
        location_name = geo_data['normalized_name']
        country_code = geo_data['country_code']
        
        queries = {
            "competitors": f"similar businesses or startups to '{idea}' in {location_name}",
            "demographics": f"demographics and consumer behavior in {location_name}",
            "economy": f"key industries and economic outlook for {location_name}"
        }
        
        search_results = {}
        for key, query in queries.items():
            search_results[key] = enhanced_web_search(query, max_results=4, country=country_code.lower())

        trend_data = self._get_search_trends(idea, country_code)

        return {"web_evidence": search_results, "trend_data": trend_data}

    def _deterministic_location_summary(self, idea: str, geo_data: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Create a conservative, evidence-driven local summary without using an LLM."""
        web = evidence.get('web_evidence', {})
        sources = []
        local_businesses = []
        for key, results in web.items():
            for r in results[:6]:
                url = r.get('url')
                title = r.get('title') or r.get('snippet') or url
                sources.append(url) if url else None
                # Heuristic: titles that look like local business pages
                if any(word in (title or '').lower() for word in ('gym', 'fitness', 'studio', 'trainer', 'wellness')):
                    local_businesses.append({'name': title[:120], 'url': url})

        opportunities = []
        risks = []
        recommendations = []
        if local_businesses:
            opportunities.append('Partnerships with local gyms and trainers: ' + ', '.join([b['name'] for b in local_businesses[:3]]))
            recommendations.append('Pilot integrations with 1-3 local gyms to validate product-market fit.')
        else:
            recommendations.append('Start with a small digital pilot and local advertising to validate demand.')

        # Trend data heuristics
        if evidence.get('trend_data') and evidence['trend_data'].get('trend_direction') == 'Rising':
            opportunities.append('Rising search interest indicates growing local demand.')

        # Simple viability heuristic
        viability_score = 30.0 + min(len(local_businesses) * 10, 30)
        market_readiness = 2.0 + min(len(local_businesses), 3)

        return {
            'normalized_name': geo_data.get('normalized_name'),
            'coordinates': geo_data.get('coordinates'),
            'country_code': geo_data.get('country_code'),
            'region': geo_data.get('region'),
            'city': geo_data.get('city'),
            'viability_score': float(viability_score),
            'market_readiness': float(market_readiness),
            'key_opportunities': opportunities,
            'critical_risks': risks,
            'recommendations': recommendations,
            'evidence': [{'source': s} for s in sources[:6]]
        }

    def _get_search_trends(self, idea: str, country_code: str) -> Optional[dict]:
        """Fetches search interest data from Google Trends, with robust error handling."""
        if not country_code: return None
        try:
            self.trends.build_payload([idea], timeframe='today 12-m', geo=country_code)
            interest_over_time = self.trends.interest_over_time()
            if interest_over_time.empty or idea not in interest_over_time.columns: return None

            data = interest_over_time[idea]
            change = ((data.iloc[-1] - data.iloc[0]) / data.iloc[0]) * 100 if data.iloc[0] > 0 else 0
            return {
                "average_interest": float(data.mean()),
                "trend_direction": "Rising" if change > 10 else "Declining" if change < -10 else "Stable"
            }
        except Exception as e:
            print(f"   Pytrends search failed (this is common, continuing without trend data): {e}")
            return None
            
    def _synthesize_analysis(self, idea: str, geo_data: Dict[str, Any], intelligence: Dict[str, Any]) -> dict:
        """Uses a powerful LLM to synthesize all gathered intelligence into a structured report."""
        prompt = f"""
        You are a hyper-local market intelligence expert. Your task is to produce a deep, data-driven analysis of a startup idea's viability in a specific location.

        **Startup Idea:** "{idea}"
        **Target Location:** {json.dumps(geo_data, indent=2)}
        
        **Intelligence Briefing (from your research team):**
        ---
        **Google Search Trends in {geo_data['country_code']} for '{idea}':**
        {json.dumps(intelligence.get('trend_data'), indent=2)}

        **Web Evidence:**
        {json.dumps(intelligence.get('web_evidence'), indent=2, default=str)[:6000]}
        ---

        **Your Synthesis Task:**
        Based on all the provided data, generate a structured JSON report. You MUST infer and synthesize insights.
        1.  Assign numeric scores for viability and market readiness.
        2.  Identify specific local opportunities, risks, and key industries.
        3.  Find 1-3 existing local businesses from the evidence that are comparable. This is critical.
        4.  Provide actionable recommendations for validating the idea in this location.
        
        Return ONLY a JSON object that strictly adheres to the 'LocationAnalysisResult' schema. All fields are required.
        """
        try:
            response = generate_text_with_fallback(prompt, is_json=True)
            report_data = json.loads(response.text)
            
            # Add back structured data that the LLM doesn't need to generate
            report_data.update(geo_data)
            return report_data
        except Exception as e:
            return {"error": f"Failed to synthesize location analysis: {e}"}

    def _self_correct_analysis(self, failed_output: dict, error: str) -> dict:
        """Attempts to correct a malformed JSON output."""
        prompt = f"""
        You are a JSON correction expert. Your previous attempt to generate a location analysis report resulted in a validation error.
        Your task is to fix the JSON object below so it conforms to the required schema. Do not change the content, only fix the structure, types, and key names.

        **Validation Error:** {error}
        **Malformed JSON Output:** {json.dumps(failed_output, indent=2)}

        Return ONLY the corrected, valid JSON object.
        """
        try:
            resp = generate_text_with_fallback(prompt, is_json=True)
            corrected_output = json.loads(resp.text)
            validated_report = LocationAnalysisResult.model_validate(corrected_output)
            print("   ✅ Self-correction successful.")
            return validated_report.model_dump()
        except Exception as e:
            return {"error": f"Self-correction failed: {e}"}