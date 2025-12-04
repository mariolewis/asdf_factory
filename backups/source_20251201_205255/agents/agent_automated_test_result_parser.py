# agents/agent_automated_test_result_parser.py
import logging
import textwrap
import json
from llm_service import LLMService, parse_llm_json

class AutomatedTestResultParserAgent:
    """
    Agent responsible for parsing the output of an automated test runner.
    """
    def __init__(self, llm_service: LLMService):
        if not llm_service:
            raise ValueError("llm_service is required for the AutomatedTestResultParserAgent.")
        self.llm_service = llm_service
        logging.info("AutomatedTestResultParserAgent initialized.")

    def _build_prompt(self, test_output: str) -> str:
        """Constructs the prompt for the LLM to parse test results."""
        return textwrap.dedent(f"""
            You are an expert QA Analyst. Your task is to parse the raw output from a test runner and determine the outcome.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze the Log:** Read the provided "Test Runner Output".
                Look for keywords like "FAILED", "ERROR", "passed", "x failed", "y passed", and summary lines.
            2.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            3.  **JSON Schema:** The JSON object MUST have two keys:
                - `success`: A boolean (`true` if all tests passed, `false` otherwise).
                - `summary`: A string. If tests failed, this must be a concise, human-readable summary of the failures, extracting the most relevant error messages.
                If all tests passed, it should be a simple success message (e.g., "All UI tests passed successfully.").
            4.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON object itself.

            **--- Test Runner Output ---**
            {test_output}
            **--- End Output ---**

            **--- JSON Result ---**
        """)

    def parse_results(self, test_output: str) -> dict:
        """
        Parses test runner output and returns a structured result.

        Returns:
            A dictionary with keys 'success' (bool) and 'summary' (str).
        """
        logging.info("Parsing automated test runner output...")
        try:
            prompt = self._build_prompt(test_output)
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")

            result = parse_llm_json(response_text)

            if "success" in result and "summary" in result:
                logging.info(f"Test parsing complete. Success: {result['success']}")
                return result
            else:
                raise ValueError("LLM response was missing required keys.")
        except Exception as e:
            logging.error(f"Failed to parse test results: {e}", exc_info=True)
            return {
                "success": False,
                "summary": f"An error occurred while parsing the test results: {e}"
            }