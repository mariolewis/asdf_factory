# gui/coding_standard_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_coding_standard_page import Ui_CodingStandardPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_coding_standard_app_target import CodingStandardAgent_AppTarget

class CodingStandardPage(QWidget):
    """
    The logic handler for the Coding Standard Generation page.
    """
    coding_standard_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.coding_standard_draft = ""

        self.ui = Ui_CodingStandardPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page to its initial state."""
        logging.info("Resetting CodingStandardPage for a new project.")
        self.coding_standard_draft = ""
        self.ui.standardTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.generatePage)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.generateButton.clicked.connect(self.run_generation_task)
        self.ui.approveButton.clicked.connect(self.on_approve_clicked)

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

    def run_generation_task(self):
        """Initiates the background task to generate the coding standard."""
        self._execute_task(self._task_generate_standard, self._handle_generation_result)

    def _handle_generation_result(self, standard_draft):
        """Handles the result from the worker thread."""
        try:
            self.coding_standard_draft = standard_draft
            self.ui.standardTextEdit.setText(self.coding_standard_draft)
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
        finally:
            self._set_ui_busy(False)

    def on_approve_clicked(self):
        """Saves the final coding standard and proceeds to the next phase."""
        final_standard = self.ui.standardTextEdit.toPlainText()
        if not final_standard.strip():
            QMessageBox.warning(self, "Approval Failed", "The coding standard cannot be empty.")
            return

        self.orchestrator.finalize_and_save_coding_standard(final_standard)
        QMessageBox.information(self, "Success", "Coding Standard approved and saved.")
        self.coding_standard_complete.emit()

    # --- Backend Logic (to be run in worker thread) ---

    def _task_generate_standard(self, **kwargs):
        """The actual function that runs in the background."""
        with self.orchestrator.db_manager as db:
            project_details = db.get_project_by_id(self.orchestrator.project_id)
            tech_spec_text = project_details['tech_spec_text']

        if not tech_spec_text:
            raise Exception("Could not retrieve the Technical Specification. Cannot generate a coding standard.")

        agent = CodingStandardAgent_AppTarget(llm_service=self.orchestrator.llm_service)
        return agent.generate_standard(tech_spec_text)