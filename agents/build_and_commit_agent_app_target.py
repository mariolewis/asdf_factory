"""
This module contains the BuildAndCommitAgentAppTarget class.
"""
import subprocess
import git
from pathlib import Path

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

    def build_component(self, build_command: str) -> tuple[bool, str]:
        """
        Runs the specified build command in the root of the project repository.

        Args:
            build_command (str): The build command to execute (e.g., "mvn clean install").

        Returns:
            tuple[bool, str]: A tuple containing:
                              - A boolean indicating build success (True) or failure (False).
                              - A string containing the combined stdout and stderr from the build process.
        """
        try:
            # Using subprocess.run to execute the external build command.
            # We capture the output to return it for logging and debugging.
            # shell=True is used for simplicity in executing complex commands.
            result = subprocess.run(
                build_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.repo_path,  # Execute the command in the project's root directory
                check=False  # We manually check the return code instead of auto-raising an exception
            )

            combined_output = f"--- STDOUT ---\n{result.stdout}\n--- STDERR ---\n{result.stderr}"

            if result.returncode == 0:
                # A return code of 0 indicates success.
                return True, combined_output
            else:
                # Any other return code indicates a build failure.
                return False, combined_output

        except Exception as e:
            # Handle unexpected errors during subprocess execution.
            error_message = f"An unexpected error occurred while running the build command: {e}"
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