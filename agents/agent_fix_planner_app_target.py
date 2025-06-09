import google.generativeai as genai
import logging

"""
This module contains the FixPlannerAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FixPlannerAgent_AppTarget:
    """
    Agent responsible for creating a detailed plan to fix a bug.

    Based on a root cause hypothesis from the TriageAgent, this agent
    generates a micro-specification for change that instructs other agents
    on how to modify the code to resolve the issue.
    """

    def __init__(self, api_key: str):
        """
        Initializes the FixPlannerAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        genai.configure(api_key=self.api_key)

    def create_fix_plan(self, root_cause_hypothesis: str, relevant_code: str) -> str:
        """
        Generates a step-by-step plan to fix a diagnosed bug.

        Args:
            root_cause_hypothesis (str): The diagnosis of the bug from the TriageAgent.
            relevant_code (str): The source code of the component(s) that need to be fixed.

        Returns:
            str: A detailed, step-by-step plan (micro-specification) for fixing the code.
                 Returns an error message string if an API call fails.
        """
        try:
            model = genai.GenerativeModel('gemini-pro')

            prompt = f"""
            You are a Principal Software Architect specializing in code remediation and refactoring.
            Your task is to take a root cause analysis of a bug and create a precise, step-by-step
            technical plan to fix it. This plan will be executed by other AI code-generation agents.

            **MANDATORY INSTRUCTIONS:**
            1.  **Actionable Steps:** The plan must consist of clear, unambiguous, and actionable steps.
            2.  **Be Specific:** Explicitly state which file, class, and function/method to modify. If code needs to be added, specify exactly where. If code needs to be removed or replaced, show the exact code to be changed.
            3.  **Logical Flow:** The steps should be in a logical order for implementation.
            4.  **Clarity over Brevity:** The plan must be detailed enough for another developer (or an AI) to execute without having to make its own assumptions. Explain the 'why' behind the proposed changes.
            5.  **Format:** Use a numbered list for the steps.

            **--- INPUTS ---**

            **1. Root Cause Hypothesis (The problem to solve):**
            ```
            {root_cause_hypothesis}
            ```

            **2. Current Source Code (The code to be fixed):**
            ```python
            {relevant_code}
            ```

            **--- Detailed Fix Plan (Micro-Specification for Change) ---**
            """

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            logging.error(error_message)
            return error_message