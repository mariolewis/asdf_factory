# gui/tech_spec_page.py

import logging
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
    tech_spec_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.tech_spec_draft = ""

        self.ui = Ui_TechSpecPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting TechSpecPage for a new project.")
        self.tech_spec_draft = ""
        self.ui.techSpecTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.ui.pmGuidelinesTextEdit.clear()
        self.ui.osComboBox.setCurrentIndex(0)
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.proposeStackButton.clicked.connect(self.run_propose_stack_task)
        self.ui.pmDefineButton.clicked.connect(self.on_pm_define_clicked)
        self.ui.generateFromGuidelinesButton.clicked.connect(self.run_generate_from_guidelines_task)
        self.ui.refineButton.clicked.connect(self.run_refine_task)
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
        # CORRECTED: The finished signal is NOT used to control the UI.
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        """Handles errors from the worker thread."""
        error_msg = f"An error occurred in a background task:\n{error_tuple[2]}"
        QMessageBox.critical(self, "Error", error_msg)
        self._set_ui_busy(False) # Re-enable UI on error

    # --- Task Initiators ---

    def run_propose_stack_task(self):
        target_os = self.ui.osComboBox.currentText()
        self._execute_task(self._task_propose_stack, self._handle_generation_result, target_os)

    def on_pm_define_clicked(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.pmDefinePage)

    def run_generate_from_guidelines_task(self):
        guidelines = self.ui.pmGuidelinesTextEdit.toPlainText().strip()
        if not guidelines:
            QMessageBox.warning(self, "Input Required", "Please provide your technology guidelines.")
            return
        target_os = self.ui.osComboBox.currentText()
        self._execute_task(self._task_generate_from_guidelines, self._handle_generation_result, guidelines, target_os)

    def run_refine_task(self):
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback to refine the draft.")
            return
        self.tech_spec_draft = self.ui.techSpecTextEdit.toPlainText()
        target_os = self.ui.osComboBox.currentText()
        self._execute_task(self._task_refine_spec, self._handle_refinement_result, feedback, target_os)

    # --- Result Handlers (Slots) ---

    def _handle_generation_result(self, tech_spec_draft):
        try:
            self.tech_spec_draft = tech_spec_draft
            self.ui.techSpecTextEdit.setText(self.tech_spec_draft)
            self.ui.feedbackTextEdit.clear()
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
        finally:
            self._set_ui_busy(False) # Re-enable UI after processing the result

    def _handle_refinement_result(self, new_draft):
        try:
            self.tech_spec_draft = new_draft
            self.ui.techSpecTextEdit.setText(self.tech_spec_draft)
            self.ui.feedbackTextEdit.clear()
            QMessageBox.information(self, "Success", "The technical specification has been refined.")
        finally:
            self._set_ui_busy(False) # Re-enable UI after processing the result

    def on_approve_clicked(self):
        final_tech_spec = self.ui.techSpecTextEdit.toPlainText()
        if not final_tech_spec.strip():
            QMessageBox.warning(self, "Approval Failed", "The technical specification cannot be empty.")
            return
        target_os = self.ui.osComboBox.currentText()
        self.orchestrator.finalize_and_save_tech_spec(final_tech_spec, target_os)
        QMessageBox.information(self, "Success", "Technical Specification approved and saved.")
        self.tech_spec_complete.emit()

    # --- Backend Logic (to be run in worker threads) ---

    def _task_propose_stack(self, target_os, **kwargs):
        with self.orchestrator.db_manager as db:
            project_details = db.get_project_by_id(self.orchestrator.project_id)
            final_spec_text = project_details['final_spec_text']
        if not final_spec_text:
            raise Exception("Could not retrieve the application specification.")
        agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)
        return agent.propose_stack(final_spec_text, target_os)

    def _task_generate_from_guidelines(self, guidelines, target_os, **kwargs):
        with self.orchestrator.db_manager as db:
            project_details = db.get_project_by_id(self.orchestrator.project_id)
            final_spec_text = project_details['final_spec_text']
        context = f"{final_spec_text}\n\n--- PM Directive for Technology Stack ---\n{guidelines}"
        agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)
        return agent.propose_stack(context, target_os)

    def _task_refine_spec(self, feedback, target_os, **kwargs):
        with self.orchestrator.db_manager as db:
            project_details = db.get_project_by_id(self.orchestrator.project_id)
            final_spec_text = project_details['final_spec_text']
        context = (
            f"{final_spec_text}\n\n"
            f"--- Current Draft to Refine ---\n{self.tech_spec_draft}\n\n"
            f"--- PM Feedback for Refinement ---\n{feedback}"
        )
        agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)
        return agent.propose_stack(context, target_os)