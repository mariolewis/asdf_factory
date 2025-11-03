# gui/tech_spec_page.py

import re
from datetime import datetime
from pathlib import Path
import logging
import html
from gui.utils import render_markdown_to_html
import warnings
import json
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_tech_spec_page import Ui_TechSpecPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator, FactoryPhase
from agents.agent_tech_stack_proposal import TechStackProposalAgent
from agents.agent_project_bootstrap import ProjectBootstrapAgent

class TechSpecPage(QWidget):
    """
    The logic handler for the Technical Specification page.
    """
    state_changed = Signal()
    tech_spec_complete = Signal()
    project_cancelled = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_TechSpecPage()
        self.ui.setupUi(self)
        self.threadpool = QThreadPool()

        self.tech_spec_draft = ""
        self.selected_files = []
        self.ai_analysis = ""
        self.refinement_iteration_count = 1
        self.review_is_error_state = False
        self.last_failed_action = None # 'generation', 'guidelines', or 'refinement'
        self.retry_count = 0

        self.connect_signals()
        self.ui.pauseProjectButton.setVisible(False)

    def prepare_for_display(self):
        """Prepares the page based on the orchestrator's current phase."""
        current_phase = self.orchestrator.current_phase
        logging.debug(f"TechSpecPage preparing for display in phase: {current_phase.name}")

        if current_phase == FactoryPhase.TECHNICAL_SPECIFICATION:
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
            self.refinement_iteration_count = 1 # Reset counter

        elif current_phase == FactoryPhase.AWAITING_TECH_SPEC_RECTIFICATION:
            task_data = self.orchestrator.task_awaiting_approval or {}
            self.tech_spec_draft = task_data.get("draft_spec_from_guidelines", "# Your guidelines will appear here.")
            self.ai_analysis = task_data.get("ai_analysis", "No analysis found.")

            self.ui.techSpecTextEdit.setHtml(render_markdown_to_html(self.tech_spec_draft))
            self.ui.aiAnalysisTextEdit.setHtml(render_markdown_to_html(self.ai_analysis))
            self.ui.feedbackTextEdit.clear()
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
            self.ui.reviewTabWidget.setCurrentIndex(1)

        elif self.orchestrator.active_spec_draft is not None:
            logging.info("Resuming tech spec with a saved draft.")
            self.tech_spec_draft = self.orchestrator.active_spec_draft
            self.orchestrator.set_active_spec_draft(None)
            self.ui.techSpecTextEdit.setHtml(markdown.markdown(self.tech_spec_draft, extensions=['fenced_code', 'extra']))
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting TechSpecPage for a new project.")
        self.tech_spec_draft = ""
        self.selected_files = []
        self.ai_analysis = ""
        self.refinement_iteration_count = 1
        self.review_is_error_state = False
        self.last_failed_action = None
        self.retry_count = 0

        # Block signals to prevent handlers from firing during programmatic clear
        self.ui.techSpecTextEdit.blockSignals(True)
        self.ui.feedbackTextEdit.blockSignals(True)
        self.ui.pmGuidelinesTextEdit.blockSignals(True)

        # Clear all UI inputs
        self.ui.techSpecTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.ui.pmGuidelinesTextEdit.clear()
        self.ui.uploadPathLineEdit.clear()

        # Re-enable signals
        self.ui.techSpecTextEdit.blockSignals(False)
        self.ui.feedbackTextEdit.blockSignals(False)
        self.ui.pmGuidelinesTextEdit.blockSignals(False)

        # Reset UI state
        self.ui.osComboBox.setCurrentIndex(0)
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
        self.ui.pauseProjectButton.setVisible(False)
        self.setEnabled(True)

    def connect_signals(self):
        self.ui.proposeStackButton.clicked.connect(self.on_propose_stack_clicked)
        self.ui.pmDefineButton.clicked.connect(self.on_pm_define_clicked)
        self.ui.browseFilesButton.clicked.connect(self.on_browse_files_clicked)
        self.ui.generateFromGuidelinesButton.clicked.connect(self.run_generate_from_guidelines_task)
        self.ui.generateProposalButton.clicked.connect(self.run_propose_stack_task)
        self.ui.refineButton.clicked.connect(self.run_refine_task)
        self.ui.approveButton.clicked.connect(self.on_approve_or_retry_clicked)
        self.ui.pauseProjectButton.clicked.connect(self.on_pause_project_clicked)
        self.ui.techSpecTextEdit.textChanged.connect(self.on_draft_changed)

    def on_approve_or_retry_clicked(self):
        if self.review_is_error_state:
            if self.last_failed_action == 'generation':
                self.run_propose_stack_task()
            elif self.last_failed_action == 'guidelines':
                self.run_generate_from_guidelines_task()
            elif self.last_failed_action == 'refinement':
                self.run_refine_task()
        else:
            self.on_approve_clicked()

    def on_pause_project_clicked(self):
        self.orchestrator.pause_project()
        self.project_cancelled.emit()

    def on_draft_changed(self):
        """Saves the current text content to the orchestrator's active draft variable."""
        draft_text = self.ui.techSpecTextEdit.toPlainText()
        if self.orchestrator:
            self.orchestrator.set_active_spec_draft(draft_text)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the main window and updates the status bar."""
        main_window = self.window()
        if not main_window:
            self.setEnabled(not is_busy)
            return

        main_window.setEnabled(not is_busy)
        if hasattr(main_window, 'statusBar'):
            if is_busy:
                self.ui.processingLabel.setText(message)
                self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
                main_window.statusBar().showMessage(message)
            else:
                main_window.statusBar().clearMessage()
                # Switch back to review page after processing is done.
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
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

    def on_propose_stack_clicked(self):
        """Switches to the OS selection view."""
        self.ui.stackedWidget.setCurrentWidget(self.ui.osSelectionPage)

    def on_pm_define_clicked(self):
        """Switches to the PM guidelines input view."""
        self.ui.stackedWidget.setCurrentWidget(self.ui.pmDefinePage)

    def on_browse_files_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Specification Documents", "", "Documents (*.txt *.md *.pdf *.docx)")
        if files:
            self.selected_files = files
            self.ui.uploadPathLineEdit.setText("; ".join(files))

    def run_propose_stack_task(self):
        """Runs the task to generate a tech spec without PM guidelines."""
        self.last_failed_action = 'generation'
        target_os = self.ui.osComboBox.currentText()
        self._execute_task(self._task_propose_stack, self._handle_generation_result, target_os, None,
                           status_message="Generating tech architecture proposal...")

    def run_generate_from_guidelines_task(self):
        """Validates PM guidelines and then generates the tech spec."""
        self.last_failed_action = 'guidelines'
        guidelines = self.ui.pmGuidelinesTextEdit.toPlainText().strip()
        if not guidelines and not self.selected_files:
            QMessageBox.warning(self, "Input Required", "Please provide technology guidelines or upload a document.")
            return

        target_os = self.ui.osComboBox.currentText()
        self._execute_task(self._task_validate_and_generate, self._handle_validation_result, guidelines, self.selected_files, target_os,
                           status_message="Analyzing guidelines...")

    def run_refine_task(self):
        self.last_failed_action = 'refinement'
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback to refine the draft.")
            return

        current_draft = self.ui.techSpecTextEdit.toPlainText()
        ai_issues = self.ui.aiAnalysisTextEdit.toPlainText()
        target_os = self.ui.osComboBox.currentText()

        self._execute_task(self._task_refine_spec, self._handle_refinement_result, current_draft, feedback, target_os, self.refinement_iteration_count, ai_issues,
                         status_message="Refining technical specification...")

        self.refinement_iteration_count += 1

    def _handle_generation_result(self, result_tuple):
        try:
            tech_spec_draft, ai_analysis = result_tuple
            self.tech_spec_draft = tech_spec_draft
            self.ai_analysis = ai_analysis
            is_error = tech_spec_draft.strip().startswith("Error:") or tech_spec_draft.strip().startswith("### Error")

            if is_error:
                self.review_is_error_state = True
                self.retry_count += 1
                self.ui.techSpecTextEdit.setText(self.tech_spec_draft)
                if self.last_failed_action == 'generation':
                    self.ui.approveButton.setText("Retry Generation")
                else: # From guidelines
                    self.ui.approveButton.setText("Retry from Guidelines")

                if self.retry_count >= 2:
                    self.ui.pauseProjectButton.setVisible(True)
            else:
                self.review_is_error_state = False
                self.last_failed_action = None
                self.retry_count = 0
                self.ui.pauseProjectButton.setVisible(False)
                self.ui.techSpecTextEdit.setHtml(render_markdown_to_html(self.tech_spec_draft))
                self.ui.aiAnalysisTextEdit.setHtml(render_markdown_to_html(self.ai_analysis))
                self.ui.approveButton.setText("Approve Technical Specification")

            self.ui.feedbackTextEdit.clear()
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
            self.ui.reviewTabWidget.setCurrentIndex(0) # Ensure focus is on the draft
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def _handle_validation_result(self, result):
        """Handles the result of the validation task, routing to generation or refinement."""
        try:
            if isinstance(result, str):
                self._handle_generation_result(result)
            elif isinstance(result, dict) and "compatible" in result:
                user_guidelines = result.get("user_guidelines", "")
                recommendation = result.get("recommendation", "No recommendation provided.")
                self.orchestrator.handle_tech_spec_validation_failure(user_guidelines, recommendation)
                self.tech_spec_complete.emit()
        finally:
            self._set_ui_busy(False)

    def _handle_refinement_result(self, result_tuple):
        try:
            new_draft, new_analysis = result_tuple
            self.tech_spec_draft = new_draft
            self.ai_analysis = new_analysis
            is_error = new_draft.strip().startswith("Error:") or new_draft.strip().startswith("### Error")

            # Make the destination tab visible BEFORE setting content
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
            self.ui.reviewTabWidget.setCurrentIndex(0)

            if is_error:
                self.review_is_error_state = True
                self.last_failed_action = 'refinement'
                self.retry_count += 1
                self.ui.techSpecTextEdit.setText(self.tech_spec_draft)
                self.ui.approveButton.setText("Retry Refinement")
                if self.retry_count >= 2:
                    self.ui.pauseProjectButton.setVisible(True)
            else:
                self.review_is_error_state = False
                self.last_failed_action = None
                self.retry_count = 0
                self.ui.pauseProjectButton.setVisible(False)
                self.ui.techSpecTextEdit.setHtml(render_markdown_to_html(self.tech_spec_draft))
                self.ui.aiAnalysisTextEdit.setHtml(render_markdown_to_html(self.ai_analysis))
                self.ui.approveButton.setText("Approve Technical Specification")

            self.ui.feedbackTextEdit.clear()
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def on_approve_clicked(self):
        """Finalizes the tech spec."""
        final_tech_spec_markdown = self.ui.techSpecTextEdit.toMarkdown()
        final_tech_spec_plaintext = self.ui.techSpecTextEdit.toPlainText()

        if not final_tech_spec_plaintext.strip():
            QMessageBox.warning(self, "Approval Failed", "The technical specification cannot be empty.")
            return
        target_os = self.ui.osComboBox.currentText()

        # Pass both versions to the background task
        self._execute_task(self._task_approve_spec, self._handle_approval_result,
                           final_tech_spec_markdown, final_tech_spec_plaintext, target_os,
                           status_message="Finalizing tech spec and extracting primary technology...")

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

    def _task_approve_spec(self, final_spec_markdown, final_spec_plaintext, target_os, **kwargs):
        """Background worker task to save the tech spec."""
        self.orchestrator.finalize_and_save_tech_spec(final_spec_markdown, final_spec_plaintext, target_os)
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

    def _task_propose_stack(self, target_os, pm_guidelines, **kwargs):
        template_content = self._get_template_content("Default Technical Specification")
        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        final_spec_text = project_details['final_spec_text']
        if not final_spec_text:
            raise Exception("Could not retrieve the application specification.")

        agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)
        draft_content = agent.propose_stack(final_spec_text, target_os, template_content=template_content, pm_guidelines=pm_guidelines)
        full_draft = self.orchestrator.prepend_standard_header(draft_content, "Technical Specification")

        # Now, immediately analyze the new draft
        ai_analysis = agent.analyze_draft(full_draft, iteration_count=1, previous_analysis="")
        return full_draft, ai_analysis

    def _task_validate_and_generate(self, guidelines, uploaded_files, target_os, **kwargs):
        """Background task for the full PM-led workflow."""
        full_guidelines = guidelines
        if uploaded_files:
            bootstrap_agent = ProjectBootstrapAgent(self.orchestrator.db_manager)
            text_from_files, _, error = bootstrap_agent.extract_text_from_file_paths(uploaded_files)
            if error:
                raise Exception(f"Failed to process uploaded files: {error}")
            full_guidelines += "\n\n--- Content from Uploaded Documents ---\n" + text_from_files

        if not full_guidelines.strip():
            raise Exception("No guidelines were provided in the text box or extracted from files.")

        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        final_spec_text = project_details['final_spec_text']
        agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)
        validation_result = agent.validate_guidelines(full_guidelines, final_spec_text)

        if validation_result.get("compatible"):
            # This now calls the original generation logic and then immediately runs analysis.
            agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)
            db = self.orchestrator.db_manager
            project_details = db.get_project_by_id(self.orchestrator.project_id)
            final_spec_text = project_details['final_spec_text']
            template_content = self._get_template_content("Default Technical Specification")

            draft_content = agent.propose_stack(final_spec_text, target_os, template_content=template_content, pm_guidelines=full_guidelines)
            full_draft = self.orchestrator.prepend_standard_header(draft_content, "Technical Specification")

            ai_analysis = agent.analyze_draft(full_draft, iteration_count=1, previous_analysis="")
            return full_draft, ai_analysis
        else:
            validation_result["user_guidelines"] = full_guidelines
            return validation_result

    def _task_refine_spec(self, current_draft, feedback, target_os, iteration_count, ai_issues, **kwargs):
        """Background worker task that calls the orchestrator to handle the full refinement loop."""
        template_content = self._get_template_content("Default Technical Specification")
        self.orchestrator.handle_tech_spec_refinement(current_draft, feedback, target_os, iteration_count, ai_issues, template_content=template_content)

        # Retrieve the results that the orchestrator just prepared
        task_data = self.orchestrator.task_awaiting_approval or {}
        new_draft = task_data.get("draft_spec_from_guidelines", "Error: Draft not found.")
        new_analysis = task_data.get("ai_analysis", "Error: Analysis not found.")
        return new_draft, new_analysis