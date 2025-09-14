# gui/ux_spec_page.py

import logging
import markdown
import warnings
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_ux_spec_page import Ui_UXSpecPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator

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

        # Block signals during widget clearing ---
        self.ui.specTextEdit.blockSignals(True)
        self.ui.feedbackTextEdit.blockSignals(True)

        self.ui.specTextEdit.clear()
        self.ui.feedbackTextEdit.clear()

        self.ui.specTextEdit.blockSignals(False)
        self.ui.feedbackTextEdit.blockSignals(False)

        self.setEnabled(True)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.ui.refineButton.clicked.disconnect()
        self.ui.refineButton.clicked.connect(self.run_refinement_task)
        self.ui.approveButton.clicked.connect(self.on_approve_clicked)
        self.ui.specTextEdit.textChanged.connect(self.on_draft_changed)

    def on_draft_changed(self):
        """Saves the current text content to the orchestrator's active draft variable."""
        draft_text = self.ui.specTextEdit.toPlainText()
        if self.orchestrator:
            self.orchestrator.set_active_spec_draft(draft_text)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the main window and updates the status bar."""
        main_window = self.window()
        if not main_window:
            self.setEnabled(not is_busy) # Fallback
            return

        main_window.setEnabled(not is_busy)
        if hasattr(main_window, 'statusBar'):
            if is_busy:
                self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
                main_window.statusBar().showMessage(message)
            else:
                main_window.statusBar().clearMessage()
                self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)

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
            self.ui.specTextEdit.setText(f"Failed to generate draft. Error:\n{error_tuple[1]}")
        finally:
            self._set_ui_busy(False)

    def prepare_for_display(self):
        """
        Triggers the UX_Spec_Agent to generate the initial draft, unless a
        resumable draft exists.
        """
        # Prioritize Resumed Draft ---
        if self.orchestrator.active_spec_draft is not None:
            logging.info("Resuming UX spec with a saved draft.")
            self.ux_spec_draft = self.orchestrator.active_spec_draft
            self.orchestrator.set_active_spec_draft(None) # Clear the draft

            self.ui.specTextEdit.setHtml(markdown.markdown(self.ux_spec_draft, extensions=['fenced_code']))
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
            return
        # --- END ---

        logging.info("UXSpecPage: Preparing for display, starting draft generation.")
        self._execute_task(self._task_generate_draft, self._handle_generation_result,
                        status_message="Generating UX/UI specification draft...")

    def _task_generate_draft(self, **kwargs):
        """The actual function that runs in the background."""
        return self.orchestrator.generate_initial_ux_spec_draft()

    def _handle_generation_result(self, draft_text: str):
        """Handles the result from the worker thread."""
        try:
            self.ux_spec_draft = draft_text
            self.ui.specTextEdit.setHtml(markdown.markdown(self.ux_spec_draft, extensions=['fenced_code']))
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
        self._execute_task(self._task_refine_draft, self._handle_refinement_result, current_draft, feedback,
                           status_message="Refining UX/UI specification...")

    def _task_refine_draft(self, current_draft, feedback, **kwargs):
        """Background task to call the orchestrator for refinement."""
        return self.orchestrator.refine_ux_spec_draft(current_draft, feedback)

    def _handle_refinement_result(self, new_draft: str):
        """Handles the result from the refinement worker thread."""
        try:
            self.ux_spec_draft = new_draft
            self.ui.specTextEdit.setHtml(markdown.markdown(self.ux_spec_draft, extensions=['fenced_code']))
            self.ui.feedbackTextEdit.clear()
            QMessageBox.information(self, "Success", "Success: The UX/UI Specification has been refined based on your feedback.")
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
            self._execute_task(self._task_finalize_spec, self._handle_finalization_result, final_spec,
                               status_message="Saving design to .json file for external graphical review...")

    def _task_finalize_spec(self, final_spec, **kwargs):
        """Background task for the finalization step."""
        return self.orchestrator.handle_ux_spec_completion(final_spec)

    def _handle_finalization_result(self, success):
        """Handles the result of the finalization task."""
        try:
            if success:
                QMessageBox.information(self, "Success", "Success: UX/UI Specification approved and saved. Proceeding to Application Specification.")
                logging.debug("on_approve_clicked: Emitting ux_spec_complete signal.")
                self.ux_spec_complete.emit()
            else:
                error_msg = self.orchestrator.task_awaiting_approval.get('error', 'An unknown error occurred.')
                QMessageBox.critical(self, "Error", f"Failed to finalize the UX/UI Specification:\n{error_msg}")
        finally:
            self._set_ui_busy(False)