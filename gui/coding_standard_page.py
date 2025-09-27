# gui/coding_standard_page.py

import logging
import markdown
import warnings
import html
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QListWidgetItem
from PySide6.QtCore import Signal, QThreadPool
from pathlib import Path

from gui.ui_coding_standard_page import Ui_CodingStandardPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_project_bootstrap import ProjectBootstrapAgent
from agents.agent_coding_standard_app_target import CodingStandardAgent_AppTarget

class CodingStandardPage(QWidget):
    state_changed = Signal()
    coding_standard_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.coding_standard_draft = ""
        self.selected_files = []
        self.current_technology = ""
        self.tech_status = {}
        self.review_is_error_state = False
        self.last_failed_action = None # Will be 'generation' or 'refinement'

        self.ui = Ui_CodingStandardPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()
        self.ui.reviewTabWidget.setTabVisible(1, False)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.aiProposedButton.clicked.connect(self.on_ai_proposed_clicked)
        self.ui.pmGuidedButton.clicked.connect(self.on_pm_guided_clicked)
        self.ui.browseFilesButton.clicked.connect(self.on_browse_files_clicked)
        self.ui.generateFromGuidelinesButton.clicked.connect(self.run_generate_from_guidelines_task)
        self.ui.cancelButton_1.clicked.connect(self.on_cancel_clicked)
        self.ui.refineButton.clicked.connect(self.run_refinement_task)
        self.ui.approveButton.clicked.connect(self.on_approve_or_retry_clicked) # Single, stable handler
        self.ui.cancelButton_2.clicked.connect(self.on_cancel_clicked)
        self.ui.standardTextEdit.textChanged.connect(self.on_draft_changed)

    def on_approve_or_retry_clicked(self):
        """
        Handles the primary action on the review page. Either approves the draft
        or retries the last failed action based on the current state.
        """
        if self.review_is_error_state:
            if self.last_failed_action == 'generation':
                self.run_generation_task()
            elif self.last_failed_action == 'refinement':
                self.run_refinement_task()
        else:
            self.on_approve_clicked()

    def _handle_generation_result(self, standard_draft):
        """Handles the result from the generation worker, reconfiguring the UI on success or failure."""
        try:
            self.coding_standard_draft = standard_draft
            self.ui.reviewHeaderLabel.setText(f"Review Coding Standard for {self.current_technology}")

            is_error = standard_draft.strip().startswith("Error:") or standard_draft.strip().startswith("### Error")

            if is_error:
                self.review_is_error_state = True
                self.last_failed_action = 'generation'
                self.ui.standardTextEdit.setText(standard_draft)
                self.ui.approveButton.setText("Retry Generation")
            else:
                self.review_is_error_state = False
                self.last_failed_action = None
                self.ui.standardTextEdit.setHtml(markdown.markdown(self.coding_standard_draft, extensions=['fenced_code', 'extra']))
                self.ui.approveButton.setText("Approve Standard")

            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def _handle_refinement_result(self, new_draft):
        """Handles the result from the refinement worker, reconfiguring the UI on success or failure."""
        try:
            self.coding_standard_draft = new_draft
            is_error = new_draft.strip().startswith("Error:") or new_draft.strip().startswith("### Error")

            if is_error:
                self.review_is_error_state = True
                self.last_failed_action = 'refinement'
                self.ui.standardTextEdit.setText(new_draft) # Show error in the main window
                self.ui.approveButton.setText("Retry Refinement")
            else:
                self.review_is_error_state = False
                self.last_failed_action = None
                self.ui.standardTextEdit.setHtml(markdown.markdown(html.unescape(self.coding_standard_draft), extensions=['fenced_code', 'extra']))
                self.ui.feedbackTextEdit.clear()
                self.ui.reviewTabWidget.setCurrentIndex(0)
                self.ui.approveButton.setText("Approve Standard")

            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)

    # (All other methods remain the same as the last full version I provided)
    # ... copy the rest of the methods from my response that started with "Step 11b of 11" ...
    def prepare_for_new_project(self):
        """Resets the page to its initial state."""
        logging.info("Resetting CodingStandardPage for a new project.")
        self.coding_standard_draft = ""
        self.selected_files = []
        self.current_technology = ""
        self.tech_status = {}
        self.review_is_error_state = False
        self.last_failed_action = None
        self.ui.techListWidget.clear()
        self.ui.pmGuidelinesTextEdit.clear()
        self.ui.uploadPathLineEdit.clear()
        self.ui.standardTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
        self.setEnabled(True)

    def prepare_for_display(self):
        """Prepares the page by detecting technologies and populating the list."""
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
        self.ui.techListWidget.clear()
        self.ui.techListWidget.addItem("Detecting technologies...")
        self.ui.aiProposedButton.setEnabled(False)
        self.ui.pmGuidedButton.setEnabled(False)
        self._execute_task(self._task_detect_tech, self._handle_tech_detection_result,
                           status_message="Detecting technologies from spec...")

    def _task_detect_tech(self, **kwargs):
        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        tech_spec_text = project_details['tech_spec_text'] if project_details else ""
        return self.orchestrator.detect_technologies_in_spec(tech_spec_text)

    def _handle_tech_detection_result(self, technologies):
        try:
            self.ui.techListWidget.clear()
            self.tech_status = {tech: "Pending" for tech in technologies}
            if not self.tech_status:
                self.ui.techListWidget.addItem("No specific technologies detected.")
                return

            self._update_tech_list_widget()
            self.ui.aiProposedButton.setEnabled(True)
            self.ui.pmGuidedButton.setEnabled(True)
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
        finally:
            self._set_ui_busy(False)

    def _update_tech_list_widget(self):
        self.ui.techListWidget.clear()
        for tech, status in self.tech_status.items():
            self.ui.techListWidget.addItem(f"{tech} [{status}]")

    def on_ai_proposed_clicked(self):
        selected_items = self.ui.techListWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a technology from the list first.")
            return

        self.current_technology = selected_items[0].text().split(" ")[0]
        if self.tech_status.get(self.current_technology) == "Completed":
            QMessageBox.information(self, "Already Completed", f"A standard for {self.current_technology} has already been completed.")
            return
        self.run_generation_task()

    def on_pm_guided_clicked(self):
        selected_items = self.ui.techListWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a technology from the list first.")
            return

        self.current_technology = selected_items[0].text().split(" ")[0]
        if self.tech_status.get(self.current_technology) == "Completed":
            QMessageBox.information(self, "Already Completed", f"A standard for {self.current_technology} has already been completed.")
            return

        self.ui.pmDefineHeaderLabel.setText(f"Define Guidelines for {self.current_technology}")
        self.ui.stackedWidget.setCurrentWidget(self.ui.pmDefinePage)

    def on_browse_files_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Guideline Documents", "", "Documents (*.txt *.md *.pdf *.docx)")
        if files:
            self.selected_files = files
            self.ui.uploadPathLineEdit.setText("; ".join(files))

    def on_cancel_clicked(self):
        """Returns to the tech list and clears the state of the aborted task."""
        self.coding_standard_draft = ""
        self.current_technology = ""
        self.review_is_error_state = False
        self.last_failed_action = None
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

    def on_draft_changed(self):
        draft_text = self.ui.standardTextEdit.toPlainText()
        if self.orchestrator:
            self.orchestrator.set_active_spec_draft(draft_text)

    def on_approve_clicked(self):
        """Finalizes the coding standard and transitions to the backlog gateway."""
        final_draft = self.ui.standardTextEdit.toPlainText()
        if not final_draft.strip():
            QMessageBox.warning(self, "Approval Failed", "The coding standard cannot be empty.")
            return

        self.orchestrator.finalize_and_save_coding_standard(final_draft, self.current_technology)
        self.tech_status[self.current_technology] = "Completed"
        self._update_tech_list_widget()

        if all(status == "Completed" for status in self.tech_status.values()):
            QMessageBox.information(self, "All Standards Complete", "All required coding standards have been generated. Proceeding to the Backlog Gateway.")
            self.coding_standard_complete.emit()
        else:
            QMessageBox.information(self, "Standard Approved", f"Coding standard for {self.current_technology} has been approved. Please select the next technology.")
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        main_window = self.window()
        if not main_window: return
        main_window.setEnabled(not is_busy)
        if hasattr(main_window, 'statusBar'):
            if is_busy:
                self.ui.processingLabel.setText(message)
                self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
                main_window.statusBar().showMessage(message)
            else:
                main_window.statusBar().clearMessage()

    def _execute_task(self, task_function, on_result, *args, status_message="Processing..."):
        self._set_ui_busy(True, status_message)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        try:
            QMessageBox.critical(self, "Error", f"An error occurred: {error_tuple[1]}")
        finally:
            self._set_ui_busy(False)
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

    def run_generation_task(self):
        """Initiates the background task to generate the coding standard."""
        self._execute_task(self._task_generate_standard, self._handle_generation_result,
                           status_message=f"Generating standard for {self.current_technology}...")

    def _task_generate_standard(self, **kwargs):
        """Background task that calls the orchestrator to generate the standard."""
        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        tech_spec_text = project_details['tech_spec_text']
        if not tech_spec_text: raise Exception("Technical Specification not found.")
        draft_content = self.orchestrator.generate_coding_standard(tech_spec_text, self.current_technology)
        full_draft = self.orchestrator.prepend_standard_header(draft_content, f"Coding Standard ({self.current_technology})")
        return full_draft

    def run_refinement_task(self):
        """Initiates the background task to refine the coding standard."""
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback for refinement.")
            return
        current_draft = self.ui.standardTextEdit.toPlainText()
        self._execute_task(self._task_refine_standard, self._handle_refinement_result, current_draft, feedback,
                           status_message=f"Refining standard for {self.current_technology}...")

    def _task_refine_standard(self, current_draft, feedback, **kwargs):
        """Background worker task that handles the refinement logic."""
        agent = CodingStandardAgent_AppTarget(llm_service=self.orchestrator.llm_service)
        pure_content = self.orchestrator._strip_header_from_document(current_draft)

        refined_content_from_agent = agent.refine_standard(pure_content, feedback)

        unescaped_content = html.unescape(refined_content_from_agent)

        clean_refined_body = self.orchestrator._strip_header_from_document(unescaped_content)

        final_draft = self.orchestrator.prepend_standard_header(clean_refined_body, f"Coding Standard ({self.current_technology})")
        return final_draft

    def run_generate_from_guidelines_task(self):
        guidelines = self.ui.pmGuidelinesTextEdit.toPlainText().strip()
        if not guidelines and not self.selected_files:
            QMessageBox.warning(self, "Input Required", "Please provide text guidelines or upload a document.")
            return
        self._execute_task(self._task_generate_from_guidelines, self._handle_generation_result, guidelines, self.selected_files,
                           status_message=f"Generating standard for {self.current_technology} from guidelines...")

    def _task_generate_from_guidelines(self, guidelines, uploaded_files, **kwargs):
        full_guidelines = guidelines
        if uploaded_files:
            bootstrap_agent = ProjectBootstrapAgent(self.orchestrator.db_manager)
            text_from_files, _, error = bootstrap_agent.extract_text_from_file_paths(uploaded_files)
            if error: raise Exception(f"Failed to process files: {error}")
            full_guidelines += "\n\n--- Content from Uploaded Documents ---\n" + text_from_files
        if not full_guidelines.strip(): raise Exception("No guidelines were provided or extracted.")

        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        tech_spec_text = project_details['tech_spec_text']

        draft_content = self.orchestrator.generate_standard_from_guidelines(tech_spec_text, full_guidelines)
        full_draft = self.orchestrator.prepend_standard_header(draft_content, f"Coding Standard ({self.current_technology})")
        return full_draft