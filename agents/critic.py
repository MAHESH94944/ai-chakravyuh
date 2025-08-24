from .base_agent import BaseAgent
from core.clients import gemini_model
import json

class CriticAgent(BaseAgent):
    """
    An agent that provides a critical review of the analysis from other agents.
    """
    def run(self, idea: str, finance_data: dict, risk_data: dict, tech_data: dict) -> dict:
        """
        Executes the agent's task to critique the analysis.

        Args:
            idea: The startup idea text.
            finance_data: The JSON output from the FinanceAgent.
            risk_data: The JSON output from the RiskAgent.
            tech_data: The JSON output from the TechnicalFeasibilityAgent.
        
        Returns:
            A dictionary containing the critical assessment.
        """
        prompt = f"""
        You are a highly experienced and skeptical venture capitalist, known for finding the single biggest flaw in any business plan.
        Your task is to provide a sharp, concise critique of the following startup idea and its analysis.

        **Startup Idea:**
        "{idea}"

        **Provided Analysis:**
        1. Financial Outlook: {json.dumps(finance_data, indent=2)}
        2. Identified Risks: {json.dumps(risk_data, indent=2)}
        3. Technical Feasibility: {json.dumps(tech_data, indent=2)}

        **Your Task:**
        Review all the provided analysis. Identify the single most critical blind spot, contradiction, or overly optimistic assumption. Do not summarize the existing points; provide a new, critical insight. Your critique should be a direct, concise paragraph.

        Return your response as a single, clean JSON object with one key, "critique".
        
        Example Format:
        {{
          "critique": "The analysis overlooks the immense challenge of..."
        }}
        """

        try:
            # Call the Gemini API for advanced reasoning
            response = gemini_model.generate_content(prompt)
            
            # Clean and parse the JSON response
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_response)
            
            return result
        except Exception as e:
            print(f"An error occurred in CriticAgent: {e}")
            return {"error": f"Failed to generate critique: {e}"}