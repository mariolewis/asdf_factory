# agent_verification_app_target.py

import logging
import subprocess
import textwrap
import json
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

    def _get_test_execution_details(self, tech_spec_text: str) -> Optional[Dict[str, any]]:
        """
        Determines the test command and required tools based on the tech spec.
        """
        prompt = textwrap.dedent(f"""
            You are a build engineering expert. Based on the provided technical specification, determine the standard command-line instruction to run the project's test suite and the tools required.

            Your response MUST be a single, valid JSON object with two keys:
            - "command": A string containing the single, standard, non-interactive command to run all tests from the repository root (e.g., "pytest", "mvn test", "gradlew test").
            - "required_tools": A JSON array of human-readable strings listing the necessary tools (e.g., ["pytest"], ["Java JDK", "Maven"], ["Go"]).

            Do not include any other text or explanations outside of the raw JSON object.

            **--- Technical Specification ---**
            {tech_spec_text}
            **--- End of Specification ---**

            **JSON Output:**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            result = json.loads(cleaned_response)
            if result.get("command") and isinstance(result.get("required_tools"), list):
                return result
            logging.error("LLM output was missing 'command' or 'required_tools' keys.")
            return None
        except Exception as e:
            logging.error(f"LLM call failed to determine test command details: {e}.")
            return None

    def run_all_tests(self, project_root: str | Path, test_command_str: str) -> tuple[str, str]:
        """
        Executes the entire test suite for the project using a provided command.

        Args:
            project_root (str | Path): The root directory of the target project.
            test_command_str (str): The specific command to execute to run all tests.

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
            result = subprocess.run(
                test_command_str,
                shell=True,
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False
            )
            output = result.stdout + "\n" + result.stderr
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