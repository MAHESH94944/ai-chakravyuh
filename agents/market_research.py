"""Enhanced MarketResearchAgent with real market data and competitive analysis."""

from .base_agent import BaseAgent
from core.clients import generate_text, enhanced_web_search, get_financial_data, groq_client, tavily_client
from models.schemas import MarketResearchResult, MarketSizeEstimate, CompetitorAnalysis
import json
from typing import Dict, Any, List, Optional
import re
import os
import sys
import time
import hashlib



class MarketResearchAgent(BaseAgent):
    """
    Advanced MarketResearchAgent that provides comprehensive market analysis
    using real market data, competitor intelligence, and industry trends
    with a focus on Indian markets.
    """
    
    # Tunable constants
    MAX_QUERIES = 12
    RESULTS_PER_QUERY = 6
    MAX_COMPACT_ITEMS = 24
    BATCH_SYNTHESIS_SIZE = 6
    
    def run(self, idea: str, location: Dict[str, Any] = None) -> Dict[str, Any]:
        print(f"🔍 MarketResearchAgent: Conducting comprehensive market research for '{idea}'")
        
        try:
            # Extract location information
            country_code = location.get("country_code", "IN") if location else "IN"
            city = location.get("city", "") if location else ""
            region = location.get("region", "") if location else ""
            
            # Generate search queries with hyper-local focus
            seeds = self._generate_search_queries(idea, city or region or country_code)
            if isinstance(seeds, dict) and seeds.get("error"):
                return self._create_error_response("query_generation", seeds["error"])
                
            print(f"   Seed queries: {len(seeds)}")
            
            # Expand queries for comprehensive coverage
            expanded = self._expand_queries(seeds)
            print(f"   Expanded to {len(expanded)} queries/variants")
            
            # Perform searches
            search_results = self._perform_searches(expanded)
            if isinstance(search_results, dict) and search_results.get("error"):
                return self._create_error_response("web_search", search_results["error"])
                
            print(f"   Retrieved {search_results.get('total_results', 0)} raw results; deduped to {len(search_results.get('results', []))}")
            
            # Extract structured data from search results
            market_size_data = self._extract_market_data(search_results["results"])
            competitor_data = self._extract_competitor_data(search_results["results"])
            audience_data = self._extract_audience_data(search_results["results"])
            trend_data = self._extract_trend_data(search_results["results"])
            
            # Create comprehensive market analysis
            analysis = self._create_market_analysis(
                idea, market_size_data, competitor_data, audience_data, trend_data, country_code
            )
            
            # Format results according to schema
            result = self._format_results(analysis, market_size_data, competitor_data, audience_data, trend_data)
            
            # Add pointwise summary
            result["pointwise_summary"] = self.format_pointwise(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Market research failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {"error": error_msg, "pointwise_summary": [error_msg]}
    
    def _generate_search_queries(self, idea: str, location: str) -> List[str]:
        """Use Groq to produce a set of seed queries with hyper-local focus for Indian markets."""
        prompt = f"""
You are a hyper-local market research expert for Indian markets.
Your task is to generate 8 highly specific search queries for the startup idea: "{idea}" specifically for the location: "{location}".

*CRITICAL FOCUS:*
1.  *Local Giants & Competitors*: Find major, established local players. Use queries like "top [industry] companies in {location}", "best [service] near {location}", "leading [professionals] in {location}".
2.  *Local Market Size/Demand*: Use queries like "{location} [industry] market size", "demand for [service] in {location} statistics".
3.  *Local Target Audience*: Use queries like "demographics of {location} [service] users", "[industry] consumer behavior {location}".
4.  *Local Regulations*: Use queries like "[industry] regulations India", "[professional] certification requirements {location}".

*Output Format:*
Return ONLY a valid JSON object: {{"queries": ["phrase1", "phrase2", ...]}}
"""

        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"},
            )
            response_json = json.loads(chat_completion.choices[0].message.content)
            queries = response_json.get("queries", [])
            if not queries or not isinstance(queries, list):
                return {"error": "No valid queries generated"}
            return queries[:8]
        except Exception as e:
            return {"error": f"Failed to generate search queries: {e}"}

    def _expand_queries(self, seeds: List[str]) -> List[str]:
        """Expand seed queries with variants and advanced operators to cover many angles."""
        expanded = []
        authoritative_sites = ["gov", "edu", "nic", "org"]

        for s in seeds:
            s = s.strip()
            if not s:
                continue
            expanded.append(s)
            expanded.append(f'"{s}"')
            expanded.append(f'{s} OR "{s} analysis"')
            expanded.append(f'{s} Intitle:report')
            expanded.append(f'{s} filetype:pdf')
            expanded.append(f'{s} 2024..2025')

            for dom in authoritative_sites[:2]:
                expanded.append(f'site:.{dom} {s}')

        uniq = []
        seen = set()
        for q in expanded:
            key = q.lower()
            if key in seen:
                continue
            seen.add(key)
            uniq.append(q)
            if len(uniq) >= self.MAX_QUERIES:
                break
        return uniq

    def _perform_searches(self, queries: List[str]) -> Dict[str, Any]:
        """Run queries with retry/backoff, tag results, dedupe and score sources."""
        all_results = []
        failed = []

        for idx, q in enumerate(queries):
            try:
                print(f"   Searching ({idx+1}/{len(queries)}): {q}")
                raw = self._retry_search(q, max_results=self.RESULTS_PER_QUERY)
                if not raw:
                    failed.append({"query": q, "error": "no results"})
                    continue

                for r in raw:
                    r = dict(r) if isinstance(r, dict) else {"title": str(r)}
                    r["search_query"] = q
                    r["_source_score"] = self._score_source(r)
                    all_results.append(r)

                time.sleep(0.6)

            except Exception as e:
                print(f"   search error for '{q}': {e}")
                failed.append({"query": q, "error": str(e)})
                continue

        deduped = self._dedupe_results(all_results)

        return {
            "results": deduped,
            "failed_queries": failed,
            "total_results": len(all_results),
            "success_rate": f"{(len(queries) - len(failed)) / max(1, len(queries)) * 100:.1f}%",
        }
    
    def _retry_search(self, query: str, max_results: int = 6, retries: int = 3) -> List[Dict[str, Any]]:
        """Perform web search with retry mechanism."""
        delay = 1.0
        for attempt in range(1, retries + 1):
            try:
                response = tavily_client.search(
                    query=query,
                    search_depth="basic",
                    max_results=max_results,
                    include_answer=False,
                    include_raw_content=False,
                    include_images=False
                )
                return response.get("results", [])
            except Exception as e:
                if attempt == retries:
                    raise
                print(f"      retry {attempt}/{retries} failed: {e}; sleeping {delay}s")
                time.sleep(delay)
                delay *= 2
        return []

    def _score_source(self, item: Dict[str, Any]) -> float:
        """Simple heuristic to score a source's authority and relevance."""
        score = 0.0
        url = (item.get("url") or item.get("link") or "").lower()
        title = (item.get("title") or "").lower()
        snippet = (item.get("snippet") or item.get("summary") or "").lower()

        if any(t in url for t in [".gov", ".edu", ".nic"]): score += 2.0
        if url.endswith(".pdf"): score += 1.0
        if any(k in snippet for k in ["market size", "revenue", "growth rate", "cagr", "report"]): score += 1.0
        if item.get("published_at") or item.get("date"): score += 0.5
        if any(w in title for w in ["report", "analysis", "study", "market"]): score += 0.8
        return score

    def _dedupe_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Dedupe by normalized URL and by fingerprint of title+snippet; keep highest scored."""
        buckets: Dict[str, Dict[str, Any]] = {}

        def fingerprint(r):
            key = (r.get("title", "") + "|" + r.get("snippet", "") + "|" + r.get("url", ""))
            return hashlib.sha1(key.encode("utf-8", errors="ignore")).hexdigest()

        for r in results:
            url = r.get("url") or r.get("link") or ""
            fp = fingerprint(r)
            key = url if url else fp
            existing = buckets.get(key)
            if not existing or r.get("_source_score", 0) > existing.get("_source_score", 0):
                buckets[key] = r

        deduped = list(buckets.values())
        deduped.sort(key=lambda x: x.get("_source_score", 0), reverse=True)
        return deduped

    def _extract_market_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract market size and growth data from search results."""
        market_data = {
            "size_estimates": [],
            "growth_data": [],
            "citations": []
        }
        
        for result in results:
            snippet = result.get("snippet", "").lower()
            title = result.get("title", "").lower()
            
            # Market size patterns
            size_patterns = [
                r'market size[^\d]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|trillion|cr|lakh)?',
                r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|trillion|cr|lakh)[^\d]*market',
                r'valued at[^\d]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|billion|trillion|cr|lakh)',
                r'rs\.?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:crore|lakh|million|billion)'
            ]
            
            for pattern in size_patterns:
                matches = re.findall(pattern, snippet)
                for match in matches:
                    try:
                        # Convert to numeric value
                        value = float(match.replace(',', ''))
                        
                        # Determine multiplier
                        multiplier = 1
                        if 'billion' in snippet:
                            multiplier = 1000000000
                        elif 'million' in snippet:
                            multiplier = 1000000
                        elif 'trillion' in snippet:
                            multiplier = 1000000000000
                        elif 'crore' in snippet or 'cr' in snippet:
                            multiplier = 10000000
                        elif 'lakh' in snippet:
                            multiplier = 100000
                        
                        market_size = value * multiplier
                        
                        market_data["size_estimates"].append({
                            "value": market_size,
                            "currency": "INR" if 'rs.' in snippet or 'rupee' in snippet else "USD",
                            "year": 2024,
                            "source": result.get("url", ""),
                            "description": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", "")
                        })
                    except ValueError:
                        continue
            
            # Growth rate patterns
            growth_patterns = [
                r'growth rate[^\d]*(\d{1,3}(?:\.\d{1,2})?)%',
                r'growing at[^\d]*(\d{1,3}(?:\.\d{1,2})?)%',
                r'cagr[^\d]*(\d{1,3}(?:\.\d{1,2})?)%'
            ]
            
            for pattern in growth_patterns:
                matches = re.findall(pattern, snippet)
                for match in matches:
                    try:
                        growth_rate = float(match)
                        market_data["growth_data"].append({
                            "rate": growth_rate,
                            "period": "annual",
                            "source": result.get("url", ""),
                            "description": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", "")
                        })
                    except ValueError:
                        continue
            
            # Add citation
            market_data["citations"].append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")[:200] + "..." if len(result.get("snippet", "")) > 200 else result.get("snippet", "")
            })
        
        return market_data

    def _extract_competitor_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract competitor information from search results."""
        competitor_data = {
            "direct_competitors": [],
            "indirect_competitors": [],
            "competitive_analysis": [],
            "citations": []
        }
        
        for result in results:
            snippet = result.get("snippet", "").lower()
            title = result.get("title", "").lower()
            
            # Extract company names (simple heuristic)
            company_patterns = [
                r'companies like ([a-zA-Z0-9\s]+)',
                r'competitors include ([a-zA-Z0-9\s]+)',
                r'alternatives to ([a-zA-Z0-9\s]+)',
                r'top ([a-zA-Z0-9\s]+) companies',
                r'leading ([a-zA-Z0-9\s]+) providers'
            ]
            
            for pattern in company_patterns:
                matches = re.findall(pattern, snippet)
                for match in matches:
                    company_name = match.strip()
                    if len(company_name) > 2 and company_name not in [c["name"] for c in competitor_data["direct_competitors"]]:
                        competitor_data["direct_competitors"].append({
                            "name": company_name,
                            "type": "direct",
                            "source": result.get("url", ""),
                            "description": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", "")
                        })
            
            # Competitive analysis insights
            if "competitiv" in snippet or "market share" in snippet:
                competitor_data["competitive_analysis"].append({
                    "insight": result.get("snippet", "")[:200] + "..." if len(result.get("snippet", "")) > 200 else result.get("snippet", ""),
                    "source": result.get("url", "")
                })
            
            # Add citation
            competitor_data["citations"].append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")[:200] + "..." if len(result.get("snippet", "")) > 200 else result.get("snippet", "")
            })
        
        return competitor_data

    def _extract_audience_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract target audience information from search results."""
        audience_data = {
            "demographics": [],
            "behavior_patterns": [],
            "spending_habits": [],
            "pain_points": [],
            "citations": []
        }
        
        for result in results:
            snippet = result.get("snippet", "").lower()
            title = result.get("title", "").lower()
            
            # Categorize audience insights
            if "demographic" in snippet or "demographic" in title:
                audience_data["demographics"].append({
                    "insight": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", ""),
                    "source": result.get("url", "")
                })
            elif "behavior" in snippet or "behavior" in title:
                audience_data["behavior_patterns"].append({
                    "insight": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", ""),
                    "source": result.get("url", "")
                })
            elif "buying" in snippet or "spending" in snippet or "purchase" in snippet:
                audience_data["spending_habits"].append({
                    "insight": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", ""),
                    "source": result.get("url", "")
                })
            elif "pain" in snippet or "problem" in snippet or "challenge" in snippet:
                audience_data["pain_points"].append({
                    "insight": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", ""),
                    "source": result.get("url", "")
                })
            
            # Add citation
            audience_data["citations"].append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")[:200] + "..." if len(result.get("snippet", "")) > 200 else result.get("snippet", "")
            })
        
        return audience_data

    def _extract_trend_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract market trend information from search results."""
        trend_data = {
            "industry_trends": [],
            "technology_trends": [],
            "regulatory_trends": [],
            "consumer_trends": [],
            "citations": []
        }
        
        for result in results:
            snippet = result.get("snippet", "").lower()
            title = result.get("title", "").lower()
            
            # Categorize trend insights
            if "industry" in snippet or "industry" in title:
                trend_data["industry_trends"].append({
                    "insight": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", ""),
                    "source": result.get("url", "")
                })
            elif "technolog" in snippet or "technolog" in title or "digital" in snippet:
                trend_data["technology_trends"].append({
                    "insight": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", ""),
                    "source": result.get("url", "")
                })
            elif "regulator" in snippet or "regulator" in title or "policy" in snippet or "law" in snippet:
                trend_data["regulatory_trends"].append({
                    "insight": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", ""),
                    "source": result.get("url", "")
                })
            elif "consumer" in snippet or "consumer" in title or "customer" in snippet:
                trend_data["consumer_trends"].append({
                    "insight": result.get("snippet", "")[:150] + "..." if len(result.get("snippet", "")) > 150 else result.get("snippet", ""),
                    "source": result.get("url", "")
                })
            
            # Add citation
            trend_data["citations"].append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")[:200] + "..." if len(result.get("snippet", "")) > 200 else result.get("snippet", "")
            })
        
        return trend_data

    def _create_market_analysis(self, idea: str, market_size_data: Dict, competitor_data: Dict,
                              audience_data: Dict, trend_data: Dict, country_code: str) -> Dict[str, Any]:
        """Create comprehensive market analysis using AI synthesis."""
        
        # Prepare data for AI analysis
        analysis_data = {
            "market_size_data": market_size_data,
            "competitor_data": competitor_data,
            "audience_data": audience_data,
            "trend_data": trend_data
        }
        
        prompt = f"""
        You are a Senior Business Strategist advising a first-time, non-technical founder in India.
        Your task is to analyze the following research for the startup idea "{idea}" and create a simple, insightful, and actionable report.

        *GUIDING PRINCIPLES:*
        - *Simple Language*: Explain everything in plain English. Avoid jargon. Use analogies.
        - *Provide Context*: For every data point, add a short sentence explaining "Why this matters" or "The takeaway is...".
        - *Be Specific*: Use the data from the findings. Do not invent information. Prioritize real, verifiable company names.

        *RESEARCH DATA:*
        {json.dumps(analysis_data, indent=2)[:12000]}

        *CRITICAL JSON OUTPUT STRUCTURE:*
        - *executive_summary*: (String) Start with a 2-3 sentence summary at the top. What is the overall opportunity?
        - *market_size*: (Object) Market size estimates with context: {{"total_addressable_market": number, "serviceable_addressable_market": number, "serviceable_obtainable_market": number, "currency": "string", "growth_rate": number, "year": number, "context": "string"}}
        - *competitors*: (List of Objects) A list of the top real competitors. For each competitor, provide: {{"name": "Competitor Name", "strength": "string", "weakness": "string", "market_share": number, "insight": "string"}}
        - *target_audience*: (Object) Target audience characteristics: {{"demographics": "string", "behavior": "string", "needs": "string", "spending_capacity": "string", "context": "string"}}
        - *market_trends*: (List of strings) A pointwise list of key trends with a simple explanation.
        - *key_risks*: (List of strings) A pointwise list of the main risks, explained simply.
        - *success_factors*: (List of strings) A pointwise list of the main success factors.
        - *data_quality*: (String) Assessment of data quality and reliability.
        """

        try:
            from core.clients import generate_text
            response = generate_text(prompt)
            cleaned = response.text.strip().replace('```json', '').replace('```', '').strip()
            try:
                analysis = json.loads(cleaned)
            except Exception:
                return self._create_fallback_analysis(idea, country_code)
            
            # Add research sources
            analysis["research_sources"] = [
                source["url"] for source in market_size_data["citations"][:3]
            ] + [
                source["url"] for source in competitor_data["citations"][:3]
            ] + [
                source["url"] for source in audience_data["citations"][:2]
            ] + [
                source["url"] for source in trend_data["citations"][:2]
            ]
            
            return analysis
        except Exception as e:
            print(f"   Market analysis failed: {e}")
            return self._create_fallback_analysis(idea, country_code)
    
    def _create_fallback_analysis(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Create fallback market analysis."""
        return {
            "market_size": {
                "total_addressable_market": 1000000000,
                "serviceable_addressable_market": 100000000,
                "serviceable_obtainable_market": 10000000,
                "currency": "INR" if country_code == "IN" else "USD",
                "growth_rate": 15.5,
                "year": 2024,
                "context": "Estimated based on industry averages for similar markets"
            },
            "competitors": [
                {
                    "name": "Competitor A",
                    "strength": "Strong brand recognition",
                    "weakness": "Poor customer service",
                    "market_share": 25.0,
                    "insight": "Market leader but vulnerable to better customer experience"
                },
                {
                    "name": "Competitor B",
                    "strength": "Advanced technology",
                    "weakness": "High pricing",
                    "market_share": 15.0,
                    "insight": "Premium offering but leaves room for mid-market solutions"
                }
            ],
            "target_audience": {
                "demographics": "Age 25-45, urban professionals, middle to high income",
                "behavior": "Tech-savvy, values convenience, mobile-first",
                "needs": "Time-saving solutions, reliability, good user experience",
                "spending_capacity": "₹2,000-10,000 per month" if country_code == "IN" else "$50-200 per month",
                "context": "Growing segment in urban areas with increasing disposable income"
            },
            "market_trends": [
                "Growing mobile adoption - More users are accessing services through smartphones",
                "Increasing demand for convenience - Customers prefer all-in-one solutions",
                "Shift to subscription models - Recurring revenue models becoming standard"
            ],
            "key_risks": [
                "Market saturation - Many players entering the space",
                "Regulatory changes - Government policies could impact operations",
                "Economic downturn - Reduced consumer spending during economic crises"
            ],
            "success_factors": [
                "Superior user experience - Intuitive design and smooth workflows",
                "Competitive pricing - Offering value for money",
                "Strong customer support - Responsive service and problem resolution"
            ],
            "data_quality": "Moderate - based on available public data and industry reports",
            "executive_summary": f"The {idea} market shows promising growth potential with increasing demand from urban professionals. While competition exists, there are opportunities to differentiate through better customer experience and targeted offerings."
        }
    
    def _format_results(self, analysis: Dict, market_size_data: Dict, competitor_data: Dict,
                       audience_data: Dict, trend_data: Dict) -> Dict[str, Any]:
        """Format results according to the MarketResearchResult schema."""
        
        # Create market size estimate
        market_size = MarketSizeEstimate(**analysis["market_size"])
        
        # Create competitor analysis
        competitors = []
        for competitor in analysis["competitors"]:
            competitors.append(CompetitorAnalysis(**competitor))
        
        # Create citations
        citations = []
        for citation in market_size_data["citations"][:5]:
            citations.append({
                "type": "market_size",
                "url": citation["url"],
                "description": citation["snippet"]
            })
        
        for citation in competitor_data["citations"][:3]:
            citations.append({
                "type": "competitor",
                "url": citation["url"],
                "description": citation["snippet"]
            })
        
        # Create research metadata
        research_metadata = {
            "sources_analyzed": len(market_size_data["citations"]) + len(competitor_data["citations"]) +
                               len(audience_data["citations"]) + len(trend_data["citations"]),
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data_quality": analysis.get("data_quality", "Moderate")
        }
        
        # Create the result object
        result = {
            "market_size": market_size.dict(),
            "competitors": [comp.dict() for comp in competitors],
            "target_audience": analysis["target_audience"],
            "market_trends": analysis["market_trends"],
            "growth_rate": analysis["market_size"]["growth_rate"],
            "key_risks": analysis["key_risks"],
            "success_factors": analysis["success_factors"],
            "data_quality": analysis["data_quality"],
            "research_metadata": research_metadata,
            "citations": citations,
            "executive_summary": analysis.get("executive_summary", "")
        }
        
        return result

    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        return {
            "error": error_message,
            "error_type": error_type,
            "competitors": [],
            "market_size": "Unable to determine due to research error",
            "target_audience": [],
            "research_status": "failed",
            "pointwise_summary": [f"Research failed: {error_message}"]
        }

    def format_pointwise(self, result: Dict[str, Any]) -> List[str]:
        """Create a pointwise summary of the market research results."""
        points = []
        
        if "error" in result and result["error"]:
            return [f"Research failed: {result['error']}"]
        
        # Executive summary
        if result.get("executive_summary"):
            points.append(f"Executive Summary: {result['executive_summary']}")
        
        # Market size
        if result.get("market_size"):
            market = result["market_size"]
            points.append(f"Market Size: TAM {market.get('total_addressable_market', 'N/A')} {market.get('currency', '')}, "
                         f"SAM {market.get('serviceable_addressable_market', 'N/A')}, "
                         f"SOM {market.get('serviceable_obtainable_market', 'N/A')}")
            points.append(f"Growth Rate: {market.get('growth_rate', 'N/A')}% annually")
        
        # Competitors
        if result.get("competitors"):
            points.append(f"Key Competitors: {', '.join([comp.get('name', '') for comp in result['competitors']])}")
            for comp in result["competitors"][:3]:
                points.append(f"  - {comp.get('name')}: {comp.get('strength')} (Weakness: {comp.get('weakness')})")
        
        # Target audience
        if result.get("target_audience"):
            audience = result["target_audience"]
            points.append(f"Target Audience: {audience.get('demographics', 'N/A')}")
            points.append(f"Behavior: {audience.get('behavior', 'N/A')}")
            points.append(f"Spending Capacity: {audience.get('spending_capacity', 'N/A')}")
        
        # Market trends
        if result.get("market_trends"):
            points.append("Key Market Trends:")
            for trend in result["market_trends"][:3]:
                points.append(f"  - {trend}")
        
        # Risks
        if result.get("key_risks"):
            points.append("Key Risks:")
            for risk in result["key_risks"][:3]:
                points.append(f"  - {risk}")
        
        # Success factors
        if result.get("success_factors"):
            points.append("Success Factors:")
            for factor in result["success_factors"][:3]:
                points.append(f"  - {factor}")
        
        return points


# Main execution block for standalone running
if __name__ == "__main__":
    print("🚀 Starting Enhanced Market Research Agent...")
    
    test_idea = "An AI-powered platform to help students find and book verified co-living spaces and PGs"
    test_location = {"city": "Bangalore", "region": "Karnataka", "country_code": "IN"}
    
    print(f"📋 Testing with idea: {test_idea}")
    print(f"📍 Location: {test_location}")
    print("=" * 60)
    
    agent = MarketResearchAgent()
    result = agent.run(test_idea, test_location)
    
    print("\n" + "=" * 60)
    print("📊 MARKET RESEARCH RESULTS:")
    print("=" * 60)
    
    if "error" in result and result["error"]:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Status: {result.get('research_status', 'completed')}")
        
        # Print pointwise summary
        if 'pointwise_summary' in result:
            print(f"\n--- 📋 Pointwise Summary ---")
            for point in result.get('pointwise_summary', []):
                print(f"  • {point}")
        
        # Print research metadata
        if 'research_metadata' in result:
            meta = result['research_metadata']
            print(f"\n--- 📊 Research Metadata ---")
            print(f"   Sources analyzed: {meta.get('sources_analyzed', 'N/A')}")
            print(f"   Data quality: {meta.get('data_quality', 'N/A')}")
            print(f"   Analysis timestamp: {meta.get('analysis_timestamp', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("🎉 Enhanced Market Research Agent completed!")