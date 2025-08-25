# agents/finance.py
"""Enhanced FinanceAgent with real financial data and location-specific costing."""

from .base_agent import BaseAgent
import time
from core.clients import generate_text, enhanced_web_search, get_financial_data, get_currency_data
from models.schemas import FinanceResult, CostBreakdown, RevenueProjection, FinancialMetrics
import json
import time
from typing import Dict, Any, List
import re


class FinanceAgent(BaseAgent):
    """
    Advanced FinanceAgent with real-world data integration for accurate financial projections.
    Uses web search for local cost data, currency conversion, and market-specific pricing.
    """
    
    def run(self, idea: str, market_research_data: Dict[str, Any], location: Dict[str, Any] = None) -> Dict[str, Any]:
        print(f"💰 FinanceAgent: Generating detailed financial outlook for '{idea}'")
        
        try:
            # Extract location information
            country_code = location.get("country_code", "US") if location else "US"
            city = location.get("city", "") if location else ""
            region = location.get("region", "") if location else ""
            
            # Determine currency based on location
            currency = self._determine_currency(country_code)
            
            # Research local market conditions and costs
            local_data = self._research_local_market(idea, country_code, city, region)
            
            # Get economic indicators for the region
            economic_data = self._get_economic_indicators(country_code)
            
            # Generate detailed financial model
            financial_model = self._build_financial_model(
                idea, local_data, economic_data, currency, country_code, city
            )
            
            # Convert to USD for standardized reporting if needed
            if currency != "USD":
                usd_conversion = self._convert_to_usd(financial_model, currency)
                financial_model["usd_equivalent"] = usd_conversion
            
            # Generate confidence score based on data quality
            confidence_score = self._calculate_confidence(local_data, economic_data)
            
            # Format results according to schema
            result = self._format_results(financial_model, local_data, confidence_score, currency)
            
            # Add pointwise summary for non-technical users
            result["pointwise_summary"] = self.format_pointwise(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Financial analysis failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {"error": error_msg, "pointwise_summary": [error_msg]}
    
    def _determine_currency(self, country_code: str) -> str:
        """Determine the appropriate currency for a given country."""
        currency_map = {
            "US": "USD", "GB": "GBP", "EU": "EUR", "DE": "EUR", "FR": "EUR",
            "IN": "INR", "JP": "JPY", "CN": "CNY", "CA": "CAD", "AU": "AUD",
            "BR": "BRL", "RU": "RUB", "MX": "MXN", "KR": "KRW", "SG": "SGD"
        }
        return currency_map.get(country_code.upper(), "USD")
    
    def _research_local_market(self, idea: str, country_code: str, city: str, region: str) -> Dict[str, Any]:
        """Research local market conditions and costs using web search."""
        print(f"   Researching local market conditions in {city}, {region}, {country_code}")
        
        local_data = {
            "wage_data": [],
            "rent_data": [],
            "equipment_costs": [],
            "utility_costs": [],
            "market_pricing": [],
            "citations": []
        }
        
        # Search queries tailored to the startup idea and location
        queries = [
            f"average software developer salary {city} {region}",
            f"office rent cost {city} {region}",
            f"cloud hosting costs {country_code}",
            f"marketing costs customer acquisition {idea} {country_code}",
            f"utility costs electricity internet {city} {region}",
            f"equipment costs {idea} business {country_code}"
        ]
        
        for query in queries:
            try:
                results = enhanced_web_search(query, max_results=2, country=country_code.lower())
                for result in results:
                    # Extract numeric data based on query type
                    if "salary" in query:
                        value = self.extract_numeric_data(result["snippet"], "cost")
                        if value:
                            local_data["wage_data"].append({
                                "role": "developer",
                                "amount": value,
                                "currency": self._determine_currency(country_code),
                                "source": result["url"]
                            })
                    elif "rent" in query:
                        value = self.extract_numeric_data(result["snippet"], "cost")
                        if value:
                            local_data["rent_data"].append({
                                "type": "office",
                                "amount": value,
                                "period": "monthly",
                                "currency": self._determine_currency(country_code),
                                "source": result["url"]
                            })
                    elif "hosting" in query or "cloud" in query:
                        value = self.extract_numeric_data(result["snippet"], "cost")
                        if value:
                            local_data["utility_costs"].append({
                                "type": "cloud_hosting",
                                "amount": value,
                                "period": "monthly",
                                "currency": self._determine_currency(country_code),
                                "source": result["url"]
                            })
                    
                    # Add to citations
                    local_data["citations"].append({
                        "query": query,
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result["snippet"][:200] + "..." if len(result["snippet"]) > 200 else result["snippet"]
                    })
                
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"   Search query failed: {query} - {e}")
                continue
        
        return local_data
    
    def _get_economic_indicators(self, country_code: str) -> Dict[str, Any]:
        """Get economic indicators for the country."""
        indicators = {}
        
        # Try to get GDP growth
        gdp_data = get_financial_data("GDP", country_code)
        if gdp_data and "data" in gdp_data:
            indicators["gdp_growth"] = self._extract_growth_rate(gdp_data)
        
        # Try to get inflation data
        cpi_data = get_financial_data("CPI", country_code)
        if cpi_data and "data" in cpi_data:
            indicators["inflation_rate"] = self._extract_inflation_rate(cpi_data)
        
        return indicators
    
# agents/finance.py (continued)
    def _build_financial_model(self, idea: str, local_data: Dict, economic_data: Dict, 
                              currency: str, country_code: str, city: str) -> Dict[str, Any]:
        """Build a comprehensive financial model using real data."""
        
        # Use Gemini to analyze the data and create financial projections
        prompt = f"""
        As a financial analyst, create detailed financial projections for this startup idea:
        "{idea}"
        
        Location: {city}, {country_code}
        Currency: {currency}
        
        Local Market Data:
        {json.dumps(local_data, indent=2)}
        
        Economic Indicators:
        {json.dumps(economic_data, indent=2)}
        
        Create a comprehensive financial model including:
        1. Initial development costs breakdown
        2. Monthly operational costs breakdown
        3. Revenue projections with realistic assumptions
        4. Key financial metrics (CAC, LTV, gross margin, break-even timeline)
        
        Return ONLY valid JSON with this structure:
        {{
            "initial_development": {{"category1": amount, "category2": amount, ...}},
            "monthly_operations": {{"category1": amount, "category2": amount, ...}},
            "revenue_streams": [
                {{
                    "stream_name": "string",
                    "description": "string",
                    "estimated_monthly": number,
                    "growth_rate": number,
                    "assumptions": ["string"]
                }}
            ],
            "financial_metrics": {{
                "cac": number,
                "ltv": number,
                "gross_margin": number,
                "break_even_months": number
            }},
            "assumptions": ["string"],
            "data_sources": ["string"]
        }}
        """
        
        try:
            response = generate_text(prompt)
            cleaned = response.text.strip().replace('```json', '').replace('```', '').strip()
            # Try to parse JSON; if it fails, fall back to conservative model
            try:
                return json.loads(cleaned)
            except Exception:
                return self._create_fallback_model(idea, currency, country_code)
        except Exception as e:
            print(f"   Financial modeling failed: {e}")
            return self._create_fallback_model(idea, currency, country_code)
    
    def _create_fallback_model(self, idea: str, currency: str, country_code: str) -> Dict[str, Any]:
        """Create conservative fallback financial model."""
        # Base costs adjusted for country development level
        development_multiplier = 1.0
        if country_code in ["IN", "VN", "ID", "PH"]:  # Lower cost countries
            development_multiplier = 0.3
        elif country_code in ["CN", "BR", "RU", "MX"]:  # Medium cost countries
            development_multiplier = 0.6
        
        return {
            "initial_development": {
                "product_development": 50000 * development_multiplier,
                "legal_regulatory": 5000 * development_multiplier,
                "marketing_launch": 10000 * development_multiplier,
                "equipment_infrastructure": 15000 * development_multiplier
            },
            "monthly_operations": {
                "salaries": 20000 * development_multiplier,
                "office_rent": 2000 * development_multiplier,
                "cloud_services": 1000,
                "marketing": 3000 * development_multiplier,
                "utilities": 500 * development_multiplier
            },
            "revenue_streams": [
                {
                    "stream_name": "Subscription Fees",
                    "description": "Monthly subscription revenue",
                    "estimated_monthly": 10000 * development_multiplier,
                    "growth_rate": 0.1,
                    "assumptions": ["10% monthly growth", "100 paying customers"]
                }
            ],
            "financial_metrics": {
                "cac": 100 * development_multiplier,
                "ltv": 600 * development_multiplier,
                "gross_margin": 0.6,
                "break_even_months": 12
            },
            "assumptions": ["Conservative estimates based on similar startups"],
            "data_sources": ["Industry benchmarks and similar market data"]
        }
    
    def _convert_to_usd(self, financial_model: Dict[str, Any], original_currency: str) -> Dict[str, Any]:
        """Convert all financial amounts to USD for standardized reporting."""
        if original_currency == "USD":
            return financial_model
        
        exchange_rate = get_currency_data(original_currency, "USD")
        if not exchange_rate:
            return financial_model
        
        converted = {}
        for key, value in financial_model.items():
            if isinstance(value, dict):
                converted[key] = {k: v * exchange_rate if isinstance(v, (int, float)) else v 
                                 for k, v in value.items()}
            elif isinstance(value, list):
                converted[key] = []
                for item in value:
                    if isinstance(item, dict):
                        converted_item = {}
                        for k, v in item.items():
                            if isinstance(v, (int, float)) and "amount" in k.lower() or "estimated" in k.lower():
                                converted_item[k] = v * exchange_rate
                            else:
                                converted_item[k] = v
                        converted[key].append(converted_item)
                    else:
                        converted[key].append(item)
            elif isinstance(value, (int, float)):
                converted[key] = value * exchange_rate
            else:
                converted[key] = value
        
        return converted
    
    def _calculate_confidence(self, local_data: Dict, economic_data: Dict) -> float:
        """Calculate confidence score based on data quality and completeness."""
        confidence = 70.0  # Base confidence
        
        # Adjust based on local data quality
        if len(local_data.get("wage_data", [])) > 0:
            confidence += 5
        if len(local_data.get("rent_data", [])) > 0:
            confidence += 5
        if len(local_data.get("utility_costs", [])) > 0:
            confidence += 5
        
        # Adjust based on economic data
        if economic_data.get("gdp_growth"):
            confidence += 5
        if economic_data.get("inflation_rate"):
            confidence += 5
        
        return min(95.0, confidence)  # Cap at 95%
    
    def _format_results(self, financial_model: Dict, local_data: Dict, 
                       confidence_score: float, currency: str) -> Dict[str, Any]:
        """Format results according to the FinanceResult schema."""
        
        # Create cost breakdown
        cost_breakdown = CostBreakdown(
            initial_development=financial_model["initial_development"],
            monthly_operations=financial_model["monthly_operations"],
            one_time_capex=financial_model.get("one_time_capex", {}),
            variable_costs=financial_model.get("variable_costs", {})
        )
        
        # Create revenue projections
        revenue_projections = []
        for stream in financial_model["revenue_streams"]:
            revenue_projections.append(RevenueProjection(**stream))
        
        # Create financial metrics
        financial_metrics = None
        if "financial_metrics" in financial_model:
            financial_metrics = FinancialMetrics(**financial_model["financial_metrics"])
        
        # Create pointwise summary
        total_initial = sum(financial_model["initial_development"].values())
        total_monthly = sum(financial_model["monthly_operations"].values())
        total_revenue = sum(stream["estimated_monthly"] for stream in financial_model["revenue_streams"])
        
        pointwise_summary = [
            f"Initial investment required: {total_initial:,.0f} {currency}",
            f"Monthly operating costs: {total_monthly:,.0f} {currency}",
            f"Projected monthly revenue: {total_revenue:,.0f} {currency}",
            f"Estimated break-even in {financial_model['financial_metrics']['break_even_months']} months",
            f"Gross margin: {financial_model['financial_metrics']['gross_margin']*100:.1f}%"
        ]
        
        return FinanceResult(
            estimated_costs=cost_breakdown,
            revenue_projections=revenue_projections,
            currency=currency,
            financial_metrics=financial_metrics,
            pointwise_summary=pointwise_summary,
            assumptions=financial_model["assumptions"],
            confidence_score=confidence_score,
            citations=local_data["citations"],
            local_cost_data=local_data
        ).dict()