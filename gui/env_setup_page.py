# gui/env_setup_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import Signal
from pathlib import Path
import os
import subprocess
import sys

from gui.ui_env_setup_page import Ui_EnvSetupPage
from gui.utils import validate_security_input
from master_orchestrator import MasterOrchestrator

class EnvSetupPage(QWidget):
    """
    The logic handler for the Environment Setup page (env_setup_page.ui).
    Now handles both greenfield and brownfield project setup.
    """
    setup_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_EnvSetupPage()
        self.ui.setupUi(self)
        self.is_brownfield = False

        self.connect_signals()
        self.prepare_for_new_project() # Set initial state

    def prepare_for_greenfield(self, path: str):
        """Prepares the UI for a new (greenfield) project."""
        self.is_brownfield = False
        self.ui.projectPathLineEdit.setText(path)
        self.ui.projectPathLineEdit.setReadOnly(False)
        self.ui.confirmPathButton.setVisible(True)
        self.ui.vcsChoiceWidget.setVisible(False)
        self.ui.vcsLine.setVisible(False)
        self.ui.headerLabel.setText("New Project Setup")
        self.ui.instructionLabel.setText("Define the root folder for the new target application.")

    def prepare_for_brownfield(self, path: str):
        """Prepares the UI for an existing (brownfield) project."""
        self.is_brownfield = True
        project_path = Path(path)
        self.ui.projectPathLineEdit.setText(str(project_path))
        self.ui.projectPathLineEdit.setReadOnly(True)
        self.ui.confirmPathButton.setVisible(False)
        self.ui.vcsChoiceWidget.setVisible(True)
        self.ui.vcsLine.setVisible(True)
        self.ui.headerLabel.setText("Onboard Existing Project")
        self.ui.instructionLabel.setText(f"The following existing project folder will be onboarded: {path}")

        # Update VCS button text based on whether a .git folder exists
        if (project_path / ".git").is_dir():
            self.ui.initGitButton.setText("Use Existing Git Repository & Proceed")
        else:
            self.ui.initGitButton.setText("Initialize New Git Repository & Proceed")

        self.ui.localWorkspaceButton.setText("Use as Local Workspace & Proceed")

    def prepare_for_new_project(self):
        """Resets the page to its initial UI state."""
        self.is_brownfield = False
        self.ui.projectPathLineEdit.clear()
        self.ui.projectPathLineEdit.setReadOnly(False)
        self.ui.confirmPathButton.setVisible(True)
        self.ui.confirmPathButton.setEnabled(True)
        self.ui.vcsChoiceWidget.setVisible(False)
        self.ui.vcsLine.setVisible(False)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.confirmPathButton.clicked.connect(self.on_confirm_path_clicked)
        self.ui.initGitButton.clicked.connect(self.on_init_git_and_proceed_clicked)
        self.ui.localWorkspaceButton.clicked.connect(self.on_local_workspace_and_proceed_clicked)

    def _check_for_brownfield_project(self, directory_path: str) -> bool:
        """Scans a directory for signs of an existing project."""
        path = Path(directory_path)
        if not path.exists():
            return False
        if (path / '.git').exists():
            return True
        if any(path.iterdir()):
            logging.warning(f"Brownfield check: Found existing files/folders in {directory_path}")
            return True
        return False

    def on_confirm_path_clicked(self):
        """Creates directories for a NEW project and shows VCS choice."""
        path_input = self.ui.projectPathLineEdit.text().strip()
        if not path_input:
            QMessageBox.warning(self, "Input Required", "Please enter a path for the project folder.")
            return
        # Security Validation for File System Paths
        if not validate_security_input(self, path_input, "PATH"):
            return

        try:
            project_path = Path(path_input).resolve()

            if self._check_for_brownfield_project(str(project_path)):
                QMessageBox.critical(self, "Project Exists", "The selected folder appears to contain files or an existing project. Please choose a new or empty folder for a greenfield project.")
                return

            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "docs" / "uploads").mkdir(parents=True, exist_ok=True)

            self.ui.projectPathLineEdit.setEnabled(False)
            self.ui.confirmPathButton.setEnabled(False)
            self.ui.vcsChoiceWidget.setVisible(True)
            self.ui.vcsLine.setVisible(True)

        except Exception as e:
            logging.error(f"Error confirming project path: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while confirming the path:\n{e}")

    def on_init_git_and_proceed_clicked(self):
        """Handles Git initialization/confirmation and proceeds to the next phase."""
        project_path_str = self.ui.projectPathLineEdit.text().strip()
        project_path = Path(project_path_str)

        try:
            # Finalize the project record in the database
            self.orchestrator.finalize_project_creation(
                project_id=self.orchestrator.project_id,
                project_name=self.orchestrator.project_name,
                project_root=project_path_str
            )

            # If it's not already a git repo, initialize it.
            repo_message = ""
            if not (project_path / ".git").is_dir():
                # Prepare suppression flags for Windows
                run_kwargs = {}
                if sys.platform == "win32":
                    run_kwargs['creationflags'] = 0x08000000

                subprocess.run(['git', 'init'], cwd=project_path, check=True, capture_output=True, text=True, **run_kwargs)
                gitignore_path = project_path / ".gitignore"
                gitignore_content = (
                    "# Environments\n.env\n.venv\nvenv/\nenv/\n\n"
                    "# IDE / Editor specific\n.vscode/\n.idea/\n"
                )
                gitignore_path.write_text(gitignore_content, encoding='utf-8')
                subprocess.run(['git', 'add', '.gitignore'], cwd=project_path, check=True, **run_kwargs)
                subprocess.run(['git', 'commit', '-m', 'Initial commit: Add .gitignore'], cwd=project_path, check=True, **run_kwargs)
                repo_message = "Successfully initialized new Git repository."
            else:
                repo_message = "Confirmed existing Git repository."

            self.orchestrator.db_manager.update_project_field(self.orchestrator.project_id, "version_control_enabled", 1)

            # --- CONDITIONAL LOGIC FOR GREENFIELD VS BROWNFIELD ---
            if self.is_brownfield:
                # Proactively create the docs folder to solve the tree-view bug
                (project_path / "docs").mkdir(exist_ok=True)

                # Show the confirmation dialog for analysis
                reply = QMessageBox.question(self, "Confirm Analysis",
                                             f"{repo_message}\n\nThe system will now proceed with a deep analysis of the codebase. This may take some time.\n\nDo you wish to proceed?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.Yes)

                if reply == QMessageBox.StandardButton.Yes:
                    self.orchestrator.set_phase("ANALYZING_CODEBASE")
                    self.setup_complete.emit()
                else:
                    # User cancelled. Reset the project state and UI.
                    self.orchestrator.reset()
                    self.prepare_for_new_project()
                    self.setup_complete.emit()
            else:  # Greenfield workflow
                QMessageBox.information(self, "Success", repo_message)
                self.orchestrator.set_phase("SPEC_ELABORATION")
                self.setup_complete.emit()

        except Exception as e:
            logging.error(f"Failed during Git setup: {e}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred during Git setup:\n{e}")
            # Also reset on error
            self.orchestrator.reset()
            self.prepare_for_new_project()
            self.setup_complete.emit()

    def on_local_workspace_and_proceed_clicked(self):
        """Handles proceeding without Git and moves to the next phase."""
        project_path_str = self.ui.projectPathLineEdit.text().strip()
        project_path = Path(project_path_str)

        try:
            # Finalize the project record in the database
            self.orchestrator.finalize_project_creation(
                project_id=self.orchestrator.project_id,
                project_name=self.orchestrator.project_name,
                project_root=project_path_str
            )

            self.orchestrator.db_manager.update_project_field(self.orchestrator.project_id, "version_control_enabled", 0)

            # --- CONDITIONAL LOGIC FOR GREENFIELD VS BROWNFIELD ---
            if self.is_brownfield:
                # Proactively create the docs folder
                (project_path / "docs").mkdir(exist_ok=True)

                # Show the confirmation dialog for analysis
                reply = QMessageBox.question(self, "Confirm Analysis",
                                             "Local workspace confirmed.\n\nThe system will now proceed with a deep analysis of the codebase. This may take some time.\n\nDo you wish to proceed?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.Yes)

                if reply == QMessageBox.StandardButton.Yes:
                    self.orchestrator.set_phase("ANALYZING_CODEBASE")
                    self.setup_complete.emit()
                else:
                    # User cancelled. Reset the project state and UI.
                    self.orchestrator.reset()
                    self.prepare_for_new_project()
                    self.setup_complete.emit()
            else:  # Greenfield workflow
                QMessageBox.information(self, "Local Workspace", "Proceeding without Git. You can initialize a repository manually later if needed.")
                self.orchestrator.set_phase("SPEC_ELABORATION")
                self.setup_complete.emit()

        except Exception as e:
            logging.error(f"Failed during local workspace setup: {e}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred during setup:\n{e}")
            # Also reset on error
            self.orchestrator.reset()
            self.prepare_for_new_project()
            self.setup_complete.emit()