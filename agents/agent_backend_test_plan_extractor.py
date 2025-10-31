# agents/agent_backend_test_plan_extractor.py

import logging
import textwrap
import json
from llm_service import LLMService

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
            prompt = textwrap.dedent(f"""
                You are an expert QA Engineer who specializes in reverse-engineering test plans from existing code. Your task is to analyze a set of test files for a project using the following technologies: {', '.join(technology_list)}. You must produce a structured JSON test plan.

                **MANDATORY INSTRUCTIONS:**
                1.  **Analyze the Code:** Read all the provided test files. Identify each individual test case, its purpose, and what it asserts.
                2.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array of objects `[]`.
                3.  **JSON Object Schema:** Each object in the array represents one test case and MUST have the keys: `test_case_id` (a short, unique identifier you create, e.g., "TC-01"), `scenario` (a one-sentence description of what the test does), and `expected_result` (a one-sentence description of the expected outcome, inferred from the test's assertions).
                4.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON array itself.

                **--- INPUT: Test Code Files (Languages: {', '.join(technology_list)}) ---**
                {code_context}

                **--- OUTPUT: Structured Test Plan (JSON Array) ---**
            """)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            json.loads(cleaned_response) # Final validation
            return cleaned_response

        except Exception as e:
            logging.error(f"Failed to extract backend test plan: {e}", exc_info=True)
            return json.dumps([{"error": f"An error occurred while extracting the test plan: {e}"}])