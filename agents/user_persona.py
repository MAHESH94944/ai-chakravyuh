"""Enhanced UserPersonaAgent with real demographic data and validation."""

from .base_agent import BaseAgent
import time
from core.clients import generate_text, enhanced_web_search, get_location_data
from models.schemas import UserPersonaResult, UserPersonaDetail
import json
from typing import Dict, Any, List
import re


class UserPersonaAgent(BaseAgent):
    """
    Advanced UserPersonaAgent that creates realistic user personas based on 
    actual demographic data and market research.
    """
    
    def run(self, idea: str, market_research_data: Dict[str, Any] = None, 
            location: Dict[str, Any] = None) -> Dict[str, Any]:
        print(f"👤 UserPersonaAgent: Creating realistic user persona for '{idea}'")
        
        try:
            # Extract location information
            country_code = location.get("country_code", "US") if location else "US"
            city = location.get("city", "") if location else ""
            region = location.get("region", "") if location else ""
            
            # Research target audience demographics
            demographic_data = self._research_demographics(idea, country_code, city, region)
            
            # Research user behavior and pain points
            behavior_data = self._research_user_behavior(idea, country_code)
            
            # Create validated persona using real data
            persona = self._create_validated_persona(
                idea, demographic_data, behavior_data, country_code, city
            )
            
            # Generate usage scenario
            scenario = self._create_usage_scenario(idea, persona, demographic_data)
            
            # Format results according to schema
            result = self._format_results(persona, scenario, demographic_data, behavior_data)
            
            # Add pointwise summary
            result["pointwise_summary"] = self.format_pointwise(result)
            
            return result
            
        except Exception as e:
            error_msg = f"User persona creation failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            # Return schema-compliant minimal persona result
            fp = self._create_fallback_persona(idea, 'US')
            result = UserPersonaResult(
                name=fp.get('name'),
                age=fp.get('age', 30),
                occupation=fp.get('occupation', 'Unknown'),
                story=fp.get('location', ''),
                pain_points=fp.get('pain_points', [])
            ).model_dump()
            result["pointwise_summary"] = [error_msg]
            return result
    
    def _research_demographics(self, idea: str, country_code: str, city: str, region: str) -> Dict[str, Any]:
        """Research demographic data for the target audience."""
        print(f"   Researching demographics in {city}, {region}, {country_code}")
        
        demographic_data = {
            "age_data": [],
            "income_data": [],
            "occupation_data": [],
            "tech_adoption_data": [],
            "citations": []
        }
        
        # Search queries for demographic information
        queries = [
            f"target audience demographics {idea} {country_code}",
            f"average income {city} {region}",
            f"tech adoption rates {country_code}",
            f"occupation statistics {city} {region}",
            f"age distribution {idea} users {country_code}"
        ]
        
        for query in queries:
            try:
                results = enhanced_web_search(query, max_results=3, country=country_code.lower())
                for result in results:
                    # Extract and categorize demographic data
                    self._extract_demographic_data(result, demographic_data, query)
                    
                    # Add to citations
                    demographic_data["citations"].append({
                        "query": query,
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": (result.get("snippet") or result.get("content", ""))[:200] + "..." if len((result.get("snippet") or result.get("content", ""))) > 200 else (result.get("snippet") or result.get("content", ""))
                    })
                
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"   Demographic search failed: {query} - {e}")
                continue
        
        return demographic_data
    
    def _extract_demographic_data(self, result: Dict, demographic_data: Dict, query: str):
        """Extract and categorize demographic data from search results."""
        snippet = (result.get("snippet") or result.get("content", "")).lower()
        
        # Age data
        age_patterns = [
            r'average age[^\d]*(\d+)',
            r'aged[^\d]*(\d+)[^\d]*to[^\d]*(\d+)',
            r'age group[^\d]*(\d+)[^\d]*-\s*(\d+)'
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, snippet)
            for match in matches:
                if len(match) == 1:
                    demographic_data["age_data"].append({
                        "value": int(match[0]),
                        "type": "average_age",
                        "source": result.get("url")
                    })
                elif len(match) == 2:
                    demographic_data["age_data"].append({
                        "range": [int(match[0]), int(match[1])],
                        "type": "age_range",
                        "source": result.get("url")
                    })
        
        # Income data
        income_patterns = [
            r'average income[^\d]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'median income[^\d]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'salary[^\d]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in income_patterns:
            matches = re.findall(pattern, snippet)
            for match in matches:
                try:
                    income = float(match.replace(',', ''))
                    demographic_data["income_data"].append({
                        "amount": income,
                        "type": "average_income",
                        "currency": "USD",  # Will be converted later if needed
                        "source": result.get("url")
                    })
                except ValueError:
                    continue
    
    def _research_user_behavior(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Research user behavior and pain points."""
        behavior_data = {
            "pain_points": [],
            "behavior_patterns": [],
            "motivations": [],
            "citations": []
        }
        
        queries = [
            f"user pain points {idea}",
            f"customer challenges {idea} {country_code}",
            f"user behavior patterns {idea}",
            f"what do users want from {idea}"
        ]
        
        for query in queries:
            try:
                results = enhanced_web_search(query, max_results=3, country=country_code.lower())
                for result in results:
                    # Extract behavioral insights
                    self._extract_behavioral_insights(result, behavior_data)
                    
                    behavior_data["citations"].append({
                        "query": query,
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": (result.get("snippet") or result.get("content", ""))[:200] + "..." if len((result.get("snippet") or result.get("content", ""))) > 200 else (result.get("snippet") or result.get("content", ""))
                    })
                
                time.sleep(0.5)
            except Exception as e:
                print(f"   Behavior research failed: {query} - {e}")
                continue
        
        return behavior_data
    
    def _extract_behavioral_insights(self, result: Dict, behavior_data: Dict):
        """Extract behavioral insights from search results."""
        snippet = (result.get("snippet") or result.get("content", "")).lower()
        
        # Pain points
        pain_keywords = ["frustrated", "difficult", "challenge", "problem", "issue", "pain point"]
        if any(keyword in snippet for keyword in pain_keywords):
            behavior_data["pain_points"].append({
                "description": (result.get("snippet") or result.get("content", ""))[:150] + "..." if len((result.get("snippet") or result.get("content", ""))) > 150 else (result.get("snippet") or result.get("content", "")),
                "source": result.get("url")
            })
        
        # Motivations
        motivation_keywords = ["want", "need", "desire", "looking for", "goal"]
        if any(keyword in snippet for keyword in motivation_keywords):
            behavior_data["motivations"].append({
                "description": (result.get("snippet") or result.get("content", ""))[:150] + "..." if len((result.get("snippet") or result.get("content", ""))) > 150 else (result.get("snippet") or result.get("content", "")),
                "source": result.get("url")
            })
    
    def _create_validated_persona(self, idea: str, demographic_data: Dict, 
                                behavior_data: Dict, country_code: str, city: str) -> Dict[str, Any]:
        """Create a validated user persona using real data."""
        
        schema_str = '''{
    "name": "string",
    "age": number,
    "occupation": "string",
    "income": number,
    "income_currency": "string",
    "location": "string",
    "goals": ["string"],
    "pain_points": ["string"],
    "tech_savviness": number,
    "buying_behavior": "string",
    "validation_sources": ["string"]
}'''

        prompt = (
            "Create a realistic user persona for this startup idea: \"" + idea + "\"\n\n"
            "Location: " + (city or "") + ", " + (country_code or "") + "\n\n"
            "Demographic Research Data:\n" + json.dumps(demographic_data, indent=2) + "\n\n"
            "Behavioral Research Data:\n" + json.dumps(behavior_data, indent=2) + "\n\n"
            "Create a detailed user persona with the following structure. Return ONLY valid JSON:\n" + schema_str
        )
        
        try:
            response = generate_text(prompt)
            cleaned = response.text.strip().replace('```json', '').replace('```', '').strip()
            try:
                persona_data = json.loads(cleaned)
            except Exception:
                fp = self._create_fallback_persona(idea, country_code)
                # Ensure required fields exist
                persona_data = fp

            # Add validation sources (safe)
            persona_data.setdefault("validation_sources", [])
            persona_data["validation_sources"] += [
                source.get("url") for source in demographic_data.get("citations", [])[:3]
            ]
            persona_data["validation_sources"] += [
                source.get("url") for source in behavior_data.get("citations", [])[:2]
            ]

            return persona_data
        except Exception as e:
            print(f"   Persona creation failed: {e}")
            return self._create_fallback_persona(idea, country_code)
    
    def _create_fallback_persona(self, idea: str, country_code: str) -> Dict[str, Any]:
        """Create a fallback persona when research data is limited."""
        # Base persona templates for different regions. Make them idea-aware (fitness vs generic business).
        idea_lower = (idea or '').lower()
        is_fitness = any(k in idea_lower for k in ['fitness', 'wellness', 'workout', 'diet', 'health', 'gym'])

        # Base persona templates for different regions
        if country_code in ["US", "CA", "GB", "AU"]:
            return {
                "name": "Sarah Johnson",
                "age": 32,
                "occupation": "Marketing Manager",
                "income": 75000,
                "income_currency": "USD",
                "location": "Urban area",
                "goals": ["Save time", "Increase productivity", "Stay organized"],
                "pain_points": ["Too many manual tasks", "Inefficient processes", "High costs"],
                "tech_savviness": 4,
                "buying_behavior": "Researches online reviews before purchasing",
                "validation_sources": ["Industry standard persona template"]
            }
        elif country_code in ["IN", "PK", "BD", "LK"]:
            if is_fitness:
                return {
                    "name": "Raj Sharma",
                    "age": 30,
                    "occupation": "Software Engineer",
                    "income": 900000,
                    "income_currency": "INR",
                    "location": "Metro city",
                    "goals": ["Stay fit despite a busy schedule", "Eat healthier with local cuisine", "Track workouts and progress"],
                    "pain_points": ["Difficulty tracking diet with Indian foods", "Lack of time for the gym", "Confusion over local nutrition guidance"],
                    "tech_savviness": 5,
                    "buying_behavior": "Values cost-effective, localized solutions",
                    "validation_sources": ["Regional persona template"]
                }
            else:
                return {
                    "name": "Raj Sharma",
                    "age": 28,
                    "occupation": "Software Engineer",
                    "income": 1200000,
                    "income_currency": "INR",
                    "location": "Metro city",
                    "goals": ["Career advancement", "Skill development", "Work-life balance"],
                    "pain_points": ["Limited growth opportunities", "High competition", "Work pressure"],
                    "tech_savviness": 5,
                    "buying_behavior": "Values quality and brand reputation",
                    "validation_sources": ["Regional persona template"]
                }
        else:
            return {
                "name": "David Chen",
                "age": 35,
                "occupation": "Business Professional",
                "income": 50000,
                "income_currency": "USD",
                "location": "City center",
                "goals": ["Business growth", "Efficiency improvement", "Cost reduction"],
                "pain_points": ["Manual processes", "High operational costs", "Time constraints"],
                "tech_savviness": 3,
                "buying_behavior": "Seeks recommendations from peers",
                "validation_sources": ["Generic business persona template"]
            }
    
    def _create_usage_scenario(self, idea: str, persona: Dict, demographic_data: Dict) -> str:
        """Create a realistic usage scenario for the persona."""
        
        prompt = f"""
        Create a realistic usage scenario for this user persona using the startup idea: "{idea}"
        
        Persona Details:
        {json.dumps(persona, indent=2)}
        
        Write a compelling short story (1-2 paragraphs) showing how this persona would discover,
        evaluate, and use the product in their daily life. Include specific pain points and how
        the product solves them.
        
        Return ONLY the scenario text without any additional formatting.
        """
        
        try:
            response = generate_text(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"   Scenario creation failed: {e}")
            return f"{persona.get('name', 'User')} discovers {idea} while searching for solutions to {persona.get('pain_points',[None])[0] if persona.get('pain_points') else 'a problem'}. After evaluating options, they decide to use it because it addresses their specific needs for {persona.get('goals',[None])[0] if persona.get('goals') else 'their goals'}."
    
    def _format_results(self, persona: Dict, scenario: str, 
                       demographic_data: Dict, behavior_data: Dict) -> Dict[str, Any]:
        """Format results according to the UserPersonaResult schema."""
        # Create primary persona detail
        try:
            primary_persona = UserPersonaDetail(**persona)
        except Exception as e:
            # Fallback to deterministic persona
            print(f"   Persona validation failed, using fallback persona: {e}")
            fallback = self._create_fallback_persona(scenario if isinstance(scenario, str) else 'Idea', persona.get('income_currency', 'US')) if isinstance(persona, dict) else self._create_fallback_persona('Idea', 'US')
            primary_persona = UserPersonaDetail(**fallback)
        
        # Create demographic validation sources
        demographic_validation = []
        for citation in demographic_data.get("citations", [])[:5]:
            demographic_validation.append({
                "type": "demographic_research",
                "source": citation.get("url"),
                "description": citation.get("snippet")
            })
        
        for citation in behavior_data.get("citations", [])[:3]:
            demographic_validation.append({
                "type": "behavioral_research",
                "source": citation.get("url"),
                "description": citation.get("snippet")
            })
        
        # Build a concise pointwise summary (useful for fallbacks too)
        summary_points = []
        summary_points.append(f"Name: {primary_persona.name}, Age: {primary_persona.age}, Occupation: {primary_persona.occupation}")
        if getattr(primary_persona, 'goals', None):
            summary_points.append("Top goals: " + ", ".join(primary_persona.goals[:3]))
        if primary_persona.pain_points:
            summary_points.append("Key pain points: " + ", ".join(primary_persona.pain_points[:3]))

        # Collect validation sources
        validation_sources = []
        validation_sources += [c.get('url') for c in demographic_data.get('citations', []) if c.get('url')][:5]
        validation_sources += [c.get('url') for c in behavior_data.get('citations', []) if c.get('url')][:3]

        # Ensure we have a short deterministic story when LLM is unavailable
        if not scenario or not isinstance(scenario, str) or not scenario.strip():
            first_pain = primary_persona.pain_points[0] if primary_persona.pain_points else 'managing fitness and diet'
            location_hint = primary_persona.location if getattr(primary_persona, 'location', None) else 'their city'
            scenario_text = f"{primary_persona.name}, a {primary_persona.age}-year-old {primary_persona.occupation} from {location_hint}, struggles with {first_pain}. They would use the app to get short personalized workouts and meal plans that fit their schedule."
        else:
            scenario_text = scenario

        result_obj = UserPersonaResult(
            name=primary_persona.name,
            age=primary_persona.age,
            occupation=primary_persona.occupation,
            story=scenario_text,
            pain_points=primary_persona.pain_points
        ).model_dump()

        # Attach extra helpful fields for consumers (not part of strict UserPersonaResult schema but useful internally)
        result_obj.setdefault('pointwise_summary', summary_points)
        if validation_sources:
            result_obj.setdefault('validation_sources', validation_sources)

        # Ensure pointwise_summary is not empty
        if not result_obj.get('pointwise_summary'):
            result_obj['pointwise_summary'] = summary_points if summary_points else [f"{primary_persona.name}: {primary_persona.occupation}"]

        return result_obj