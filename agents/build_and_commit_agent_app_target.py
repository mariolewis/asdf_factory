"""
This module contains the BuildAndCommitAgentAppTarget class.
"""
import subprocess
import os
import sys
from pathlib import Path
import logging
import git
import watermarker
from agents.agent_verification_app_target import VerificationAgent_AppTarget
from llm_service import LLMService

class BuildAndCommitAgentAppTarget:
    """
    Agent responsible for handling the build process and Git commit operations
    for a target application's components.
    """

    def __init__(self, project_repo_path: str, version_control_enabled: bool):
        """
        Initializes the BuildAndCommitAgentAppTarget.

        Args:
            project_repo_path (str): The absolute local path to the target
                                     application's project folder.
            version_control_enabled (bool): Flag indicating if Git is used.
        """
        import git

        self.repo_path = Path(project_repo_path)
        self.repo = None

        if not self.repo_path.is_dir():
            raise FileNotFoundError(f"Project repository path does not exist or is not a directory: {self.repo_path}")

        if version_control_enabled:
            try:
                # Initialize a Repo object from the GitPython library
                self.repo = git.Repo(self.repo_path)
            except git.InvalidGitRepositoryError:
                # This error is now handled by the pre-flight check, but this is a safeguard.
                raise git.InvalidGitRepositoryError(f"The path provided is not a valid Git repository: {self.repo_path}")

    def _sanitize_path(self, raw_path: str | None) -> str | None:
        """
        Cleans and validates a file path string received from an LLM.
        ...
        """
        if not raw_path or not raw_path.strip():
            return None

        # Check for common invalid placeholder values
        if raw_path.lower().strip() in ["n/a", "none", "tbd"]:
            logging.warning(f"Sanitizer rejected an invalid placeholder path: '{raw_path}'")
            return None

        # Take the first part if there are commas or spaces in a list
        path = raw_path.split(',')[0].strip()

        # Remove characters invalid in most filesystems
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            path = path.replace(char, '')

        # Replace backslashes with forward slashes for consistency
        path = path.replace('\\', '/')

        # Structural validation: ensure no part of the path is empty
        if any(not part.strip() for part in path.split('/')):
            logging.warning(f"Sanitizer rejected a structurally invalid path: '{path}'")
            return None

        # Ensure it's a relative path to prevent absolute path injections
        if Path(path).is_absolute():
            logging.warning(f"Sanitizer received an absolute path, which is not allowed: {path}. Ignoring.")
            return None

        return path

    def build_and_commit_component(self, component_path_str: str, component_code: str, test_path_str: str, test_code: str, test_command: str, llm_service: LLMService, version_control_enabled: bool) -> tuple[str, str]:
        """
        Writes files, runs tests, and conditionally commits on success.
        Returns a tuple of (status, message), where status is 'SUCCESS',
        'CODE_FAILURE', 'ENVIRONMENT_FAILURE', or 'AGENT_ERROR'.
        """
        try:
            sanitized_component_path = self._sanitize_path(component_path_str)
            sanitized_test_path = self._sanitize_path(test_path_str)

            files_to_commit = []

            if sanitized_component_path:
                component_path = self.repo_path / sanitized_component_path
                component_path.parent.mkdir(parents=True, exist_ok=True)
                component_path.write_text(component_code, encoding='utf-8', newline='\n')
                files_to_commit.append(str(sanitized_component_path))
                logging.info(f"Wrote source code to {component_path}")
                watermarker.apply_watermark(str(component_path))

            if sanitized_test_path:
                test_path = self.repo_path / sanitized_test_path
                test_path.parent.mkdir(parents=True, exist_ok=True)
                test_path.write_text(test_code, encoding='utf-8', newline='\n')
                files_to_commit.append(str(sanitized_test_path))
                logging.info(f"Wrote unit tests to {test_path}")
                watermarker.apply_watermark(str(test_path))

            logging.info(f"Running test suite with command: '{test_command}'")
            verification_agent = VerificationAgent_AppTarget(llm_service=llm_service)
            status, test_output = verification_agent.run_all_tests(self.repo_path, test_command)

            if status != 'SUCCESS':
                logging.error(f"Test run failed with status {status}. Aborting commit.")
                # Return the specific status received from the verification agent
                return status, test_output

            if not version_control_enabled:
                logging.info("Version control is disabled. Skipping commit.")
                return "SUCCESS", "Component saved and tests passed (local workspace)."

            if not files_to_commit:
                logging.warning("No files were written to disk for this component, but tests passed. Skipping commit.")
                return "SUCCESS", "Tests passed, but no files were generated to commit."

            component_name = Path(files_to_commit[0]).name
            commit_message = f"feat: Add component {component_name} and unit tests"
            commit_success, commit_result = self.commit_changes(files_to_commit, commit_message)

            if not commit_success:
                raise Exception(f"Git commit failed after tests passed: {commit_result}")

            logging.info(f"Successfully tested and committed component {component_name}.")
            return "SUCCESS", commit_result

        except Exception as e:
            error_message = f"An unexpected error occurred in build_and_commit_component: {e}"
            logging.error(error_message, exc_info=True)
            return "AGENT_ERROR", error_message

    def run_command(self, command_to_run: str) -> tuple[bool, str]:
        """
        Runs the specified command in the root of the project repository.
        """
        try:
            # CORRECTED: Changed 'build_command' to the correct parameter name 'command_to_run'
            result = subprocess.run(
                command_to_run,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.repo_path,
                check=False
            )

            combined_output = f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}"

            if result.returncode == 0:
                return True, combined_output
            else:
                return False, combined_output

        except Exception as e:
            error_message = f"An unexpected error occurred while running the command: {e}"
            return False, error_message

    def commit_changes(self, files_to_add: list[str], commit_message: str) -> tuple[bool, str]:
        """
        Stages the specified files and commits them with the given message.

        Args:
            files_to_add (list[str]): A list of file paths (relative to the repo root)
                                      to be added to this commit.
            commit_message (str): The commit message.

        Returns:
            tuple[bool, str]: A tuple containing:
                              - A boolean indicating success (True) or failure (False).
                              - The new commit hash as a string on success, or an error message on failure.
        """
        try:
            # The repo object was initialized in the constructor.
            index = self.repo.index

            # Stage the specified files.
            index.add(files_to_add)

            # Commit the staged changes.
            new_commit = index.commit(commit_message)

            commit_hash = new_commit.hexsha
            success_message = f"Successfully committed changes. New commit hash: {commit_hash}"
            return True, success_message

        except git.GitCommandError as e:
            error_message = f"An error occurred during git commit: {e}"
            return False, error_message
        except Exception as e:
            error_message = f"An unexpected error occurred during commit: {e}"
            return False, error_message

    def run_test_suite_only(self, test_command: str) -> tuple[bool, str]:
        """
        Runs the provided test command and captures the output.

        Args:
            test_command (str): The command to execute to run the test suite.

        Returns:
            A tuple containing a boolean for success and the captured output.
        """
        try:
            logging.info(f"Running test suite with command: '{test_command}'")
            # For Windows, create a startupinfo object to hide the console window
            # Prepare suppression flags for Windows
            run_kwargs = {}
            if sys.platform == "win32":
                run_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                test_command.split(),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
                **run_kwargs
            )

            if result.returncode == 0:
                logging.info("Test suite passed.")
                return True, result.stdout
            else:
                logging.warning("Test suite failed.")
                # Combine stdout and stderr for a complete failure log
                failure_output = f"--- STDOUT ---\n{result.stdout}\n\n--- STDERR ---\n{result.stderr}"
                return False, failure_output

        except FileNotFoundError:
            error_msg = f"Error: The command '{test_command.split()[0]}' was not found. Please ensure it is installed and in your system's PATH."
            logging.error(error_msg)
            return False, error_msg
        except Exception as e:
            logging.error(f"An unexpected error occurred while running the test suite: {e}")
            return False, f"An unexpected error occurred: {e}"

    def commit_all_changes(self, commit_message: str) -> tuple[bool, str]:
        """
        Stages all changes in the repository (new, modified, deleted) and commits them.

        Args:
            commit_message (str): The message to use for the commit.

        Returns:
            A tuple containing a boolean for success and a status message.
        """
        try:
            repo = git.Repo(self.repo_path)

            # Stage all changes, including untracked files
            repo.git.add(A=True)

            # Check if there is anything to commit after staging.
            # This now handles the edge case of a new repo with no commits yet.
            has_changes_to_commit = False
            if not repo.head.is_valid(): # Checks if HEAD exists (i.e., if there are any commits)
                if repo.index.entries: # Check if anything is staged
                    has_changes_to_commit = True
            elif repo.index.diff("HEAD"): # Standard check for existing repos
                has_changes_to_commit = True

            if not has_changes_to_commit:
                logging.info("No changes to commit after staging.")
                return True, "No changes detected to commit."

            commit = repo.index.commit(commit_message)
            logging.info(f"Successfully committed all changes. New commit hash: {commit.hexsha}")
            return True, f"New commit hash: {commit.hexsha}"

        except git.GitCommandError as e:
            logging.error(f"Failed to commit all changes: {e}")
            return False, str(e)
        except Exception as e:
            logging.error(f"An unexpected error occurred during commit: {e}")
            return False, f"An unexpected error occurred: {e}"

