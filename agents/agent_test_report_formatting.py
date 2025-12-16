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
        Generates a human-readable report in Markdown format.
        Includes robust safeguards for CLI errors and empty tables.
        """
        logging.info("TestReportFormattingAgent: Formatting final test report...")

        # 1. Immediate Fallback for Empty/Whitespace output
        if not raw_output or not raw_output.strip():
            return "## Execution Error\n\nNo output was captured from the test runner."

        # 2. Heuristic: Detect common Shell/CLI errors immediately
        # If the command failed to run, there's no point asking the LLM to find "Test Cases".
        lower_out = raw_output.lower()
        error_keywords = [
            "is not recognized as an internal or external command", # Windows
            "command not found", # Linux/Mac
            "syntax error",
            "python: can't open file"
        ]

        if any(keyword in lower_out for keyword in error_keywords):
            logging.warning("TestReportFormattingAgent: Detected CLI error. Skipping LLM.")
            # Manually constructing the string to avoid nested backtick issues
            return "## Test Execution Failure\n\nThe test command failed to execute properly.\n\n### System Output\n```text\n" + raw_output + "\n```"

        try:
            # 3. Escape braces to prevent .format() crashes if output contains JSON/Code
            safe_output = raw_output.replace("{", "{{").replace("}", "}}")

            prompt = vault.get_prompt("agent_test_report_formatting__prompt_30").format(plan_json=plan_json, raw_output=safe_output)

            report_markdown = self.llm_service.generate_text(prompt, task_complexity="simple")

            # 4. Strict Validation:
            # - Must contain "|" (Pipe)
            # - Must have at least 3 lines (Header, Separator, AND Data Row)
            lines = report_markdown.strip().split('\n')
            if "|" not in report_markdown or len(lines) < 3:
                logging.warning("TestReportFormattingAgent: LLM returned invalid or empty table. Falling back to raw error display.")

                fallback = "## Test Execution Failure\n\n"
                fallback += "The automated test runner executed, but the results could not be parsed into a structured table. This often indicates a crash or an unstructured error message.\n\n"
                fallback += "### Raw Execution Output\n"
                fallback += "```text\n" + raw_output + "\n```"
                return fallback

            return report_markdown.strip()

        except Exception as e:
            logging.error(f"Failed to format test report: {e}", exc_info=True)
            # Fallback if the agent crashes entirely
            return f"## Report Generation Error\n\nAn error occurred while formatting the report: {e}\n\n### Raw Output\n```text\n{raw_output}\n```"