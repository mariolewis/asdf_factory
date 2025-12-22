import logging
from llm_service import LLMService
import vault

"""
This module contains the UITestPlannerAgent_AppTarget class.
"""

# Configure basic logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UITestPlannerAgent_AppTarget:
    """
    Agent responsible for generating UI test case content for a target application.

    Based on the application's specifications, this agent produces a structured,
    human-readable test plan for the Product Manager to execute manually.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the UITestPlannerAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the UITestPlannerAgent_AppTarget.")
        self.llm_service = llm_service

    def generate_ui_test_plan(self, functional_spec_text: str, technical_spec_text: str, ux_spec_text: str) -> str:
        """
        Generates a UI test plan based on functional, technical, and UX specs.

        Args:
            functional_spec_text (str): The complete functional specification.
            technical_spec_text (str): The complete technical specification.
            ux_spec_text (str): The complete UX/UI specification, including the JSON blueprint.

        Returns:
            str: A string containing the UI test plan in Markdown table format.
                Returns an error message string if an API call fails.
        """
        try:
            prompt = vault.get_prompt("agent_ui_test_planner_app_target__prompt_44").format(ux_spec_text=ux_spec_text, functional_spec_text=functional_spec_text, technical_spec_text=technical_spec_text)

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")

            if "|" in response_text and "---" in response_text:
                return response_text
            else:
                logging.warning("LLM response did not appear to be a Markdown table.")
                return "Error: The AI did not return a valid Markdown table. Please try again."

        except Exception as e:
            error_message = f"An error occurred during UI test plan generation: {e}"
            logging.error(error_message)
            return error_message