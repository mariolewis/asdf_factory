import logging
import json
from llm_service import LLMService

class OrchestrationCodeAgent:
    """
    A specialized agent that modifies existing code files based on a
    structured integration plan.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the OrchestrationCodeAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the OrchestrationCodeAgent.")
        self.llm_service = llm_service

    def apply_modifications(self, original_code: str, modifications_json: str) -> str:
        """
        Applies a list of modifications to an existing code file.

        Args:
            original_code (str): The original source code of the file to be modified.
            modifications_json (str): A JSON string list of modification actions for this file.

        Returns:
            str: The complete source code of the file after all modifications
                 have been applied.
        """
        try:
            prompt = f"""
            You are an expert, precise, and careful software engineer performing a code refactoring task.
            Your task is to apply a series of specific modifications to an original source code file.

            **MANDATORY INSTRUCTIONS:**
            1.  **Apply ONLY the specified modifications.** Do not add, change, or delete any other part of the code. Do not add any new logic or comments.
            2.  **Output the Complete File:** Your entire response MUST be the complete, full text of the source code file after the modifications have been applied. Do not output only the changed snippets, diffs, or any explanations.
            3.  **Preserve Formatting:** Maintain the original code's indentation and formatting as much as possible.

            **--- INPUTS ---**

            **1. Original Source Code:**
            ```
            {original_code}
            ```

            **2. Modifications to Apply (JSON):**
            ```json
            {modifications_json}
            ```

            **--- Full Source Code After Modifications ---**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            # The raw text of the response is the full, modified code file.
            return response_text.strip()

        except Exception as e:
            error_msg = f"An unexpected error occurred while applying code modifications: {e}"
            logging.error(error_msg)
            # Returning the original code is a safe fallback on failure
            return original_code