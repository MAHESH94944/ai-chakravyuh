from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Dict
import os
import logging
from core import clients

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def tavily_search(query: str, max_results: int = 5) -> List[Dict]:
    """Perform web search using an available backend.

    Priority:
      1. Tavily client (project private SDK)
      2. SerpAPI (public service) if SERPAPI API key is present as env var
      3. Return empty list (caller should gracefully degrade)

    Returns a list of dicts with keys: title, url, snippet
    """
    # Debug fast-mode: return quickly to avoid long external retries
    if os.getenv("DEBUG_FAST_MODE") in ("1", "true", "True"):
        logger.debug("DEBUG_FAST_MODE enabled: returning no results for '%s'", query)
        return []

    # 1) Tavily client if configured
    tavily_client = getattr(clients, "tavily_client", None)
    if tavily_client:
        try:
            logger.debug("Using Tavily client for query: %s", query)
            response = tavily_client.search(query=query, search_depth="basic", max_results=max_results)
            return response.get("results", [])
        except Exception as e:
            logger.warning("Tavily search failed, falling back: %s", e)

    # 2) SerpAPI if API key is provided
    serpapi_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI")
    if serpapi_key:
        try:
            logger.debug("Using SerpAPI for query: %s", query)
            # import here to keep SerpAPI optional
            from serpapi import GoogleSearch

            params = {
                "q": query,
                "num": max_results,
                "api_key": serpapi_key,
                # use Google engine by default
                "engine": "google",
            }
            search = GoogleSearch(params)
            data = search.get_dict() or {}
            results = []
            for item in data.get("organic_results", [])[:max_results]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link") or item.get("url"),
                    "snippet": item.get("snippet") or item.get("snippet"),
                })
            return results
        except Exception as e:
            logger.warning("SerpAPI search failed: %s", e)

    # 3) No backend available
    logger.info("No web-search backend configured; skipping search for query: %s", query)
    return []