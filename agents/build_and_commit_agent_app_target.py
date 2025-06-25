"""
This module contains the BuildAndCommitAgentAppTarget class.
"""
import subprocess
import git
from pathlib import Path
import logging

class BuildAndCommitAgentAppTarget:
    """
    Agent responsible for handling the build process and Git commit operations
    for a target application's components.
    """

    def __init__(self, project_repo_path: str):
        """
        Initializes the BuildAndCommitAgentAppTarget.

        Args:
            project_repo_path (str): The absolute local path to the target
                                     application's Git repository.

        Raises:
            FileNotFoundError: If the provided repository path does not exist.
            git.InvalidGitRepositoryError: If the path is not a valid Git repository.
        """
        self.repo_path = Path(project_repo_path)

        if not self.repo_path.is_dir():
            raise FileNotFoundError(f"Project repository path does not exist or is not a directory: {self.repo_path}")

        try:
            # Initialize a Repo object from the GitPython library
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            raise git.InvalidGitRepositoryError(f"The path provided is not a valid Git repository: {self.repo_path}")

    def build_and_commit_component(self, component_path_str: str, component_code: str, test_path_str: str, test_code: str, test_command: str) -> tuple[bool, str]:
        """
        Writes the component and its tests, runs all tests, and commits on success.
        This version now correctly handles null/placeholder file paths.
        """
        try:
            files_to_commit = []

            # --- CORRECTED: Only write files if a valid path is provided ---
            if component_path_str and component_path_str.lower() not in ["n/a", "none"]:
                component_path = self.repo_path / component_path_str
                component_path.parent.mkdir(parents=True, exist_ok=True)
                component_path.write_text(component_code, encoding='utf-8')
                files_to_commit.append(component_path_str)
                logging.info(f"Wrote source code to {component_path}")

            if test_path_str and test_path_str.lower() not in ["n/a", "none"]:
                test_path = self.repo_path / test_path_str
                test_path.parent.mkdir(parents=True, exist_ok=True)
                test_path.write_text(test_code, encoding='utf-8')
                files_to_commit.append(test_path_str)
                logging.info(f"Wrote unit tests to {test_path}")

            logging.info(f"Running test suite with command: '{test_command}'")
            tests_passed, test_output = self.run_command(test_command)

            if not tests_passed:
                logging.error("Unit tests failed for new component. Aborting commit.")
                # Return the detailed test output for better debugging
                return False, f"Unit tests failed:\n{test_output}"

            # Only commit if there are files to commit and tests passed
            if not files_to_commit:
                logging.warning("No files were written to disk for this component, but tests passed. Skipping commit.")
                return True, "Tests passed, but no files were generated to commit."

            component_name = Path(files_to_commit[0]).name
            commit_message = f"feat: Add component {component_name} and unit tests"
            commit_success, commit_result = self.commit_changes(files_to_commit, commit_message)

            if not commit_success:
                raise Exception(f"Git commit failed after tests passed: {commit_result}")

            logging.info(f"Successfully tested and committed component {component_name}.")
            return True, commit_result

        except Exception as e:
            error_message = f"An unexpected error occurred in build_and_commit_component: {e}"
            logging.error(error_message)
            return False, error_message

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