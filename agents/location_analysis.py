from .base_agent import BaseAgent
from core.clients import groq_client
from tools.web_search import tavily_search
from models.schemas import LocationAnalysisResult
from typing import Optional, Dict, Any, List
import time
import json

try:
    from geopy.geocoders import Nominatim
except Exception:
    Nominatim = None

try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None


class LocationAnalysisAgent(BaseAgent):
    """Advanced, location-aware analysis using geocoding, trends, and web evidence."""

    def __init__(self):
        self.geolocator = Nominatim(user_agent="startup_validator") if Nominatim else None

    def run(self, idea: str, location_text: str) -> Dict[str, Any]:
        print(f"🌍 LocationAnalysisAgent: Starting analysis for '{idea}' in '{location_text}'")

        # 1. Normalize Location
        normalized_location = self._normalize_location(location_text)
        if "error" in normalized_location:
            return normalized_location

        # 2. Get Search Interest Trend
        trend = self._get_search_interest(idea, normalized_location.get("country_code"))

        # 3. Perform Localized Web Search
        queries = self._build_local_queries(idea, normalized_location.get("address") or location_text)
        search_content = self._run_local_searches(queries)

        # 4. Synthesize Final Report
        report = self._synthesize_report(idea, normalized_location.get("address") or location_text, trend, search_content)

        # Add normalized location to the final report and validate
        if isinstance(report, dict) and not report.get("error"):
            report["location"] = normalized_location
            try:
                validated_report = LocationAnalysisResult.parse_obj(report)
                return validated_report.dict()
            except Exception as e:
                return {"error": f"Final validation failed for location report: {e}"}
        return report

    def _normalize_location(self, location_text: str) -> Dict[str, Any]:
        try:
            if self.geolocator:
                location = self.geolocator.geocode(location_text, addressdetails=True)
                if not location:
                    return {"error": f"Could not geocode location: {location_text}"}
                address = location.raw.get("address", {})
                return {
                    "address": location.address,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "country_code": address.get("country_code", "").upper(),
                }
            # Fallback
            return {"address": location_text, "latitude": None, "longitude": None, "country_code": None}
        except Exception as e:
            return {"error": f"Geocoding failed: {e}"}

    def _get_search_interest(self, idea: str, country_code: Optional[str]) -> str:
        if not TrendReq or not country_code:
            return "Not Available"
        try:
            pytrends = TrendReq(hl="en-US", tz=360)
            geo = country_code
            pytrends.build_payload([idea], timeframe="today 12-m", geo=geo)
            df = pytrends.interest_over_time()
            if df.empty:
                return "Stable (low volume)"
            data = df[idea]
            if len(data) < 2:
                return "Stable"
            start_avg = data.iloc[: len(data) // 2].mean()
            end_avg = data.iloc[len(data) // 2 :].mean()
            if end_avg > start_avg * 1.2:
                return "Rising"
            if end_avg < start_avg * 0.8:
                return "Declining"
            return "Stable"
        except Exception as e:
            print(f"   Pytrends search failed: {e}")
            return "Not Available"

    def _build_local_queries(self, idea: str, location: str) -> List[str]:
        return [
            f"{idea} startups in {location}",
            f"consumer behavior {location}",
            f"market trends for {idea} in {location}",
            f"local business regulations {location}",
        ]

    def _run_local_searches(self, queries: List[str]) -> str:
        content = []
        for q in queries:
            try:
                results = tavily_search(q, max_results=4)
                for r in results:
                    # generous: try content, snippet, title
                    content.append(r.get("content") or r.get("snippet") or r.get("title") or "")
            except Exception:
                continue
            time.sleep(0.3)
        return " ".join([c for c in content if c])[:8000]

    def _synthesize_report(self, idea: str, location: str, trend: str, search_content: str) -> Dict[str, Any]:
        prompt = f"""
        As a local business analyst, create a structured report on the viability of the startup idea '{idea}' in '{location}'.

        Context:
        - Local Google Search Trend for '{idea}': {trend}
        - Web Search Results (compacted): {search_content}

        Your Task:
        Provide a JSON object with keys: local_need_score (0-10), local_need_reasoning, local_competitors (list), cultural_fit_score (0-10), cultural_fit_reasoning, search_interest_trend.
        Return only JSON.
        """
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.1,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            return {"error": f"Failed to synthesize local report: {e}"}
