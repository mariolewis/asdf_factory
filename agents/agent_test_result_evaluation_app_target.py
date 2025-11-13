import logging
from llm_service import LLMService

# ... (module docstring & logging config)

class TestResultEvaluationAgent_AppTarget:
    """
    Agent responsible for evaluating the results of manually executed UI tests.
    It parses a structured text input (e.g., a Markdown table) containing
    test results and identifies which tests failed, providing a summary that
    can be used to initiate the debugging pipeline.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the TestResultEvaluationAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the TestResultEvaluationAgent_AppTarget.")
        self.llm_service = llm_service

    def evaluate_ui_test_results(self, test_results_text: str) -> str:
        """
        Parses UI test results and provides a summary of failures.
        This method prompts the LLM API to analyze a block of text containing
        test results and extract the details of any failed tests into a
        structured, easy-to-read summary.
        """
        try:
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

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            return response_text.strip()

        except Exception as e:
            error_message = f"An error occurred during UI test result evaluation: {e}"
            logging.error(error_message)
            raise e # Re-raise the exception