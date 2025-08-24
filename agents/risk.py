from .base_agent import BaseAgent
from core.clients import gemini_model
import json

class RiskAgent(BaseAgent):
    """
    An agent that identifies potential business risks based on market research.
    """
    def run(self, idea: str, market_research_data: dict) -> dict:
        """
        Executes the agent's task to identify risks.

        Args:
            idea: The startup idea text.
            market_research_data: The JSON output from the MarketResearchAgent.
        
        Returns:
            A dictionary containing a list of identified risks.
        """
        prompt = f"""
        You are a meticulous business risk analyst for a venture capital firm.
        Your job is to identify the top 3-5 potential risks for a startup based on its idea and the provided market research.

        **Startup Idea:**
        "{idea}"

        **Market Research Data:**
        {json.dumps(market_research_data, indent=2)}

        **Your Task:**
        For each risk you identify, provide a short title, a one-sentence detail explaining the risk, and a severity level (High, Medium, or Low).

        Return your response as a single, clean JSON object with a single key "risks". This key should contain a list of objects, where each object has "risk", "detail", and "severity" keys.
        
        Example Format:
        {{
          "risks": [
            {{ "risk": "Title of Risk 1", "detail": "...", "severity": "High" }},
            {{ "risk": "Title of Risk 2", "detail": "...", "severity": "Medium" }}
          ]
        }}
        """

        try:
            # Call the Gemini API for its analytical capabilities
            response = gemini_model.generate_content(prompt)
            
            # Clean and parse the JSON response
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_response)
            
            return result
        except Exception as e:
            print(f"An error occurred in RiskAgent: {e}")
            return {"error": f"Failed to generate risk analysis: {e}"}