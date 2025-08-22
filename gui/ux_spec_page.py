# gui/ux_spec_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_ux_spec_page import Ui_UXSpecPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_ux_spec import UX_Spec_Agent

class UXSpecPage(QWidget):
    """
    The logic handler for the UX/UI Specification page.
    """
    state_changed = Signal()
    ux_spec_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_UXSpecPage()
        self.ui.setupUi(self)
        self.threadpool = QThreadPool()

        self.ux_spec_draft = ""

        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting UXSpecPage for a new project.")
        self.ux_spec_draft = ""
        self.ui.specTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.setEnabled(True)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.refineButton.clicked.connect(self.run_refinement_task)
        self.ui.approveButton.clicked.connect(self.on_approve_clicked)

    def _set_ui_busy(self, is_busy):
        """Disables or enables the page while a background task runs."""
        self.setEnabled(not is_busy)
        if is_busy:
            self.ui.specTextEdit.setText("Generating UX/UI Specification Draft...")

    def _execute_task(self, task_function, on_result, *args):
        """Generic method to run a task in the background."""
        self._set_ui_busy(True)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        """Handles errors from the worker thread."""
        error_msg = f"An error occurred in a background task:\n{error_tuple[1]}"
        QMessageBox.critical(self, "Error", error_msg)
        self.ui.specTextEdit.setText(f"Failed to generate draft. Error:\n{error_tuple[1]}")
        self._set_ui_busy(False)

    def prepare_for_display(self):
        """
        Triggers the UX_Spec_Agent to generate the initial draft when the page is shown.
        """
        logging.info("UXSpecPage: Preparing for display, starting draft generation.")
        self._execute_task(self._task_generate_draft, self._handle_generation_result)

    def _task_generate_draft(self, **kwargs):
        """The actual function that runs in the background."""
        return self.orchestrator.generate_initial_ux_spec_draft()

    def _handle_generation_result(self, draft_text: str):
        """Handles the result from the worker thread."""
        try:
            self.ux_spec_draft = draft_text
            self.ui.specTextEdit.setText(self.ux_spec_draft)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def run_refinement_task(self):
        """Initiates the background task to refine the UX spec."""
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback for refinement.")
            return

        current_draft = self.ui.specTextEdit.toPlainText()
        self._execute_task(self._task_refine_draft, self._handle_refinement_result, current_draft, feedback)

    def _task_refine_draft(self, current_draft, feedback, **kwargs):
        """Background task to call the orchestrator for refinement."""
        return self.orchestrator.refine_ux_spec_draft(current_draft, feedback)

    def _handle_refinement_result(self, new_draft: str):
        """Handles the result from the refinement worker thread."""
        try:
            self.ux_spec_draft = new_draft
            self.ui.specTextEdit.setText(self.ux_spec_draft)
            self.ui.feedbackTextEdit.clear()
            QMessageBox.information(self, "Success", "The UX/UI Specification has been refined based on your feedback.")
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def on_approve_clicked(self):
        """Saves the final UX/UI spec and proceeds to the next phase."""
        final_spec = self.ui.specTextEdit.toPlainText().strip()
        if not final_spec:
            QMessageBox.warning(self, "Approval Failed", "The specification draft cannot be empty.")
            return

        reply = QMessageBox.question(self, "Approve Specification",
                                     "Are you sure you want to approve this UX/UI Specification? This will lock the document and proceed to the next phase.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self._set_ui_busy(True)
            # The orchestrator method will run in the main thread for this final step
            success = self.orchestrator.handle_ux_spec_completion(final_spec)
            self._set_ui_busy(False)

            if success:
                QMessageBox.information(self, "Success", "UX/UI Specification approved and saved. Proceeding to Application Specification.")
                logging.debug("on_approve_clicked: Emitting ux_spec_complete signal.")
                self.ux_spec_complete.emit()
            else:
                error_msg = self.orchestrator.active_ux_spec.get('error', 'An unknown error occurred.')
                QMessageBox.critical(self, "Error", f"Failed to finalize the UX/UI Specification:\n{error_msg}")