# agents/base_agent.py
"""Base class for all agents with common functionality."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import time
from core.clients import generate_text, enhanced_web_search

class BaseAgent(ABC):
    def __init__(self):
        self.agent_type = self.__class__.__name__
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        pass
    
    def generate_structured_response(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate and validate structured response with retry logic."""
        max_retries = 2
        last_error = None
        for attempt in range(max_retries):
            try:
                resp_obj = generate_text(prompt, is_json=True)
                text = getattr(resp_obj, "text", str(resp_obj))
                parsed = json.loads(text)

                if self.validate_response(parsed, response_schema):
                    return parsed

                last_error = "validation_failed"
                # ask for correction once
                if attempt < max_retries - 1:
                    fix_prompt = (
                        "The previous response did not strictly follow the expected JSON schema. "
                        "Please reformat ONLY valid JSON that matches the schema.\n"
                        f"Schema: {json.dumps(response_schema)}\nPrevious response: {json.dumps(parsed)}"
                    )
                    time.sleep(0.2)
                    prompt = fix_prompt
                    continue
            except Exception as e:
                last_error = str(e)
                time.sleep(0.2)

        fallback = self.create_fallback_response()
        fallback["_error"] = last_error
        return fallback
    
    def validate_response(self, response: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Basic response validation against expected schema."""
        try:
            if isinstance(schema, dict):
                required_fields = list(schema.keys())
                return all(field in response for field in required_fields)
            # If schema is not a dict, fall back to basic sanity checks
            return isinstance(response, dict) and len(response) > 0
        except:
            return False
    
    def create_fallback_response(self) -> Dict[str, Any]:
        """Create a fallback response when all else fails."""
        return {
            "error": "Analysis unavailable",
            "status": "fallback",
            "pointwise_summary": ["Unable to complete analysis at this time"]
        }
    
    def format_pointwise(self, data: Dict[str, Any]) -> List[str]:
        """Convert complex data into simple bullet points."""
        points = []
        
        if "error" in data:
            return [f"Error: {data['error']}"]
        
        # Add relevant points based on data content
        if "executive_summary" in data:
            points.append(data["executive_summary"])
        
        if "market_size" in data and data["market_size"].get("total_addressable_market"):
            points.append(f"Market size: {data['market_size']['total_addressable_market']:,.0f} {data['market_size'].get('currency', 'USD')}")
        
        return points[:5]  # Return top 5 points