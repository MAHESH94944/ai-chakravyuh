from .base_agent import BaseAgent
from core.clients import groq_client
from tools.web_search import tavily_search
import json
from typing import List, Dict, Any
import time

class MarketResearchAgent(BaseAgent):
    """
    A robust agent that performs comprehensive market research using web search.
    """
    
    def run(self, idea: str) -> dict:
        """
        Executes comprehensive market research for the given startup idea.
        
        Args:
            idea: The startup idea to research
            
        Returns:
            Dictionary containing competitors, market_size, target_audience, trends, and risks
        """
        print(f"🔍 MarketResearchAgent: Starting comprehensive research for '{idea}'")
        
        try:
            # Step 1: Generate diverse search queries
            queries = self._generate_search_queries(idea)
            if "error" in queries:
                return self._create_error_response("query_generation", str(queries.get("error", "Unknown error")))
            
            print(f"   Generated {len(queries)} search queries: {queries}")

            # Step 2: Execute web searches with retry logic
            search_results = self._perform_searches(queries)
            if "error" in search_results:
                return self._create_error_response("web_search", search_results["error"])

            print(f"   Retrieved {len(search_results.get('results', []))} search results")

            # Step 3: Synthesize comprehensive results
            report = self._synthesize_results(idea, search_results)
            
            if "error" in report:
                return self._create_error_response("synthesis", report["error"])
            
            print(f"   ✅ Research completed successfully")
            return report
            
        except Exception as e:
            error_msg = f"Unexpected error in MarketResearchAgent: {str(e)}"
            print(f"   ❌ {error_msg}")
            return self._create_error_response("unexpected", error_msg)

    def _generate_search_queries(self, idea: str) -> List[str]:
        """Generate diverse search queries covering multiple market research aspects."""
        prompt = f"""
        As an expert market research analyst, generate 5-7 comprehensive search queries for the startup idea: "{idea}"

        Generate queries that cover:
        1. Direct and indirect competitors
        2. Market size, growth rate, and industry trends
        3. Target audience demographics and psychographics
        4. Industry reports and market analysis
        5. Regulatory environment and barriers to entry
        6. Customer pain points and unmet needs
        7. Pricing models and revenue streams in this space

        Return ONLY a JSON object with this structure:
        {{
            "queries": [
                "competitors for [specific aspect]",
                "market size [industry] 2024",
                "target audience for [product type]",
                ...
            ]
        }}
        """
        
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",  # Use larger model for better query generation
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            
            response_json = json.loads(chat_completion.choices[0].message.content)
            queries = response_json.get("queries", [])
            
            # Validate we have queries
            if not queries or not isinstance(queries, list):
                return {"error": "No valid queries generated"}
                
            return queries[:7]  # Limit to 7 queries max
            
        except Exception as e:
            return {"error": f"Failed to generate search queries: {e}"}

    def _perform_searches(self, queries: List[str]) -> Dict[str, Any]:
        """Execute web searches with retry logic and comprehensive result gathering."""
        all_results = []
        failed_queries = []
        
        for i, query in enumerate(queries):
            try:
                print(f"   Searching: '{query}' ({i+1}/{len(queries)})")
                results = tavily_search(query, max_results=5)  # Get more results per query
                
                if results and isinstance(results, list):
                    for result in results:
                        result['search_query'] = query  # Tag which query produced this result
                    all_results.extend(results)
                
                # Add delay to avoid rate limiting
                if i < len(queries) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"   Failed search for '{query}': {e}")
                failed_queries.append({"query": query, "error": str(e)})
                continue
        
        return {
            "results": all_results,
            "failed_queries": failed_queries,
            "total_results": len(all_results),
            "success_rate": f"{(len(queries) - len(failed_queries)) / len(queries) * 100:.1f}%"
        }

    def _synthesize_results(self, idea: str, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize search results into a comprehensive market research report."""
        if not search_data.get("results"):
            return {"error": "No search results available for synthesis"}
        # To avoid exceeding model token limits, compress search results:
        # keep only key fields (title/snippet/url/query) and limit count.
        raw_results = search_data.get("results", [])
        max_items = min(20, len(raw_results))
        compact = []
        for r in raw_results[:max_items]:
            compact.append({
                "title": r.get("title") or r.get("headline") or r.get("name") or "",
                "snippet": r.get("snippet") or r.get("summary") or r.get("description") or "",
                "url": r.get("url") or r.get("link") or "",
                "query": r.get("search_query", "")
            })

        prompt = f"""
        As a senior market research analyst, synthesize the following compacted search results into a concise market research report for the startup idea: "{idea}"

        COMPACT SEARCH RESULTS (title/snippet/url/query, max {max_items} items):
        {json.dumps(compact, indent=2)[:6000]}

        FAILED QUERIES (for context):
        {json.dumps(search_data.get('failed_queries', []), indent=2)}

        Produce a JSON object with these keys: competitors, market_size, target_audience, market_trends, growth_rate, key_risks, success_factors, data_quality.
        Be concise and prioritize facts that can be inferred from the compact results. If data is insufficient, state that explicitly in data_quality.
        """

        try:
            # Use a smaller model and lower max_tokens to reduce TPM and token usage
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.1,
                max_tokens=700,
                response_format={"type": "json_object"},
            )

            result = json.loads(chat_completion.choices[0].message.content)

            # Add metadata about the research process
            result["research_metadata"] = {
                "search_queries_attempted": len(queries) if 'queries' in locals() else 0,
                "search_results_analyzed": search_data.get("total_results", 0),
                "search_success_rate": search_data.get("success_rate", "0%"),
                "synthesis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            return result

        except Exception as e:
            # Handle token/rate-limit errors explicitly where possible
            err_str = str(e)
            if "tokens" in err_str or "rate_limit" in err_str or "rate_limit_exceeded" in err_str:
                return {"error": "Model token/rate limit exceeded during synthesis. Try using fewer search results or a smaller model."}
            return {"error": f"Failed to synthesize results: {e}"}

    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "error": error_message,
            "error_type": error_type,
            "competitors": [],
            "market_size": "Unable to determine due to research error",
            "target_audience": "Unable to determine due to research error",
            "research_status": "failed"
        }