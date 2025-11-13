# agents/agent_code_review.py

"""
This module contains the CodeReviewAgent class.
(ASDF Change Request CR-ASDF-002)
"""

import logging
import textwrap
from typing import Tuple
from llm_service import LLMService

class CodeReviewAgent:
    """
    Acts as an automated code reviewer, validating new source code against its
    specification, logic plan, and the existing codebase context.
    (ASDF Change Request CR-ASDF-002)
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the CodeReviewAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the CodeReviewAgent.")
        self.llm_service = llm_service
        logging.info("CodeReviewAgent initialized.")

    def review_code(self, micro_spec: str, logic_plan: str, new_source_code: str, rowd_json: str, coding_standard: str) -> Tuple[str, str]:
        """
        Performs a deep-dive review of new source code. It now has three possible outcomes
        and uses a technology-agnostic prompt.
        """
        logging.info("CodeReviewAgent: Starting comprehensive code review and auto-fixing...")

        prompt = textwrap.dedent(f"""
            You are an expert, detail-oriented code reviewer and auto-formatter. Your primary objective is to analyze the provided source code and ensure it perfectly adheres to its requirements and a given Coding Standard.

            **MANDATORY INSTRUCTIONS:**

            1.  **Check for MAJOR Issues First:** Analyze the code for logical errors, security vulnerabilities, or significant deviations from the Micro-Specification or Logic Plan.
                -   If you find any MAJOR issues, your response MUST begin with the single word "FAIL:", followed by a detailed list of only the major discrepancies.

            2.  **Check for MINOR Stylistic Issues Second:** If there are no major issues, you must meticulously check the code against all rules in the provided "Coding Standard" document.
                -   If you find ONLY minor stylistic/formatting issues (e.g., incorrect line length, improper blank lines, missing documentation), you MUST automatically FIX them. Your response must then begin with the phrase "PASS_WITH_FIXES:", followed immediately by the complete, corrected, and clean source code.

            3.  **Check for Perfection:** If the code has no major or minor issues and perfectly adheres to all rules, your ENTIRE response MUST be the single word "PASS:".

            4.  **Enforcement:** Your analysis must be strict. Your entire response must start with one of three phrases: "FAIL:", "PASS_WITH_FIXES:", or "PASS:". Do not include any other conversational text or markdown fences.

            **--- INPUTS ---**
            **1. Micro-Specification (What to build):**
            {micro_spec}

            **2. Logic Plan (How to build it):**
            {logic_plan}

            **3. Coding Standard to Enforce (The rules):**
            ```
            {coding_standard}
            ```

            **4. New Source Code to Review:**
            ```
            {new_source_code}
            ```

            **--- Review Assessment (Must start with "FAIL:", "PASS_WITH_FIXES:", or "PASS:") ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            response_text = response_text.strip()

            if response_text.startswith("PASS:"):
                logging.info("Code review status: PASS")
                return "pass", response_text[5:].strip()
            elif response_text.startswith("PASS_WITH_FIXES:"):
                logging.info("Code review status: PASS_WITH_FIXES")
                return "pass_with_fixes", response_text[18:].strip()
            elif response_text.startswith("FAIL:"):
                logging.warning("Code review status: FAIL")
                return "fail", response_text[5:].strip()
            else:
                logging.error("Received an invalid response format from the review agent.")
                return "fail", "The code review agent returned a response in an invalid format."

        except Exception as e:
            logging.error(f"CodeReviewAgent API call failed: {e}")
            raise e # Re-raise the exception