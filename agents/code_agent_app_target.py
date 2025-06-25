import logging
import google.generativeai as genai
from typing import Optional

"""
This module contains the CodeAgent_AppTarget class.
"""

class CodeAgent_AppTarget:
    """
    Agent responsible for generating the actual source code for a target
    application component. It translates a logical plan into a specific
    programming language, adhering to the project's coding standard.
    """

    def __init__(self, api_key: str):
        """
        Initializes the CodeAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        # Configure the genai library with the API key upon initialization.
        genai.configure(api_key=self.api_key)

    def generate_code_for_component(self, logic_plan: str, coding_standard: str, target_language: str, feedback: Optional[str] = None) -> str:
        """
        Generates source code based on a logic plan and a coding standard,
        explicitly targeting a specific programming language.
        """
        try:
            # Re-instating the Pro model as it is required for this level of instruction following.
            model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')

            correction_context = ""
            if feedback:
                correction_context = f"""
                **IMPORTANT - CORRECTION REQUIRED:**
                A previous version failed a code review. You MUST correct the code based on the following feedback.
                Your entire response MUST STILL BE ONLY the raw source code. Do not include conversational text.

                **--- Code Review Feedback to Address ---**
                {feedback}
                """

            # --- RE-ENGINEERED PROMPT ---
            prompt = f"""
            You are an expert software developer with an extreme attention to detail. Your primary objective is to write production-ready source code that perfectly adheres to a strict set of rules. Functional correctness and rule adherence are equally important.

            **NON-NEGOTIABLE RULES OF ENGAGEMENT:**
            1.  **Output Format:** Your entire response MUST BE ONLY the raw source code for the component. Do not include any conversational text, explanations, or markdown fences like ```python.
            2.  **Coding Standard Adherence:** You MUST treat the provided Coding Standard as a set of absolute, mandatory requirements. Before providing your response, double-check your generated code against this checklist:
                - Does the file start with a module-level docstring?
                - Are there exactly two blank lines before all top-level class and function definitions?
                - Do all public classes, methods, and functions have complete docstrings?
                - Does any line in a docstring or comment exceed 72 characters?
                - Does any line of code exceed 88 characters?
                - Are all inline comments explaining the 'why', not the 'what'?
            3.  **Target Language:** The code MUST be written in **{target_language}**.
            4.  **Logic Implementation:** The code MUST implement ONLY the logic described in the provided Logical Plan.

            {correction_context}

            **--- INPUT 1: The Logical Plan to Implement ---**
            ```
            {logic_plan}
            ```

            **--- INPUT 2: The Coding Standard to Follow (MANDATORY) ---**
            ```
            {coding_standard}
            ```

            **--- Generated Source Code (Language: {target_language}) ---**
            """

            response = model.generate_content(prompt)
            # We still clean the response as a fallback, but the new prompt should prevent this.
            cleaned_code = response.text.strip().removeprefix("```python").removesuffix("```").strip()
            return cleaned_code

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            logging.error(error_message)
            return error_message