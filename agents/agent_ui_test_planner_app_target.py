import google.generativeai as genai
import logging

"""
This module contains the UITestPlannerAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UITestPlannerAgent_AppTarget:
    """
    Agent responsible for generating UI test case content for a target application.

    Based on the application's specifications, this agent produces a structured,
    human-readable test plan for the Product Manager to execute manually.
    """

    def __init__(self, api_key: str):
        """
        Initializes the UITestPlannerAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        # Configure the genai library with the API key upon initialization.
        genai.configure(api_key=self.api_key)

    def generate_ui_test_plan(self, functional_spec_text: str, technical_spec_text: str) -> str:
        """
        Generates a UI test plan based on functional and technical specs.

        Args:
            functional_spec_text (str): The complete functional specification.
            technical_spec_text (str): The complete technical specification.

        Returns:
            str: A string containing the UI test plan in Markdown table format.
                 Returns an error message string if an API call fails.
        """
        try:
            model = genai.GenerativeModel('gemini-1.5-pro-latest') # Using the more powerful model as discussed

            prompt = f"""
            You are a meticulous Software Quality Assurance (QA) Specialist.
            Your task is to create a detailed, human-readable UI test plan.
            You MUST consider both the functional requirements and the technical architecture.

            **MANDATORY INSTRUCTIONS:**
            1.  **Format:** Your entire response MUST be a single Markdown table. Do not include any other text.
            2.  **Table Columns:** The table MUST have the columns: "Test Case ID", "Feature", "Test Scenario", "Steps to Reproduce", and "Expected Result".
            3.  **Comprehensive Coverage:** Your test cases must cover:
                - All user-facing features described in the Functional Specification.
                - Technical constraints and components mentioned in the Technical Specification (e.g., test API error responses, database validation rules).
            4.  **Clarity:** Provide clear, numbered steps that a non-technical user can follow.

            **--- INPUT 1: Functional Specification ---**
            ```
            {functional_spec_text}
            ```

            **--- INPUT 2: Technical Specification ---**
            ```
            {technical_spec_text}
            ```

            **--- Generated UI Test Plan (Markdown Table) ---**
            """

            response = model.generate_content(prompt)

            if "|" in response.text and "---" in response.text:
                return response.text
            else:
                logging.warning("LLM response did not appear to be a Markdown table.")
                return "Error: The AI did not return a valid Markdown table. Please try again."

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            logging.error(error_message)
            return error_message