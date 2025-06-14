# agents/agent_code_review.py

"""
This module contains the CodeReviewAgent class.
(ASDF Change Request CR-ASDF-002)
"""

import logging
import textwrap
import google.generativeai as genai
from typing import Tuple

class CodeReviewAgent:
    """
    Acts as an automated code reviewer, validating new source code against its
    specification, logic plan, and the existing codebase context.
    (ASDF Change Request CR-ASDF-002)
    """

    def __init__(self, api_key: str):
        """
        Initializes the CodeReviewAgent.

        Args:
            api_key (str): The Gemini API key for LLM interactions.
        """
        if not api_key:
            raise ValueError("API key is required for the CodeReviewAgent.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        logging.info("CodeReviewAgent initialized.")

    def review_code(self, micro_spec: str, logic_plan: str, new_source_code: str, rowd_json: str, coding_standard: str) -> Tuple[str, str]:
        """
        Performs a deep-dive review of the newly generated source code.

        Args:
            micro_spec: The original micro-specification for the component.
            logic_plan: The intermediate logic plan for the component.
            new_source_code: The newly generated source code to be reviewed.
            rowd_json: A JSON string of the full Record-of-Work-Done.
            coding_standard (str): The coding standard to enforce.

        Returns:
            A tuple containing:
            - A status string: "pass" or "fail".
            - A detailed report of discrepancies if "fail", otherwise an empty string.
        """
        logging.info("CodeReviewAgent: Starting comprehensive code review...")

        prompt = textwrap.dedent(f"""
            You are an expert, detail-oriented code reviewer. Your task is to perform a deep-dive analysis and answer the question: "Does this source code perfectly and completely implement the logic plan, satisfy all requirements of the micro-specification, adhere to the coding standard, and contain no unwanted text, considering the existing artifacts in the Record-of-Work-Done (RoWD)? List all discrepancies."

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Holistically:** You MUST consider all five inputs: the micro-specification, the logic plan, the RoWD, the new source code, and the coding standard.
            2.  **Check for Contamination:** You MUST FAIL the review if the code contains any non-code text or markers that are not part of a valid docstring or a required inline comment (e.g., citation markers like ``, ``).
            3.  **Check Coding Standard:** You MUST verify that the `new_source_code` strictly adheres to all rules in the provided `Coding Standard`. This is a critical check.
            4.  **Check Logic & Requirements:** You MUST validate that the code correctly implements the `Logic Plan` and fulfills all requirements of the `Micro-Specification`.
            5.  **Check Cross-Referencing:** You MUST cross-reference the `new_source_code` against the plan implied by the `RoWD` for inconsistencies (e.g., using unplanned libraries or database columns).
            6.  **Output Format:**
                -   If the source code is perfect and has NO discrepancies of any kind, your ENTIRE response MUST begin with the single word "PASS:".
                -   If there are ANY discrepancies, your ENTIRE response MUST begin with the single word "FAIL:", followed by a detailed, numbered list of every discrepancy you found.

            **--- INPUT 1: Micro-Specification ---**
            {micro_spec}

            **--- INPUT 2: Logic Plan ---**
            {logic_plan}

            **--- INPUT 3: Existing Project Context (Record-of-Work-Done) ---**
            {rowd_json}

            **--- INPUT 4: Coding Standard to Enforce ---**
            {coding_standard}

            **--- INPUT 5: New Source Code to Review ---**
            ```
            {new_source_code}
            ```

            **--- Review Assessment (Must start with "PASS:" or "FAIL:") ---**
        """)

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            if response_text.startswith("PASS:"):
                logging.info("Code review status: PASS")
                return "pass", response_text[5:].strip()
            elif response_text.startswith("FAIL:"):
                logging.warning("Code review status: FAIL")
                return "fail", response_text[5:].strip()
            else:
                logging.error("Received an invalid response format from the review agent.")
                return "fail", "The code review agent returned a response in an invalid format."

        except Exception as e:
            logging.error(f"CodeReviewAgent API call failed: {e}")
            return "fail", f"An unexpected error occurred during code review: {e}"