from .base_agent import BaseAgent
from core.clients import gemini_model
import json

class FinanceAgent(BaseAgent):
    """
    An agent that provides a high-level financial outlook based on market research.
    """
    def run(self, market_research_data: dict) -> dict:
        """
        Executes the agent's task to generate a financial outlook.

        Args:
            market_research_data: The JSON output from the MarketResearchAgent.
        
        Returns:
            A dictionary containing estimated costs and potential revenue streams.
        """
        print(f"FinanceAgent: Starting financial analysis based on market data: {market_research_data.get('market_size', 'N/A')}")
        
        prompt = f"""
        You are an expert financial analyst for startups and venture capital.
        
        Based on the following market research data, provide a high-level financial outlook for this startup idea.
        
        Market Research Data:
        {json.dumps(market_research_data, indent=2)}
        
        Please provide:
        1. Estimated startup costs (initial development, marketing, operations)
        2. Potential revenue streams and business models
        
        Return your response as a JSON object with the following structure:
        {{
            "estimated_costs": {{
                "initial_development": "cost estimate range (e.g., $50,000 - $100,000)",
                "monthly_operations": "monthly operational cost range"
            }},
            "potential_revenue_streams": [
                "revenue stream 1",
                "revenue stream 2",
                "revenue stream 3"
            ]
        }}
        
        Be realistic in your estimates based on the market size, competition, and technical complexity implied by the idea.
        Consider factors like development time, team size, marketing needs, and ongoing operational expenses.
        """

        try:
            # Call the Gemini API
            response = gemini_model.generate_content(prompt)
            
            # Extract and parse the JSON response
            # The response might be in a markdown code block, so we clean it up
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_response)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in FinanceAgent: {e}")
            return {"error": "Failed to parse financial analysis response."}
        except Exception as e:
            print(f"An error occurred in FinanceAgent: {e}")
            return {"error": "Failed to generate financial analysis."}