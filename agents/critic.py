# agents/critic.py
"""Enhanced CriticAgent with deep analysis and real-world validation."""

from .base_agent import BaseAgent
import time
from core.clients import generate_text, enhanced_web_search
from models.schemas import CriticResult
import json
from typing import Dict, Any, List


class CriticAgent(BaseAgent):
    """
    Advanced CriticAgent that provides deep critical analysis identifying
    blind spots, contradictions, and validation requirements.
    """
    
    def run(self, idea: str, finance_data: Dict[str, Any], risk_data: Dict[str, Any],
            tech_data: Dict[str, Any], market_data: Dict[str, Any] = None,
            location: Dict[str, Any] = None) -> Dict[str, Any]:
        print(f"🎯 CriticAgent: Providing critical analysis for '{idea}'")
        
        try:
            # Extract location information
            country_code = location.get("country_code", "US") if location else "US"
            
            # Research common startup failures and pitfalls
            failure_research = self._research_failures(idea, country_code)
            
            # Research validation methods and due diligence
            validation_research = self._research_validation(idea, country_code)
            
            # Create comprehensive critical analysis
            critique = self._create_critical_analysis(
                idea, finance_data, risk_data, tech_data, market_data,
                failure_research, validation_research, country_code
            )
            
            # Format results according to schema
            result = self._format_results(critique, failure_research, validation_research)
            
            # Add pointwise summary
            result["pointwise_summary"] = self.format_pointwise(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Critical analysis failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {"error": error_msg, "pointwise_summary": [error_msg]}
    
    def _research_failures(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Research common startup failures and pitfalls."""
        failure_data = {
            "common_failures": [],
            "pitfalls": [],
            "warning_signs": [],
            "citations": []
        }
        
        queries = [
            f"why startups fail {idea} {country_code}",
            f"common pitfalls {idea} business",
            f"startup failure reasons {country_code}",
            f"warning signs startup failure",
            f"business model flaws {idea}"
        ]
        
        for query in queries:
            try:
                results = enhanced_web_search(query, max_results=3, country=country_code.lower())
                for result in results:
                    # Extract failure insights
                    self._extract_failure_insights(result, failure_data, query)
                    
                    failure_data["citations"].append({
                        "query": query,
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result["snippet"][:200] + "..." if len(result["snippet"]) > 200 else result["snippet"]
                    })
                
                time.sleep(0.5)
            except Exception as e:
                print(f"   Failure research failed: {query} - {e}")
                continue
        
        return failure_data
    
    def _extract_failure_insights(self, result: Dict, failure_data: Dict, query: str):
        """Extract failure insights from search results."""
        snippet = result["snippet"].lower()
        
        if "fail" in query or "pitfall" in query:
            failure_data["common_failures"].append({
                "insight": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
        elif "warning" in query:
            failure_data["warning_signs"].append({
                "insight": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
    
    def _research_validation(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Research validation methods and due diligence."""
        validation_data = {
            "validation_methods": [],
            "due_diligence": [],
            "success_factors": [],
            "citations": []
        }
        
        queries = [
            f"startup validation methods {idea}",
            f"due diligence {idea} business",
            f"how to validate {idea} idea",
            f"success factors startups {country_code}",
            f"minimum viable product validation"
        ]
        
        for query in queries:
            try:
                results = enhanced_web_search(query, max_results=3, country=country_code.lower())
                for result in results:
                    # Extract validation insights
                    self._extract_validation_insights(result, validation_data, query)
                    
                    validation_data["citations"].append({
                        "query": query,
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result["snippet"][:200] + "..." if len(result["snippet"]) > 200 else result["snippet"]
                    })
                
                time.sleep(0.5)
            except Exception as e:
                print(f"   Validation research failed: {query} - {e}")
                continue
        
        return validation_data
    
    def _extract_validation_insights(self, result: Dict, validation_data: Dict, query: str):
        """Extract validation insights from search results."""
        snippet = result["snippet"].lower()
        
        if "validation" in query or "validate" in query:
            validation_data["validation_methods"].append({
                "method": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
        elif "due diligence" in query:
            validation_data["due_diligence"].append({
                "insight": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
        elif "success" in query:
            validation_data["success_factors"].append({
                "factor": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
    
    def _create_critical_analysis(self, idea: str, finance_data: Dict, risk_data: Dict,
                                tech_data: Dict, market_data: Dict,
                                failure_research: Dict, validation_research: Dict,
                                country_code: str) -> Dict[str, Any]:
        """Create comprehensive critical analysis."""
        
        prompt = f"""
        As an experienced venture capitalist and startup critic, provide a brutally honest
        critical analysis of this startup idea: "{idea}"
        
        Location: {country_code}
        
        Financial Analysis:
        {json.dumps(finance_data, indent=2)}
        
        Risk Assessment:
        {json.dumps(risk_data, indent=2)}
        
        Technical Feasibility:
        {json.dumps(tech_data, indent=2)}
        
        Market Research:
        {json.dumps(market_data, indent=2) if market_data else "No market research data available"}
        
        Failure Research:
        {json.dumps(failure_research, indent=2)}
        
        Validation Research:
        {json.dumps(validation_research, indent=2)}
        
        Provide a comprehensive critical analysis including:
        1. The single most critical blind spot or flaw in the analysis
        2. Contradictory findings between different analyses
        3. Key validation questions that must be answered
        4. Evidence-based critique of assumptions
        5. Confidence score in the critique
        
        Return ONLY valid JSON with this structure:
        {{
            "critique": "string",
            "blind_spots": ["string"],
            "contradictory_findings": ["string"],
            "validation_questions": ["string"],
            "confidence_score": number,
            "evidence": ["string"]
        }}
        """
        
        try:
            response = generate_text(prompt)
            cleaned = response.text.strip().replace('```json', '').replace('```', '').strip()
            try:
                analysis = json.loads(cleaned)
            except Exception:
                return self._create_fallback_critique(idea, country_code)

            # Add evidence sources
            analysis["evidence"] = [
                source["url"] for source in failure_research["citations"][:3]
            ] + [
                source["url"] for source in validation_research["citations"][:2]
            ]

            return analysis
        except Exception as e:
            print(f"   Critical analysis failed: {e}")
            return self._create_fallback_critique(idea, country_code)
    
    def _create_fallback_critique(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Create fallback critical analysis."""
        return {
            "critique": f"The analysis for '{idea}' appears overly optimistic and lacks sufficient validation of key assumptions. The financial projections may not account for customer acquisition costs and market saturation risks.",
            "blind_spots": [
                "Customer validation and product-market fit testing",
                "Competitive response and market dynamics",
                "Operational scalability challenges"
            ],
            "contradictory_findings": [
                "Market research shows growth potential but risk assessment indicates high competition",
                "Technical feasibility suggests complexity but financials show low development costs"
            ],
            "validation_questions": [
                "Have you conducted customer interviews to validate the problem?",
                "What evidence supports the revenue projections?",
                "How will you differentiate from established competitors?",
                "What is your plan for customer acquisition and retention?"
            ],
            "confidence_score": 75,
            "evidence": ["Industry failure patterns and startup validation best practices"]
        }
    
    def _format_results(self, critique: Dict, failure_research: Dict, 
                       validation_research: Dict) -> Dict[str, Any]:
        """Format results according to the CriticResult schema."""
        
        # Create evidence list
        try:
            evidence = []
            for citation in failure_research["citations"][:3]:
                evidence.append({
                    "type": "failure_research",
                    "url": citation["url"],
                    "description": citation["snippet"]
                })
    
            for citation in validation_research["citations"][:2]:
                evidence.append({
                    "type": "validation_research",
                    "url": citation["url"],
                    "description": citation["snippet"]
                })
        except Exception as e:
            print(f"   Critic formatting failed to collect citations: {e}")
            evidence = [{"type": "fallback", "url": "", "description": "No citations available"}]
        
        return CriticResult(
            critique=critique["critique"],
            blind_spots=critique["blind_spots"],
            contradictory_findings=critique["contradictory_findings"],
            validation_questions=critique["validation_questions"],
            confidence_score=critique["confidence_score"],
            evidence=evidence
        ).dict()