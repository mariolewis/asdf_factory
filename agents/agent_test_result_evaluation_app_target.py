import google.generativeai as genai
import logging

"""
This module contains the TestResultEvaluationAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestResultEvaluationAgent_AppTarget:
    """
    Agent responsible for evaluating the results of manually executed UI tests.

    It parses a structured text input (e.g., a Markdown table) containing
    test results and identifies which tests failed, providing a summary that
    can be used to initiate the debugging pipeline.
    """

    def __init__(self, api_key: str):
        """
        Initializes the TestResultEvaluationAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        # Configure the genai library with the API key upon initialization.
        genai.configure(api_key=self.api_key)

    def evaluate_ui_test_results(self, test_results_text: str) -> str:
        """
        Parses UI test results and provides a summary of failures.

        This method prompts the Gemini API to analyze a block of text containing
        test results and extract the details of any failed tests into a
        structured, easy-to-read summary.

        Args:
            test_results_text (str): A string containing the completed test plan,
                                     typically as a Markdown table, with a
                                     'Status' (e.g., Pass/Fail) column filled in.

        Returns:
            str: A structured summary of the failed test cases. If all tests
                 passed, it returns a confirmation message. Returns an error
                 message string if an API call fails.
        """
        try:
            model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

            prompt = f"""
            You are a highly efficient Software Quality Assurance (QA) Analyst.
            Your task is to analyze the provided UI test results and produce a clear, structured summary of ONLY the failed test cases.

            **MANDATORY INSTRUCTIONS:**
            1.  **Identify Failures:** Carefully parse the input text, which is a completed test plan. Identify all rows where the result or status is marked as "Fail", "Failed", or "Failure".
            2.  **Ignore Passes:** Do not include any information about tests that passed. Your output must only contain the failures.
            3.  **Structured Summary:** For each failed test case, you MUST extract and present the following information in a clear, readable format:
                -   The Test Case ID
                -   The Test Scenario
                -   The full Steps to Reproduce the failure
                -   The Expected Result
                -   The Actual Result that was recorded
            4.  **No Failures Scenario:** If you analyze the input and find that absolutely no tests have failed, your entire response must be the single phrase: "ALL_TESTS_PASSED". Do not include any other text.
            5.  **Output Format:** Structure the output for the failures logically. Use Markdown for clarity (e.g., headings for each failed test case).

            **--- Completed UI Test Results ---**
            ```
            {test_results_text}
            ```

            **--- Summary of Failed Tests ---**
            """

            response = model.generate_content(prompt)

            return response.text.strip()

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            logging.error(error_message)
            return error_message