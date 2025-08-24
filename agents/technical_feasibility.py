from .base_agent import BaseAgent
from core.clients import gemini_model
import json

class TechnicalFeasibilityAgent(BaseAgent):
    """
    An agent that assesses the technical feasibility of a startup idea.
    """
    def run(self, idea: str) -> dict:
        """
        Executes the agent's task to assess technical feasibility.

        Args:
            idea: The startup idea text.
        
        Returns:
            A dictionary containing the technical feasibility analysis.
        """
        prompt = f"""
        You are a seasoned Chief Technology Officer (CTO) and software architect.
        Your task is to provide a high-level technical feasibility analysis for a startup idea.

        **Startup Idea:**
        "{idea}"

        **Your Task:**
        1.  Identify the top 3 most significant technical challenges to building this product.
        2.  Suggest a high-level technology stack, specifying a choice for the frontend, backend, database, and any key AI/ML models or services.

        Return your response as a single, clean JSON object with the following structure:
        {{
          "key_challenges": ["...", "...", "..."],
          "suggested_stack": {{
            "frontend": "...",
            "backend": "...",
            "database": "...",
            "ai_ml": "..."
          }}
        }}
        """

        try:
            # Call the Gemini API for its technical reasoning
            response = gemini_model.generate_content(prompt)
            
            # Clean and parse the JSON response
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_response)
            
            return result
        except Exception as e:
            print(f"An error occurred in TechnicalFeasibilityAgent: {e}")
            return {"error": f"Failed to generate technical feasibility analysis: {e}"}