# agents/agent_rollback_app_target.py

"""
This module contains the RollbackAgent class.

This agent is responsible for handling Git rollback operations for a target
application's repository, as directed by the MasterOrchestrator.
(ASDF PRD v0.6, Section 3.6)
"""

import git
from pathlib import Path
import logging

class RollbackAgent:
    """
    Agent responsible for rolling back a Git repository to its last clean state.
    """

    def discard_local_changes(self, project_repo_path: str | Path) -> tuple[bool, str]:
        """
        Performs a 'git reset --hard HEAD' and 'git clean -fdx' to revert
        all uncommitted changes, including new untracked files.

        Args:
            project_repo_path (str | Path): The absolute local path to the target
                                             application's Git repository.

        Returns:
            A tuple containing a boolean for success/failure and a status message.
        """
        logging.warning(f"Executing atomic rollback for repository at: {project_repo_path}")
        try:
            repo_path = Path(project_repo_path)
            if not repo_path.is_dir() or not (repo_path / '.git').is_dir():
                raise git.InvalidGitRepositoryError(f"The path provided is not a valid Git repository: {repo_path}")

            repo = git.Repo(repo_path)

            # Revert any modified tracked files to their last committed state.
            if repo.heads:
                repo.git.reset('--hard', 'HEAD')
                logging.info("Successfully reset repository to HEAD.")
            else:
                logging.warning("Repository has no commits; skipping reset.")

            # Remove all untracked files and directories.
            repo.git.clean('-fdx')
            logging.info("Successfully cleaned untracked files and directories.")

            return True, "Repository successfully reverted to the last clean state."

        except git.InvalidGitRepositoryError as e:
            logging.error(f"Rollback failed: Invalid Git repository. {e}")
            return False, str(e)
        except Exception as e:
            logging.error(f"An unexpected error occurred during atomic rollback: {e}")
            return False, f"An unexpected error occurred during rollback: {e}"