import logging
from llm_service import LLMService

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
            prompt = f"""
            You are an expert software architect. Your task is to take a detailed "micro-specification"
            for a single software component and break it down into a clear, language-agnostic,
            step-by-step logical plan or pseudocode. This plan will be given to another AI agent that
            will write the actual code.

            **Key Requirements for the Output:**
            - The plan must be detailed enough for a developer (or another AI) to write code from it without having to make major assumptions.
            - It must cover the main logic, data handling, and any error conditions mentioned in the spec.
            - It must be language-agnostic. Do not use Python, Java, or any other specific language syntax. Use clear, English-based pseudocode.
            - Be explicit and low-level in your instructions. Detail loops, conditionals, function/method calls, and variable assignments. Avoid high-level abstract descriptions.
            - Structure the output with clear steps.

            **Micro-Specification to Process:**
            ---
            {micro_spec_content}
            ---

            **Generated Logical Plan:**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            return response_text

        except Exception as e:
            # As per the programming standard, we handle foreseeable errors gracefully.
            error_message = f"An error occurred while generating the logical plan: {e}"
            logging.error(error_message)
            return error_message