import logging
from llm_service import LLMService

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
            prompt = f"""
            You are an expert Software Quality Assurance (QA) Engineer specializing in automated testing.
            Your task is to write a comprehensive suite of unit tests for the provided source code, based on its specification and adhering to a strict coding standard.

            **MANDATORY INSTRUCTIONS:**
            1.  **Target Language:** The component is written in **{target_language}**. Your unit tests MUST be written for this language and its standard testing frameworks (e.g., pytest for Python, JUnit/Mockito for Java/Kotlin).
            2.  **Comprehensive Coverage:** Your tests MUST cover the "happy path," edge cases (e.g., null inputs, empty lists, boundary values), and error handling.
            3.  **Adherence to Coding Standard:** The unit test code you generate MUST follow all rules in the provided coding standard.
            4.  **RAW CODE ONLY:** Your entire response MUST BE ONLY the raw source code for the unit tests. Do not include any conversational text or markdown fences like ```python.

            **--- INPUTS ---**

            **1. The Component's Specification (What it should do):**
            ```
            {component_spec}
            ```

            **2. The Component's Source Code (Language: {target_language}):**
            ```
            {source_code}
            ```

            **3. The Coding Standard to Follow:**
            ```
            {coding_standard}
            ```

            **--- Generated Unit Test Source Code (Language: {target_language}) ---**
            """

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

            prompt = f"""
            You are an expert Software Quality Assurance (QA) Engineer specializing in automated integration testing.
            Your task is to write a comprehensive suite of integration tests for the provided software components, based on the overall integration goal.

            **MANDATORY INSTRUCTIONS:**
            1.  **Focus on Interaction:** Your tests MUST validate the interactions BETWEEN the provided components. Verify that they pass data correctly and that their combined behavior matches the integration specification.
            2.  **Adherence to Coding Standard:** The test code you generate MUST follow all established coding standards.
            3.  **Use Standard Testing Frameworks:** Assume the use of standard testing frameworks for the target language (e.g., pytest for Python, JUnit/Mockito for Java/Kotlin).
            4.  **Raw Code Output:** Your entire response MUST BE ONLY the raw source code for the integration tests. Do not include any conversational text or explanations outside of the code itself. The code you generate MUST include comments and docstrings as required by the coding standard.

            **--- INPUTS ---**

            **1. The Overall Integration Specification (What the components should achieve together):**
            ```
            {integration_spec}
            ```

            **2. The Interacting Components:**
            {component_context}

            **--- Generated Integration Test Source Code ---**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text

        except Exception as e:
            error_message = f"An error occurred during integration test generation: {e}"
            # In a real scenario, this would use the configured logger
            logging.error(error_message)
            raise e # Re-raise the exception