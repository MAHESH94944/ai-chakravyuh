# agents/technical_feasibility.py
"""Enhanced TechnicalFeasibilityAgent with real technology research and validation."""

from .base_agent import BaseAgent
import time
from core.clients import generate_text, enhanced_web_search
from models.schemas import TechnicalFeasibilityResult, TechnicalStack, DevelopmentTimeline
import json
from typing import Dict, Any, List
import re


class TechnicalFeasibilityAgent(BaseAgent):
    """
    Advanced TechnicalFeasibilityAgent that provides realistic technical assessments
    based on current technology trends, implementation complexity, and resource requirements.
    """
    
    def run(self, idea: str, market_research_data: Dict[str, Any] = None,
            location: Dict[str, Any] = None) -> Dict[str, Any]:
        print(f"🛠 TechnicalFeasibilityAgent: Analyzing technical feasibility for '{idea}'")
        
        try:
            # Extract location information for talent availability
            country_code = location.get("country_code", "US") if location else "US"
            city = location.get("city", "") if location else ""
            
            # Research technology requirements and trends
            tech_research = self._research_technology(idea, country_code)
            
            # Research implementation challenges
            challenge_research = self._research_challenges(idea, country_code)
            
            # Research talent availability and costs
            talent_research = self._research_talent(idea, country_code, city)
            
            # Create comprehensive technical assessment
            assessment = self._create_technical_assessment(
                idea, tech_research, challenge_research, talent_research, country_code
            )
            
            # Format results according to schema
            result = self._format_results(assessment, tech_research, challenge_research, talent_research)
            
            # Add pointwise summary
            result["pointwise_summary"] = self.format_pointwise(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Technical feasibility analysis failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {"error": error_msg, "pointwise_summary": [error_msg]}
    
    def _research_technology(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Research technology requirements and trends."""
        print(f"   Researching technology requirements for '{idea}'")
        
        tech_data = {
            "frontend_trends": [],
            "backend_trends": [],
            "database_options": [],
            "infrastructure_services": [],
            "ai_ml_services": [],
            "citations": []
        }
        
        queries = [
            f"technology stack for {idea} startup",
            f"best frontend framework for {idea}",
            f"backend technology for {idea} application",
            f"database solutions for {idea}",
            f"cloud infrastructure for {idea}",
            f"AI ML services for {idea}"
        ]
        
        for query in queries:
            try:
                results = enhanced_web_search(query, max_results=3, country=country_code.lower())
                for result in results:
                    # Categorize technology findings
                    self._categorize_technology_findings(result, tech_data, query)
                    
                    tech_data["citations"].append({
                        "query": query,
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result["snippet"][:200] + "..." if len(result["snippet"]) > 200 else result["snippet"]
                    })
                
                time.sleep(0.5)
            except Exception as e:
                print(f"   Technology research failed: {query} - {e}")
                continue
        
        return tech_data
    
    def _categorize_technology_findings(self, result: Dict, tech_data: Dict, query: str):
        """Categorize technology findings from search results."""
        snippet = result["snippet"].lower()
        title = result["title"].lower()
        
        # Frontend technologies
        frontend_keywords = ["react", "angular", "vue", "svelte", "frontend", "ui framework", "javascript", "typescript"]
        if any(keyword in snippet or keyword in title for keyword in frontend_keywords):
            tech_data["frontend_trends"].append({
                "technology": self._extract_technology_name(snippet),
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
        
        # Backend technologies
        backend_keywords = ["node", "python", "django", "flask", "spring", "java", "backend", "api", "server"]
        if any(keyword in snippet or keyword in title for keyword in backend_keywords):
            tech_data["backend_trends"].append({
                "technology": self._extract_technology_name(snippet),
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
        
        # Database technologies
        database_keywords = ["mysql", "postgresql", "mongodb", "redis", "database", "sql", "nosql"]
        if any(keyword in snippet or keyword in title for keyword in database_keywords):
            tech_data["database_options"].append({
                "technology": self._extract_technology_name(snippet),
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
    
    def _extract_technology_name(self, text: str) -> str:
        """Extract technology names from text."""
        # Common technology patterns
        patterns = [
            r'react(?:\.js)?', r'angular', r'vue\.js', r'svelte',
            r'node\.js', r'python', r'django', r'flask', r'spring',
            r'mysql', r'postgresql', r'mongodb', r'redis',
            r'aws', r'azure', r'google cloud', r'firebase',
            r'tensorflow', r'pytorch', r'scikit-learn'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(0).title()
        
        return "Technology mentioned"
    
    def _research_challenges(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Research implementation challenges and risks."""
        challenge_data = {
            "technical_challenges": [],
            "scaling_issues": [],
            "security_concerns": [],
            "integration_problems": [],
            "citations": []
        }
        
        queries = [
            f"technical challenges implementing {idea}",
            f"scaling issues {idea} application",
            f"security concerns {idea}",
            f"integration challenges {idea}",
            f"common problems building {idea}"
        ]
        
        for query in queries:
            try:
                results = enhanced_web_search(query, max_results=3, country=country_code.lower())
                for result in results:
                    # Categorize challenge findings
                    self._categorize_challenge_findings(result, challenge_data, query)
                    
                    challenge_data["citations"].append({
                        "query": query,
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result["snippet"][:200] + "..." if len(result["snippet"]) > 200 else result["snippet"]
                    })
                
                time.sleep(0.5)
            except Exception as e:
                print(f"   Challenge research failed: {query} - {e}")
                continue
        
        return challenge_data
    
    def _categorize_challenge_findings(self, result: Dict, challenge_data: Dict, query: str):
        """Categorize challenge findings from search results."""
        snippet = result["snippet"].lower()
        
        if "challenge" in query or "problem" in query:
            challenge_data["technical_challenges"].append({
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
        elif "scaling" in query:
            challenge_data["scaling_issues"].append({
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
        elif "security" in query:
            challenge_data["security_concerns"].append({
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
        elif "integration" in query:
            challenge_data["integration_problems"].append({
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
    
    def _research_talent(self, idea: str, country_code: str, city: str) -> Dict[str, Any]:
        """Research talent availability and costs."""
        talent_data = {
            "developer_availability": [],
            "salary_data": [],
            "skill_availability": [],
            "citations": []
        }
        
        location_suffix = f" in {city}" if city else f" in {country_code}"
        queries = [
            f"software developer availability{location_suffix}",
            f"tech talent{location_suffix}",
            f"developer salaries{location_suffix}",
            f"hiring challenges{location_suffix}",
            f"required skills for {idea}"
        ]
        
        for query in queries:
            try:
                results = enhanced_web_search(query, max_results=3, country=country_code.lower())
                for result in results:
                    # Extract talent information
                    self._extract_talent_information(result, talent_data, query)
                    
                    talent_data["citations"].append({
                        "query": query,
                        "title": result["title"],
                        "url": result["url"],
                        "snippet": result["snippet"][:200] + "..." if len(result["snippet"]) > 200 else result["snippet"]
                    })
                
                time.sleep(0.5)
            except Exception as e:
                print(f"   Talent research failed: {query} - {e}")
                continue
        
        return talent_data
    
    def _extract_talent_information(self, result: Dict, talent_data: Dict, query: str):
        """Extract talent information from search results."""
        snippet = result["snippet"].lower()
        
        # Salary data
        salary_patterns = [
            r'average salary[^\d]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'median salary[^\d]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'developer earn[^\d]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in salary_patterns:
            matches = re.findall(pattern, snippet)
            for match in matches:
                try:
                    salary = float(match.replace(',', ''))
                    talent_data["salary_data"].append({
                        "amount": salary,
                        "currency": "USD",
                        "role": "developer",
                        "source": result["url"]
                    })
                except ValueError:
                    continue
        
        # Availability data
        availability_keywords = ["shortage", "high demand", "difficult to find", "competitive", "scarce"]
        if any(keyword in snippet for keyword in availability_keywords):
            talent_data["developer_availability"].append({
                "description": result["snippet"][:150] + "..." if len(result["snippet"]) > 150 else result["snippet"],
                "source": result["url"]
            })
    
    def _create_technical_assessment(self, idea: str, tech_research: Dict, 
                                   challenge_research: Dict, talent_research: Dict,
                                   country_code: str) -> Dict[str, Any]:
        """Create comprehensive technical assessment."""
        
        prompt = f"""
        Create a detailed technical feasibility assessment for this startup idea: "{idea}"
        
        Location: {country_code}
        
        Technology Research:
        {json.dumps(tech_research, indent=2)}
        
        Challenge Research:
        {json.dumps(challenge_research, indent=2)}
        
        Talent Research:
        {json.dumps(talent_research, indent=2)}
        
        Provide a comprehensive assessment including:
        1. Recommended technology stack (frontend, backend, database, infrastructure)
        2. Key technical challenges and risks
        3. Development timeline estimates
        4. Team requirements and roles
        5. Cost estimates for development
        6. Feasibility rating (feasible/feasible_with_research/high_risk)
        7. Confidence score (0-100)
        
        Return ONLY valid JSON with this structure:
        {{
            "key_challenges": ["string"],
            "suggested_stack": {{
                "frontend": ["string"],
                "backend": ["string"],
                "database": ["string"],
                "infrastructure": ["string"],
                "third_party_services": ["string"]
            }},
            "architecture_overview": "string",
            "data_pipeline": "string",
            "development_timeline": {{
                "research_phase": number,
                "design_phase": number,
                "development_phase": number,
                "testing_phase": number,
                "deployment_phase": number
            }},
            "cost_estimate": {{
                "development": number,
                "infrastructure": number,
                "maintenance": number
            }},
            "team_requirements": ["string"],
            "feasibility": "string",
            # agents/technical_feasibility.py (continued)
            "confidence_score": number,
            "research_sources": ["string"]
        }}
        """
        
        try:
            response = generate_text(prompt)
            cleaned = response.text.strip().replace('```json', '').replace('```', '').strip()
            try:
                assessment = json.loads(cleaned)
            except Exception:
                return self._create_fallback_assessment(idea, country_code)

            # Add research sources
            assessment["research_sources"] = [
                source["url"] for source in tech_research["citations"][:5]
            ] + [
                source["url"] for source in challenge_research["citations"][:3]
            ] + [
                source["url"] for source in talent_research["citations"][:2]
            ]

            return assessment
        except Exception as e:
            print(f"   Technical assessment failed: {e}")
            return self._create_fallback_assessment(idea, country_code)
    
    def _create_fallback_assessment(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Create fallback technical assessment."""
        return {
            "key_challenges": [
                "Scalability for rapid user growth",
                "Data security and privacy compliance",
                "Integration with existing systems",
                "Real-time data processing requirements"
            ],
            "suggested_stack": {
                "frontend": ["React", "TypeScript", "Tailwind CSS"],
                "backend": ["Node.js", "Express", "Python"],
                "database": ["PostgreSQL", "Redis", "MongoDB"],
                "infrastructure": ["AWS", "Docker", "Kubernetes"],
                "third_party_services": ["Stripe", "Twilio", "SendGrid"]
            },
            "architecture_overview": "Microservices architecture with API gateway, separate services for different functionalities, and cloud-native deployment",
            "data_pipeline": "Real-time data ingestion through Kafka, processing with Spark, storage in data lake, and analytics with Presto",
            "development_timeline": {
                "research_phase": 2,
                "design_phase": 3,
                "development_phase": 16,
                "testing_phase": 4,
                "deployment_phase": 2
            },
            "cost_estimate": {
                "development": 150000,
                "infrastructure": 5000,
                "maintenance": 2000
            },
            "team_requirements": [
                "Full-stack developers (2-3)",
                "Backend engineer",
                "DevOps engineer",
                "UI/UX designer",
                "Product manager"
            ],
            "feasibility": "feasible_with_research",
            "confidence_score": 75,
            "research_sources": ["Industry standard technology patterns"]
        }
    
    def _format_results(self, assessment: Dict, tech_research: Dict, 
                       challenge_research: Dict, talent_research: Dict) -> Dict[str, Any]:
        """Format results according to the TechnicalFeasibilityResult schema."""
        try:
            technical_stack = TechnicalStack(**assessment["suggested_stack"])
        except Exception as e:
            print(f"   TechnicalFeasibility formatting failed, using fallback: {e}")
            return self._create_fallback_assessment(assessment.get('idea', 'Idea'), assessment.get('country_code', 'US'))
        
        # Create development timeline
        development_timeline = DevelopmentTimeline(**assessment["development_timeline"])
        
        # Create research sources
        research_sources = []
        for citation in tech_research["citations"][:3]:
            research_sources.append({
                "type": "technology_research",
                "url": citation["url"],
                "description": citation["snippet"]
            })
        
        for citation in challenge_research["citations"][:2]:
            research_sources.append({
                "type": "challenge_research",
                "url": citation["url"],
                "description": citation["snippet"]
            })
        
        return TechnicalFeasibilityResult(
            key_challenges=assessment["key_challenges"],
            suggested_stack=technical_stack,
            architecture_overview=assessment["architecture_overview"],
            data_pipeline=assessment["data_pipeline"],
            development_timeline=development_timeline,
            cost_estimate=assessment["cost_estimate"],
            team_requirements=assessment["team_requirements"],
            feasibility=assessment["feasibility"],
            confidence_score=assessment["confidence_score"],
            research_sources=research_sources
        ).dict()
