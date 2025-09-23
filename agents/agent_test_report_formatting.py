# agents/agent_test_report_formatting.py

import logging
import textwrap
import json
from llm_service import LLMService

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
            prompt = textwrap.dedent(f"""
                You are an expert QA Analyst responsible for writing final test reports. Your task is to correlate a structured test plan with the raw, unstructured output from a test runner and produce a clean, human-readable summary in a Markdown table.

                **MANDATORY INSTRUCTIONS:**
                1.  **Correlate Results:** For each test case in the "Structured Test Plan", you MUST find its result in the "Raw Test Runner Output".
                2.  **Determine Status:** Based on the output, determine if each test case's status is "Pass" or "Fail".
                3.  **Summarize Actual Result:** For each test case, write a concise, one-sentence summary of the actual result from the raw output. For failures, this summary MUST include the primary reason for the failure.
                4.  **Markdown Table ONLY:** Your entire response MUST be a single, well-formatted Markdown table and nothing else. The first character of your response must be the `|` of the table header.
                5.  **Table Columns:** The table MUST have the columns: "Test Case ID", "Scenario", "Expected Result", "Actual Result", and "Status".

                **--- INPUT 1: Structured Test Plan (JSON) ---**
                ```json
                {plan_json}
                ```

                **--- INPUT 2: Raw Test Runner Output ---**
                ```
                {raw_output}
                ```

                **--- OUTPUT: Final Test Report (Markdown Table Only) ---**
            """)

            report_markdown = self.llm_service.generate_text(prompt, task_complexity="simple")
            return report_markdown.strip()

        except Exception as e:
            logging.error(f"Failed to format test report: {e}", exc_info=True)
            return f"### Error\nAn error occurred while formatting the test report: {e}"