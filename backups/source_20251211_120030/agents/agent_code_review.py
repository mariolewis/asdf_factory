# agents/agent_code_review.py

"""
This module contains the CodeReviewAgent class.
(Klyve Change Request CR-Klyve-002)
"""

import logging
import textwrap
from typing import Tuple
from llm_service import LLMService
import vault

class CodeReviewAgent:
    """
    Acts as an automated code reviewer, validating new source code against its
    specification, logic plan, and the existing codebase context.
    (Klyve Change Request CR-Klyve-002)
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

        prompt = vault.get_prompt("agent_code_review__prompt_39").format(micro_spec=micro_spec, logic_plan=logic_plan, coding_standard=coding_standard, new_source_code=new_source_code)

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