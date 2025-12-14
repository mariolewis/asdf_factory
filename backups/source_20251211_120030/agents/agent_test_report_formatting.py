# agents/agent_test_report_formatting.py

import logging
import textwrap
import json
from llm_service import LLMService, parse_llm_json
import vault

class TestReportFormattingAgent:
    """
    An agent that takes a structured test plan and raw execution output,
    and formats them into a human-readable report.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the TestReportFormattingAgent.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the TestReportFormattingAgent.")
        self.llm_service = llm_service
        logging.info("TestReportFormattingAgent initialized.")

    def format_report(self, plan_json: str, raw_output: str) -> str:
        """
        Generates a human-readable report in Markdown format by correlating a
        test plan with raw test execution output.
        """
        logging.info("TestReportFormattingAgent: Formatting final test report...")
        try:
            prompt = vault.get_prompt("agent_test_report_formatting__prompt_30").format(plan_json=plan_json, raw_output=raw_output)

            report_markdown = self.llm_service.generate_text(prompt, task_complexity="simple")
            return report_markdown.strip()

        except Exception as e:
            logging.error(f"Failed to format test report: {e}", exc_info=True)
            raise e # Re-raise the exception