# agent_verification_app_target.py

import logging
import subprocess
import textwrap
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, List
import google.generativeai as genai

class VerificationAgent_AppTarget:
    """
    Agent responsible for running the entire test suite for a project
    by intelligently determining the command and its tool dependencies.
    """

    def __init__(self, api_key: str):
        """
        Initializes the VerificationAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for LLM interactions.
        """
        if not api_key:
            raise ValueError("API key is required for the VerificationAgent_AppTarget.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
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
            response = self.model.generate_content(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(cleaned_response)
            if result.get("command") and isinstance(result.get("required_tools"), list):
                return result
            logging.error("LLM output was missing 'command' or 'required_tools' keys.")
            return None
        except Exception as e:
            logging.error(f"LLM call failed to determine test command details: {e}.")
            return None

    def run_all_tests(self, project_root: str | Path, tech_spec_text: str) -> tuple[bool, str]:
        """
        Executes the entire test suite for the project, providing clear dependency info.

        Args:
            project_root (str | Path): The root directory of the target project.
            tech_spec_text (str): The technical specification for the project.

        Returns:
            A tuple containing a boolean for success/failure and the test runner output.
        """
        logging.info(f"Running full test suite for project at: {project_root}")
        project_root = Path(project_root)

        if not project_root.is_dir():
            return False, f"Verification failed: Project root '{project_root}' is not a valid directory."

        # 1. Determine test command and dependencies
        exec_details = self._get_test_execution_details(tech_spec_text)
        if not exec_details:
            return False, "Failed to determine test execution command from the Technical Specification."

        test_command_str = exec_details["command"]
        required_tools = exec_details["required_tools"]
        logging.info(f"Determined test command: '{test_command_str}'. Required tools: {required_tools}")

        try:
            # 2. Execute the command from the project's root directory
            result = subprocess.run(
                test_command_str,
                shell=True,
                cwd=project_root,
                capture_output=True,
                text=True
            )
            output = result.stdout + "\n" + result.stderr
            logging.info(f"Test suite execution finished with exit code: {result.returncode}")

            # 3. Return the result
            return result.returncode == 0, output

        except FileNotFoundError:
            # 4. Provide a helpful error message if the command's tool is not found
            tool_name = test_command_str.split()[0]
            error_msg = (
                f"Test execution failed: The command '{tool_name}' could not be found.\n"
                f"Please ensure the required tool(s) ({', '.join(required_tools)}) are installed and accessible in your system's PATH."
            )
            logging.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred during test verification: {e}"
            logging.error(error_msg)
            return False, error_msg