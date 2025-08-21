# gui/spec_elaboration_page.py

import logging
import json
import re
from datetime import datetime
import os
from pathlib import Path
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
        self.refinement_iteration_count = 1

        self.ui = Ui_SpecElaborationPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_new_project(self):
        logging.info("Resetting SpecElaborationPage for a new project.")
        self.spec_draft = None
        self.selected_files = []
        self.ai_issues = ""
        self.refinement_iteration_count = 1
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
        self.ui.confirmAnalysisButton.clicked.connect(self.on_confirm_analysis_clicked)
        self.ui.cancelProjectButton.clicked.connect(self.on_cancel_project_clicked)
        self.ui.submitFeedbackButton.clicked.connect(self.run_refinement_task)
        self.ui.approveSpecButton.clicked.connect(self.on_approve_spec_clicked)
        self.ui.submitForAnalysisButton.clicked.connect(self.run_refinement_and_analysis_task)

    def _set_ui_busy(self, is_busy):
        self.setEnabled(not is_busy)

    def _execute_task(self, task_function, on_result, *args):
        self._set_ui_busy(True)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        error_msg = f"An error occurred in a background task:\n{error_tuple[1]}"
        QMessageBox.critical(self, "Error", error_msg)
        self._set_ui_busy(False)

    def _format_assessment_for_display(self, analysis_data: dict) -> str:
        """Converts the JSON assessment data into a formatted HTML string for display."""
        if not analysis_data or "complexity_analysis" not in analysis_data:
            return "<p>Could not parse the analysis result.</p>"

        html = []

        # --- Complexity Analysis Section ---
        html.append("<h3>Complexity Analysis</h3>")
        comp_analysis = analysis_data.get("complexity_analysis", {})

        for key, value in comp_analysis.items():
            title = key.replace('_', ' ').title()
            rating = value.get('rating', 'N/A')
            justification = value.get('justification', 'No details provided.')
            html.append(f"<p><b>{title}:</b> {rating}<br/><i>{justification}</i></p>")

        html.append("<hr>")

        # --- Risk Assessment Section ---
        html.append("<h3>Risk Assessment</h3>")
        risk_assessment = analysis_data.get("risk_assessment", {})

        overall_risk = risk_assessment.get('overall_risk_level', 'N/A')
        summary = risk_assessment.get('summary', 'No summary provided.')
        token_outlook = risk_assessment.get('token_consumption_outlook', 'N/A')
        recommendations = risk_assessment.get('recommendations', [])

        html.append(f"<p><b>Overall Risk Level:</b> {overall_risk}</p>")
        html.append(f"<p><b>Summary:</b> {summary}</p>")
        html.append(f"<p><b>Token Consumption Outlook:</b> {token_outlook}</p>")

        if recommendations:
            html.append("<p><b>Recommendations:</b></p><ul>")
            for rec in recommendations:
                html.append(f"<li>{rec}</li>")
            html.append("</ul>")

        return "".join(html)

    def on_browse_files_clicked(self):
        try:
            default_path = self.orchestrator.db_manager.get_config_value("DEFAULT_PROJECT_PATH")
            start_dir = default_path if default_path and os.path.isdir(default_path) else str(Path.home())

            files, _ = QFileDialog.getOpenFileNames(self, "Select Specification Documents", start_dir, "Documents (*.txt *.md *.pdf *.docx)")
            if files:
                self.selected_files = files
                self.ui.uploadPathLineEdit.setText("; ".join(self.selected_files))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file browser:\n{e}")

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

    def run_refinement_task(self):
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback or clarifications.")
            return
        current_draft = self.ui.specDraftTextEdit.toPlainText()
        self._execute_task(self._task_refine_spec, self._handle_refinement_result, current_draft, feedback)

    def _handle_analysis_result(self, result_tuple):
        """Handles the result of the initial spec generation and complexity analysis."""
        try:
            analysis_result, self.spec_draft = result_tuple

            # This is the changed part: Call the new formatting method
            analysis_for_display = self._format_assessment_for_display(analysis_result)

            # The QTextEdit widget will render this HTML
            self.ui.analysisResultTextEdit.setHtml(analysis_for_display)

            self.ui.stackedWidget.setCurrentWidget(self.ui.complexityReviewPage)
            self.orchestrator.is_project_dirty = True
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def on_confirm_analysis_clicked(self):
        """
        Handles the user confirming the complexity analysis. This transitions
        to the new full-width PM review page.
        """
        # The spec_draft was stored when the initial analysis was run.
        # Now, we display it in the new full-width editor.
        self.ui.pmReviewTextEdit.setText(self.spec_draft)
        self.ui.pmFeedbackTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.pmFirstReviewPage)
        self.state_changed.emit()

    def run_refinement_and_analysis_task(self):
        """
        Gathers PM input from the first review, then runs the combined
        refinement and analysis task in the background.
        """
        current_draft = self.ui.pmReviewTextEdit.toPlainText()
        feedback = self.ui.pmFeedbackTextEdit.toPlainText().strip()

        # Feedback is optional, but the draft cannot be empty
        if not current_draft.strip():
            QMessageBox.warning(self, "Input Required", "The specification draft cannot be empty.")
            return

        self._execute_task(self._task_refine_and_analyze, self._handle_refinement_and_analysis_result, current_draft, feedback)

    def _task_refine_and_analyze(self, current_draft, feedback, **kwargs):
        """
        Background task to first refine the spec, then identify issues in the refined version.
        """
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)

        # Step 1: Refine the draft based on PM's edits and feedback.
        # In this initial refinement, there are no prior "AI Issues", so we pass an empty string.
        refined_draft = spec_agent.refine_specification(current_draft, "", feedback)

        # Step 2: Analyze the newly refined draft for issues. This is the first analysis iteration.
        ai_issues = spec_agent.identify_potential_issues(refined_draft, iteration_count=1)

        return refined_draft, ai_issues

    def _handle_refinement_and_analysis_result(self, result_tuple):
        """
        Handles the result of the combined task, populating the final split-screen review page.
        """
        try:
            refined_draft, ai_issues = result_tuple

            # Store the results for the next refinement cycle
            self.spec_draft = refined_draft
            self.ai_issues = ai_issues
            self.refinement_iteration_count = 2 # Set counter to 2 for the *next* refinement

            # Populate the final split-screen review page
            self.ui.specDraftTextEdit.setText(self.spec_draft)
            self.ui.aiIssuesTextEdit.setText(self.ai_issues)
            self.ui.feedbackTextEdit.clear()

            # Switch to the final review page
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalReviewPage)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def _handle_refinement_result(self, new_draft):
        try:
            self.spec_draft = new_draft
            self.ui.specDraftTextEdit.setText(self.spec_draft)
            self.ui.aiIssuesTextEdit.setText("Draft has been refined. Please review the new version on the left.")
            self.ui.feedbackTextEdit.clear()
            QMessageBox.information(self, "Success", "Draft has been updated.")
            self.state_changed.emit()
            self.refinement_iteration_count += 1
        finally:
            self._set_ui_busy(False)

    def on_cancel_project_clicked(self):
        reply = QMessageBox.question(self, "Cancel Project",
                                     "Are you sure you want to cancel and archive this project?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            archive_name = f"{self.orchestrator.project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            archive_path_from_db = self.orchestrator.db_manager.get_config_value("DEFAULT_ARCHIVE_PATH")
            if not archive_path_from_db or not archive_path_from_db.strip():
                QMessageBox.warning(self, "Configuration Error", "The Default Project Archive Path is not set.")
                return
            self.orchestrator.stop_and_export_project(archive_path_from_db, archive_name)
            self.project_cancelled.emit()

    def on_approve_spec_clicked(self):
        final_spec = self.ui.specDraftTextEdit.toPlainText()
        self.orchestrator.finalize_and_save_app_spec(final_spec)
        QMessageBox.information(self, "Success", "Specification approved and saved.")
        self.orchestrator.is_project_dirty = True
        self.spec_elaboration_complete.emit()

    def _task_generate_and_analyze(self, input_data, **kwargs):
        """
        Saves the user's brief, generates the spec draft, analyzes it, and adds the standard header.
        """
        # --- Template Loading Logic ---
        template_content = None
        try:
            template_record = self.orchestrator.db_manager.get_template_by_name("Default Application Specification")
            if template_record:
                template_path = Path(template_record['file_path'])
                if template_path.exists():
                    template_content = template_path.read_text(encoding='utf-8')
                    logging.info("Found and loaded 'Default Application Specification' template.")
        except Exception as e:
            logging.warning(f"Could not load default application spec template: {e}")
        # --- End Template Loading ---

        if isinstance(input_data, list):
            # This part handles file uploads
            self.orchestrator.save_uploaded_brief_files(input_data)
            bootstrap_agent = ProjectBootstrapAgent(self.orchestrator.db_manager)
            initial_text, _, error = bootstrap_agent.extract_text_from_file_paths(input_data)
            if error: raise Exception(error)
        else:
            # This part handles text input
            initial_text = input_data
            self.orchestrator.save_text_brief_as_file(initial_text)

        if not initial_text or not initial_text.strip():
            raise Exception("No text could be extracted from the provided input.")

        # The agent generates the raw content of the specification
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        spec_draft_content = spec_agent.expand_brief_description(initial_text, template_content=template_content)

        # The scoping agent analyzes the raw content
        scoping_agent = ProjectScopingAgent(self.orchestrator.llm_service)
        analysis_result = scoping_agent.analyze_complexity(spec_draft_content)
        if "error" in analysis_result:
            raise Exception(f"Failed to analyze project complexity: {analysis_result.get('details')}")

        analysis_json_str = json.dumps(analysis_result)
        self.orchestrator.finalize_and_save_complexity_assessment(analysis_json_str)

        # CRUCIAL STEP: Add the header to the raw draft before returning it to the UI
        full_spec_draft = self.orchestrator.prepend_standard_header(spec_draft_content, "Application Specification")

        return analysis_result, full_spec_draft

    def _task_refine_spec(self, current_draft, feedback, **kwargs):
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)

        # Get the refined content from the agent
        refined_draft = spec_agent.refine_specification(current_draft, self.ai_issues, feedback)

        # Reliably update the date in the header using Python
        current_date = datetime.now().strftime('%x')
        # This MORE ROBUST regex finds the "Date: " line and replaces the rest of the line
        date_updated_draft = re.sub(
            r"(Date: ).*",
            r"\g<1>" + current_date,
            refined_draft
        )

        return date_updated_draft