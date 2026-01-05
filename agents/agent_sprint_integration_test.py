# agents/agent_sprint_integration_test.py

import logging
import textwrap
import json
import ast
import re
import os
import sys
from pathlib import Path
from typing import Tuple, Optional
# Add parent directory to path to locate watermarker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from watermarker import apply_watermark

from llm_service import LLMService, parse_llm_json
from klyve_db_manager import KlyveDBManager

class SprintIntegrationTestAgent:
    """
    Agent responsible for generating a sprint-specific integration test.

    This agent gathers all code artifacts from a completed sprint, analyzes their
    interactions, and generates a temporary test script and the command needed
    to execute it[cite: 2192, 2196].
    """

    def __init__(self, llm_service: LLMService, db_manager: KlyveDBManager):
        """
        Initializes the SprintIntegrationTestAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
            db_manager (KlyveDBManager): An instance of the database manager.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the SprintIntegrationTestAgent.")
        if not db_manager:
            raise ValueError("db_manager is required for the SprintIntegrationTestAgent.")
        self.llm_service = llm_service
        self.db_manager = db_manager
        logging.info("SprintIntegrationTestAgent initialized.")

    def generate_test(self, project_id: str, sprint_id: str) -> Optional[Tuple[str, str]]:
        """
        Generates a temporary integration test script and the command to run it.

        Args:
            project_id (str): The ID of the current project.
            sprint_id (str): The ID of the sprint to generate tests for.

        Returns:
            A tuple containing the (relative_script_path, execution_command), or None on failure[cite: 2202].
        """
        logging.info(f"Generating sprint-specific integration test for sprint '{sprint_id}'.")
        try:
            # 1. Gather context: project details and sprint artifacts
            project_details = self.db_manager.get_project_by_id(project_id)
            if not project_details:
                raise FileNotFoundError("Project details could not be retrieved.")

            project_root = Path(project_details['project_root_folder'])
            tech_spec = project_details['tech_spec_text']
            sprint_items = self.db_manager.get_items_for_sprint(sprint_id)

            if not sprint_items:
                logging.warning(f"No backlog items found for sprint '{sprint_id}'. Cannot generate integration test.")
                return None

            sprint_artifacts_context = ""
            for item in sprint_items:
                preview = item['technical_preview_text'] or item['description']
                sprint_artifacts_context += f"--- Backlog Item: {item['title']} ---\n{preview}\n\n"

            # 2. Build the prompt for the LLM
            prompt = self._build_prompt(tech_spec, sprint_artifacts_context)

            # 3. Call LLM and parse response robustly
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("LLM response did not contain a valid JSON object for the test plan.")

            try:
                result = parse_llm_json(json_match.group(0))
            except json.JSONDecodeError:
                # Fallback: parse as Python dictionary (handles single quotes)
                result = ast.literal_eval(json_match.group(0))
            script_code = result.get("test_script_code")
            execution_command = result.get("execution_command")

            if not script_code or not execution_command:
                raise ValueError("LLM response was missing 'test_script_code' or 'execution_command'.")

            # 4. Save the temporary test script
            tests_dir = project_root / "tests"
            tests_dir.mkdir(exist_ok=True, parents=True)
            temp_test_path = tests_dir / "sprint_integration_temp_test.py"
            temp_test_path.write_text(script_code, encoding='utf-8', newline='\n')
            # Apply watermark to the saved file
            apply_watermark(str(temp_test_path))
            logging.info(f"Saved temporary integration test to: {temp_test_path}")

            relative_script_path = str(temp_test_path.relative_to(project_root)).replace('\\', '/')

            return relative_script_path, execution_command

        except Exception as e:
            logging.error(f"Failed to generate sprint integration test: {e}", exc_info=True)
            raise e # Re-raise the exception

    def _build_prompt(self, tech_spec: str, sprint_artifacts_context: str) -> str:
        """Constructs the prompt for the LLM to generate the test script and command."""
        return textwrap.dedent(f"""
            You are an expert QA Automation Engineer. Your task is to write a single, temporary integration test file and determine the command to run it. The test must validate that the components and changes implemented in a sprint work together correctly.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Context:** Analyze the 'Technical Specification' to understand the project's language and testing frameworks. Analyze the 'Sprint Artifacts Context' to understand what was changed in this sprint.
            2.  **Generate Test Script:** Write a single test script file that specifically tests the interactions between the components described in the sprint context. The test should be meaningful but not exhaustive. Focus on a key integration path. The code MUST conform to the language and frameworks in the tech spec.
            3.  **Generate Command:** Based on the tech spec and the test file you generated (which you should name `sprint_integration_temp_test.py` inside a `tests/` directory), determine the exact command-line instruction to run ONLY this single test file[cite: 2201].
            4.  **JSON Output:** Your entire response MUST be a single, valid JSON object with two keys:
                - `test_script_code`: A string containing the complete, raw source code for the test script.
                - `execution_command`: A string containing the exact command to run the script (e.g., "pytest tests/sprint_integration_temp_test.py", "mvn test -Dtest=SprintIntegrationTempTest").
            5.  **No Other Text:** Do not include any text, explanations, or markdown formatting outside of the raw JSON object itself.

            **--- INPUT 1: Technical Specification (for language/framework context) ---**
            ```
            {tech_spec}
            ```

            **--- INPUT 2: Sprint Artifacts Context (what to test) ---**
            ```
            {sprint_artifacts_context}
            ```

            **--- Required JSON Output ---**
        """)