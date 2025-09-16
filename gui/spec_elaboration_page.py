# gui/spec_elaboration_page.py

import logging
import json
import re
from datetime import datetime
import markdown
import warnings
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QApplication
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_spec_elaboration_page import Ui_SpecElaborationPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from master_orchestrator import FactoryPhase
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

        # Block signals during widget clearing ---
        self.ui.briefDescriptionTextEdit.blockSignals(True)
        self.ui.pmReviewTextEdit.blockSignals(True)
        self.ui.specDraftTextEdit.blockSignals(True)

        self.ui.briefDescriptionTextEdit.clear()
        self.ui.uploadPathLineEdit.clear()
        self.ui.analysisResultTextEdit.clear()
        self.ui.pmReviewTextEdit.clear()
        self.ui.pmFeedbackTextEdit.clear()
        self.ui.specDraftTextEdit.clear()
        self.ui.aiIssuesTextEdit.clear()
        self.ui.feedbackTextEdit.clear()

        self.ui.briefDescriptionTextEdit.blockSignals(False)
        self.ui.pmReviewTextEdit.blockSignals(False)
        self.ui.specDraftTextEdit.blockSignals(False)

        self.ui.stackedWidget.setCurrentWidget(self.ui.initialInputPage)

    def connect_signals(self):
        # print(f"Object type: {type(self)}")
        # print(f"Has 'run_generation_task' attribute? {hasattr(self, 'run_generation_task')}")
        # if hasattr(self, 'run_generation_task'):
        #     print(f"Attribute type: {type(self.run_generation_task)}")
        #    print(f"Is it a method? {inspect.ismethod(self.run_generation_task)}")
        # print("--- END DEBUGGING BLOCK ---")

        self.ui.processTextButton.clicked.connect(self.run_generation_task)
        self.ui.browseFilesButton.clicked.connect(self.on_browse_files_clicked)
        self.ui.processFilesButton.clicked.connect(self.run_generation_task)
        self.ui.confirmAnalysisButton.clicked.connect(self.on_confirm_analysis_clicked)
        self.ui.cancelProjectButton.clicked.connect(self.on_cancel_project_clicked)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.ui.submitFeedbackButton.clicked.disconnect()
            self.ui.submitForAnalysisButton.clicked.disconnect()
        self.ui.submitFeedbackButton.clicked.connect(self.run_refinement_task)
        self.ui.approveSpecButton.clicked.connect(self.on_approve_spec_clicked)
        self.ui.submitForAnalysisButton.clicked.connect(self.run_refinement_and_analysis_task)
        self.ui.pmReviewTextEdit.textChanged.connect(self.on_draft_changed)
        self.ui.specDraftTextEdit.textChanged.connect(self.on_draft_changed)

    def on_draft_changed(self):
        """Saves the current text content to the orchestrator's active draft variable."""
        # Determine which text edit is currently visible and get its content
        active_widget = self.ui.stackedWidget.currentWidget()
        draft_text = ""
        if active_widget == self.ui.pmFirstReviewPage:
            draft_text = self.ui.pmReviewTextEdit.toPlainText()
        elif active_widget == self.ui.finalReviewPage:
            draft_text = self.ui.specDraftTextEdit.toPlainText()

        if self.orchestrator:
            self.orchestrator.set_active_spec_draft(draft_text)

    # This is the new, fully corrected method
    def prepare_for_display(self):
        """
        Configures the page based on the orchestrator's current phase.
        """
        current_phase = self.orchestrator.current_phase
        logging.debug(f"SpecElaborationPage preparing for display in phase: {current_phase.name}")

        if current_phase == FactoryPhase.SPEC_ELABORATION:
            # STATE 1: Initial entry. Show the brief intake form.
            self.ui.headerLabel.setText("Your Requirements")
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialInputPage)
            self.ui.briefDescriptionTextEdit.clear()

        elif current_phase == FactoryPhase.GENERATING_APP_SPEC_AND_RISK_ANALYSIS:
            # STATE 2: Trigger background task to generate draft and risk analysis.
            self.ui.headerLabel.setText("Application Specification Generation")
            self.window().statusBar().showMessage("Generating initial draft and analyzing project risk...")
            self.window().setEnabled(False) # Disable main window during processing
            self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
            self.ui.processingLabel.setText("Generating initial draft and analyzing project risk...")

            task_data = self.orchestrator.task_awaiting_approval or {}
            initial_brief = task_data.get("pending_brief")

            if not initial_brief:
                QMessageBox.critical(self, "Error", "Could not find the initial brief text to start the analysis.")
                # Safely transition back to a stable state instead of looping
                self.orchestrator.set_phase("SPEC_ELABORATION")
                self.window().setEnabled(True)
                self.window().statusBar().clearMessage()
                self.window().update_ui_after_state_change()
                return

            worker = Worker(self.orchestrator.generate_application_spec_draft_and_risk_analysis, initial_brief)

            # When the worker is finished, the orchestrator's state will have changed.
            # A single call to the main window's update function is all that's needed.
            worker.signals.finished.connect(self._on_generation_finished)
            worker.signals.error.connect(self._on_task_error)
            self.threadpool.start(worker)

        elif current_phase == FactoryPhase.AWAITING_SPEC_REFINEMENT_SUBMISSION:
            # STATE 3: Risk approved. Show the first draft for PM review.
            self.ui.headerLabel.setText("Draft Application Specification")
            self.ui.stackedWidget.setCurrentWidget(self.ui.pmFirstReviewPage)
            task_data = self.orchestrator.task_awaiting_approval or {}
            draft = task_data.get("generated_spec_draft", "Error: Could not load spec draft.")
            self.ui.pmReviewTextEdit.setHtml(markdown.markdown(draft, extensions=['fenced_code', 'extra']))
            self.ui.pmFeedbackTextEdit.clear()

        elif current_phase == FactoryPhase.AWAITING_SPEC_FINAL_APPROVAL:
            # STATE 4: In refinement loop. Show the 3-tab review view.
            self.ui.headerLabel.setText("Refine Application Specification")
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalReviewPage)
            self.ui.reviewTabWidget.setCurrentIndex(0)
            task_data = self.orchestrator.task_awaiting_approval or {}
            refined_draft = task_data.get("refined_spec_draft", "Error: Could not load refined draft.")
            ai_analysis = task_data.get("ai_analysis", "Error: Could not load AI analysis.")
            self.ui.specDraftTextEdit.setHtml(markdown.markdown(refined_draft, extensions=['fenced_code', 'extra']))
            self.ui.aiIssuesTextEdit.setHtml(markdown.markdown(ai_analysis, extensions=['fenced_code', 'extra']))
            self.ui.feedbackTextEdit.clear()

    def on_task_finished():
        """A nested function to re-enable the UI and trigger the next state update."""
        self.window().setEnabled(True)
        self.window().statusBar().clearMessage()
        self.window().update_ui_after_state_change()

        worker.signals.finished.connect(on_task_finished)
        self.threadpool.start(worker)

    def _task_generate_app_spec_draft(self, spec_text, **kwargs):
        """Background task for generating ONLY the application spec draft."""
        return self.orchestrator.generate_application_spec_draft(spec_text)

    def _handle_draft_generation_result(self, draft_text: str):
        """Handles the result of the draft generation and shows the first review page."""
        try:
            self.ui.headerLabel.setText("Draft Application Specification")
            self.spec_draft = draft_text
            self.ui.pmReviewTextEdit.setHtml(markdown.markdown(self.spec_draft, extensions=['fenced_code', 'extra']))
            self.ui.pmFeedbackTextEdit.clear()
            self.ui.stackedWidget.setCurrentWidget(self.ui.pmFirstReviewPage)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the main window and updates the status bar."""
        main_window = self.window()
        if not main_window:
            self.setEnabled(not is_busy) # Fallback
            return

        main_window.setEnabled(not is_busy)
        if hasattr(main_window, 'statusBar'):
            if is_busy:
                self.ui.processingLabel.setText(message) # This line is added
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
            self.ui.headerLabel.setText("Elaborating & Assessing Application Specifications") # Reset header on error
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialInputPage)
        finally:
            self._set_ui_busy(False)

    def _on_generation_finished(self):
        """A dedicated handler to run after the generation/analysis worker is complete."""
        main_window = self.window()
        if main_window:
            main_window.setEnabled(True)
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().clearMessage()

        # Now that the UI is responsive again, trigger the state update
        # which will display the new page (the risk assessment).
        self.window().update_ui_after_state_change()

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
        """
        Processes the initial user brief (from text or files) and passes it to the
        orchestrator's UX Triage workflow.
        """
        sender = self.sender()
        input_data = None
        status_message = "Processing brief for initial analysis..."

        if sender == self.ui.processTextButton:
            input_data = self.ui.briefDescriptionTextEdit.toPlainText().strip()
            if not input_data:
                QMessageBox.warning(self, "Input Required", "Please enter a brief description.")
                return
        elif sender == self.ui.processFilesButton:
            input_data = self.selected_files
            status_message = "Processing uploaded documents..."
            if not input_data:
                QMessageBox.warning(self, "Input Required", "Please select at least one document file.")
                return

        if input_data:
            self._execute_task(self._task_process_brief,
                            self._handle_brief_processing_result,
                            input_data,
                            status_message=status_message)

    def _task_process_brief(self, input_data, **kwargs):
        """Background task to process the initial brief from either text or files."""
        initial_text = ""
        if isinstance(input_data, list):
            bootstrap_agent = ProjectBootstrapAgent(self.orchestrator.db_manager)
            text_from_files, messages, error = bootstrap_agent.extract_text_from_file_paths(input_data)
            if error:
                raise Exception(f"Failed to process uploaded files: {error}")
            initial_text = text_from_files
        else:
            initial_text = input_data

        if not initial_text or not initial_text.strip():
            raise Exception("No text could be extracted from the provided input.")

        # This single orchestrator call handles the entire triage workflow.
        self.orchestrator.handle_ux_ui_brief_submission(initial_text)
        return "Triage initiated."

    def _handle_brief_processing_result(self, result):
        """
        Handles the completion of the initial brief processing and triggers a
        main UI state update to show the next page (the UX Triage decision).
        """
        try:
            logging.info(f"Brief processing background task completed with result: {result}")
            # This signal tells the main window to refresh its view based on the
            # orchestrator's new state, which is now awaiting the UX/UI decision.
            self.spec_elaboration_complete.emit()
        finally:
            self._set_ui_busy(False)

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

    def on_confirm_analysis_clicked(self):
        self.ui.headerLabel.setText("Draft Application Specification")
        self.ui.pmReviewTextEdit.setHtml(markdown.markdown(self.spec_draft, extensions=['fenced_code', 'extra']))
        self.ui.pmFeedbackTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.pmFirstReviewPage)
        self.state_changed.emit()

    def run_refinement_and_analysis_task(self):
        """
        Handles the submission for AI analysis and refinement from the first review page.
        """
        current_draft = self.ui.pmReviewTextEdit.toPlainText()
        pm_feedback = self.ui.pmFeedbackTextEdit.toPlainText().strip()
        if not current_draft.strip():
            QMessageBox.warning(self, "Input Required", "The specification draft cannot be empty.")
            return

        # Note: Even if feedback is empty, the process runs to analyze for issues.
        self._execute_task(self._task_refine_and_analyze,
                        self._handle_refinement_and_analysis_result,
                        current_draft,
                        pm_feedback,
                        status_message="Refining draft and analyzing for issues...")

    def _task_run_complexity_assessment(self, spec_draft_with_header, **kwargs):
        """Background task to run the orchestrator's complexity assessment."""
        # This call returns the analysis result and sets the orchestrator's
        # phase to AWAITING_COMPLEXITY_ASSESSMENT.
        analysis_result = self.orchestrator.run_complexity_assessment(spec_draft_with_header)
        # We also pass the analysis result to the orchestrator's task variable so the UI can find it.
        self.orchestrator.task_awaiting_approval = {"analysis_result": analysis_result}
        return True

    def _task_refine_and_analyze(self, current_draft, pm_feedback, **kwargs):
        """Background worker task that calls the orchestrator for refinement and issue analysis."""
        self.orchestrator.handle_spec_refinement_submission(current_draft, pm_feedback)
        return True # Indicate success

    def _handle_refinement_and_analysis_result(self, success):
        """Handles the completion of the refinement task by triggering a full UI update."""
        try:
            if success:
                # The orchestrator's phase has been updated. A full UI refresh will show the new 3-tab page.
                self.window().update_ui_after_state_change()
            else:
                QMessageBox.critical(self, "Error", "The refinement and analysis process failed.")
        finally:
            self._set_ui_busy(False)

    def _handle_assessment_result(self, success: bool):
        """
        Handles the result of the assessment. It emits a signal that tells the
        main window to refresh, which will now show the complexity review page.
        """
        try:
            if success:
                self.spec_elaboration_complete.emit()
            else:
                QMessageBox.critical(self, "Error", "The complexity assessment process failed.")
        finally:
            self._set_ui_busy(False)

    def run_refinement_task(self):
        """
        Handles the submission for AI analysis and refinement from the final
        review page, now using a background worker to prevent UI freeze.
        """
        current_draft = self.ui.specDraftTextEdit.toPlainText()
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback for refinement in the third tab.")
            return

        self._execute_task(self._task_refine_spec, self._handle_refinement_result, current_draft, feedback,
                           status_message="Refining specification based on your feedback...")

    def _task_refine_spec(self, current_draft, feedback, **kwargs):
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        refined_draft = spec_agent.refine_specification(current_draft, self.ai_issues, feedback)
        current_date = datetime.now().strftime('%x')
        # This is the corrected regex to prevent the crash
        date_updated_draft = re.sub(r"(Date: ).*", r"\g<1>" + current_date, refined_draft)
        return date_updated_draft

    def _handle_refinement_result(self, new_draft):
        """Handles the result from the refinement worker thread."""
        try:
            self.spec_draft = new_draft
            self.ui.specDraftTextEdit.setHtml(markdown.markdown(self.spec_draft, extensions=['fenced_code', 'extra']))
            self.ui.aiIssuesTextEdit.setText("Draft has been refined. Please review the new version.")
            self.ui.feedbackTextEdit.clear()

            # Switch back to the review page and set the active tab to the first one
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalReviewPage)
            self.ui.reviewTabWidget.setCurrentIndex(0)

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
        """
        Handles the final approval of the application specification from the final
        review page.
        """
        final_draft = self.ui.specDraftTextEdit.toPlainText()
        reply = QMessageBox.question(self, "Confirm Approval",
                                    "Are you sure you want to approve this specification? It will be finalized and the process will move to the Technical Specification phase.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.orchestrator.finalize_and_save_app_spec(final_draft)
            self.spec_elaboration_complete.emit()

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