# agent_verification_app_target.py

import logging
import subprocess
import textwrap
import json
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from llm_service import LLMService

class VerificationAgent_AppTarget:
    """
    Agent responsible for running the entire test suite for a project
    by intelligently determining the command and its tool dependencies.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the VerificationAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the VerificationAgent_AppTarget.")
        self.llm_service = llm_service
        logging.info("VerificationAgent initialized.")

    def _get_test_execution_details(self, tech_spec_text: str) -> dict:
        """
        Analyzes the tech spec to determine the test command and required tools.
        Returns a dictionary with 'command' and 'required_tools' keys.
        """
        prompt = textwrap.dedent(f"""
            Analyze the following Technical Specification to determine the command needed to run unit tests and a list of any required testing libraries or frameworks.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            2.  **Structure:** The JSON object must have two keys: "command" (a string with the exact test command, e.g., "pytest") and "required_tools" (a JSON array of strings, e.g., ["pytest", "pytest-cov"]).
            3.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON object.

            **--- Technical Specification ---**
            {tech_spec_text}
            **--- End Specification ---**

            **--- JSON Output ---**
        """)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            details = json.loads(cleaned_response)
            if "command" in details and "required_tools" in details:
                return details
            else:
                logging.error("LLM output was missing 'command' or 'required_tools' keys.")
                return {"command": "pytest", "required_tools": []}
        except Exception as e:
            logging.error(f"Failed to get test execution details from LLM: {e}")
            return {"command": "pytest", "required_tools": []}

    def run_all_tests(self, project_root: str | Path, test_command_str: str) -> tuple[str, str]:
        """
        Executes the entire test suite for the project using a provided command.

        Returns:
            A tuple containing a status string ('SUCCESS', 'CODE_FAILURE',
            'ENVIRONMENT_FAILURE') and the test runner output.
        """
        logging.info(f"Running full test suite for project at: {project_root}")
        project_root = Path(project_root)

        if not project_root.is_dir():
            return 'ENVIRONMENT_FAILURE', f"Verification failed: Project root '{project_root}' is not a valid directory."

        if not test_command_str:
            return 'ENVIRONMENT_FAILURE', "Verification failed: Test execution command was not provided."

        logging.info(f"Executing verification command: '{test_command_str}'")

        try:
            win_venv_activate = project_root / "venv" / "Scripts" / "activate.bat"
            nix_venv_activate = project_root / "venv" / "bin" / "activate"

            full_command = ""
            if sys.platform == "win32":
                if win_venv_activate.exists():
                    full_command = f'call "{win_venv_activate}" & {test_command_str}'
                else:
                    full_command = test_command_str
                command_to_run = f'cmd /c "{full_command}"'
            else:  # Linux/macOS
                if nix_venv_activate.exists():
                    full_command = f'source "{nix_venv_activate}" & {test_command_str}'
                else:
                    full_command = test_command_str
                command_to_run = f'bash -c "{full_command}"'

            logging.info(f"Executing full insulated command: '{command_to_run}'")
            result = subprocess.run(
                test_command_str,
                shell=True,
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False
            )
            output = result.stdout + "\n" + result.stderr

            if result.returncode == 127 or "is not recognized" in output or "command not found" in output:
                logging.error(f"Environment Failure: Test command '{test_command_str}' not found.")
                return 'ENVIRONMENT_FAILURE', output

            logging.info(f"Verification execution finished with exit code: {result.returncode}")

            if result.returncode == 0:
                return 'SUCCESS', output
            else:
                return 'CODE_FAILURE', output

        except FileNotFoundError:
            tool_name = test_command_str.split()[0]
            error_msg = (
                f"Test execution failed: The command '{tool_name}' could not be found.\n"
                f"Please ensure the required testing tools are installed and accessible in your system's PATH."
            )
            logging.error(error_msg)
            return 'ENVIRONMENT_FAILURE', error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred during test verification: {e}"
            logging.error(error_msg)
            return 'ENVIRONMENT_FAILURE', error_msg