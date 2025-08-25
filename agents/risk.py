from .base_agent import BaseAgent
import time
from core.clients import generate_text
import json
from typing import Optional, List, Dict, Any
import hashlib
import re
import time
from datetime import datetime


class RiskAgent(BaseAgent):
    """
    Enhanced RiskAgent with industry awareness, better prioritization, 
    comprehensive risk categories, and robust fallback mechanisms.
    
    Produces a normalized dictionary with:
      - summary: Comprehensive risk overview
      - overall_risk_score: 0-100 with risk level categorization
      - risk_categories: Organized by risk types
      - risks: Prioritized list with detailed analysis
      - recommendations: Actionable next steps
      - risk_matrix: Visual risk prioritization
      - metadata: Analysis timestamp and confidence
    """

    def run(self, idea: str, market_research_data: dict, location: Optional[dict] = None) -> Dict[str, Any]:
        """
        Enhanced risk analysis with industry detection, better error handling,
        and comprehensive risk categorization.
        """
        try:
            # Enhanced location resolution
            resolved_location = self._resolve_location(location, market_research_data)
            
            # Detect industry for targeted risk analysis
            industry = self._detect_industry(idea)
            
            # Build context-aware prompt
            prompt = self._build_enhanced_prompt(idea, resolved_location, market_research_data, industry)
            
            # Call API with retry mechanism
            response_text = self._call_gemini_with_retry(prompt)
            
            # Parse and validate response
            parsed = self._parse_response(response_text)
            
            # Enhanced normalization with risk categorization
            result = self._normalize_enhanced_output(parsed, idea, resolved_location, industry)
            
            return result

        except Exception as e:
            print(f"RiskAgent error: {e}")
            # Fallback to deterministic risk analysis
            out = self._comprehensive_fallback_analysis(idea, resolved_location, market_research_data)
            # Ensure pointwise summary for non-technical output
            out.setdefault("pointwise_summary", self.format_pointwise(out))
            return out

    def _resolve_location(self, location: Optional[dict], market_data: dict) -> str:
        """Enhanced location resolution with multiple fallbacks"""
        if isinstance(location, dict):
            return (location.get("text") or location.get("address") or 
                   location.get("name") or str(location))
        elif isinstance(location, str):
            return location
        elif isinstance(market_data, dict):
            return (market_data.get("location") or 
                   market_data.get("target_audience", {}).get("location") or
                   market_data.get("market_size", {}).get("region"))
        return None

    def _detect_industry(self, idea: str) -> str:
        """Detect industry from idea text with better accuracy"""
        idea_lower = idea.lower()
        
        industry_mapping = {
            'tech': ['tech', 'software', 'app', 'ai', 'ml', 'algorithm', 'platform', 'saas'],
            'healthcare': ['health', 'medical', 'care', 'fitness', 'wellness', 'diet', 'nutrition', 'therapy'],
            'finance': ['finance', 'fintech', 'banking', 'investment', 'payment', 'insurance', 'loan'],
            'education': ['edu', 'learn', 'course', 'education', 'training', 'tutorial', 'skill'],
            'retail': ['retail', 'ecommerce', 'shop', 'market', 'store', 'product', 'inventory'],
            'agriculture': ['agri', 'farm', 'crop', 'food', 'agriculture', 'farming', 'harvest'],
            'real_estate': ['real estate', 'property', 'housing', 'rent', 'mortgage', 'construction'],
            'transportation': ['transport', 'logistics', 'delivery', 'shipping', 'mobility', 'ride']
        }
        
        for industry, keywords in industry_mapping.items():
            if any(keyword in idea_lower for keyword in keywords):
                return industry
                
        return "general"

    def _build_enhanced_prompt(self, idea: str, location: str, market_data: dict, industry: str) -> str:
        """Build comprehensive, industry-aware risk analysis prompt"""
        
        industry_context = self._get_industry_context(industry)
        location_context = self._get_location_context(location)
        market_insights = self._extract_key_market_insights(market_data)
        
        return f"""
You are a senior risk management expert with specialization in {industry} businesses. 
Conduct a comprehensive risk analysis for the startup idea below, specifically tailored for {location if location else "the target market"}.

*INDUSTRY CONTEXT:* {industry_context}
*LOCATION CONTEXT:* {location_context}

*STARTUP IDEA:* "{idea}"

*MARKET RESEARCH INSIGHTS:*
{json.dumps(market_insights, indent=2)[:6000]}

*COMPREHENSIVE RISK ANALYSIS FRAMEWORK:*

Analyze risks across these categories (prioritize by severity):

1. *MARKET & COMPETITION RISKS*
   - Market saturation and competitive intensity
   - Customer acquisition cost (CAC) and lifetime value (LTV) assumptions
   - Market size validation and growth rate assumptions
   - Local vs national competition dynamics

2. *FINANCIAL & OPERATIONAL RISKS*
   - Burn rate and runway projections
   - Working capital requirements and cash flow timing
   - Revenue model viability and pricing assumptions
   - Operational cost structure and scalability

3. *TECHNICAL & PRODUCT RISKS*
   - Implementation complexity and technical debt
   - Scalability challenges and infrastructure requirements
   - Data security, privacy, and compliance requirements
   - Technology stack viability and maintenance costs

4. *REGULATORY & LEGAL RISKS*
   - Industry-specific regulations and compliance requirements
   - Licensing and permit requirements for the location
   - Intellectual property protection and patent risks
   - Liability and insurance requirements

5. *TALENT & OPERATIONAL RISKS*
   - Key talent acquisition and retention challenges
   - Specialized skill requirements and availability
   - Team composition gaps and leadership risks
   - Operational execution capabilities

6. *EXTERNAL & MACRO RISKS*
   - Economic sensitivity and market cycle risks
   - Supply chain and vendor dependency risks
   - Geopolitical and regulatory change risks
   - Technology disruption and obsolescence risks

*OUTPUT REQUIREMENTS:*
Return strict JSON with these keys:
- summary: Comprehensive risk overview paragraph
- overall_risk_score: 0-100 with risk level (low: 0-39, medium: 40-69, high: 70-100)
- risk_categories: Object with risk counts by category
- risks: Array of objects with: 
  - id: unique identifier
  - title: risk title
  - description: detailed explanation
  - category: one of [market, financial, technical, regulatory, talent, external]
  - likelihood: high/medium/low
  - impact: high/medium/low  
  - severity_score: calculated score (likelihood * impact)
  - mitigation: concrete mitigation strategy
  - validation_experiment: specific test to validate
- risk_matrix: Array of top 5 highest severity risks
- recommendations: Prioritized list of 3-5 actionable next steps
- confidence_score: 0-100 confidence in analysis

*BE SPECIFIC AND ACTIONABLE:* Provide concrete numbers, local examples, and validation experiments.
"""

    def _get_industry_context(self, industry: str) -> str:
        """Provide industry-specific risk context"""
        contexts = {
            "tech": "High competition, rapid obsolescence, talent wars, regulatory scrutiny on AI/data privacy",
            "healthcare": "Stringent regulations, long sales cycles, liability risks, reimbursement challenges, clinical validation requirements",
            "finance": "Heavy regulation, compliance costs, fraud risks, economic sensitivity, trust barriers",
            "education": "Seasonal revenue, adoption barriers, content development costs, accreditation requirements",
            "retail": "Inventory risks, thin margins, supply chain dependencies, consumer sentiment sensitivity",
            "agriculture": "Seasonality, weather dependency, commodity price volatility, supply chain complexity",
            "real_estate": "Market cycle sensitivity, regulatory changes, high capital requirements, location dependency",
            "general": "Market competition, execution risk, funding availability, team capability gaps"
        }
        return contexts.get(industry, contexts["general"])

    def _get_location_context(self, location: str) -> str:
        """Provide location-specific business context"""
        if not location:
            return "Global market - consider international regulations, currency risks, and cross-border complexities"
        
        location_lower = location.lower()
        context = f"Operating in {location} - "
        
        if any(region in location_lower for region in ['india', 'pune', 'mumbai', 'delhi', 'bangalore']):
            return context + "Consider Indian market dynamics: price sensitivity, digital adoption trends, regulatory complexity, infrastructure challenges, and competitive local ecosystem"
        elif any(region in location_lower for region in ['us', 'usa', 'united states', 'california', 'new york']):
            return context + "Consider US market: high competition, regulatory complexity, expensive talent, but strong funding ecosystem and mature customers"
        elif any(region in location_lower for region in ['europe', 'eu', 'uk', 'germany', 'france']):
            return context + "Consider European market: strong regulations (GDPR), high compliance costs, language diversity, but premium pricing potential"
        
        return context + "Research local regulations, market maturity, infrastructure quality, and competitive landscape"

    def _extract_key_market_insights(self, market_data: dict) -> dict:
        """Extract and structure key market insights for risk analysis"""
        if not isinstance(market_data, dict):
            return {"error": "No market data available"}
        
        return {
            "competitors": market_data.get("competitors", []),
            "market_size": market_data.get("market_size", "Unknown"),
            "target_audience": market_data.get("target_audience", {}),
            "growth_trends": market_data.get("market_trends", []),
            "key_risks": market_data.get("key_risks", []),
            "success_factors": market_data.get("success_factors", []),
            "data_quality": market_data.get("data_quality", "unknown")
        }

    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Enhanced API call with robust retry mechanism"""
        for attempt in range(max_retries):
            try:
                response = generate_text(prompt)
                text = getattr(response, "text", str(response)).strip()
                if text and len(text) > 50:  # Basic validation
                    return text
                raise ValueError("Empty or invalid response")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        raise Exception("Max retries exceeded")

    def _parse_response(self, response_text: str) -> Any:
        """Robust JSON parsing with multiple fallback strategies"""
        cleaned = re.sub(r"```(?:json)?", "", response_text).strip()
        
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON object with regex
        try:
            json_match = re.search(r"\{[\s\S]*\}", cleaned)
            if json_match:
                return json.loads(json_match.group(0))
        except:
            pass
        
        # Strategy 3: Try to find array format
        try:
            array_match = re.search(r"\[[\s\S]*\]", cleaned)
            if array_match:
                parsed_array = json.loads(array_match.group(0))
                return {"risks": parsed_array}
        except:
            pass
        
        raise ValueError("Could not parse model output as JSON")

    def _normalize_enhanced_output(self, parsed: Any, idea: str, location: str, industry: str) -> Dict[str, Any]:
        """Normalize and enhance the parsed risk analysis"""
        
        # Initialize output structure
        output = {
            "summary": "",
            "overall_risk_score": None,
            "risk_level": "unknown",
            "risk_categories": {},
            "risks": [],
            "risk_matrix": [],
            "recommendations": [],
            "confidence_score": 80,
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "industry": industry,
                "location": location,
                "idea": idea
            }
        }
        
        # Extract basic fields
        if isinstance(parsed, dict):
            output["summary"] = parsed.get("summary") or parsed.get("overview") or ""
            output["overall_risk_score"] = self._validate_score(parsed.get("overall_risk_score"))
            output["recommendations"] = parsed.get("recommendations") or []
            output["confidence_score"] = self._validate_score(parsed.get("confidence_score"), 80)
        
        # Extract and normalize risks
        raw_risks = self._extract_risks(parsed)
        normalized_risks = []
        
        for i, risk in enumerate(raw_risks):
            if not isinstance(risk, dict):
                continue
                
            normalized_risk = self._normalize_risk(risk, i)
            if normalized_risk:
                normalized_risks.append(normalized_risk)
        
        output["risks"] = normalized_risks
        
        # Calculate overall score if missing
        if output["overall_risk_score"] is None and normalized_risks:
            output["overall_risk_score"] = self._calculate_overall_score(normalized_risks)
        
        # Determine risk level
        output["risk_level"] = self._determine_risk_level(output["overall_risk_score"])
        
        # Categorize risks
        output["risk_categories"] = self._categorize_risks(normalized_risks)
        
        # Create risk matrix (top 5 by severity)
        output["risk_matrix"] = self._create_risk_matrix(normalized_risks)
        
        # Ensure recommendations
        if not output["recommendations"]:
            output["recommendations"] = self._generate_recommendations(normalized_risks)
        
        return output

    def _extract_risks(self, parsed: Any) -> List[Any]:
        """Extract risks from various response formats"""
        risks = []
        
        if isinstance(parsed, dict):
            # Standard risks array
            if isinstance(parsed.get("risks"), list):
                risks.extend(parsed["risks"])
            
            # Alternative key names
            for key in ["risk_items", "risk_analysis", "items"]:
                if isinstance(parsed.get(key), list):
                    risks.extend(parsed[key])
        
        elif isinstance(parsed, list):
            # Direct array of risks
            risks.extend(parsed)
        
        return risks

    def _normalize_risk(self, risk: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Normalize individual risk item"""
        if not risk or not isinstance(risk, dict):
            return None
        
        # Extract and validate fields
        title = (risk.get("title") or risk.get("risk") or risk.get("name") or 
                f"Risk {index + 1}")
        description = (risk.get("description") or risk.get("detail") or 
                      risk.get("explanation") or "")
        
        if not description:
            return None
        
        # Normalize likelihood and impact
        likelihood = self._normalize_level(risk.get("likelihood") or risk.get("probability") or risk.get("severity"))
        impact = self._normalize_level(risk.get("impact") or risk.get("impact_level"))
        
        # Calculate severity score
        severity_score = self._calculate_severity_score(likelihood, impact)
        
        # Determine category
        category = self._determine_risk_category(title, description, risk.get("category"))
        
        return {
            "id": hashlib.sha1(f"{title}{description}".encode()).hexdigest()[:12],
            "title": title,
            "description": description,
            "category": category,
            "likelihood": likelihood,
            "impact": impact,
            "severity_score": severity_score,
            "mitigation": risk.get("mitigation") or risk.get("remediation") or "",
            "validation_experiment": risk.get("validation_experiment") or risk.get("experiment") or ""
        }

    def _normalize_level(self, value: Any) -> str:
        """Normalize risk level to high/medium/low"""
        if not value:
            return "medium"
        
        s = str(value).strip().lower()
        if s in ["high", "h", "3", "critical"]:
            return "high"
        elif s in ["low", "l", "1", "minor"]:
            return "low"
        return "medium"

    def _calculate_severity_score(self, likelihood: str, impact: str) -> int:
        """Calculate numerical severity score"""
        scores = {"low": 1, "medium": 2, "high": 3}
        return scores.get(likelihood, 2) * scores.get(impact, 2)

    def _determine_risk_category(self, title: str, description: str, existing_category: Any) -> str:
        """Determine risk category from content"""
        if existing_category and isinstance(existing_category, str):
            return existing_category.lower()
        
        text = f"{title} {description}".lower()
        
        category_keywords = {
            "market": ["market", "competition", "customer", "acquisition", "demand", "saturation"],
            "financial": ["financial", "revenue", "cost", "cash", "funding", "burn", "profit"],
            "technical": ["technical", "technology", "software", "development", "scalability", "infrastructure"],
            "regulatory": ["regulatory", "legal", "compliance", "law", "regulation", "license"],
            "talent": ["talent", "team", "hire", "skill", "recruitment", "retention"],
            "external": ["external", "economic", "political", "environment", "supply chain", "vendor"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "operational"

    def _calculate_overall_score(self, risks: List[Dict[str, Any]]) -> int:
        """Calculate overall risk score from individual risks"""
        if not risks:
            return 50
        
        total_severity = sum(risk.get("severity_score", 0) for risk in risks)
        max_possible = len(risks) * 9  # 3 (high likelihood) * 3 (high impact)
        
        if max_possible == 0:
            return 50
            
        return min(100, int((total_severity / max_possible) * 100))

    def _determine_risk_level(self, score: Optional[int]) -> str:
        """Determine risk level from score"""
        if score is None:
            return "unknown"
        elif score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"

    def _categorize_risks(self, risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorize risks and count by category"""
        categories = {}
        for risk in risks:
            category = risk.get("category", "other")
            categories[category] = categories.get(category, 0) + 1
        
        return categories

    def _create_risk_matrix(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create prioritized risk matrix (top 5 by severity)"""
        sorted_risks = sorted(risks, key=lambda x: x.get("severity_score", 0), reverse=True)
        return sorted_risks[:5]

    def _generate_recommendations(self, risks: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations from top risks"""
        top_risks = sorted(risks, key=lambda x: x.get("severity_score", 0), reverse=True)[:3]
        
        recommendations = []
        for risk in top_risks:
            if risk.get("mitigation"):
                recommendations.append(risk["mitigation"])
            else:
                recommendations.append(f"Address {risk['title']} risk through validation and mitigation planning")
        
        # Add general recommendations
        recommendations.extend([
            "Conduct thorough market validation with potential customers",
            "Develop detailed financial projections with conservative assumptions",
            "Create comprehensive risk mitigation plan with assigned owners"
        ])
        
        return recommendations[:5]  # Return top 5

    def _validate_score(self, score: Any, default: Optional[int] = None) -> Optional[int]:
        """Validate and normalize score values"""
        if score is None:
            return default
        
        try:
            score_int = int(score)
            return max(0, min(100, score_int))
        except (ValueError, TypeError):
            return default

    def _comprehensive_fallback_analysis(self, idea: str, location: str, market_data: dict) -> Dict[str, Any]:
        """Comprehensive fallback analysis when API fails"""
        industry = self._detect_industry(idea)
        
        base_risks = [
            {
                "id": "fallback_1",
                "title": "Market Competition and Saturation",
                "description": "High competition in this space may limit market share and profitability",
                "category": "market",
                "likelihood": "high",
                "impact": "high",
                "severity_score": 9,
                "mitigation": "Conduct thorough competitive analysis and identify unique differentiated value proposition",
                "validation_experiment": "Survey potential customers about existing solutions and unmet needs"
            },
            {
                "id": "fallback_2",
                "title": "Customer Acquisition Cost (CAC) Sustainability",
                "description": "Potential high cost to acquire customers may make business model unviable",
                "category": "financial",
                "likelihood": "medium",
                "impact": "high",
                "severity_score": 6,
                "mitigation": "Test multiple acquisition channels and focus on organic growth strategies with lower CAC",
                "validation_experiment": "Run small-scale acquisition tests to measure actual CAC"
            },
            {
                "id": "fallback_3",
                "title": "Technical Implementation Complexity",
                "description": "Complex technical requirements may lead to delays, cost overruns, and scalability issues",
                "category": "technical",
                "likelihood": "medium",
                "impact": "high",
                "severity_score": 6,
                "mitigation": "Build experienced technical team and consider phased implementation approach",
                "validation_experiment": "Create technical proof-of-concept to validate implementation approach"
            }
        ]
        
        # Add industry-specific risks
        if industry == "healthcare":
            base_risks.append({
                "id": "fallback_health_1",
                "title": "Regulatory Compliance and Liability",
                "description": "Healthcare regulations and potential liability risks require careful compliance planning",
                "category": "regulatory",
                "likelihood": "high",
                "impact": "high",
                "severity_score": 9,
                "mitigation": "Engage healthcare legal experts early and implement robust compliance protocols",
                "validation_experiment": "Consult with regulatory experts to understand specific requirements"
            })
        
        return {
            "summary": f"Comprehensive risk analysis for {idea} in {location or 'target market'}. Analysis identifies key risks across market, financial, and technical dimensions that require careful mitigation planning.",
            "overall_risk_score": 65,
            "risk_level": "medium",
            "risk_categories": {"market": 1, "financial": 1, "technical": 1, "regulatory": 1 if industry == "healthcare" else 0},
            "risks": base_risks,
            "risk_matrix": base_risks[:3],
            "recommendations": [
                "Conduct thorough market validation with potential customers",
                "Develop detailed financial projections with conservative assumptions",
                "Build experienced team with relevant industry expertise",
                "Create comprehensive risk mitigation plan with assigned owners"
            ],
            "confidence_score": 70,
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "industry": industry,
                "location": location,
                "idea": idea,
                "is_fallback": True
            }
        }