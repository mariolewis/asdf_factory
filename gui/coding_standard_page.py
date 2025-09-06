# gui/coding_standard_page.py

import re
from datetime import datetime
from pathlib import Path
import logging
import markdown
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
    state_changed = Signal()
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
        self.setEnabled(True)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.generateButton.clicked.connect(self.run_generation_task)
        self.ui.approveButton.clicked.connect(self.on_approve_clicked)
        self.ui.refineButton.clicked.connect(self.run_refinement_task)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the main window and updates the status bar."""
        main_window = self.window() # Get the top-level window
        if not main_window:
            self.setEnabled(not is_busy) # Fallback if parent isn't found
            return

        main_window.setEnabled(not is_busy)
        if hasattr(main_window, 'statusBar'):
            if is_busy:
                self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
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

    def run_generation_task(self):
        """Initiates the background task to generate the coding standard."""
        self._execute_task(self._task_generate_standard, self._handle_generation_result,
                           status_message="Generating coding standard draft...")

    def _handle_generation_result(self, standard_draft):
        """Handles the result from the worker thread."""
        try:
            self.coding_standard_draft = standard_draft
            self.ui.standardTextEdit.setHtml(markdown.markdown(self.coding_standard_draft)) # Corrected line
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def run_refinement_task(self):
        """Initiates the background task to refine the coding standard."""
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback for refinement.")
            return

        current_draft = self.ui.standardTextEdit.toPlainText()
        self._execute_task(self._task_refine_standard, self._handle_refinement_result, current_draft, feedback,
                           status_message="Refining coding standard...")

    def _handle_refinement_result(self, new_draft):
        """Handles the result from the refinement worker thread."""
        try:
            self.coding_standard_draft = new_draft
            self.ui.standardTextEdit.setHtml(markdown.markdown(self.coding_standard_draft)) # Corrected line
            self.ui.feedbackTextEdit.clear()
            QMessageBox.information(self, "Success", "Success: The coding standard has been refined based on your feedback.")
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def _task_refine_standard(self, current_draft, feedback, **kwargs):
        """The actual function that runs in the background to refine the standard."""
        agent = CodingStandardAgent_AppTarget(llm_service=self.orchestrator.llm_service)

        # Get the refined content from the agent
        refined_draft = agent.refine_standard(current_draft, feedback)

        # Reliably update the date in the header using Python
        current_date = datetime.now().strftime('%x')
        # This corrected regex finds the "Date: " line and replaces the rest of the line
        date_updated_draft = re.sub(
            r"(Date: ).*",
            r"\g<1>" + current_date,
            refined_draft
        )

        return date_updated_draft

    def on_approve_clicked(self):
        """
        Confirms approval with the user, then triggers the background task
        for finalization and backlog generation.
        """
        self.final_standard_for_processing = self.ui.standardTextEdit.toPlainText()
        if not self.final_standard_for_processing.strip():
            QMessageBox.warning(self, "Approval Failed", "The coding standard cannot be empty.")
            return

        reply = QMessageBox.question(self, "Approve Coding Standard",
                                    "The Coding Standard has been approved and will be saved.\n\nThe system will now proceed to generate the initial project backlog based on all specifications. This may take a moment.",
                                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

        if reply == QMessageBox.Ok:
            self.run_approval_and_generation_task()

    def run_approval_and_generation_task(self):
        """Initiates the background worker for the finalization process."""
        self.ui.headerLabel.setText("Backlog Generation")
        self._execute_task(self._task_approve_and_generate_backlog,
                        self._handle_approval_result,
                        self.final_standard_for_processing,
                        status_message="Generating backlog from specification...")

    def _task_approve_and_generate_backlog(self, final_standard, **kwargs):
        """
        Background worker task that calls the orchestrator to save the coding
        standard and generate the backlog.
        """
        self.orchestrator.finalize_and_save_coding_standard(final_standard)
        # The orchestrator's phase is now BACKLOG_RATIFICATION
        return True

    def _handle_approval_result(self, success):
        """Handles the result of the background finalization task."""
        try:
            if success:
                self.orchestrator.is_project_dirty = True
                self.coding_standard_complete.emit()
            else:
                QMessageBox.critical(self, "Error", "The finalization and backlog generation process failed.")
        finally:
            self._set_ui_busy(False)
            # Switch back to the review page in case the user needs to see it again
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)

    def _task_generate_standard(self, **kwargs):
        """The actual function that runs in the background."""
        # --- Template Loading Logic ---
        template_content = None
        try:
            template_record = self.orchestrator.db_manager.get_template_by_name("Default Coding Standard")
            if template_record:
                template_path = Path(template_record['file_path'])
                if template_path.exists():
                    template_content = template_path.read_text(encoding='utf-8')
                    logging.info("Found and loaded 'Default Coding Standard' template.")
        except Exception as e:
            logging.warning(f"Could not load default coding standard template: {e}")
        # --- End Template Loading ---

        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)

        # --- ADDED SAFETY CHECK ---
        if not project_details:
            raise Exception("Could not retrieve project details. A project must be active to generate a standard.")
        # --- END OF CHECK ---

        tech_spec_text = project_details['tech_spec_text']

        if not tech_spec_text:
            raise Exception("Could not retrieve the Technical Specification. Cannot generate a coding standard.")

        agent = CodingStandardAgent_AppTarget(llm_service=self.orchestrator.llm_service)

        draft_content = agent.generate_standard(tech_spec_text, template_content=template_content)

        full_draft = self.orchestrator.prepend_standard_header(draft_content, "Coding Standard")
        return full_draft