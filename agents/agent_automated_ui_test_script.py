# agents/agent_automated_ui_test_script.py
import logging
import textwrap
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
        """Constructs the prompt for the LLM to generate test scripts."""
        return textwrap.dedent(f"""
            You are an expert QA Automation Engineer. Your task is to write a Python test script using the `pytest` framework and the `selenium` library to perform automated UI testing.

            **MANDATORY INSTRUCTIONS:**
            1.  **Use `pytest` and `selenium`:** The entire script must be a valid Python script designed to be run with `pytest`.
                Use standard selenium WebDriver calls to interact with UI elements.
            2.  **Base Tests on Sprint Scope:** The tests you write must validate the features and user stories described in the "Sprint Backlog Items".
            3.  **Use UI Blueprint for Selectors:** Use the "UI Blueprint" to identify the names and structure of UI components to create reliable selenium selectors (e.g., finding elements by `objectName`).
            4.  **RAW CODE ONLY:** Your entire response MUST be a single, raw Python code block enclosed in ```python ... ```.
                Do not include any other text, explanations, or conversational preamble.
            5.  **Include Setup/Teardown:** The script must include a pytest fixture to set up and tear down the WebDriver instance.
                For this project, assume the application is a local PySide6 desktop app and use the appropriate selenium driver for that context if possible, or a standard web driver as a fallback.

            **--- INPUT 1: Sprint Backlog Items (The "What" to test) ---**
            ```json
            {sprint_items_json}
            --- INPUT 2: UI Blueprint (The UI structure) ---

            JSON

            {ux_blueprint_json}
            --- Generated pytest Script ---
        """)

    def generate_scripts(self, sprint_items_json: str, ux_blueprint_json: str, project_root: str) -> bool:
        """
        Generates a UI test script and saves it to the project.

        Returns:
            bool: True on success, False on failure.
        """
        logging.info("Generating automated UI test script...")
        try:
            prompt = self._build_prompt(sprint_items_json, ux_blueprint_json)
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            # Extract code from markdown block
            code_match = re.search(r"```python\n(.*)```", response_text, re.DOTALL)
            if not code_match:
                logging.error("Agent failed to generate a valid Python code block from the LLM response.")
                return False

            script_code = code_match.group(1).strip()
            if not script_code:
                logging.error("Agent generated an empty Python code block.")
                return False

            # Save the script to a file
            test_dir = Path(project_root) / "tests" / "ui_tests"
            test_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            test_file_path = test_dir / f"test_sprint_{timestamp}.py"
            test_file_path.write_text(script_code, encoding='utf-8')

            logging.info(f"Successfully generated and saved UI test script to {test_file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to generate UI test script: {e}", exc_info=True)
            return False