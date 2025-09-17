# gui/tech_spec_page.py

import re
from datetime import datetime
from pathlib import Path
import logging
import markdown
import warnings
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_tech_spec_page import Ui_TechSpecPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_tech_stack_proposal import TechStackProposalAgent

class TechSpecPage(QWidget):
    """
    The logic handler for the Technical Specification page.
    """
    state_changed = Signal()
    tech_spec_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.tech_spec_draft = ""

        self.ui = Ui_TechSpecPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_display(self):
        """Prepares the page, loading a resumed draft if one exists."""
        if self.orchestrator.active_spec_draft is not None:
            logging.info("Resuming tech spec with a saved draft.")
            self.tech_spec_draft = self.orchestrator.active_spec_draft
            self.orchestrator.set_active_spec_draft(None) # Clear the draft

            self.ui.techSpecTextEdit.setHtml(markdown.markdown(self.tech_spec_draft, extensions=['fenced_code', 'extra']))
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
        else:
            # Default behavior if not resuming
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting TechSpecPage for a new project.")
        self.tech_spec_draft = ""

        self.ui.techSpecTextEdit.blockSignals(True)
        self.ui.feedbackTextEdit.blockSignals(True)
        self.ui.pmGuidelinesTextEdit.blockSignals(True)

        self.ui.techSpecTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.ui.pmGuidelinesTextEdit.clear()

        self.ui.techSpecTextEdit.blockSignals(False)
        self.ui.feedbackTextEdit.blockSignals(False)
        self.ui.pmGuidelinesTextEdit.blockSignals(False)

        self.ui.osComboBox.setCurrentIndex(0)
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
        self.setEnabled(True)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.proposeStackButton.clicked.connect(self.run_propose_stack_task)
        self.ui.pmDefineButton.clicked.connect(self.on_pm_define_clicked)
        self.ui.generateFromGuidelinesButton.clicked.connect(self.run_generate_from_guidelines_task)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.ui.refineButton.clicked.disconnect()
        self.ui.refineButton.clicked.connect(self.run_refine_task)
        self.ui.approveButton.clicked.connect(self.on_approve_clicked)
        self.ui.techSpecTextEdit.textChanged.connect(self.on_draft_changed)

    def on_draft_changed(self):
        """Saves the current text content to the orchestrator's active draft variable."""
        draft_text = self.ui.techSpecTextEdit.toPlainText()
        if self.orchestrator:
            self.orchestrator.set_active_spec_draft(draft_text)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the page and updates the main status bar."""
        self.setEnabled(not is_busy)
        main_window = self.window()
        if main_window and hasattr(main_window, 'statusBar'):
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
        finally:
            self._set_ui_busy(False)

    def run_propose_stack_task(self):
        target_os = self.ui.osComboBox.currentText()
        self._execute_task(self._task_propose_stack, self._handle_generation_result, target_os,
                           status_message="Generating tech stack proposal...")

    def on_pm_define_clicked(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.pmDefinePage)

    def run_generate_from_guidelines_task(self):
        guidelines = self.ui.pmGuidelinesTextEdit.toPlainText().strip()
        if not guidelines:
            QMessageBox.warning(self, "Input Required", "Please provide your technology guidelines.")
            return
        target_os = self.ui.osComboBox.currentText()
        self._execute_task(self._task_generate_from_guidelines, self._handle_generation_result, guidelines, target_os,
                           status_message="Generating specification from guidelines...")

    def run_refine_task(self):
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback to refine the draft.")
            return
        current_draft = self.ui.techSpecTextEdit.toPlainText()
        target_os = self.ui.osComboBox.currentText()
        # This is the corrected line that now includes the status_message
        self._execute_task(self._task_refine_spec, self._handle_refinement_result, current_draft, feedback, target_os,
                        status_message="Refining technical specification...")

    def _handle_generation_result(self, tech_spec_draft):
        try:
            self.tech_spec_draft = tech_spec_draft
            self.ui.techSpecTextEdit.setHtml(markdown.markdown(self.tech_spec_draft, extensions=['fenced_code', 'extra']))
            self.ui.feedbackTextEdit.clear()
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def _handle_refinement_result(self, new_draft):
        try:
            self.tech_spec_draft = new_draft
            self.ui.techSpecTextEdit.setHtml(markdown.markdown(self.tech_spec_draft, extensions=['fenced_code', 'extra']))
            self.ui.feedbackTextEdit.clear()
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def on_approve_clicked(self):
        """
        Finalizes the tech spec by running the save and commit operations in a
        background thread to keep the UI responsive.
        """
        final_tech_spec = self.ui.techSpecTextEdit.toPlainText()
        if not final_tech_spec.strip():
            QMessageBox.warning(self, "Approval Failed", "The technical specification cannot be empty.")
            return

        target_os = self.ui.osComboBox.currentText()
        self._execute_task(self._task_approve_spec, self._handle_approval_result, final_tech_spec, target_os,
                           status_message="Finalizing technical specification...")

    def _get_template_content(self, template_name: str) -> str | None:
        """A helper to load a specific template from the database."""
        template_content = None
        try:
            template_record = self.orchestrator.db_manager.get_template_by_name(template_name)
            if template_record:
                template_path = Path(template_record['file_path'])
                if template_path.exists():
                    template_content = template_path.read_text(encoding='utf-8')
                    logging.info(f"Found and loaded '{template_name}' template.")
        except Exception as e:
            logging.warning(f"Could not load '{template_name}' template: {e}")
        return template_content

    def _task_approve_spec(self, final_spec, target_os, **kwargs):
        """Background worker task to save the tech spec."""
        self.orchestrator.finalize_and_save_tech_spec(final_spec, target_os)
        return True

    def _handle_approval_result(self, success):
        """Handles the result of the background finalization task."""
        try:
            if success:
                QMessageBox.information(self, "Success", "Success: Technical Specification approved and saved.")
                self.orchestrator.is_project_dirty = True
                self.tech_spec_complete.emit()
            else:
                QMessageBox.critical(self, "Error", "The finalization process failed.")
        finally:
            self._set_ui_busy(False)

    def _task_propose_stack(self, target_os, **kwargs):

        template_content = self._get_template_content("Default Technical Specification")

        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        final_spec_text = project_details['final_spec_text']
        if not final_spec_text:
            raise Exception("Could not retrieve the application specification.")
        agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)

        draft_content = agent.propose_stack(final_spec_text, target_os, template_content=template_content)

        full_draft = self.orchestrator.prepend_standard_header(draft_content, "Technical Specification")
        return full_draft

    def _task_generate_from_guidelines(self, guidelines, target_os, **kwargs):

        template_content = self._get_template_content("Default Technical Specification")

        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        final_spec_text = project_details['final_spec_text']
        context = f"{final_spec_text}\n\n--- PM Directive for Technology Stack ---\n{guidelines}"
        agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)

        draft_content = agent.propose_stack(context, target_os, template_content=template_content)

        full_draft = self.orchestrator.prepend_standard_header(draft_content, "Technical Specification")
        return full_draft

    def _task_refine_spec(self, current_draft, feedback, target_os, **kwargs):
        """
        The actual function that runs in the background to refine the tech spec.
        This version now handles stripping and prepending the document header.
        """
        agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)

        # 1. Strip the header to get pure content
        pure_content = self.orchestrator._strip_header_from_document(current_draft)

        # 2. Get the refined content from the agent
        refined_content = agent.refine_stack(pure_content, feedback, target_os)

        # 3. Prepend a fresh, updated header
        final_draft = self.orchestrator.prepend_standard_header(refined_content, "Technical Specification")

        return final_draft