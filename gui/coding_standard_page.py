# gui/coding_standard_page.py

import re
from datetime import datetime
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
        error_msg = f"An error occurred in a background task:\n{error_tuple[1]}"
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
        self._execute_task(self._task_refine_standard, self._handle_refinement_result, current_draft, feedback)

    def _handle_refinement_result(self, new_draft):
        """Handles the result from the refinement worker thread."""
        try:
            self.coding_standard_draft = new_draft
            self.ui.standardTextEdit.setText(self.coding_standard_draft)
            self.ui.feedbackTextEdit.clear()
            QMessageBox.information(self, "Success", "The coding standard has been refined based on your feedback.")
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def _task_refine_standard(self, current_draft, feedback, **kwargs):
        """The actual function that runs in the background to refine the standard."""
        agent = CodingStandardAgent_AppTarget(llm_service=self.orchestrator.llm_service)

        # Get the refined content from the agent
        refined_draft = agent.refine_standard(current_draft, feedback)

        # Reliably update the date in the header using Python
        current_date = datetime.now().strftime('%Y-%m-%d')
        # This robust regex finds the "Date: " line and replaces the rest of the line
        date_updated_draft = re.sub(
            r"(Date: ).*",
            rf"\g{current_date}",
            refined_draft
        )

        return date_updated_draft

    def on_approve_clicked(self):
        """Saves the final coding standard and proceeds to the next phase."""
        final_standard = self.ui.standardTextEdit.toPlainText()
        if not final_standard.strip():
            QMessageBox.warning(self, "Approval Failed", "The coding standard cannot be empty.")
            return

        self.orchestrator.finalize_and_save_coding_standard(final_standard)
        QMessageBox.information(self, "Success", "Coding Standard approved and saved.")
        self.orchestrator.is_project_dirty = True
        self.coding_standard_complete.emit()

    def _task_generate_standard(self, **kwargs):
        """The actual function that runs in the background."""
        # --- Template Loading Logic ---
        template_content = None
        try:
            # Note: The user can create specific templates like "Python Coding Standard".
            # For now, we look for a generic default. This can be enhanced later.
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
        tech_spec_text = project_details['tech_spec_text']

        if not tech_spec_text:
            raise Exception("Could not retrieve the Technical Specification. Cannot generate a coding standard.")

        agent = CodingStandardAgent_AppTarget(llm_service=self.orchestrator.llm_service)

        draft_content = agent.generate_standard(tech_spec_text, template_content=template_content)

        full_draft = self.orchestrator.prepend_standard_header(draft_content, "Coding Standard")
        return full_draft