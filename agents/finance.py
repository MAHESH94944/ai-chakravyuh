from .base_agent import BaseAgent
from core.clients import gemini_model
import json

class FinanceAgent(BaseAgent):
    """
    An agent that provides a high-level financial outlook for a startup idea
    based on market research data.
    """
    def run(self, idea: str, market_research_data: dict) -> dict:
        """
        Executes the agent's task to generate a financial outlook.

        Args:
            idea: The startup idea text.
            market_research_data: The JSON output from the MarketResearchAgent.
        
        Returns:
            A dictionary containing the financial analysis.
        """
        prompt = f"""
        You are a seasoned venture capitalist and financial analyst.
        Your task is to provide a high-level financial outlook for a startup idea based on the market research provided.
        Use the market size and growth rate data to inform your estimates.

        **Startup Idea:**
        "{idea}"

        **Market Research Data:**
        {json.dumps(market_research_data, indent=2)}

        **Your Task:**
        1.  Estimate the initial development costs required to launch a minimum viable product (MVP).
        2.  Estimate the ongoing monthly operational costs (servers, APIs, staff).
        3.  Suggest three potential revenue streams for this business model.

        Return your response as a single, clean JSON object with the following structure:
        {{
          "estimated_costs": {{
            "initial_development": "...",
            "monthly_operations": "..."
          }},
          "potential_revenue_streams": ["...", "...", "..."]
        }}
        """

        try:
            # Call the Gemini API for its strong reasoning
            response = gemini_model.generate_content(prompt)
            
            # Clean and parse the JSON response
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_response)
            
            return result
        except Exception as e:
            print(f"An error occurred in FinanceAgent: {e}")
            return {"error": f"Failed to generate financial analysis: {e}"}