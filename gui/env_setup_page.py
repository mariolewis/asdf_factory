# gui/env_setup_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import Signal
from pathlib import Path
import os
import subprocess

from gui.ui_env_setup_page import Ui_EnvSetupPage
from master_orchestrator import MasterOrchestrator

class EnvSetupPage(QWidget):
    """
    The logic handler for the Environment Setup page (env_setup_page.ui).
    """
    setup_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_EnvSetupPage()
        self.ui.setupUi(self)
        self.connect_signals()

    def set_initial_path(self, path: str):
        """Receives the suggested path from the main window."""
        self.ui.projectPathLineEdit.setText(path)

    def prepare_for_new_project(self):
        """Resets the page to its initial UI state."""
        logging.info("Resetting EnvSetupPage for a new project.")
        self.ui.projectPathLineEdit.setEnabled(True)
        self.ui.confirmPathButton.setEnabled(True)
        self.ui.initGitButton.setEnabled(False)
        self.ui.proceedButton.setEnabled(False)
        self.ui.gitLabel.setText("Git repository not initialized.")
        self.ui.gitLabel.setStyleSheet("color: orange;")

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.confirmPathButton.clicked.connect(self.on_confirm_path_clicked)
        self.ui.initGitButton.clicked.connect(self.on_init_git_clicked)
        self.ui.proceedButton.clicked.connect(self.on_proceed_clicked)

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
        """Creates directories and saves the confirmed path to the database."""
        path_input = self.ui.projectPathLineEdit.text().strip()
        if not path_input:
            QMessageBox.warning(self, "Input Required", "Please enter a path for the project folder.")
            return

        try:
            project_path = Path(path_input).resolve()

            if self._check_for_brownfield_project(str(project_path)):
                QMessageBox.critical(self, "Project Exists", "The selected folder appears to contain files or an existing project. Please choose a new or empty folder.")
                return

            # Create the project directory structure now.
            docs_dir = project_path / "_docs"
            uploads_dir = docs_dir / "_uploads"
            project_path.mkdir(parents=True, exist_ok=True)
            docs_dir.mkdir(exist_ok=True)
            uploads_dir.mkdir(exist_ok=True)

            # Save the confirmed path to the database and orchestrator memory.
            self.orchestrator.db_manager.update_project_field(self.orchestrator.project_id, "project_root_folder", str(project_path))
            self.orchestrator.project_root_path = str(project_path)

            QMessageBox.information(self, "Path Confirmed", f"Project folder created and set to:\n{project_path}")

            self.ui.projectPathLineEdit.setEnabled(False)
            self.ui.confirmPathButton.setEnabled(False)
            self.ui.initGitButton.setEnabled(True)

        except Exception as e:
            logging.error(f"Error confirming project path: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while confirming the path:\n{e}")

    def on_init_git_clicked(self):
        """Handles the logic for the 'Initialize Git Repository' button."""
        project_path = self.orchestrator.project_root_path
        if not project_path:
            QMessageBox.critical(self, "Error", "Project path is not set. Please confirm the project folder first.")
            return

        try:
            subprocess.run(['git', 'init'], cwd=project_path, check=True, capture_output=True, text=True)
            gitignore_path = Path(project_path) / ".gitignore"
            gitignore_content = (
                "# Environments\n.env\n.venv\nvenv/\nenv/\n\n"
                "# IDE / Editor specific\n.vscode/\n.idea/\n"
            )
            gitignore_path.write_text(gitignore_content, encoding='utf-8')
            subprocess.run(['git', 'add', '.gitignore'], cwd=project_path, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit: Add .gitignore'], cwd=project_path, check=True)

            self.ui.gitLabel.setText("Git repository initialized successfully.")
            self.ui.gitLabel.setStyleSheet("color: green;")
            self.ui.initGitButton.setEnabled(False)
            self.ui.proceedButton.setEnabled(True)
            QMessageBox.information(self, "Success", "Successfully initialized Git repository.")

        except Exception as e:
            logging.error(f"Failed to initialize Git repository: {e}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{e}")

    def on_proceed_clicked(self):
        """Finalizes the setup and signals completion."""
        self.orchestrator.set_phase("SPEC_ELABORATION")
        self.setup_complete.emit()