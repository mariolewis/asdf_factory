import logging
import json
from llm_service import LLMService, parse_llm_json
import vault

"""
This module contains the FixPlannerAgent_AppTarget class.
"""

# Configure basic logging
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FixPlannerAgent_AppTarget:
    """
    Agent responsible for creating a detailed plan to fix a bug.

    Based on a root cause hypothesis from the TriageAgent, this agent
    generates a micro-specification for change that instructs other agents
    on how to modify the code to resolve the issue.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the FixPlannerAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the FixPlannerAgent_AppTarget.")
        self.llm_service = llm_service

    def create_fix_plan(self, root_cause_hypothesis: str, relevant_code: str) -> str:
        """
        Generates a detailed, sequential JSON plan to fix a diagnosed bug.
        """
        try:
            prompt = vault.get_prompt("agent_fix_planner_app_target__prompt_37").format(root_cause_hypothesis=root_cause_hypothesis, relevant_code=relevant_code)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            # Clean the response to remove potential markdown fences
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()

            # Validate that the response is a JSON array
            if cleaned_response.startswith('[') and cleaned_response.endswith(']'):
                parse_llm_json(cleaned_response) # Final validation check
                return cleaned_response
            else:
                logging.error(f"FixPlannerAgent received non-JSON-array response: {cleaned_response}")
                raise ValueError("The AI response was not in the expected JSON array format.")

        except Exception as e:
            error_message = f"An error occurred during fix plan generation: {e}"
            logging.error(error_message)
            raise e # Re-raise the exception