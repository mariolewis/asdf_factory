import logging
import re
from typing import Optional
from llm_service import LLMService
import vault

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
                You MUST ensure the generated code, especially for UI components, strictly adheres to the visual styling rules defined in this guide.
                The guide contains a "Prescriptive Style Guide" section with key-value rules (e.g., "Primary Button: background: accent_color...").
                You MUST find these rules and translate them into the correct syntax and properties for the target language.
                ```
                {style_guide}
                ```
                """

            prompt = vault.get_prompt("code_agent_app_target__prompt_57").format(correction_context=correction_context, logic_plan=logic_plan, coding_standard=coding_standard, style_guide_context=style_guide_context)

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