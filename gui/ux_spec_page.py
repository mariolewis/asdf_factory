# gui/ux_spec_page.py

import logging
from gui.utils import render_markdown_to_html
import warnings
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_ux_spec_page import Ui_UXSpecPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator

class UXSpecPage(QWidget):
    state_changed = Signal()
    ux_spec_complete = Signal()
    project_cancelled = Signal() # Used to signal a return to main screen after pause

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_UXSpecPage()
        self.ui.setupUi(self)
        self.threadpool = QThreadPool()

        self.ux_spec_draft = ""
        self.review_is_error_state = False
        self.last_failed_action = None # Will be 'generation' or 'refinement'
        self.retry_count = 0

        self.connect_signals()
        self.ui.pauseProjectButton.setVisible(False)

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting UXSpecPage for a new project.")
        self.ux_spec_draft = ""
        self.review_is_error_state = False
        self.last_failed_action = None
        self.retry_count = 0

        self.ui.specTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.ui.pauseProjectButton.setVisible(False)
        self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
        self.setEnabled(True)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.ui.refineButton.clicked.disconnect()
        self.ui.refineButton.clicked.connect(self.run_refinement_task)
        self.ui.approveButton.clicked.connect(self.on_approve_or_retry_clicked)
        self.ui.pauseProjectButton.clicked.connect(self.on_pause_project_clicked)
        self.ui.specTextEdit.textChanged.connect(self.on_draft_changed)

    def on_draft_changed(self):
        """Saves the current text content to the orchestrator's active draft variable."""
        draft_text = self.ui.specTextEdit.toPlainText()
        if self.orchestrator:
            self.orchestrator.set_active_spec_draft(draft_text)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        main_window = self.window()
        if not main_window:
            self.setEnabled(not is_busy)
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
        self._set_ui_busy(True, status_message)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        try:
            error_msg = f"An error occurred in a background task:\n{error_tuple[1]}"
            QMessageBox.critical(self, "Error", error_msg)
            self.ui.specTextEdit.setText(f"Failed to generate draft. Error:\n{error_tuple[1]}")
        finally:
            self._set_ui_busy(False)

    def prepare_for_display(self):
        """
        Populates the page with the UX/UI spec draft that was generated in the
        previous 'GENERATING_UX_UI_SPEC_DRAFT' phase.
        """
        logging.info("UXSpecPage: Preparing to display pre-generated draft.")
        self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)

        # The draft is now generated in the previous step and stored here by the orchestrator
        task_data = self.orchestrator.task_awaiting_approval or {}
        draft = task_data.get("ux_spec_draft", "### Error\nCould not retrieve the generated UX/UI specification draft.")

        self.ux_spec_draft = draft # Store it locally

        # This handles both success and error messages from the previous step
        is_error = draft.strip().startswith("### Error")
        if is_error:
            self.review_is_error_state = True
            self.last_failed_action = 'generation'
            self.ui.specTextEdit.setText(self.ux_spec_draft)
            self.ui.approveButton.setText("Retry Generation")
        else:
            self.review_is_error_state = False
            self.last_failed_action = None
            self.ui.specTextEdit.setHtml(render_markdown_to_html(self.ux_spec_draft))
            self.ui.approveButton.setText("Approve Specification")

    def run_generation_task(self):
        self._execute_task(self._task_generate_draft, self._handle_generation_result,
                        status_message="Generating UX/UI specification draft...")

    def _task_generate_draft(self, **kwargs):
        return self.orchestrator.generate_initial_ux_spec_draft()

    def _handle_generation_result(self, draft_text: str):
        try:
            self.ux_spec_draft = draft_text
            is_error = draft_text.strip().startswith("Error:") or draft_text.strip().startswith("### Error")

            if is_error:
                self.review_is_error_state = True
                self.last_failed_action = 'generation'
                self.retry_count += 1
                self.ui.specTextEdit.setText(self.ux_spec_draft)
                self.ui.approveButton.setText("Retry Generation")
                if self.retry_count >= 2:
                    self.ui.pauseProjectButton.setVisible(True)
            else:
                self.review_is_error_state = False
                self.last_failed_action = None
                self.retry_count = 0
                self.ui.pauseProjectButton.setVisible(False)
                self.ui.specTextEdit.setHtml(render_markdown_to_html(self.ux_spec_draft))
                self.ui.approveButton.setText("Approve Specification")

            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def run_refinement_task(self):
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback for refinement.")
            return

        current_draft = self.ux_spec_draft
        self._execute_task(self._task_refine_draft, self._handle_refinement_result, current_draft, feedback,
                           status_message="Refining UX/UI specification...")

    def _task_refine_draft(self, current_draft, feedback, **kwargs):
        return self.orchestrator.refine_ux_spec_draft(current_draft, feedback)

    def _handle_refinement_result(self, new_draft: str):
        try:
            self.ux_spec_draft = new_draft
            is_error = new_draft.strip().startswith("Error:") or new_draft.strip().startswith("### Error")

            if is_error:
                self.review_is_error_state = True
                self.last_failed_action = 'refinement'
                self.retry_count += 1
                self.ui.specTextEdit.setText(self.ux_spec_draft) # Show error in main window
                self.ui.approveButton.setText("Retry Refinement")
                if self.retry_count >= 2:
                    self.ui.pauseProjectButton.setVisible(True)
            else:
                self.review_is_error_state = False
                self.last_failed_action = None
                self.retry_count = 0
                self.ui.pauseProjectButton.setVisible(False)
                self.ui.specTextEdit.setHtml(render_markdown_to_html(self.ux_spec_draft))
                self.ui.approveButton.setText("Approve Specification")

            self.ui.feedbackTextEdit.clear()
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def on_approve_or_retry_clicked(self):
        if self.review_is_error_state:
            if self.last_failed_action == 'generation':
                self.run_generation_task()
            elif self.last_failed_action == 'refinement':
                self.run_refinement_task()
        else:
            self.on_approve_clicked()

    def on_approve_clicked(self):
        """Saves the final UX/UI spec and proceeds to the next phase."""
        final_spec_markdown = self.ux_spec_draft
        final_spec_plaintext = self.ui.specTextEdit.toPlainText().strip()

        if not final_spec_plaintext.strip():
            QMessageBox.warning(self, "Approval Failed", "The specification draft cannot be empty.")
            return

        reply = QMessageBox.question(self, "Approve Specification",
                                     "Are you sure you want to approve this UX/UI Specification?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self._execute_task(self._task_finalize_spec, self._handle_finalization_result,
                               final_spec_markdown, final_spec_plaintext,
                               status_message="Saving design to .json file for external graphical review...")

    def _task_finalize_spec(self, final_spec_markdown, final_spec_plaintext, **kwargs):
        return self.orchestrator.handle_ux_spec_completion(final_spec_markdown, final_spec_plaintext)

    def _handle_finalization_result(self, success):
        try:
            if success:
                self.ux_spec_complete.emit()
            else:
                error_msg = self.orchestrator.task_awaiting_approval.get('error', 'An unknown error occurred.')
                QMessageBox.critical(self, "Error", f"Failed to finalize the UX/UI Specification:\n{error_msg}")
        finally:
            self._set_ui_busy(False)

    def on_pause_project_clicked(self):
        """Calls the orchestrator to save state and then signals the main window to reset."""
        self.orchestrator.pause_project()
        self.project_cancelled.emit()