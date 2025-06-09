import logging
import subprocess
import tempfile
import os
from pathlib import Path

"""
This module contains the VerificationAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VerificationAgent_AppTarget:
    """
    Agent responsible for verifying if a bug fix was successful.

    After a fix has been applied, this agent re-runs the relevant tests
    to confirm that the original failure is resolved.
    """

    def __init__(self):
        """Initializes the VerificationAgent_AppTarget."""
        logging.info("VerificationAgent initialized.")

    def run_verification_tests(self, test_code: str, project_root: str | Path) -> tuple[bool, str]:
        """
        Executes a given set of test code to verify a fix.

        NOTE: This is a basic implementation that assumes a pytest environment.
        It writes the test code to a temporary file and executes it using pytest.
        Future enhancements would involve more sophisticated environment management
        and test runner integration.

        Args:
            test_code (str): The source code of the unit/integration tests to be run.
            project_root (str | Path): The root directory of the target project,
                                       used as the working directory for the test runner.

        Returns:
            tuple[bool, str]: A tuple containing:
                              - A boolean indicating success (True) or failure (False).
                              - A string containing the output from the test runner.
        """
        logging.info("Starting verification test run...")
        project_root = Path(project_root)

        if not project_root.is_dir():
            error_msg = f"Verification failed: Project root '{project_root}' is not a valid directory."
            logging.error(error_msg)
            return False, error_msg

        try:
            # Create a temporary file to hold the test code
            with tempfile.NamedTemporaryFile(
                mode='w',
                delete=False,
                suffix='_test.py',
                dir=project_root, # Create the temp file within the project structure
                encoding='utf-8'
            ) as tmp_test_file:
                tmp_test_file.write(test_code)
                tmp_test_file_path = tmp_test_file.name

            logging.info(f"Running pytest on temporary test file: {tmp_test_file_path}")

            # Execute pytest using subprocess
            # We run it from the project's root directory to ensure all imports work correctly.
            result = subprocess.run(
                ['pytest', tmp_test_file_path],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False  # We don't want to raise an exception on non-zero exit codes
            )

            # Clean up the temporary file
            os.remove(tmp_test_file_path)

            output = result.stdout + "\n" + result.stderr
            logging.info(f"Pytest execution finished with exit code: {result.returncode}")

            # Pytest exit codes: 0 = all tests passed, 1 = tests collected and run but some failed
            # Other codes indicate different types of errors.
            if result.returncode == 0:
                logging.info("Verification successful: All tests passed.")
                return True, output
            else:
                logging.warning("Verification failed: Some tests did not pass.")
                return False, output

        except FileNotFoundError:
            error_msg = "Verification failed: 'pytest' command not found. Ensure pytest is installed in the environment."
            logging.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred during test verification: {e}"
            logging.error(error_msg)
            return False, error_msg