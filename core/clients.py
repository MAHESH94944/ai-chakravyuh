import logging
import json
import requests
from typing import Optional, List, Dict, Any

# --- Library Imports with Graceful Fallbacks ---
try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    from groq import Groq
except ImportError:
    Groq = None
try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None
try:
    import yfinance as yf
except ImportError:
    yf = None

from typing import Optional, List, Dict, Any
import logging
import json
import requests

# Optional third-party libraries
try:
    import yfinance as yf
except Exception:
    yf = None

from .config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=5))
def enhanced_web_search(query: str, max_results: int = 5, country: str = "us") -> List[Dict[str, Any]]:
    """Perform a tolerant web search using available backends.

    Returns a list of dicts with keys: title, url, snippet/content.
    """
    # Try SerpAPI if key present
    serp_key = getattr(settings, "SERPAPI_API_KEY", None)
    if serp_key:
        try:
            params = {"q": query, "api_key": serp_key, "engine": "google", "num": max_results, "gl": country}
            r = requests.get("https://serpapi.com/search", params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
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

    # No backend available
    logger.info("No web-search backend configured; returning empty results for query: %s", query)
    return []


def get_proxy_company_financials(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch key financial metrics for a public company using yfinance when available.

    Returns None when data is unavailable.
    """
    if not yf:
        logger.info("yfinance not available; cannot fetch financials for %s", ticker)
        return None
    try:
        tk = yf.Ticker(ticker)
        info = getattr(tk, "info", {}) or {}
        financials: Dict[str, Any] = {"ticker": ticker}

        # Try to get some safe fields
        financials["company_name"] = info.get("longName")
        financials["sector"] = info.get("sector")
        financials["industry"] = info.get("industry")
        financials["currency"] = info.get("currency")

        # Safely try to get recent revenue/gross profit from financials frames
        try:
            fin = getattr(tk, "financials", None)
            if fin is not None and not fin.empty:
                latest = fin.iloc[:, 0]
                # look for common labels
                for label in ["Total Revenue", "Revenue", "totalRevenue", "TOTALREVENUE"]:
                    if label in latest.index:
                        financials["recent_revenue"] = int(latest[label])
                        break
                for g in ["Gross Profit", "grossProfit"]:
                    if g in latest.index:
                        financials["recent_gross_profit"] = int(latest[g])
                        break
        except Exception:
            pass

        # Attempt to grab gross margin if available
        gm = info.get("grossMargins")
        if gm is not None:
            try:
                financials["gross_margin"] = float(gm)
            except Exception:
                pass

        return financials
    except Exception as e:
        logger.warning("Failed to fetch financials for %s: %s", ticker, e)
        return None


class SimpleResponse:
    """Compatibility wrapper: provides a .text attribute containing raw text/JSON."""
    def __init__(self, text: str):
        self.text = text


def generate_text_with_fallback(prompt: str, is_json: bool = False) -> SimpleResponse:
    """LLM compatibility wrapper. Returns a deterministic fallback indicating no model available."""
    if is_json:
        return SimpleResponse(json.dumps({"error": "LLM unavailable", "detail": "No model configured in this environment"}))
    return SimpleResponse("LLM unavailable: no model configured in this environment.")


def generate_text(prompt: str, is_json: bool = False) -> SimpleResponse:
    """Compatibility wrapper used by agents. Currently maps to generate_text_with_fallback."""
    return generate_text_with_fallback(prompt, is_json=is_json)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=5))
def get_location_data(query: str) -> Optional[Dict[str, Any]]:
    """Thin wrapper to fetch location data from OpenWeather or OpenRoutes if configured; otherwise return None."""
    try:
        if getattr(settings, 'OPENROUTING_API_KEY', None):
            try:
                url = f"https://api.openrouteservice.org/geocode/search?api_key={settings.OPENROUTING_API_KEY}&text={query}"
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
                if data and data.get('features'):
                    props = data['features'][0].get('properties', {})
                    geom = data['features'][0].get('geometry', {})
                    coords = geom.get('coordinates', [None, None])
                    return {
                        'name': props.get('name'),
                        'country': props.get('country'),
                        'country_code': props.get('country_code'),
                        'region': props.get('region'),
                        'city': props.get('locality'),
                        'latitude': coords[1],
                        'longitude': coords[0]
                    }
            except Exception:
                pass

        if getattr(settings, 'OPENWEATHER_API_KEY', None):
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={query}&appid={settings.OPENWEATHER_API_KEY}"
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
                return {
                    'name': data.get('name'),
                    'country': data.get('sys', {}).get('country'),
                    'latitude': data.get('coord', {}).get('lat'),
                    'longitude': data.get('coord', {}).get('lon')
                }
            except Exception:
                pass

    except Exception as e:
        logger.warning(f"get_location_data failed for {query}: {e}")

    return None