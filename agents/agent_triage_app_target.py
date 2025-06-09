import google.generativeai as genai
import logging

"""
This module contains the TriageAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TriageAgent_AppTarget:
    """
    Agent responsible for analyzing failures and hypothesizing the root cause.

    When a build or test fails, this agent examines error logs, test reports,
    and relevant code to determine the likely source of the problem.
    """

    def __init__(self, api_key: str):
        """
        Initializes the TriageAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        genai.configure(api_key=self.api_key)

    def analyze_and_hypothesize(self, error_logs: str, relevant_code: str, test_report: str = "") -> str:
        """
        Analyzes failure data and returns a root cause hypothesis.

        Args:
            error_logs (str): The raw error logs from the failed build or test execution.
            relevant_code (str): The source code of the component(s) suspected
                                 to be involved in the failure.
            test_report (str, optional): The summary of failed tests, especially
                                         from UI test evaluations. Defaults to "".

        Returns:
            str: A concise, structured hypothesis about the root cause of the failure.
                 Returns an error message string if an API call fails.
        """
        try:
            model = genai.GenerativeModel('gemini-pro')

            prompt = f"""
            You are a Senior Software Engineer specializing in debugging complex systems.
            Your task is to analyze the provided error logs, test reports, and source code to form a concise,
            well-reasoned hypothesis about the root cause of a failure.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Holistically:** Consider all provided inputs—the error log, the test report (if any), and the source code—to form your conclusion.
            2.  **Be Specific:** Your hypothesis must be specific. Pinpoint the likely function, class, or logical error. Avoid vague statements.
            3.  **Concise Output:** Your entire response should be a single, concise paragraph that clearly states the hypothesis. Do not include conversational text or apologies.

            **--- INPUTS ---**

            **1. Error Logs / Stack Trace:**
            ```
            {error_logs}
            ```

            **2. Failed Test Report (e.g., from UI tests):**
            ```
            {test_report if test_report else "N/A"}
            ```

            **3. Potentially Relevant Source Code:**
            ```python
            {relevant_code}
            ```

            **--- Root Cause Hypothesis ---**
            """

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            logging.error(error_message)
            return error_message