# agents/agent_automated_ui_test_script.py
import logging
import textwrap
import json
import re
from pathlib import Path
from datetime import datetime
from llm_service import LLMService

class AutomatedUITestScriptAgent:
    """
    Agent responsible for generating automated UI test scripts.
    """
    def __init__(self, llm_service: LLMService):
        if not llm_service:
            raise ValueError("llm_service is required for the AutomatedUITestScriptAgent.")
        self.llm_service = llm_service
        logging.info("AutomatedUITestScriptAgent initialized.")

    def _build_prompt(self, sprint_items_json: str, ux_blueprint_json: str) -> str:
        """Constructs the prompt for the LLM to generate test scripts and a structured plan."""
        return textwrap.dedent(f"""
            You are an expert QA Automation Engineer. Your task is to write a Python test script using `pytest` and `selenium` AND provide a structured JSON summary of the test plan.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Object Output:** Your entire response MUST be a single, valid JSON object.
            2.  **JSON Schema:** The JSON object MUST have two top-level keys:
                - `script_code`: A string containing the complete, raw Python `pytest` script.
                - `test_plan`: An array of objects, where each object represents a test case and has the keys: `test_case_id` (a short identifier like "TC-01"), `scenario` (a one-sentence description), and `expected_result`.
            3.  **Test Logic:** The tests must validate the features in "Sprint Backlog Items" and use selectors from the "UI Blueprint".
            4.  **No Other Text:** Do not include any text, explanations, or markdown formatting outside of the raw JSON object itself.

            **--- INPUT 1: Sprint Backlog Items (The "What" to test) ---**
            ```json
            {sprint_items_json}
            ```

            **--- INPUT 2: UI Blueprint (The UI structure) ---**
            ```json
            {ux_blueprint_json}
            ```

            **--- Required JSON Output ---**
        """)

    def generate_scripts(self, sprint_items_json: str, ux_blueprint_json: str, project_root: str) -> tuple[str | None, str | None]:
        """
        Generates a UI test script and a structured JSON test plan.

        Returns:
            A tuple containing (script_code, plan_json), or (None, None) on failure.
        """
        logging.info("Generating automated UI test script and plan...")
        try:
            prompt = self._build_prompt(sprint_items_json, ux_blueprint_json)
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            result_json = json.loads(cleaned_response)

            script_code = result_json.get("script_code")
            test_plan = result_json.get("test_plan")

            if not script_code or not test_plan:
                logging.error("Agent failed to generate a valid script_code or test_plan from the LLM response.")
                return None, None

            # Save the script to a file
            test_dir = Path(project_root) / "tests" / "ui_tests"
            test_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            test_file_path = test_dir / f"test_sprint_{timestamp}.py"
            test_file_path.write_text(script_code, encoding='utf-8')
            logging.info(f"Successfully generated and saved UI test script to {test_file_path}")

            plan_json_str = json.dumps(test_plan, indent=2)
            return script_code, plan_json_str
        except Exception as e:
            logging.error(f"Failed to generate UI test script and plan: {e}", exc_info=True)
            return None, None