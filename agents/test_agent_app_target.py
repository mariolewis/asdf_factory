import google.generativeai as genai

"""
This module contains the TestAgent_AppTarget class.
"""

class TestAgent_AppTarget:
    """
    Agent responsible for generating unit tests for a target application component.
    It takes the source code of a component and its specification to create
    a comprehensive suite of tests.
    """

    def __init__(self, api_key: str):
        """
        Initializes the TestAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        # Configure the genai library with the API key upon initialization.
        genai.configure(api_key=self.api_key)

    def generate_unit_tests_for_component(self, source_code: str, component_spec: str) -> str:
        """
        Generates unit test code for a given component.

        This method will interact with the Gemini API, providing the component's
        source code and specification as context to produce relevant and
        effective unit tests.

        Args:
            source_code (str): The source code of the component to be tested.
            component_spec (str): The micro-specification describing the component's
                                  expected behavior.

        Returns:
            str: The generated source code for the unit tests.
                 Returns an error message string if an API call fails.
        """
        try:
            model = genai.GenerativeModel('gemini-pro')

            prompt = f"""
            You are an expert Software Quality Assurance (QA) Engineer specializing in automated testing.
            Your task is to write a comprehensive suite of unit tests for the provided source code, based on its specification.

            **MANDATORY INSTRUCTIONS:**
            1.  **Comprehensive Coverage:** Your tests MUST cover the "happy path" (normal successful execution), edge cases (e.g., null inputs, empty lists, boundary values), and error handling (how the code should behave with invalid inputs).
            2.  **Adherence to Coding Standard:** The unit test code you generate MUST follow the same coding standards as the application code.
            3.  **Use Standard Testing Frameworks:** Assume the use of standard testing frameworks for the target language (e.g., pytest for Python, JUnit/Mockito for Java/Kotlin).
            4.  **Raw Code Output:** Your entire response MUST BE ONLY the raw source code for the unit tests. Do not include any conversational text or explanations outside of the code itself. The code you generate MUST include comments and docstrings as required by the coding standard.

            **--- INPUTS ---**

            **1. The Component's Specification (What it should do):**
            ```
            {component_spec}
            ```

            **2. The Component's Source Code (To be tested):**
            ```
            {source_code}
            ```

            **--- Generated Unit Test Source Code ---**
            """

            response = model.generate_content(prompt)

            return response.text

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            print(error_message) # Or use a proper logger
            return error_message

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            print(error_message) # Or use a proper logger
            return error_message

    def generate_integration_tests(self, components: list[dict], integration_spec: str) -> str:
        """
        Generates integration test code for a set of interacting components.

        This method prompts the Gemini API to create tests that verify the
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
            model = genai.GenerativeModel('gemini-pro')

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

            response = model.generate_content(prompt)

            return response.text

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            # In a real scenario, this would use the configured logger
            print(error_message)
            return error_message