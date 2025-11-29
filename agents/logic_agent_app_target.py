import logging
from llm_service import LLMService
import vault

"""
This module contains the LogicAgent_AppTarget class.
"""

class LogicAgent_AppTarget:
    """
    Agent responsible for generating the logic and algorithms for a target
    application component based on a micro-specification.
    Adheres to the Single Responsibility Principle as this class has one specific task.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the LogicAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("LLMService is required for the LogicAgent_AppTarget.")
        self.llm_service = llm_service

    def generate_logic_for_component(self, micro_spec_content: str) -> str:
        """
        Generates the implementation logic based on a micro-specification.

        This method will interact with the LLM service to translate a
        natural language specification into a structured logical plan or
        pseudocode for the CodeAgent.

        Args:
            micro_spec_content (str): The detailed micro-specification for the component.

        Returns:
            str: The generated logic/pseudocode for the component.
                 Returns an error message string if an API call fails.
        """
        try:
            prompt = vault.get_prompt("logic_agent_app_target__prompt_42").format(micro_spec_content=micro_spec_content)

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            return response_text

        except Exception as e:
            # As per the programming standard, we handle foreseeable errors gracefully.
            error_message = f"An error occurred while generating the logical plan: {e}"
            logging.error(error_message)
            raise e # Re-raise the exception