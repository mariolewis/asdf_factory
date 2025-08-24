# gui/spec_elaboration_page.py

import logging
import json
import re
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QApplication
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_spec_elaboration_page import Ui_SpecElaborationPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_project_bootstrap import ProjectBootstrapAgent
from agents.agent_spec_clarification import SpecClarificationAgent

class SpecElaborationPage(QWidget):
    state_changed = Signal()
    spec_elaboration_complete = Signal()
    project_cancelled = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.spec_draft = ""
        self.selected_files = []
        self.ai_issues = ""
        self.refinement_iteration_count = 1

        self.ui = Ui_SpecElaborationPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_new_project(self):
        logging.info("Resetting SpecElaborationPage for a new project.")
        self.spec_draft = ""
        self.selected_files = []
        self.ai_issues = ""
        self.refinement_iteration_count = 1
        self.ui.briefDescriptionTextEdit.clear()
        self.ui.uploadPathLineEdit.clear()
        self.ui.analysisResultTextEdit.clear()
        self.ui.pmReviewTextEdit.clear()
        self.ui.pmFeedbackTextEdit.clear()
        self.ui.specDraftTextEdit.clear()
        self.ui.aiIssuesTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialInputPage)

    def connect_signals(self):
        self.ui.processTextButton.clicked.connect(self.run_generation_task)
        self.ui.browseFilesButton.clicked.connect(self.on_browse_files_clicked)
        self.ui.processFilesButton.clicked.connect(self.run_generation_task)
        self.ui.confirmAnalysisButton.clicked.connect(self.on_confirm_analysis_clicked)
        self.ui.cancelProjectButton.clicked.connect(self.on_cancel_project_clicked)
        self.ui.submitFeedbackButton.clicked.connect(self.run_refinement_task)
        self.ui.approveSpecButton.clicked.connect(self.on_approve_spec_clicked)
        self.ui.submitForAnalysisButton.clicked.connect(self.run_refinement_and_analysis_task)

    def prepare_for_display(self):
        """
        Smart entry point that decides whether to ask for a brief or auto-generate
        the app spec from a previously completed phase.
        """
        task = self.orchestrator.task_awaiting_approval or {}
        completed_ux_spec = task.get("completed_ux_spec")
        pending_brief = task.get("pending_brief")

        if completed_ux_spec:
            logging.info("Detected completed UX Spec. Auto-generating Application Spec draft.")
            self.orchestrator.task_awaiting_approval = None
            self.ui.headerLabel.setText("Assessing Project Complexity...")
            self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
            self._execute_task(self._task_generate_from_existing_spec, self._handle_analysis_result, completed_ux_spec,
                               status_message="Generating application spec from UX design...")
        elif pending_brief:
            logging.info("Detected pending brief from UX skip. Auto-generating Application Spec draft.")
            self.orchestrator.task_awaiting_approval = None
            self.ui.headerLabel.setText("Assessing Project Complexity...")
            self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
            self._execute_task(self._task_generate_from_existing_spec, self._handle_analysis_result, pending_brief,
                               status_message="Generating application spec from brief...")
        else:
            logging.info("No pending brief found. Displaying initial brief input page.")
            self.ui.headerLabel.setText("Your Requirements")
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialInputPage)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the page and updates the main status bar."""
        self.setEnabled(not is_busy)

        # Also switch to the processing page view for clear, unmissable feedback
        if is_busy:
            self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)

        main_window = self.parent()
        if main_window and hasattr(main_window, 'statusBar'):
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
            self.ui.headerLabel.setText("Your Requirements") # Reset header on error
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialInputPage)
        finally:
            self._set_ui_busy(False)

    def _format_assessment_for_display(self, analysis_data: dict) -> str:
        if not analysis_data or "complexity_analysis" not in analysis_data:
            return "<p>Could not parse the analysis result.</p>"
        html = ["<h3>Complexity Analysis</h3>"]
        for key, value in analysis_data.get("complexity_analysis", {}).items():
            title = key.replace('_', ' ').title()
            rating = value.get('rating', 'N/A')
            justification = value.get('justification', 'No details provided.')
            html.append(f"<p><b>{title}:</b> {rating}<br/><i>{justification}</i></p>")
        html.append("<hr><h3>Risk Assessment</h3>")
        risk = analysis_data.get("risk_assessment", {})
        html.append(f"<p><b>Overall Risk Level:</b> {risk.get('overall_risk_level', 'N/A')}</p>")
        html.append(f"<p><b>Summary:</b> {risk.get('summary', 'No summary provided.')}</p>")
        if risk.get('recommendations'):
            html.append("<p><b>Recommendations:</b></p><ul>")
            for rec in risk['recommendations']:
                html.append(f"<li>{rec}</li>")
            html.append("</ul>")
        return "".join(html)

    def on_browse_files_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Specification Documents", "", "Documents (*.txt *.md *.pdf *.docx)")
        if files:
            self.selected_files = files
            self.ui.uploadPathLineEdit.setText("; ".join(files))

    def run_generation_task(self):
        """Processes a new brief submitted by the user and sends it to the UX Triage workflow."""
        sender = self.sender()
        input_data = None
        status_message = "Processing brief..."

        if sender == self.ui.processTextButton:
            input_data = self.ui.briefDescriptionTextEdit.toPlainText().strip()
            if not input_data:
                QMessageBox.warning(self, "Input Required", "Please enter a brief description.")
                return
        elif sender == self.ui.processFilesButton:
            input_data = self.selected_files
            status_message = "Processing uploaded documents..."
            if not input_data:
                QMessageBox.warning(self, "Input Required", "Please browse for at least one specification document.")
                return

        if input_data:
            self._execute_task(self._task_submit_brief_for_triage, self._handle_triage_submission_result, input_data,
                               status_message=status_message)

    def _task_submit_brief_for_triage(self, input_data, **kwargs):
        if isinstance(input_data, list):
            bootstrap_agent = ProjectBootstrapAgent(self.orchestrator.db_manager)
            initial_text, _, error = bootstrap_agent.extract_text_from_file_paths(input_data)
            if error: raise Exception(error)
        else:
            initial_text = input_data
        if not initial_text or not initial_text.strip():
            raise Exception("No text could be extracted from the provided input.")
        self.orchestrator.handle_ux_ui_brief_submission(initial_text)
        return "Triage initiated."

    def _handle_triage_submission_result(self, result):
        logging.info(f"Triage submission background task completed with result: {result}")
        self.spec_elaboration_complete.emit()

    def _task_generate_from_existing_spec(self, spec_text, **kwargs):
        """Background task for processing text from a prior phase."""
        return self.orchestrator.generate_application_spec_draft(spec_text)

    def _handle_analysis_result(self, result_tuple):
        try:
            self.ui.headerLabel.setText("Project Complexity & Risk Assessment") # Set correct header
            analysis_result, self.spec_draft = result_tuple
            analysis_for_display = self._format_assessment_for_display(analysis_result)
            self.ui.analysisResultTextEdit.setHtml(analysis_for_display)
            self.ui.stackedWidget.setCurrentWidget(self.ui.complexityReviewPage)

            # Explicitly enable buttons to ensure workflow is not blocked
            self.ui.cancelProjectButton.setEnabled(True)
            self.ui.confirmAnalysisButton.setEnabled(True)

            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def _handle_refinement_and_analysis_result(self, result_tuple):
        try:
            self.ui.headerLabel.setText("Application Specification Review")
            self.spec_draft, self.ai_issues = result_tuple
            self.refinement_iteration_count = 2

            # 1. Make the page visible first
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalReviewPage)
            # 2. Force Qt to process pending events and draw the widget
            QApplication.processEvents()

            # 3. Now, populate the content
            self.ui.specDraftTextEdit.setText(self.spec_draft)
            self.ui.aiIssuesTextEdit.setText(self.ai_issues)
            self.ui.feedbackTextEdit.clear()

            # 4. Explicitly enable buttons
            self.ui.submitFeedbackButton.setEnabled(True)
            self.ui.approveSpecButton.setEnabled(True)

            self.state_changed.emit()
        finally:
            # 5. Re-enable the entire page widget
            self._set_ui_busy(False)

    def on_confirm_analysis_clicked(self):
        self.ui.headerLabel.setText("Draft Application Specification") # Set correct header
        self.ui.pmReviewTextEdit.setText(self.spec_draft)
        self.ui.pmFeedbackTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.pmFirstReviewPage)
        self.state_changed.emit()

    def run_refinement_and_analysis_task(self):
        current_draft = self.ui.pmReviewTextEdit.toPlainText()
        feedback = self.ui.pmFeedbackTextEdit.toPlainText().strip()
        if not current_draft.strip():
            QMessageBox.warning(self, "Input Required", "The specification draft cannot be empty.")
            return
        self._execute_task(self._task_refine_and_analyze, self._handle_refinement_and_analysis_result, current_draft, feedback,
                           status_message="Refining draft and running AI analysis...")

    def _task_refine_and_analyze(self, current_draft, feedback, **kwargs):
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        refined_draft = spec_agent.refine_specification(current_draft, "", feedback)
        ai_issues = spec_agent.identify_potential_issues(refined_draft, iteration_count=1)
        return refined_draft, ai_issues

    def run_refinement_task(self):
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback or clarifications.")
            return
        current_draft = self.ui.specDraftTextEdit.toPlainText()
        self._execute_task(self._task_refine_spec, self._handle_refinement_result, current_draft, feedback,
                           status_message="Refining specification based on feedback...")

    def _task_refine_spec(self, current_draft, feedback, **kwargs):
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        refined_draft = spec_agent.refine_specification(current_draft, self.ai_issues, feedback)
        current_date = datetime.now().strftime('%x')
        date_updated_draft = re.sub(r"(Date: ).*", r"\g" + current_date, refined_draft)
        return date_updated_draft

    def _handle_refinement_result(self, new_draft):
        self.spec_draft = new_draft
        self.ui.specDraftTextEdit.setText(self.spec_draft)
        self.ui.aiIssuesTextEdit.setText("Draft has been refined. Please review the new version on the left.")
        self.ui.feedbackTextEdit.clear()
        QMessageBox.information(self, "Success", "Success: Draft has been updated.")
        self.state_changed.emit()
        self.refinement_iteration_count += 1

    def on_cancel_project_clicked(self):
        reply = QMessageBox.question(self, "Cancel Project", "Are you sure you want to cancel and archive this project?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.project_cancelled.emit()

    def on_approve_spec_clicked(self):
        final_spec = self.ui.specDraftTextEdit.toPlainText()
        if not final_spec.strip():
            QMessageBox.warning(self, "Approval Failed", "The specification cannot be empty.")
            return
        self.orchestrator.finalize_and_save_app_spec(final_spec)
        QMessageBox.information(self, "Success", "Success: Specification approved and saved.")
        self.spec_elaboration_complete.emit()