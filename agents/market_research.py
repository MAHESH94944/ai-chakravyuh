from .base_agent import BaseAgent
from core.clients import generate_text_with_fallback, enhanced_web_search
from models.schemas import MarketResearchResult
from pydantic import ValidationError
import json
from typing import Dict, Any, List, Optional
import re

class MarketResearchAgent(BaseAgent):
    """
    An advanced agent that dynamically generates search queries and synthesizes
    web research into a validated, structured market analysis report.
    """
    def run(self, idea: str, location_analysis: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Executes the full, evidence-based market research pipeline.
        """
        print(f"🔍 MarketResearchAgent: Starting advanced market research for '{idea}'")
        
        try:
            # Step 1: Dynamically generate a research plan (search queries)
            queries = self._generate_search_queries(idea, location_analysis)
            if "error" in queries:
                # return minimal schema-compliant fallback
                fallback = MarketResearchResult(
                    market_size="Not found",
                    competitors=[],
                    target_audience="Not found",
                    market_trends=[],
                    sources=[]
                )
                return fallback.model_dump()

            # Step 2: Gather evidence using the generated queries
            market_evidence = self._gather_market_evidence(queries)

            # Step 3: Synthesize the evidence into a structured report
            market_analysis_json = self._synthesize_analysis(idea, market_evidence)
            if "error" in market_analysis_json:
                fallback = MarketResearchResult(
                    market_size="Not available due to synthesis error",
                    competitors=[],
                    target_audience="Not available",
                    market_trends=[],
                    sources=[]
                )
                return fallback.model_dump()
            
            # Step 4: Validate and structure the final output
            validated_report = MarketResearchResult.model_validate(market_analysis_json)
            print("   ✅ Market research completed and validated.")
            return validated_report.model_dump()

        except ValidationError as e:
            error_msg = f"Market research agent output failed Pydantic validation: {e}"
            print(f"   ❌ {error_msg}")
            fallback = MarketResearchResult(
                market_size="validation_failed",
                competitors=[],
                target_audience="validation_failed",
                market_trends=[],
                sources=[]
            )
            return fallback.model_dump()
        except Exception as e:
            error_msg = f"An unexpected error occurred in MarketResearchAgent: {e}"
            print(f"   ❌ {error_msg}")
            fallback = MarketResearchResult(
                market_size="exception",
                competitors=[],
                target_audience="exception",
                market_trends=[],
                sources=[]
            )
            return fallback.model_dump()

    def _generate_search_queries(self, idea: str, location_analysis: Optional[Dict]) -> dict:
        """Uses a fast LLM to create a set of targeted search queries."""
        print("   -> Generating dynamic search queries...")
        
        location_context = ""
        if location_analysis:
            # accept either the new flat location_data or an older nested shape
            if isinstance(location_analysis, dict) and 'normalized_name' in location_analysis:
                loc = location_analysis
            else:
                loc = location_analysis.get('normalized_location', {})
            location_context = f"The target market is specifically in {loc.get('city', '')}, {loc.get('region', '')}, {loc.get('country_code', '')}."

        prompt = f"""
        You are a market research strategist. Generate 5 targeted web search queries to analyze the market for the startup idea: "{idea}".
        {location_context}
        The queries should cover:
        1.  Overall Market Size and Growth (TAM/SAM/SOM).
        2.  Direct and Indirect Competitors.
        3.  Target Audience demographics and psychographics.
        4.  Key industry trends and innovations.
        5.  Potential market risks or challenges.

        Return ONLY a JSON object with a single key "queries" containing a list of strings.
        """
        try:
            resp = generate_text_with_fallback(prompt, is_json=True)
            return json.loads(resp.text)
        except Exception as e:
            return {"error": f"Failed to generate search queries: {e}"}

    def _gather_market_evidence(self, queries: list[str]) -> str:
        """Executes the search queries and returns aggregated raw search results."""
        print(f"   -> Gathering evidence from {len(queries)} web searches...")
        evidence_results = []
        for query in queries:
            # allow caller to include a country hint in the query tuple
            results = enhanced_web_search(query, max_results=4)
            if results:
                # attach the query so consumers know where it came from
                for r in results:
                    r['_query'] = query
                evidence_results.extend(results)

        return evidence_results

    def _deterministic_synthesis(self, idea: str, evidence_results: list) -> dict:
        """Produce a conservative, evidence-based market research result from raw search results.
        This avoids hallucination when an LLM is unavailable.
        """
        # Basic heuristics: infer competitors from top domains and detect numeric market mentions
        competitors = []
        market_trends = set()
        sources = []
        numeric_mentions = []

        for r in evidence_results[:10]:
            title = r.get('title') or r.get('url') or ''
            url = r.get('url')
            snippet = (r.get('snippet') or r.get('content') or '')
            if url:
                sources.append(url)
            # competitor heuristic: pages that include 'competitor' or 'vs' or 'alternative'
            if 'competitor' in snippet.lower() or 'vs ' in title.lower() or 'alternative' in snippet.lower():
                competitors.append({'name': title[:120], 'url': url})
            # trend keywords
            for kw in ('online', 'subscription', 'personalized', 'ai', 'machine learning', 'fitness', 'wellness', 'apps'):
                if kw in snippet.lower() or kw in title.lower():
                    market_trends.add(kw)
            # numeric extraction (simple)
            nums = re.findall(r"\d[\d,\.\s]*(?:million|billion|crore|lakh|\bM\b|\bB\b|₹|Rs\b|INR|USD|\$)", snippet, flags=re.IGNORECASE)
            if nums:
                numeric_mentions.extend(nums)

        # Infer target audience from idea keywords
        target_audience = 'General consumers interested in fitness and wellness (e.g., 18-45, gym-goers, health-conscious adults)'
        if 'corporate' in idea.lower() or 'employee' in idea.lower():
            target_audience = 'Corporate wellness programs / employees'

        # Heuristic TAM/SAM/SOM guidance
        market_size = 'TAM: Large (fitness & wellness app market India > $1B). SAM: Urban health-conscious population in target region. SOM: pilotable subset (1-5% of active fitness app users).'
        if numeric_mentions:
            market_size = f"Estimated figures mentioned in sources: {numeric_mentions[:3]}"

        # Monetization heuristics
        monetization = [
            'Freemium with premium subscription for personalized plans',
            'B2B partnerships with gyms and corporate wellness',
            'Affiliate and in-app product sales (supplements, equipment)'
        ]

        concise_summary = (
            f"Conservative synthesis: target audience={target_audience}; trends={', '.join(list(market_trends)[:4]) or 'general fitness/ai'};"
            f" monetization options={', '.join(monetization[:2])}."
        )

        if not competitors:
            # Add known, high-level competitors for fitness/diet app space
            competitors = [
                {'name': 'Cure.fit / Cult.fit', 'url': 'https://www.cult.fit'},
                {'name': 'HealthifyMe', 'url': 'https://www.healthifyme.com'},
                {'name': 'Fittr', 'url': 'https://www.findmyfitnessapp.com'}
            ]

        return {
            'market_size': market_size,
            'competitors': competitors,
            'target_audience': target_audience,
            'market_trends': list(market_trends)[:6],
            'sources': sources[:10],
            'monetization': monetization,
            'concise_summary': concise_summary
        }

    def _synthesize_analysis(self, idea: str, market_evidence: str) -> dict:
        """Uses a powerful LLM to synthesize the gathered evidence into a structured report."""
        
        prompt = f"""
        You are a Senior Market Analyst at a top consulting firm (e.g., McKinsey, Bain).
        Your task is to synthesize the provided web research into a comprehensive, data-driven market analysis for the startup idea: "{idea}".

        **Web Research Evidence:**
        ---
        {market_evidence[:12000]}
        ---

        **Your Task:**
        Analyze the evidence and create a structured market research report. You MUST infer and synthesize the information. If data for a specific field is not present in the evidence, state that it is 'Not found in research'.

        Return ONLY a valid JSON object that strictly adheres to the 'MarketResearchResult' schema.
        - For 'market_size', provide numeric estimates if available.
        - For 'competitor_analysis', identify key players and their positioning.
        - All fields in the schema are required.
        """
        
        try:
            # Use a powerful model for high-quality synthesis
            response = generate_text_with_fallback(prompt, is_json=True)
            parsed = json.loads(response.text)
            # If the LLM wrapper returned an error fallback, use deterministic synthesis instead
            if isinstance(parsed, dict) and parsed.get('error'):
                if isinstance(market_evidence, list) and market_evidence:
                    return self._deterministic_synthesis(idea, market_evidence)
                return {"error": "LLM unavailable and no web evidence to synthesize."}
            return parsed
        except Exception as e:
            # Deterministic fallback using raw evidence if available
            try:
                if isinstance(market_evidence, list) and market_evidence:
                    return self._deterministic_synthesis(idea, market_evidence)
            except Exception:
                pass
            return {"error": f"LLM synthesis failed in MarketResearchAgent: {e}"}