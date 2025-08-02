# gui/spec_elaboration_page.py

import logging
import json
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_spec_elaboration_page import Ui_SpecElaborationPage
from gui.worker import Worker # Import the new Worker class
from master_orchestrator import MasterOrchestrator
from agents.agent_spec_clarification import SpecClarificationAgent
from agents.agent_project_bootstrap import ProjectBootstrapAgent
from agents.agent_project_scoping import ProjectScopingAgent

class SpecElaborationPage(QWidget):
    spec_elaboration_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.spec_draft = None
        self.selected_files = []
        self.ai_issues = ""

        self.ui = Ui_SpecElaborationPage()
        self.ui.setupUi(self)

        # Initialize a thread pool for running background tasks
        self.threadpool = QThreadPool()
        logging.info(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads.")

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
        self.ui.processTextButton.clicked.connect(self.run_process_brief_task)
        self.ui.browseFilesButton.clicked.connect(self.on_browse_files_clicked)
        self.ui.processFilesButton.clicked.connect(self.run_process_files_task)
        self.ui.confirmAnalysisButton.clicked.connect(self.run_ai_analysis_task)
        self.ui.submitFeedbackButton.clicked.connect(self.run_refinement_task)
        self.ui.approveSpecButton.clicked.connect(self.on_approve_spec_clicked)

    def _set_ui_busy(self, is_busy):
        """Disables or enables the entire page to prevent concurrent actions."""
        self.setEnabled(not is_busy)
        # We will add a status bar message here later
        if is_busy:
            logging.info("UI is busy, waiting for background task...")
        else:
            logging.info("Background task finished, UI is enabled.")

    # --- Worker Execution ---

    def _execute_task(self, task_function, on_result, *args):
        """Generic method to run a task in the background."""
        self._set_ui_busy(True)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        worker.signals.finished.connect(lambda: self._set_ui_busy(False))
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        """Handles errors emitted from the worker thread."""
        error_msg = f"An error occurred in a background task:\n{error_tuple[2]}"
        logging.error(error_msg)
        QMessageBox.critical(self, "Error", error_msg)

    # --- Task Handlers (Initiate Background Work) ---

    def on_browse_files_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Specification Documents", "", "Documents (*.txt *.md *.pdf *.docx)")
        if files:
            self.selected_files = files
            self.ui.uploadPathLineEdit.setText("; ".join(self.selected_files))

    def run_process_files_task(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Input Required", "Please browse for at least one specification document.")
            return
        self._execute_task(self._task_process_files, self._handle_draft_result, self.selected_files)

    def run_process_brief_task(self):
        brief_desc = self.ui.briefDescriptionTextEdit.toPlainText().strip()
        if not brief_desc:
            QMessageBox.warning(self, "Input Required", "Please enter a brief description.")
            return
        self._execute_task(self._task_process_brief, self._handle_draft_result, brief_desc)

    def run_ai_analysis_task(self):
        self._execute_task(self._task_run_ai_analysis, self._handle_ai_analysis_result)

    def run_refinement_task(self):
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback or clarifications.")
            return
        self._execute_task(self._task_refine_spec, self._handle_refinement_result, feedback)

    # --- Result Handlers (Slots for Worker Signals) ---

    def _handle_draft_result(self, spec_draft):
        self.spec_draft = spec_draft
        self._run_analysis_and_show_review(self.spec_draft)

    def _handle_ai_analysis_result(self, ai_issues):
        self.ai_issues = ai_issues
        self.ui.specDraftTextEdit.setText(self.spec_draft)
        self.ui.aiIssuesTextEdit.setText(self.ai_issues)
        self.ui.feedbackTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.finalReviewPage)

    def _handle_refinement_result(self, new_draft):
        self.spec_draft = new_draft
        self.ui.specDraftTextEdit.setText(self.spec_draft)
        self.ui.aiIssuesTextEdit.setText("Draft has been refined. Please review the new version on the left.")
        self.ui.feedbackTextEdit.clear()
        QMessageBox.information(self, "Success", "Draft has been updated.")

    def on_approve_spec_clicked(self):
        final_spec = self.ui.specDraftTextEdit.toPlainText()
        self.orchestrator.finalize_and_save_app_spec(final_spec)
        QMessageBox.information(self, "Success", "Specification approved and saved.")
        self.spec_elaboration_complete.emit()

    # --- Backend Logic (to be run in worker threads) ---

    def _task_process_files(self, file_paths):
        bootstrap_agent = ProjectBootstrapAgent(self.orchestrator.db_manager)
        extracted_text, _, error = bootstrap_agent.extract_text_from_file_paths(file_paths)
        if error:
            raise Exception(error)

        if extracted_text and extracted_text.strip():
            spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
            return spec_agent.expand_brief_description(extracted_text)
        return None

    def _task_process_brief(self, brief_desc):
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        return spec_agent.expand_brief_description(brief_desc)

    def _run_analysis_and_show_review(self, spec_text: str):
        if not spec_text or not spec_text.strip():
            QMessageBox.warning(self, "Processing Error", "Could not create a draft from the provided input.")
            self._set_ui_busy(False)
            return

        self.spec_draft = spec_text
        scoping_agent = ProjectScopingAgent(self.orchestrator.llm_service)
        analysis_result = scoping_agent.analyze_complexity(self.spec_draft)

        if "error" in analysis_result:
            raise Exception(f"Failed to analyze project complexity: {analysis_result.get('details')}")

        analysis_for_display = json.dumps(analysis_result, indent=4)
        footnote_text = "\n\nNote: This assessment is a point-in-time analysis."
        self.ui.analysisResultTextEdit.setText(analysis_for_display + footnote_text)
        self.ui.stackedWidget.setCurrentWidget(self.ui.complexityReviewPage)

    def _task_run_ai_analysis(self):
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        return spec_agent.identify_potential_issues(self.spec_draft)

    def _task_refine_spec(self, feedback):
        spec_agent = SpecClarificationAgent(self.orchestrator.llm_service, self.orchestrator.db_manager)
        return spec_agent.refine_specification(self.spec_draft, self.ai_issues, feedback)