from .base_agent import BaseAgent
from core.clients import groq_client, generate_text
import time
from tools.web_search import tavily_search
from models.schemas import LocationAnalysisResult
from geopy.geocoders import Nominatim
try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None
from typing import Dict, List, Optional, Any
import time
import json
import re

class LocationAnalysisAgent(BaseAgent):
    """Advanced location intelligence agent with multi-source data fusion."""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="startup_validator_ai_v1")
        # pytrends is optional; if not available, skip trend analysis
        if TrendReq:
            try:
                self.trends = TrendReq(hl='en-US', tz=360)
            except Exception:
                self.trends = None
        else:
            self.trends = None

    def run(self, idea: str, location_text: str, provided_location: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute full location analysis pipeline."""
        print(f"📍 Advanced Location Analysis: '{idea}' in '{location_text}'")
        
        try:
            # 1. Enhanced Location Normalization
            # If caller provided structured location (with lat/lon/country_code), use it preferentially
            geo_data = None
            if provided_location:
                try:
                    lat = provided_location.get('latitude') or provided_location.get('lat')
                    lon = provided_location.get('longitude') or provided_location.get('lon')
                    cc = provided_location.get('country_code') or provided_location.get('country')
                    city = provided_location.get('city')
                    region = provided_location.get('region')
                    if lat and lon:
                        geo_data = {
                            "normalized_name": provided_location.get('text') or provided_location.get('name') or location_text,
                            "latitude": float(lat),
                            "longitude": float(lon),
                            "country_code": (cc or '').upper(),
                            "region": region or '',
                            "city": city or '',
                            "type": "provided",
                            "importance": 1.0
                        }
                except Exception:
                    geo_data = None

            # If not provided or incomplete, try enhanced geocoding (Nominatim)
            if not geo_data:
                geo_data = self._enhanced_geocoding(location_text)
                # If geocoding failed, try the central client fallback
                if isinstance(geo_data, dict) and geo_data.get('error'):
                    try:
                        from core.clients import get_location_data
                        remote = get_location_data(location_text)
                        if remote:
                            geo_data = {
                                "normalized_name": remote.get('name') or location_text,
                                "latitude": remote.get('lat'),
                                "longitude": remote.get('lon'),
                                "country_code": (remote.get('address', {}).get('country_code') or '').upper(),
                                "region": remote.get('address', {}).get('state') or '',
                                "city": remote.get('address', {}).get('city') or remote.get('address', {}).get('town') or '',
                                "type": remote.get('type', ''),
                                "importance": remote.get('importance', 0)
                            }
                    except Exception:
                        pass

            # 2. Multi-source Intelligence Gathering
            intelligence = self._gather_intelligence(idea, geo_data)
            
            # 3. Advanced Analysis & Synthesis
            report = self._advanced_analysis(idea, geo_data, intelligence)
            
            # 4. Validation & Enrichment
            validated = self._validate_and_enrich_report(report, geo_data, intelligence)
            if isinstance(validated, dict):
                validated.setdefault("pointwise_summary", self.format_pointwise(validated))
            return validated
            
        except Exception as e:
            out = {"error": f"Location analysis failed: {str(e)}"}
            out.setdefault("pointwise_summary", self.format_pointwise(out.get("error", "")))
            return out

    def _enhanced_geocoding(self, location_text: str) -> Dict[str, Any]:
        """Get comprehensive location data with fallbacks."""
        try:
            location = self.geolocator.geocode(location_text, addressdetails=True, exactly_one=True)
            if not location:
                return {"error": f"Location '{location_text}' not found"}
            
            address = location.raw.get('address', {})
            return {
                "normalized_name": location.address,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "country_code": address.get('country_code', '').upper(),
                "region": address.get('state', address.get('county', '')),
                "city": address.get('city', address.get('town', address.get('village', ''))),
                "type": location.raw.get('type', ''),
                "importance": location.raw.get('importance', 0)
            }
        except Exception as e:
            return {"error": f"Geocoding failed: {str(e)}"}

    def _gather_intelligence(self, idea: str, geo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect intelligence from multiple sources."""
        intelligence = {
            "search_trends": self._get_search_trends(idea, geo_data.get('country_code')),
            "local_searches": self._perform_comprehensive_searches(idea, geo_data),
            "competitor_scan": self._scan_competitors(idea, geo_data),
            "regulatory_scan": self._scan_regulations(idea, geo_data),
            "talent_scan": self._scan_talent(idea, geo_data)
        }
        return intelligence

    def _get_search_trends(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Get detailed search trend analysis."""
        if not country_code:
            return {"status": "no_country_code", "trend": "Unknown"}
        # If pytrends isn't configured, return a conservative stub so downstream code continues
        if not self.trends:
            return {"status": "no_pytrends", "geo": country_code, "timeframe": "12 months", "avg_interest": 0.0, "max_interest": 0.0, "trend_direction": "insufficient_data", "rising_queries": [], "top_queries": []}

        try:
            # Get related queries for deeper insights
            self.trends.build_payload([idea], timeframe='today 12-m', geo=country_code)

            interest_over_time = self.trends.interest_over_time()
            related_queries = self.trends.related_queries()

            trend_data = {
                "status": "success",
                "geo": country_code,
                "timeframe": "12 months"
            }

            if not interest_over_time.empty:
                data = interest_over_time[idea]
                trend_data.update({
                    "avg_interest": float(data.mean()),
                    "max_interest": float(data.max()),
                    "trend_direction": self._calculate_trend_direction(data),
                    "seasonality": self._detect_seasonality(data)
                })

            if related_queries and idea in related_queries:
                related = related_queries[idea]
                trend_data["rising_queries"] = related['rising'].head(3).to_dict('records') if 'rising' in related else []
                trend_data["top_queries"] = related['top'].head(5).to_dict('records') if 'top' in related else []

            return trend_data

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _perform_comprehensive_searches(self, idea: str, geo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute targeted local searches with query optimization."""
        base_queries = [
            # Market demand queries
            f"demand for {idea} in {geo_data['normalized_name']}",
            f"market size {idea} {geo_data['region']}",
            f"consumer adoption {idea} {geo_data['city']}",
            
            # Competitor queries
            f"competitors {idea} {geo_data['normalized_name']}",
            f"similar startups {geo_data['city']}",
            f"{idea} companies {geo_data['region']}",
            
            # Regulatory queries
            f"regulations {idea} {geo_data['country_code']}",
            f"license requirements {idea} {geo_data['region']}",
            
            # Talent queries
            f"tech talent availability {geo_data['city']}",
            f"developer salaries {geo_data['normalized_name']}",
            
            # Infrastructure queries
            f"internet penetration {geo_data['city']}",
            f"digital payment adoption {geo_data['region']}"
        ]
        
        all_results = []
        for query in base_queries:
            try:
                results = tavily_search(query, max_results=3)
                for result in results:
                    enriched_result = {
                        "query": query,
                        "title": result.get('title', ''),
                        "content": self._clean_content(result.get('content', '')),
                        "url": result.get('url', ''),
                        "source": result.get('source', ''),
                        "relevance_score": self._calculate_relevance(idea, result.get('content', '')),
                        "freshness": result.get('published_date', '')
                    }
                    if enriched_result["relevance_score"] > 0.3:  # Threshold
                        all_results.append(enriched_result)
                time.sleep(0.1)  # Rate limiting
            except Exception:
                continue
        
        # Deduplicate and sort by relevance
        return sorted(all_results, key=lambda x: x["relevance_score"], reverse=True)[:15]

    def _advanced_analysis(self, idea: str, geo_data: Dict[str, Any], intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Perform sophisticated analysis using multiple AI models."""
        
        analysis_prompt = f"""
# MISSION: Location Intelligence Analysis
You are GeoIntelligence AI, an expert analyst specializing in hyper-local startup viability assessment.

## CONTEXT
- Startup Idea: {idea}
- Target Location: {geo_data['normalized_name']} ({geo_data['city']}, {geo_data['region']}, {geo_data['country_code']})
- Location Type: {geo_data.get('type', 'unknown')} (Importance: {geo_data.get('importance', 0)})

## RAW INTELLIGENCE DATA
### Search Trends:
{json.dumps(intelligence['search_trends'], indent=2)}

### Local Market Evidence (Top 10 Most Relevant):
{json.dumps(intelligence['local_searches'][:10], indent=2)}

### Competitor Scan:
{json.dumps(intelligence['competitor_scan'], indent=2)}

### Regulatory Environment:
{json.dumps(intelligence['regulatory_scan'], indent=2)}

### Talent Market:
{json.dumps(intelligence['talent_scan'], indent=2)}

## ANALYSIS TASK
Produce a comprehensive location viability assessment with precise scoring.

### REQUIRED OUTPUT STRUCTURE:
{{
  "viability_score": 0.0,  # 0-100 scale
  "market_readiness": 0.0,  # 0-10 scale
  "competitive_landscape": "string",  # saturated/moderate/emerging
  "key_opportunities": ["string"],
  "critical_risks": ["string"],
  "recommended_approaches": ["string"],
  "timeline_estimate": "string",  # immediate/6-12mo/2+years
  "investment_priority": "string"  # high/medium/low
}}

### ANALYSIS GUIDELINES:
1. Viability Score: Weight 40% search trends, 30% market evidence, 20% competition, 10% regulations
2. Be brutally honest about location-specific constraints
3. Highlight unique local advantages competitors might miss
4. Consider infrastructure limitations realistically
5. Provide actionable, specific recommendations

Return ONLY valid JSON.
"""

        try:
            response = generate_text(analysis_prompt)
            raw_output = response.text.strip()

            # Extract JSON from response (fallback generator returns JSON when asked)
            json_match = re.search(r'\{[\s\S]*\}', raw_output)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "Failed to extract JSON from analysis"}
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def _validate_and_enrich_report(self, analysis: Dict[str, Any], 
                                  geo_data: Dict[str, Any], 
                                  intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Add metadata and validate final report."""
        
        if "error" in analysis:
            return analysis
            
        # Enrich with raw data references
        analysis["metadata"] = {
            "sources_analyzed": len(intelligence['local_searches']),
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "location_data": geo_data,
            "confidence_score": self._calculate_confidence(intelligence)
        }
        
        # Add evidence citations
        analysis["key_evidence"] = [
            {
                "source": item["source"],
                "url": item["url"],
                "insight": item["content"][:200] + "..." if len(item["content"]) > 200 else item["content"]
            }
            for item in intelligence['local_searches'][:3]
        ]
        
        try:
            # Validate against schema
            validated = LocationAnalysisResult.parse_obj(analysis)
            return validated.dict()
        except Exception as e:
            return {"error": f"Validation failed: {str(e)}", "raw_analysis": analysis}

    # --- Helper Methods ---
    
    def _calculate_trend_direction(self, data) -> str:
        """Determine trend direction with statistical significance."""
        if len(data) < 4:
            return "insufficient_data"
            
        first_half = data.iloc[:len(data)//2].mean()
        second_half = data.iloc[len(data)//2:].mean()
        
        change = ((second_half - first_half) / first_half) * 100 if first_half > 0 else 0
        
        if change > 25:
            return "strong_growth"
        elif change > 10:
            return "moderate_growth"
        elif change < -25:
            return "sharp_decline"
        elif change < -10:
            return "moderate_decline"
        else:
            return "stable"

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        # Remove excessive whitespace, truncate intelligently
        content = ' '.join(content.split())
        return content[:1000] + "..." if len(content) > 1000 else content

    def _calculate_relevance(self, idea: str, content: str) -> float:
        """Calculate relevance score between 0-1."""
        idea_terms = set(idea.lower().split())
        content_terms = set(content.lower().split())
        
        if not idea_terms:
            return 0.0
            
        intersection = idea_terms.intersection(content_terms)
        return len(intersection) / len(idea_terms)

    def _calculate_confidence(self, intelligence: Dict[str, Any]) -> float:
        """Calculate overall confidence score."""
        factors = [
            len(intelligence['local_searches']) / 15,  # Max 15 results
            1.0 if intelligence['search_trends']['status'] == 'success' else 0.3,
            min(len(intelligence['competitor_scan']), 10) / 10
        ]
        return round(sum(factors) / len(factors) * 100, 1)

    def _scan_competitors(self, idea: str, geo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan for local competitors."""
        query = f"{idea} companies startups {geo_data['city']} {geo_data['region']}"
        try:
            results = tavily_search(query, max_results=5)
            return [
                {
                    "name": result.get('title', '').split(' - ')[0],
                    "url": result.get('url', ''),
                    "description": result.get('content', '')[:200]
                }
                for result in results
            ]
        except Exception:
            return []

    def _scan_regulations(self, idea: str, geo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan for regulatory information."""
        query = f"regulations license requirements {idea} {geo_data['region']} {geo_data['country_code']}"
        try:
            results = tavily_search(query, max_results=3)
            return [
                {
                    "topic": result.get('title', ''),
                    "summary": result.get('content', '')[:300],
                    "source": result.get('source', '')
                }
                for result in results
            ]
        except Exception:
            return []

    def _scan_talent(self, idea: str, geo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Scan talent availability."""
        query = f"tech talent developers {geo_data['city']} availability salaries"
        try:
            results = tavily_search(query, max_results=2)
            return {
                "summary": " ".join([r.get('content', '') for r in results])[:500],
                "sources": [r.get('source', '') for r in results]
            }
        except Exception:
            return {"summary": "No talent data available"}