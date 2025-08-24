from .base_agent import BaseAgent
from core.clients import groq_client
from tools.web_search import tavily_search
from models.schemas import MarketResearchResult
import json
from typing import List, Dict, Any, Optional
import time
import hashlib
import math


def _retry(func, retries=3, initial_delay=1.0, backoff=2.0):
    """Simple retry helper with exponential backoff."""
    def wrapper(*args, **kwargs):
        delay = initial_delay
        for attempt in range(1, retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == retries:
                    raise
                print(f"     retry {attempt}/{retries} failed: {e}; sleeping {delay}s")
                time.sleep(delay)
                delay *= backoff
    return wrapper


class MarketResearchAgent(BaseAgent):
    """
    Advanced MarketResearchAgent with query expansion, deduplication, source scoring,
    chunked synthesis to avoid token limits, and Pydantic validation of outputs.
    """

    # Tunable constants
    MAX_QUERIES = 12
    RESULTS_PER_QUERY = 6
    MAX_COMPACT_ITEMS = 24
    BATCH_SYNTHESIS_SIZE = 6  # items per batch to summarize before final aggregation

    def run(self, idea: str) -> dict:
        print(f"🔍 MarketResearchAgent: Starting comprehensive research for '{idea}'")

        try:
            seeds = self._generate_search_queries(idea)
            if isinstance(seeds, dict) and seeds.get("error"):
                return self._create_error_response("query_generation", seeds["error"])

            print(f"   Seed queries: {len(seeds)}")

            expanded = self._expand_queries(seeds)
            print(f"   Expanded to {len(expanded)} queries/variants")

            search_results = self._perform_searches(expanded)
            if isinstance(search_results, dict) and search_results.get("error"):
                return self._create_error_response("web_search", search_results["error"])

            print(f"   Retrieved {search_results.get('total_results', 0)} raw results; deduped to {len(search_results.get('results', []))}")

            report = self._synthesize_results(idea, search_results)
            # Validate/normalize against our schema
            validated = self._validate_and_format_result(report)
            if isinstance(validated, dict) and validated.get("error"):
                return self._create_error_response("validation", validated["error"])

            print("   ✅ Market research completed and validated")
            return validated

        except Exception as e:
            error_msg = f"Unexpected error in MarketResearchAgent: {e}"
            print(f"   ❌ {error_msg}")
            return self._create_error_response("unexpected", error_msg)

    def _generate_search_queries(self, idea: str) -> List[str]:
        """Use Groq to produce a set of seed queries (focused, broad, competitor-focused)."""
        prompt = f"""
        As an expert market research analyst, produce 6 short seed search phrases (not full sentences)
        for researching this startup idea: "{idea}".

        The seeds should include: direct competitors, indirect competitors, market size phrases,
        report queries, target audience phrases, and regulatory or barrier queries.

        Return ONLY a JSON object: {{"queries": ["phrase1","phrase2",...]}}
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
            return queries[:6]
        except Exception as e:
            return {"error": f"Failed to generate search queries: {e}"}

    def _expand_queries(self, seeds: List[str]) -> List[str]:
        """Expand seed queries with variants and advanced operators to cover many angles.

        Strategies include: boolean variants, site: searches for authoritative sources,
        filetype:pdf for reports, and date-limited queries.
        """
        expanded = []
        authoritative_sites = ["gov", "edu", "nic", "org"]

        for s in seeds:
            s = s.strip()
            if not s:
                continue
            # Basic seed
            expanded.append(s)
            # Boolean and exact-match
            expanded.append(f'"{s}"')
            expanded.append(f'{s} OR "{s} analysis"')
            expanded.append(f'{s} Intitle:report')
            # filetype PDF for industry reports
            expanded.append(f'{s} filetype:pdf')
            # recent timeframe (last 2 years)
            expanded.append(f'{s} 2023..2025')

            # site-specific authoritative searches
            for dom in authoritative_sites[:2]:
                expanded.append(f'site:.{dom} {s}')

        # Trim duplicates and limit
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

        search_call = _retry(tavily_search, retries=3, initial_delay=1.0, backoff=2.0)

        for idx, q in enumerate(queries):
            try:
                print(f"   Searching ({idx+1}/{len(queries)}): {q}")
                raw = search_call(q, max_results=self.RESULTS_PER_QUERY)
                if not raw:
                    failed.append({"query": q, "error": "no results"})
                    continue

                for r in raw:
                    r = dict(r) if isinstance(r, dict) else {"title": str(r)}
                    r["search_query"] = q
                    r["_source_score"] = self._score_source(r)
                    all_results.append(r)

                # Short sleep to reduce throttle risk
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

    def _score_source(self, item: Dict[str, Any]) -> float:
        """Simple heuristic to score a source's authority and relevance."""
        score = 0.0
        url = (item.get("url") or item.get("link") or "").lower()
        title = (item.get("title") or "").lower()
        snippet = (item.get("snippet") or item.get("summary") or "").lower()

        if any(t in url for t in [".gov", ".edu"]):
            score += 2.0
        if url.endswith(".pdf") or "filetype:pdf" in url:
            score += 1.0
        # presence of numeric market words
        if any(k in snippet for k in ["market size", "revenue", "growth rate", "cagr", "report"]):
            score += 1.0
        # recency boost if published_at present
        published = item.get("published_at") or item.get("date")
        if published:
            score += 0.5
        # Title relevance
        if any(w in title for w in ["report", "analysis", "study", "market"]):
            score += 0.8

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
        # sort by score desc
        deduped.sort(key=lambda x: x.get("_source_score", 0), reverse=True)
        return deduped

    def _chunk_and_summarize(self, idea: str, compact_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize items in small batches then aggregate to avoid token limits."""
        batches = [compact_items[i:i + self.BATCH_SYNTHESIS_SIZE] for i in range(0, len(compact_items), self.BATCH_SYNTHESIS_SIZE)]
        partials = []

        for i, batch in enumerate(batches):
            prompt = f"""
            You are producing a compact market research extract for the startup idea: "{idea}".
            Analyze the following {len(batch)} search results and return a JSON with: competitors (list), market_trends (list), key_findings (list of short facts), citations (list of urls).

            BATCH DATA:
            {json.dumps(batch, indent=2)[:8000]}
            """

            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192",
                    temperature=0.05,
                    max_tokens=400,
                    response_format={"type": "json_object"},
                )
                part = json.loads(chat_completion.choices[0].message.content)
                partials.append(part)
                print(f"     summarized batch {i+1}/{len(batches)} -> items {len(batch)}")
            except Exception as e:
                print(f"     batch synthesis failed: {e}")
                partials.append({"competitors": [], "market_trends": [], "key_findings": [], "citations": []})

        # Aggregate partials
        agg = {"competitors": [], "market_trends": [], "key_findings": [], "citations": []}
        for p in partials:
            for k in ["competitors", "market_trends", "key_findings", "citations"]:
                vals = p.get(k) or []
                for v in vals:
                    if v not in agg[k]:
                        agg[k].append(v)

        return agg

    def _synthesize_results(self, idea: str, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a robust, multi-step synthesis that avoids token limits and produces stable JSON."""
        raw_results = search_data.get("results", [])
        if not raw_results:
            return {"error": "No search results available for synthesis"}

        # compact top N results
        compact = []
        for r in raw_results[: self.MAX_COMPACT_ITEMS]:
            compact.append({
                "title": r.get("title") or r.get("headline") or "",
                "snippet": r.get("snippet") or r.get("summary") or "",
                "url": r.get("url") or r.get("link") or "",
                "query": r.get("search_query", ""),
                "score": r.get("_source_score", 0),
            })

        # Step 1: chunked summarization
        aggregated = self._chunk_and_summarize(idea, compact)

        # Step 2: final consolidation prompt that asks for structured MarketResearch fields
        final_prompt = f"""
        Consolidate the following aggregated findings into a strict JSON object for market research of: "{idea}".

        AGGREGATED:
        {json.dumps(aggregated, indent=2)[:6000]}

        Use these keys: competitors (list of strings), market_size (string or object), target_audience (object), market_trends (list), growth_rate (string), key_risks (list), success_factors (list), data_quality (string).
        Be conservative: only include items you can infer from the aggregated findings. When unsure, set data_quality to a short explanation.
        """

        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": final_prompt}],
                model="llama3-8b-8192",
                temperature=0.08,
                max_tokens=700,
                response_format={"type": "json_object"},
            )
            result = json.loads(chat_completion.choices[0].message.content)
            # attach metadata
            result["research_metadata"] = {
                "search_queries_attempted": len(search_data.get("failed_queries", [])) + len(search_data.get("results", [])),
                "search_results_analyzed": search_data.get("total_results", 0),
                "search_success_rate": search_data.get("success_rate", "0%"),
                "synthesis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return result

        except Exception as e:
            err_str = str(e)
            if "tokens" in err_str or "rate_limit" in err_str or "rate_limit_exceeded" in err_str:
                return {"error": "Model token/rate limit exceeded during synthesis. Try using fewer search results or smaller batch sizes."}
            return {"error": f"Failed to synthesize results: {e}"}

    def _validate_and_format_result(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Validate with Pydantic and ensure minimal defaults are present."""
        if not report or isinstance(report, dict) and report.get("error"):
            return {"error": report.get("error") if isinstance(report, dict) else "empty report"}

        try:
            # Ensure research_metadata shape exists
            if "research_metadata" in report and isinstance(report["research_metadata"], dict):
                # keep as-is; MarketResearchResult expects MarketResearchMetadata optional
                pass

            mr = MarketResearchResult.parse_obj(report)
            # return as dict
            out = mr.dict()
            out["research_status"] = "completed"
            return out
        except Exception as e:
            # Attempt a lightweight repair: ask Groq to reformat into the strict JSON
            try:
                fix_prompt = f"""
                The following partial market research JSON may be malformed or missing keys. Please return a strict JSON that matches the keys: competitors, market_size, target_audience, market_trends, growth_rate, key_risks, success_factors, data_quality, research_metadata.

                INPUT:
                {json.dumps(report, indent=2)[:8000]}
                """
                chat_completion = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": fix_prompt}],
                    model="llama3-8b-8192",
                    temperature=0.05,
                    max_tokens=600,
                    response_format={"type": "json_object"},
                )
                repaired = json.loads(chat_completion.choices[0].message.content)
                mr = MarketResearchResult.parse_obj(repaired)
                out = mr.dict()
                out["research_status"] = "completed_repaired"
                return out
            except Exception as e2:
                return {"error": f"Validation and repair failed: {e2}"}

    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        return {
            "error": error_message,
            "error_type": error_type,
            "competitors": [],
            "market_size": "Unable to determine due to research error",
            "target_audience": "Unable to determine due to research error",
            "research_status": "failed",
        }