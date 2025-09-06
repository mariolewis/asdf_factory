# gui/spec_elaboration_page.py

import logging
import json
import re
from datetime import datetime
import markdown
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QApplication
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_spec_elaboration_page import Ui_SpecElaborationPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_spec_clarification import SpecClarificationAgent
from agents.agent_project_bootstrap import ProjectBootstrapAgent

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
            self.ui.headerLabel.setText("Elaborating & Assessing Application Specifications")
            self._execute_task(self._task_generate_from_existing_spec, self._handle_analysis_result, completed_ux_spec,
                               status_message="Generating application spec from UX design...")
        elif pending_brief:
            logging.info("Detected pending brief from UX skip. Auto-generating Application Spec draft.")
            self.orchestrator.task_awaiting_approval = None
            self.ui.headerLabel.setText("Elaborating & Assessing Application Specifications")
            self._execute_task(self._task_generate_from_existing_spec, self._handle_analysis_result, pending_brief,
                               status_message="Generating application spec from brief...")
        else:
            logging.info("No pending brief found. Displaying initial brief input page.")
            self.ui.headerLabel.setText("Your Requirements")
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialInputPage)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the main window and updates the status bar."""
        main_window = self.window()
        if not main_window:
            self.setEnabled(not is_busy) # Fallback
            return

        main_window.setEnabled(not is_busy)
        if hasattr(main_window, 'statusBar'):
            if is_busy:
                main_window.statusBar().showMessage(message)
                self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
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
            self.ui.headerLabel.setText("Elaborating & Assessing Application Specifications") # Reset header on error
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
        """Background task to process the initial brief from either text or files."""
        initial_text = ""
        if isinstance(input_data, list):
            # This is the corrected logic for file processing
            bootstrap_agent = ProjectBootstrapAgent(self.orchestrator.db_manager)
            text_from_files, messages, error = bootstrap_agent.extract_text_from_file_paths(input_data)
            if error:
                raise Exception(f"Failed to process uploaded files: {error}")
            initial_text = text_from_files
        else:
            # This is the existing logic for text input, which is correct
            initial_text = input_data

        if not initial_text or not initial_text.strip():
            raise Exception("No text could be extracted from the provided input.")

        self.orchestrator.handle_ux_ui_brief_submission(initial_text)
        return "Triage initiated."

    def _handle_triage_submission_result(self, result):
        try:
            logging.info(f"Triage submission background task completed with result: {result}")
            self.spec_elaboration_complete.emit()
        finally:
            self._set_ui_busy(False)

    def _task_generate_from_existing_spec(self, spec_text, **kwargs):
        """Background task for processing text from a prior phase."""
        return self.orchestrator.generate_application_spec_draft(spec_text)

    def _handle_analysis_result(self, result_tuple):
        try:
            self.ui.headerLabel.setText("Project Complexity & Risk Assessment")
            analysis_result, self.spec_draft = result_tuple
            analysis_for_display = self._format_assessment_for_display(analysis_result)
            self.ui.analysisResultTextEdit.setHtml(analysis_for_display)
            self.ui.stackedWidget.setCurrentWidget(self.ui.complexityReviewPage)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def on_confirm_analysis_clicked(self):
        self.ui.headerLabel.setText("Draft Application Specification")
        self.ui.pmReviewTextEdit.setHtml(markdown.markdown(self.spec_draft, extensions=['fenced_code']))
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
        ai_issues = spec_agent.identify_potential_issues(refined_draft, iteration_count=self.refinement_iteration_count)
        return refined_draft, ai_issues

    def _handle_refinement_and_analysis_result(self, result_tuple):
        try:
            self.ui.headerLabel.setText("Application Specification Review")
            self.spec_draft, self.ai_issues = result_tuple
            self.refinement_iteration_count = 2

            self.ui.stackedWidget.setCurrentWidget(self.ui.finalReviewPage)
            QApplication.processEvents()

            self.ui.specDraftTextEdit.setHtml(markdown.markdown(self.spec_draft, extensions=['fenced_code']))
            self.ui.aiIssuesTextEdit.setHtml(markdown.markdown(self.ai_issues))
            self.ui.feedbackTextEdit.clear()

            self.ui.submitFeedbackButton.setEnabled(True)
            self.ui.approveSpecButton.setEnabled(True)

            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

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
        # This is the corrected regex to prevent the crash
        date_updated_draft = re.sub(r"(Date: ).*", r"\g<1>" + current_date, refined_draft)
        return date_updated_draft

    def _handle_refinement_result(self, new_draft):
        try:
            self.spec_draft = new_draft
            self.ui.specDraftTextEdit.setHtml(markdown.markdown(self.spec_draft, extensions=['fenced_code']))
            self.ui.aiIssuesTextEdit.setText("Draft has been refined. Please review the new version.")
            self.ui.feedbackTextEdit.clear()

            # This is the new line that fixes the bug by switching back to the correct page
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalReviewPage)

            QMessageBox.information(self, "Success", "Success: Draft has been updated.")
            self.state_changed.emit()
            self.refinement_iteration_count += 1
        finally:
            self._set_ui_busy(False)

    def on_cancel_project_clicked(self):
        # Corrected to use QMessageBox.warning for a more appropriate dialog
        reply = QMessageBox.warning(self, "Cancel Project",
                                    "Are you sure you want to cancel and archive this project? This action cannot be undone.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Corrected to pass the required arguments to the export function
            archive_path_from_db = self.orchestrator.db_manager.get_config_value("DEFAULT_ARCHIVE_PATH")
            if not archive_path_from_db or not archive_path_from_db.strip():
                QMessageBox.critical(self, "Configuration Error", "The Default Project Archive Path is not set. Please set it in the Settings dialog.")
                return
            archive_name = f"{self.orchestrator.project_name.replace(' ', '_')}_cancelled_{datetime.now().strftime('%Y%m%d')}"
            self.orchestrator.stop_and_export_project(archive_path_from_db, archive_name)
            self.project_cancelled.emit()


    def on_approve_spec_clicked(self):
        """Saves the final spec and triggers the backlog generation in a background thread."""
        final_spec = self.ui.specDraftTextEdit.toPlainText()
        if not final_spec.strip():
            QMessageBox.warning(self, "Approval Failed", "The specification cannot be empty.")
            return

        self._execute_task(self._task_approve_and_generate_backlog, self._handle_approval_result, final_spec,
                        status_message="Generating backlog from specification...")

    def _task_approve_and_generate_backlog(self, final_spec_text, **kwargs):
        """Background worker task to save the spec and generate the backlog."""
        self.orchestrator.finalize_and_save_app_spec(final_spec_text)
        # The orchestrator's phase is now BACKLOG_RATIFICATION
        return True

    def _handle_approval_result(self, success):
        """Handles the result of the background task."""
        # First, switch away from the processing page
        self.ui.stackedWidget.setCurrentWidget(self.ui.finalReviewPage)
        # Then, clear the busy status bar and re-enable the main window
        self._set_ui_busy(False)

        # Finally, show the result and emit the completion signal
        if success:
            QMessageBox.information(self, "Success", "Specification approved. Proceeding to Technical Specification.")
            self.spec_elaboration_complete.emit()
        else:
            QMessageBox.critical(self, "Error", "The approval and backlog generation process failed.")