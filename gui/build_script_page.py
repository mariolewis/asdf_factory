# gui/build_script_page.py

import logging
from pathlib import Path
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_build_script_page import Ui_BuildScriptPage
from gui.worker import Worker
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

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting BuildScriptPage for a new project.")
        pass

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.autoGenerateButton.clicked.connect(self.run_auto_generate_task)
        self.ui.manualCreateButton.clicked.connect(self.on_manual_create_clicked)

    def _set_ui_busy(self, is_busy):
        """Disables or enables the page while a background task runs."""
        self.setEnabled(not is_busy)

    def _execute_task(self, task_function, on_result, *args):
        """Generic method to run a task in the background."""
        self._set_ui_busy(True)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        """Handles errors from the worker thread."""
        error_msg = f"An error occurred in a background task:\n{error_tuple[2]}"
        QMessageBox.critical(self, "Error", error_msg)
        self._set_ui_busy(False)

    def run_auto_generate_task(self):
        """Initiates the background task to generate the build script."""
        self._execute_task(self._task_auto_generate, self._handle_auto_generate_result)

    def _handle_auto_generate_result(self, script_info):
        """Handles the result from the worker thread."""
        try:
            if script_info:
                filename, content = script_info
                with self.orchestrator.db_manager as db:
                    project_details = db.get_project_by_id(self.orchestrator.project_id)
                    project_root = Path(project_details['project_root_folder'])

                (project_root / filename).write_text(content, encoding='utf-8')

                with self.orchestrator.db_manager as db:
                    db.update_project_build_automation_status(self.orchestrator.project_id, True)

                QMessageBox.information(self, "Success", f"Generated and saved '{filename}' to the project root.")
                self.orchestrator.set_phase("TEST_ENVIRONMENT_SETUP")
                self.build_script_setup_complete.emit()
            else:
                QMessageBox.critical(self, "Generation Failed", "The AI was unable to generate a build script. Please proceed manually.")
        finally:
            self._set_ui_busy(False)

    def on_manual_create_clicked(self):
        """Handles the 'I Will Create It Manually' button click."""
        try:
            with self.orchestrator.db_manager as db:
                db.update_project_build_automation_status(self.orchestrator.project_id, False)
            QMessageBox.information(self, "Acknowledged", "You will be responsible for creating and maintaining the project's build script.")
            self.orchestrator.set_phase("TEST_ENVIRONMENT_SETUP")
            self.build_script_setup_complete.emit()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save build automation status:\n{e}")

    # --- Backend Logic (to be run in worker thread) ---
    def _task_auto_generate(self, **kwargs):
        with self.orchestrator.db_manager as db:
            project_details = db.get_project_by_id(self.orchestrator.project_id)
            tech_spec_text = project_details['tech_spec_text']
            target_os = project_details['target_os']

        if not all([tech_spec_text, target_os]):
            raise Exception("Missing critical project data (Tech Spec or OS).")

        agent = BuildScriptGeneratorAgent(llm_service=self.orchestrator.llm_service)
        return agent.generate_script(tech_spec_text, target_os)