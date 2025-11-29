import logging
from llm_service import LLMService
import vault

"""
This module contains the TestAgent_AppTarget class.
"""

class TestAgent_AppTarget:
    """
    Agent responsible for generating unit tests for a target application component.
    It takes the source code of a component and its specification to create
    a comprehensive suite of tests.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the TestAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the TestAgent_AppTarget.")
        self.llm_service = llm_service

    def generate_unit_tests_for_component(self, source_code: str, component_spec: str, coding_standard: str, target_language: str) -> str:
        """
        Generates unit test code for a given component, adhering to a standard
        and targeting a specific programming language.
        """
        import re
        try:
            prompt = vault.get_prompt("test_agent_app_target__prompt_33").format(target_language=target_language, component_spec=component_spec, source_code=source_code, coding_standard=coding_standard)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            # --- THIS IS THE FIX ---
            # Robustly clean markdown fences from the AI's response.
            code_text = response_text.strip()
            code_text = re.sub(r"^\s*`{3}.*?\n", "", code_text)
            code_text = re.sub(r"\n\s*`{3}\s*$", "", code_text)
            return code_text.strip()
            # --- END OF FIX ---

        except Exception as e:
            error_message = f"An error occurred during unit test generation: {e}"
            logging.error(error_message)
            raise e # Re-raise the exception

    def generate_integration_tests(self, components: list[dict], integration_spec: str) -> str:
        """
        Generates integration test code for a set of interacting components.

        This method prompts the LLM service to create tests that verify the
        collaboration between multiple components based on an overall
        integration specification.

        Args:
            components (list[dict]): A list of dictionaries, where each dictionary
                                     contains the 'source_code' and 'component_spec'
                                     for a component to be included in the test.
            integration_spec (str): A specification describing how the components
                                    are expected to interact and the overall goal
                                    of the integration test.

        Returns:
            str: The generated source code for the integration tests.
                 Returns an error message string if an API call fails.
        """
        try:
            # Build the context string with all component details
            component_context = ""
            for i, comp in enumerate(components):
                component_context += f"""
            ---
            **Component {i+1}:**

            **Specification:**
            ```
            {comp.get('component_spec', 'N/A')}
            ```

            **Source Code:**
            ```
            {comp.get('source_code', 'N/A')}
            ```
            """

            prompt = vault.get_prompt("test_agent_app_target__prompt_117").format(integration_spec=integration_spec, component_context=component_context)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text

        except Exception as e:
            error_message = f"An error occurred during integration test generation: {e}"
            # In a real scenario, this would use the configured logger
            logging.error(error_message)
            raise e # Re-raise the exception