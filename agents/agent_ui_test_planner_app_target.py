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

    def generate_ui_test_plan(self, final_spec_text: str) -> str:
        """
        Generates a UI test plan in a Markdown table format.

        This method prompts the Gemini API to act as a QA specialist and create
        a detailed test plan based on the provided application specifications.

        Args:
            final_spec_text (str): The complete, finalized specification text for
                                   the target application.

        Returns:
            str: A string containing the UI test plan in a Markdown table format.
                 Returns an error message string if an API call fails.
        """
        try:
            model = genai.GenerativeModel('gemini-pro')

            prompt = f"""
            You are a meticulous Software Quality Assurance (QA) Specialist.
            Your task is to create a detailed, human-readable UI (User Interface)
            test plan based on the provided application specifications.

            **MANDATORY INSTRUCTIONS:**
            1.  **Format:** Your entire response MUST be a single Markdown table. Do not include any other text, titles, or explanations outside of the table itself.
            2.  **Table Columns:** The Markdown table MUST have the following columns precisely: "Test Case ID", "Feature", "Test Scenario", "Steps to Reproduce", and "Expected Result".
            3.  **Content:**
                -   **Test Case ID:** Create a simple, unique ID for each test case (e.g., UI-001, UI-002).
                -   **Feature:** Name the high-level feature being tested (e.g., "User Login", "Profile Creation").
                -   **Test Scenario:** Briefly describe the specific goal of the test (e.g., "Verify successful login with valid credentials", "Verify error message on invalid email format").
                -   **Steps to Reproduce:** Provide clear, numbered, step-by-step instructions that a non-technical user can follow to execute the test.
                -   **Expected Result:** Clearly describe the expected outcome if the test passes (e.g., "User is redirected to the dashboard page", "An error message 'Invalid email address' is displayed below the email field").
            4.  **Coverage:** Ensure you cover all user-facing features, interactions, and potential user flows described in the specifications.

            **--- Application Specifications ---**
            ```
            {final_spec_text}
            ```

            **--- Generated UI Test Plan (Markdown Table) ---**
            """

            response = model.generate_content(prompt)

            # Basic validation to ensure we're getting something table-like
            if "|" in response.text and "---" in response.text:
                return response.text
            else:
                logging.warning("LLM response did not appear to be a Markdown table. Re-prompting might be needed.")
                return "Error: The AI did not return a valid Markdown table. Please try again."


        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            logging.error(error_message)
            return error_message