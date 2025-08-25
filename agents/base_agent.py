# agents/base_agent.py
"""Base class for all agents with enhanced utility methods."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from core.clients import enhanced_web_search, get_financial_data, get_location_data, get_currency_data
import re
import json
from datetime import datetime


class BaseAgent(ABC):
    """Abstract base class for all analysis agents."""
    
    def __init__(self):
        self.agent_type = self.__class__.__name__
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the agent's primary analysis task."""
        pass
    
    def format_pointwise(self, data: Any, max_bullets: int = 5) -> List[str]:
        """Convert complex data into simple, non-technical bullet points."""
        bullets = []
        
        if isinstance(data, dict):
            # Handle different agent output formats
            if "pointwise_summary" in data:
                return data["pointwise_summary"][:max_bullets]
                
            if "error" in data:
                return [f"Error: {data['error']}"]
                
            if "summary" in data:
                bullets.append(data["summary"])
                
            # Financial data
            if "estimated_costs" in data and "revenue_projections" in data:
                total_cost = sum(data["estimated_costs"].get("initial_development", {}).values())
                monthly_cost = sum(data["estimated_costs"].get("monthly_operations", {}).values())
                revenue = sum(proj["estimated_monthly"] for proj in data["revenue_projections"])
                currency = data.get("currency", "USD")
                
                bullets.append(f"Initial investment: {total_cost:,.0f} {currency}")
                bullets.append(f"Monthly operating cost: {monthly_cost:,.0f} {currency}")
                bullets.append(f"Projected monthly revenue: {revenue:,.0f} {currency}")
                
                if "financial_metrics" in data and data["financial_metrics"]:
                    metrics = data["financial_metrics"]
                    if metrics.get("break_even_months"):
                        bullets.append(f"Break-even in: {metrics['break_even_months']:.1f} months")
            
            # Risk data
            if "overall_risk_score" in data:
                score = data["overall_risk_score"]
                level = data.get("risk_level", "medium")
                bullets.append(f"Overall risk: {level} ({score}/100)")
                
            # Technical feasibility
            if "feasibility" in data:
                bullets.append(f"Technical feasibility: {data['feasibility'].replace('_', ' ').title()}")
                
        elif isinstance(data, str):
            # Split long text into bullet points
            sentences = re.split(r'[.!?]+', data)
            bullets = [s.strip() for s in sentences if len(s.strip()) > 10][:max_bullets]
        
        # Ensure we have at least something
        if not bullets:
            bullets = ["Analysis completed successfully"]
            
        return bullets[:max_bullets]
    
    def search_local_data(self, query: str, location: Optional[Dict] = None, max_results: int = 3) -> List[Dict]:
        """Search for location-specific data."""
        location_suffix = ""
        if location and "country_code" in location:
            location_suffix = f" in {location.get('city', '')} {location.get('country_code', '')}".strip()
        
        return enhanced_web_search(f"{query}{location_suffix}", max_results, 
                                 location.get("country_code", "us").lower() if location else "us")
    
    def extract_numeric_data(self, text: str, data_type: str = "cost") -> Optional[float]:
        """Extract numeric data from text with context awareness."""
        # Patterns for different types of data
        patterns = {
            "cost": [r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', r'₹?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 
                     r'€?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', r'¥?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'],
            "percentage": [r'(\d{1,3}(?:\.\d{1,2})?)%'],
            "population": [r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:people|population|residents)'],
        }
        
        text_lower = text.lower()
        patterns_to_use = patterns.get(data_type, patterns["cost"])
        
        for pattern in patterns_to_use:
            matches = re.findall(pattern, text_lower)
            if matches:
                # Take the first reasonable match (not too small for cost data)
                for match in matches:
                    try:
                        value = float(match.replace(',', ''))
                        if data_type == "cost" and value < 1:  # Skip very small values for costs
                            continue
                        return value
                    except ValueError:
                        continue
        
        return None
    
    def validate_currency_conversion(self, amount: float, from_currency: str, to_currency: str = "USD") -> Dict:
        """Validate and convert currency amounts."""
        if from_currency == to_currency:
            return {"amount": amount, "currency": to_currency, "converted": False}
        
        rate = get_currency_data(from_currency, to_currency)
        if rate:
            return {
                "amount": amount * rate,
                "original_amount": amount,
                "original_currency": from_currency,
                "currency": to_currency,
                "exchange_rate": rate,
                "converted": True
            }
        
        # Fallback: return original with warning
        return {
            "amount": amount,
            "currency": from_currency,
            "converted": False,
            "warning": f"Could not convert {from_currency} to {to_currency}"
        }
    
    def generate_citations(self, search_results: List[Dict]) -> List[Dict[str, str]]:
        """Generate formatted citations from search results."""
        citations = []
        for result in search_results:
            citations.append({
                "title": result.get("title", "Unknown"),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", "")[:200] + "..." if len(result.get("snippet", "")) > 200 else result.get("snippet", ""),
                "source": result.get("source", "web_search"),
                "date": result.get("published_date", datetime.now().strftime("%Y-%m-%d"))
            })
        return citations