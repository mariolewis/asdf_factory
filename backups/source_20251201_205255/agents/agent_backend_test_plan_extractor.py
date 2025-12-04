# agents/agent_backend_test_plan_extractor.py

import logging
import textwrap
import json
from llm_service import LLMService, parse_llm_json
import vault

class BackendTestPlanExtractorAgent:
    """
    An agent that scans existing test code files for a given technology stack
    and extracts a structured, machine-readable test plan in JSON format.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the BackendTestPlanExtractorAgent.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the BackendTestPlanExtractorAgent.")
        self.llm_service = llm_service
        logging.info("BackendTestPlanExtractorAgent initialized.")

    def extract_plan(self, technology_list: list, test_files_content: dict) -> str:
        """
        Uses an LLM to parse test files and generate a JSON test plan.

        Args:
            technology_stack (str): The primary language of the project (e.g., "Python", "Java").
            test_files_content (dict): A dictionary mapping file paths to their string content.

        Returns:
            A JSON string representing the test plan, or a JSON string with an error.
        """
        logging.info(f"Extracting backend test plan from {len(test_files_content)} {', '.join(technology_list)} files...")

        # Format the code content for the prompt
        code_context = ""
        for path, content in test_files_content.items():
            code_context += f"--- File: {path} ---\n```{technology_list[0].lower()}\n{content}\n```\n\n"

        try:
            prompt = vault.get_prompt("agent_backend_test_plan_extractor__prompt_42").format(join_technology_list=', '.join(technology_list), code_context=code_context)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            parse_llm_json(cleaned_response) # Final validation
            return cleaned_response

        except Exception as e:
            logging.error(f"Failed to extract backend test plan: {e}", exc_info=True)
            raise e # Re-raise the exception