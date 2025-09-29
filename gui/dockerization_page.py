# gui/dockerization_page.py
import logging
from pathlib import Path

from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_dockerization_page import Ui_DockerizationPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_dockerization import DockerizationAgent


class DockerizationPage(QWidget):
    """
    The logic handler for the Dockerization setup page.
    """
    dockerization_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_DockerizationPage()
        self.ui.setupUi(self)
        self.threadpool = QThreadPool()
        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.autoGenerateButton.clicked.connect(self.run_auto_generate_task)
        self.ui.skipButton.clicked.connect(self.on_skip_clicked)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the main window and updates the status bar."""
        main_window = self.window()
        if not main_window: return
        main_window.setEnabled(not is_busy)
        if hasattr(main_window, 'statusBar'):
            if is_busy:
                main_window.statusBar().showMessage(message)
            else:
                main_window.statusBar().clearMessage()

    def _execute_task(self, task_function, on_result, *args, status_message="Processing..."):
        """Generic method to run a task in the background."""
        self._set_ui_busy(True, status_message)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        """Handles errors from the worker thread."""
        try:
            error_msg = f"An error occurred in a background task:\n{error_tuple[1]}"
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            self._set_ui_busy(False)

    def run_auto_generate_task(self):
        """Initiates the background task to generate the Dockerfile."""
        self._execute_task(self._task_auto_generate, self._handle_auto_generate_result,
                           status_message="Generating Dockerfile...")

    def _task_auto_generate(self, **kwargs):
        """Background worker task that calls the DockerizationAgent."""
        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        tech_spec_text = project_details['tech_spec_text']

        if not tech_spec_text:
            raise Exception("Cannot generate Dockerfile: Technical Specification not found.")

        agent = DockerizationAgent(llm_service=self.orchestrator.llm_service)
        dockerfile_content = agent.generate_dockerfile(tech_spec_text)

        if dockerfile_content:
            project_root = Path(project_details['project_root_folder'])
            (project_root / "Dockerfile").write_text(dockerfile_content, encoding='utf-8')
            return True
        return False

    def _handle_auto_generate_result(self, success: bool):
        """Handles the result from the worker thread."""
        try:
            if success:
                QMessageBox.information(self, "Success", "Dockerfile generated and saved to the project root.")
                self.orchestrator.finalize_dockerization_setup()
                self.dockerization_complete.emit()
            else:
                QMessageBox.critical(self, "Generation Failed", "The AI was unable to generate a Dockerfile. You can create one manually later.")
                self.orchestrator.finalize_dockerization_setup()
                self.dockerization_complete.emit()
        finally:
            self._set_ui_busy(False)

    def on_skip_clicked(self):
        """Handles the skip button click."""
        QMessageBox.information(self, "Acknowledged", "Dockerization will be skipped for this project.")
        self.orchestrator.finalize_dockerization_setup()
        self.dockerization_complete.emit()