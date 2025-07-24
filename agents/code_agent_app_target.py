import logging
import re
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
            model = genai.GenerativeModel('gemini-2.5-pro-preview-05-20')

            correction_context = ""
            if feedback:
                correction_context = f"""
                **IMPORTANT - CORRECTION REQUIRED:**
                A previous version failed a code review. You MUST correct the code based on the following feedback.
                Your entire response MUST STILL BE ONLY the raw source code. Do not include conversational text.

                **--- Code Review Feedback to Address ---**
                {feedback}
                """

            prompt = f"""
            You are an expert software developer. Your only function is to write raw source code.
            Your output is being saved directly to a file and executed. Any non-code text, including conversational text, explanations, or markdown fences like ```python, will cause a critical system failure.

            **MANDATORY INSTRUCTIONS:**
            1.  **RAW CODE ONLY:** Your entire response MUST BE ONLY the raw source code for the component. The first character of your response must be the first character of the code.
            2.  **CODING STANDARD:** You MUST strictly follow all rules in the provided Coding Standard.
            3.  **TARGET LANGUAGE:** The code MUST be written in **{target_language}**.
            4.  **LOGIC:** The code MUST implement ONLY the logic described in the provided Logical Plan.

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

            # --- Robust Cleanup Logic using Regular Expressions ---
            # 1. Strip leading/trailing whitespace
            code_text = response.text.strip()
            # 2. Remove the starting markdown fence (e.g., ```python or ```) and any text on that line
            code_text = re.sub(r"^\s*`{3}.*?\n", "", code_text)
            # 3. Remove the ending markdown fence (```)
            code_text = re.sub(r"\n\s*`{3}\s*$", "", code_text)

            return code_text.strip()

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            logging.error(error_message)
            return error_message

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            logging.error(error_message)
            return error_message