from .base_agent import BaseAgent
from core.clients import gemini_model
import json

class UserPersonaAgent(BaseAgent):
    """
    An agent that creates a detailed user persona based on a startup idea.
    """
    def run(self, idea: str) -> dict:
        """
        Executes the agent's task to generate a user persona.

        Args:
            idea: The startup idea text.
        
        Returns:
            A dictionary containing the persona story.
        """
        prompt = f"""
        You are an expert product manager and storyteller.
        Based on the following startup idea, create a short, compelling user persona story.
        The story should be a single paragraph, describing a fictional user, their pain points,
        and how this product would solve their problem. Make it relatable and specific.

        Startup Idea: "{idea}"

        Return your response as a JSON object with a single key "persona_story".
        Example format: {{"persona_story": "Meet Sarah..."}}
        """

        try:
            # Call the Gemini API
            response = gemini_model.generate_content(prompt)
            
            # Extract and parse the JSON response
            # The response might be in a markdown code block, so we clean it up
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_response)
            
            return result
        except Exception as e:
            print(f"An error occurred in UserPersonaAgent: {e}")
            # Return a structured error
            return {"error": "Failed to generate user persona."}