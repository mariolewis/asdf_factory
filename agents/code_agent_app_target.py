import logging
import re
from typing import Optional
from llm_service import LLMService

"""
This module contains the CodeAgent_AppTarget class.
"""

class CodeAgent_AppTarget:
    """
    Agent responsible for generating the actual source code for a target
    application component. It translates a logical plan into a specific
    programming language, adhering to the project's coding standard.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the CodeAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the CodeAgent_AppTarget.")
        self.llm_service = llm_service

    def generate_code_for_component(self, logic_plan: str, coding_standard: str, style_guide: Optional[str] = None, feedback: Optional[str] = None) -> str:
        """
        Generates source code based on a logic plan, a coding standard, and an
        optional style guide, explicitly targeting a specific programming language.
        """
        try:
            correction_context = ""
            if feedback:
                correction_context = f"""
                **IMPORTANT - CORRECTION REQUIRED:**
                A previous version failed a code review. You MUST correct the code based on the following feedback.
                Your entire response MUST STILL BE ONLY the raw source code. Do not include conversational text.

                **--- Code Review Feedback to Address ---**
                {feedback}
                """

            style_guide_context = ""
            if style_guide:
                style_guide_context = f"""
                **--- INPUT 3: The Theming & Style Guide to Follow (MANDATORY) ---**
                You MUST ensure the generated code, especially for UI components, adheres to the following aesthetic style guide (e.g., colors, fonts, component styles).
                ```
                {style_guide}
                ```
                """

            prompt = f"""
            You are an expert software developer. Your only function is to write raw source code.
            Your output is being saved directly to a file and executed. Any non-code text, including conversational text, explanations, or markdown fences like ```python, will cause a critical system failure.

            **MANDATORY INSTRUCTIONS:**
            1.  **RAW CODE ONLY:** Your entire response MUST BE ONLY the raw source code for the component. The first character of your response must be the first character of the code.
            2.  **CODING STANDARD:** You MUST strictly follow all rules in the provided Coding Standard. This standard may contain rules for *multiple* technologies (e.g., Python and embedded SQL, or HTML/CSS/JS in a .vue file, or some other combination). You must correctly apply all relevant rules to the code you generate.
            3.  **LOGIC:** The code MUST implement ONLY the logic described in the provided Logical Plan.

            {correction_context}

            **--- INPUT 1: The Logical Plan to Implement ---**
            ```
            {logic_plan}
            ```

            **--- INPUT 2: The Coding Standard to Follow (MANDATORY) ---**
            ```
            {coding_standard}
            ```

            {style_guide_context}

            **--- Generated Source Code ---**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            # --- Robust Cleanup Logic using Regular Expressions ---
            # 1. Strip leading/trailing whitespace
            code_text = response_text.strip()
            # 2. Remove the starting markdown fence (e.g., ```python or ```) and any text on that line
            code_text = re.sub(r"^\s*`{3}.*?\n", "", code_text)
            # 3. Remove the ending markdown fence (```)
            code_text = re.sub(r"\n\s*`{3}\s*$", "", code_text)

            return code_text.strip()

        except Exception as e:
            error_message = f"An error occurred during code generation: {e}"
            logging.error(error_message)
            raise e # Re-raise the exception