# gui/build_script_page.py

import logging
from pathlib import Path
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal

from gui.ui_build_script_page import Ui_BuildScriptPage
from master_orchestrator import MasterOrchestrator
from agents.agent_build_script_generator import BuildScriptGeneratorAgent

class BuildScriptPage(QWidget):
    """
    The logic handler for the Build Script Generation page.
    """
    build_script_setup_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator

        self.ui = Ui_BuildScriptPage()
        self.ui.setupUi(self)

        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting BuildScriptPage for a new project.")
        pass

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.autoGenerateButton.clicked.connect(self.on_auto_generate_clicked)
        self.ui.manualCreateButton.clicked.connect(self.on_manual_create_clicked)

    def on_auto_generate_clicked(self):
        """Handles the 'Auto-Generate Build Script' button click."""
        try:
            with self.orchestrator.db_manager as db:
                project_details = db.get_project_by_id(self.orchestrator.project_id)
                tech_spec_text = project_details['tech_spec_text']
                target_os = project_details['target_os']
                project_root = Path(project_details['project_root_folder'])

            if not all([tech_spec_text, target_os, project_root]):
                QMessageBox.critical(self, "Error", "Missing critical project data (Tech Spec, OS, or Root Folder).")
                return

            agent = BuildScriptGeneratorAgent(llm_service=self.orchestrator.llm_service)
            script_info = agent.generate_script(tech_spec_text, target_os)

            if script_info:
                filename, content = script_info
                (project_root / filename).write_text(content, encoding='utf-8')
                with self.orchestrator.db_manager as db:
                    db.update_project_build_automation_status(self.orchestrator.project_id, True)

                QMessageBox.information(self, "Success", f"Generated and saved '{filename}' to the project root.")

                # FIX: Advance the orchestrator to the next phase
                self.orchestrator.set_phase("TEST_ENVIRONMENT_SETUP")
                self.build_script_setup_complete.emit()
            else:
                QMessageBox.critical(self, "Generation Failed", "The AI was unable to generate a build script. Please proceed manually.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during script generation:\n{e}")

    def on_manual_create_clicked(self):
        """Handles the 'I Will Create It Manually' button click."""
        try:
            with self.orchestrator.db_manager as db:
                db.update_project_build_automation_status(self.orchestrator.project_id, False)

            QMessageBox.information(self, "Acknowledged", "You will be responsible for creating and maintaining the project's build script.")

            # FIX: Advance the orchestrator to the next phase
            self.orchestrator.set_phase("TEST_ENVIRONMENT_SETUP")
            self.build_script_setup_complete.emit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save build automation status:\n{e}")