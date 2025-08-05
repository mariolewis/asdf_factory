# gui/spec_elaboration_page.py

import logging
import json
from datetime import datetime
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_spec_elaboration_page import Ui_SpecElaborationPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_spec_clarification import SpecClarificationAgent
from agents.agent_project_bootstrap import ProjectBootstrapAgent
from agents.agent_project_scoping import ProjectScopingAgent

class SpecElaborationPage(QWidget):
    state_changed = Signal()
    spec_elaboration_complete = Signal()
    project_cancelled = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.spec_draft = None
        self.selected_files = []
        self.ai_issues = ""

        self.ui = Ui_SpecElaborationPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_new_project(self):
        logging.info("Resetting SpecElaborationPage for a new project.")
        self.spec_draft = None
        self.selected_files = []
        self.ai_issues = ""
        self.ui.briefDescriptionTextEdit.clear()
        self.ui.uploadPathLineEdit.clear()
        self.ui.analysisResultTextEdit.clear()
        self.ui.specDraftTextEdit.clear()
        self.ui.aiIssuesTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialInputPage)

    def connect_signals(self):
        self.ui.processTextButton.clicked.connect(self.run_generation_task)
        self.ui.browseFilesButton.clicked.connect(self.on_browse_files_clicked)
        self.ui.processFilesButton.clicked.connect(self.run_generation_task)
        self.ui.confirmAnalysisButton.clicked.connect(self.run_ai_analysis_task)
        self.ui.cancelProjectButton.clicked.connect(self.on_cancel_project_clicked)
        self.ui.submitFeedbackButton.clicked.connect(self.run_refinement_task)
        self.ui.approveSpecButton.clicked.connect(self.on_approve_spec_clicked)

    def _set_ui_busy(self, is_busy):
        self.setEnabled(not is_busy)

    def _execute_task(self, task_function, on_result, *args):
        self._set_ui_busy(True)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        # FIX: The error handler will now also be responsible for re-enabling the UI
        worker.signals.error.connect(self._on_task_error)
        # FIX: The finished signal is no longer used to control the UI state
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        error_msg = f"An error occurred in a background task:\n{error_tuple[2]}"
        QMessageBox.critical(self, "Error", error_msg)
        self._set_ui_busy(False) # Re-enable UI on error

    # --- Task Initiators ---

    def on_browse_files_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Specification Documents", "", "Documents (*.txt *.md *.pdf *.docx)")
        if files:
            self.selected_files = files
            self.ui.uploadPathLineEdit.setText("; ".join(self.selected_files))

    def run_generation_task(self):
        sender = self.sender()
        if sender == self.ui.processTextButton:
            input_data = self.ui.briefDescriptionTextEdit.toPlainText().strip()
            if not input_data:
                QMessageBox.warning(self, "Input Required", "Please enter a brief description.")
                return
        elif sender == self.ui.processFilesButton:
            input_data = self.selected_files
            if not input_data:
                QMessageBox.warning(self, "Input Required", "Please browse for at least one specification document.")
                return
        self._execute_task(self._task_generate_and_analyze, self._handle_analysis_result, input_data)

    def run_ai_analysis_task(self):
        self._execute_task(self._task_run_ai_analysis, self._handle_ai_analysis_result)

    def run_refinement_task(self):
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback or clarifications.")
            return
        self.spec_draft = self.ui.specDraftTextEdit.toPlainText()
        self._execute_task(self._task_refine_spec, self._handle_refinement_result, feedback)

    # --- Result Handlers (Slots) ---

    def _handle_analysis_result(self, result_tuple):
        try:
            analysis_result, self.spec_draft = result_tuple
            analysis_for_display = json.dumps(analysis_result, indent=4)
            footnote_text = "\n\nNote: This assessment is a point-in-time analysis."
            self.ui.analysisResultTextEdit.setText(analysis_for_display + footnote_text)
            self.ui.stackedWidget.setCurrentWidget(self.ui.complexityReviewPage)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False) # Re-enable UI after processing the result

    def _handle_ai_analysis_result(self, ai_issues):
        try:
            self.ai_issues = ai_issues
            self.ui.specDraftTextEdit.setText(self.spec_draft)
            self.ui.aiIssuesTextEdit.setText(self.ai_issues)
            self.ui.feedbackTextEdit.clear()
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalReviewPage)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False) # Re-enable UI after processing the result

    def _handle_refinement_result(self, new_draft):
        try:
            self.spec_draft = new_draft
            self.ui.specDraftTextEdit.setText(self.spec_draft)
            self.ui.aiIssuesTextEdit.setText("Draft has been refined. Please review the new version on the left.")
            self.ui.feedbackTextEdit.clear()
            QMessageBox.information(self, "Success", "Draft has been updated.")
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False) # Re-enable UI after processing the result

    def on_cancel_project_clicked(self):
        # ... (This method remains the same)
        reply = QMessageBox.question(self, "Cancel Project",
                                     "Are you sure you want to cancel and archive this project?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            archive_name = f"{self.orchestrator.project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.orchestrator.stop_and_export_project("data/archives", archive_name)
            self.project_cancelled.emit()

    def on_approve_spec_clicked(self):
        # ... (This method remains the same)
        final_spec = self.ui.specDraftTextEdit.toPlainText()
        self.orchestrator.finalize_and_save_app_spec(final_spec)
        QMessageBox.information(self, "Success", "Specification approved and saved.")
        self.spec_elaboration_complete.emit()

    # --- Backend Logic (to be run in worker threads) ---

    def _task_generate_and_analyze(self, input_data, **kwargs):
        # ... (This method remains the same)
        if isinstance(input_data, list):
            bootstrap_agent = ProjectBootstrapAgent(self.orchestrator.db_manager)
            initial_text, _, error = bootstrap_agent.extract_text_from_file_paths(input_data)
            if error: raise Exception(error)
        else:
            initial_text = input_data

        if not initial_text or not initial_text.strip():
            raise Exception("No text could be extracted from the provided input.")

        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        spec_draft = spec_agent.expand_brief_description(initial_text)

        scoping_agent = ProjectScopingAgent(self.orchestrator.llm_service)
        analysis_result = scoping_agent.analyze_complexity(spec_draft)
        if "error" in analysis_result:
            raise Exception(f"Failed to analyze project complexity: {analysis_result.get('details')}")

        footnote = "\n\nNote: This assessment is a point-in-time analysis for the version of the specification that was provided."
        analysis_for_db = json.dumps(analysis_result) + footnote
        with self.orchestrator.db_manager as db:
            db.save_complexity_assessment(self.orchestrator.project_id, analysis_for_db)

        return analysis_result, spec_draft

    def _task_run_ai_analysis(self, **kwargs):
        # ... (This method remains the same)
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        return spec_agent.identify_potential_issues(self.spec_draft)

    def _task_refine_spec(self, feedback, **kwargs):
        # ... (This method remains the same)
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        return spec_agent.refine_specification(self.spec_draft, self.ai_issues, feedback)