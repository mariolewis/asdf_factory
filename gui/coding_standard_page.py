# gui/coding_standard_page.py

import logging
import warnings
import json
from gui.utils import render_markdown_to_html
import re
from pathlib import Path
import html
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QListWidgetItem
from PySide6.QtCore import Signal, QThreadPool, QTimer
from PySide6.QtGui import QColor
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
        self.ui.skipStandardButton.clicked.connect(self.on_skip_tech_clicked)
        self.ui.techListWidget.itemSelectionChanged.connect(self._on_tech_selection_changed)

    def on_skip_tech_clicked(self):
        """Skips the selected technology."""
        if not self.current_technology:
            return

        logging.info(f"PM skipped coding standard generation for: {self.current_technology}")

        try:
            # We must call the orchestrator to create a "skipped" artifact
            # This ensures the system knows this tech is "handled"
            self.orchestrator.finalize_and_save_coding_standard(
                self.current_technology,
                "# This technology was skipped by the Product Manager.",
                "SKIPPED" # A new status to show it was skipped
            )

            # This logic now ONLY runs if the 'try' block succeeds
            self.tech_status[self.current_technology] = "Completed"
            self._update_tech_list_widget()
            self._on_tech_selection_changed()

            # The 'if all' check is now safe.
            if all(status == "Completed" for status in self.tech_status.values()):
                logging.info("All coding standards (or skips) are complete. Proceeding to next phase.")
                self.coding_standard_complete.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save skipped status: {e}")
            logging.error(f"Failed to save skipped artifact for {self.current_technology}", exc_info=True)


    def _on_tech_selection_changed(self):
        """Enables buttons only if a 'Pending' item is selected."""
        selected_items = self.ui.techListWidget.selectedItems()
        if not selected_items:
            self.ui.aiProposedButton.setEnabled(False)
            self.ui.pmGuidedButton.setEnabled(False)
            self.ui.skipStandardButton.setEnabled(False)
            return

        selected_text = selected_items[0].text()
        self.current_technology = selected_text.split(" ")[0]

        if self.tech_status.get(self.current_technology) == "Pending":
            self.ui.aiProposedButton.setEnabled(True)
            self.ui.pmGuidedButton.setEnabled(True)
            self.ui.skipStandardButton.setEnabled(True)
        else:
            self.ui.aiProposedButton.setEnabled(False)
            self.ui.pmGuidedButton.setEnabled(False)
            self.ui.skipStandardButton.setEnabled(False)

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
                self.ui.standardTextEdit.setHtml(render_markdown_to_html(self.coding_standard_draft))
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
                self.ui.standardTextEdit.setHtml(render_markdown_to_html(self.coding_standard_draft))
                self.ui.feedbackTextEdit.clear()
                self.ui.reviewTabWidget.setCurrentIndex(0)
                self.ui.approveButton.setText("Approve Standard")

            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)

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
        """Prepares the page by reading the pre-populated technologies list."""
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
        self.ui.techListWidget.clear()
        self.ui.aiProposedButton.setEnabled(False)
        self.ui.pmGuidedButton.setEnabled(False)

        try:
            db = self.orchestrator.db_manager
            project_details_row = db.get_project_by_id(self.orchestrator.project_id)
            project_details = dict(project_details_row) if project_details_row else None
            technologies_json = project_details.get('detected_technologies') if project_details else None

            if technologies_json:
                technologies = json.loads(technologies_json)
                logging.info(f"Found pre-populated technologies list: {technologies}")
                # This is a synchronous call, no worker needed
                self._handle_tech_detection_result(technologies)
            else:
                # This is now an error state, it should have been populated
                logging.error("Coding standard page loaded, but no technologies were found in the database.")
                QMessageBox.critical(self, "Error", "Could not find detected technologies. Please check the logs.")
                self.ui.techListWidget.addItem("Error: No technologies found.")

        except Exception as e:
            logging.error(f"Error in prepare_for_display: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to prepare page: {e}")

    def _task_detect_tech(self, **kwargs):
        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        tech_spec_text = project_details['tech_spec_text'] if project_details else ""
        return self.orchestrator.detect_technologies_in_spec(tech_spec_text)

    def _handle_tech_detection_result(self, technologies):
        """Populates the tech list, checking for already completed artifacts."""
        try:
            self.ui.techListWidget.clear()

            # --- NEW: Check database for existing artifacts ---
            db = self.orchestrator.db_manager
            all_artifacts = db.get_all_artifacts_for_project(self.orchestrator.project_id)
            completed_techs = set()
            for art in all_artifacts:
                art_dict = dict(art) # Convert from sqlite3.Row
                if art_dict['artifact_type'] == 'CODING_STANDARD' and art_dict['status'] in ('COMPLETED', 'SKIPPED'):
                    # Extract language from name, e.g., "Coding Standard (Python)"
                    match = re.search(r'\((.*?)\)', art_dict['artifact_name'])
                    if match:
                        completed_techs.add(match.group(1))

            logging.info(f"Found existing completed standards for: {completed_techs}")

            # --- MODIFIED: Build tech_status based on database ---
            self.tech_status = {}
            for tech in technologies:
                if tech in completed_techs:
                    self.tech_status[tech] = "Completed"
                else:
                    self.tech_status[tech] = "Pending"
            # --- END MODIFIED LOGIC ---

            if not self.tech_status:
                self.ui.techListWidget.addItem("No specific technologies detected.")
                return

            self._update_tech_list_widget()
            # Buttons are now disabled by default.
            self.ui.aiProposedButton.setEnabled(False)
            self.ui.pmGuidedButton.setEnabled(False)
            self.ui.skipStandardButton.setEnabled(False)
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
            # --- BEGIN FIX ---
            # Check for completion *after* populating the list from the DB
            if self.tech_status and all(status == "Completed" for status in self.tech_status.values()):
                logging.info("All coding standards are already complete. Emitting completion signal automatically.")
                # Use QTimer.singleShot to allow the UI to finish rendering before transitioning
                QTimer.singleShot(0, self.coding_standard_complete.emit)
            # --- END FIX ---
        finally:
            self._set_ui_busy(False)

    def _update_tech_list_widget(self):
        self.ui.techListWidget.clear()
        for tech, status in self.tech_status.items():
            self.ui.techListWidget.addItem(f"{tech} [{status}]")

    def on_ai_proposed_clicked(self):
        """Handles AI proposal for the selected technology."""
        if not self.current_technology: # Should not happen, but a good safeguard
            QMessageBox.warning(self, "No Selection", "Please select a technology from the list first.")
            return
        self.run_generation_task()

    def on_pm_guided_clicked(self):
        """Switches to the PM guidelines page for the selected technology."""
        if not self.current_technology: # Should not happen, but a good safeguard
            QMessageBox.warning(self, "No Selection", "Please select a technology from the list first.")
            return

        self.ui.pmDefineHeaderLabel.setText(f"Define Guidelines for {self.current_technology} Coding Standard")
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
        self.ui.techListWidget.clearSelection()

    def on_draft_changed(self):
        draft_text = self.ui.standardTextEdit.toPlainText()
        if self.orchestrator:
            self.orchestrator.set_active_spec_draft(draft_text)

    def on_approve_clicked(self):
        """Finalizes the coding standard."""
        try:
            db = self.orchestrator.db_manager
            project_details = db.get_project_by_id(self.orchestrator.project_id)
            project_name = project_details['project_name']

            full_draft_with_header = self.orchestrator.prepend_standard_header(
                self.coding_standard_draft,
                f"Coding Standard ({self.current_technology})"
            )

            # This call saves the artifact and updates the DB
            self.orchestrator.finalize_and_save_coding_standard(
                self.current_technology,
                full_draft_with_header, # Pass the full content
                "COMPLETED"
            )

            self.tech_status[self.current_technology] = "Completed"
            self._update_tech_list_widget()
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

            # Check if all techs are now complete
            if all(status == "Completed" for status in self.tech_status.values()):
                logging.info("All coding standards (or skips) are complete. Proceeding to next phase.")
                self.coding_standard_complete.emit()
            else:
                logging.info(f"Coding standard for {self.current_technology} complete. Returning to list.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save coding standard:\n{e}")
        finally:
            self._set_ui_busy(False)

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
        current_draft = self.coding_standard_draft
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

        draft_content = self.orchestrator.generate_standard_from_guidelines(tech_spec_text, full_guidelines, self.current_technology)
        full_draft = self.orchestrator.prepend_standard_header(draft_content, f"Coding Standard ({self.current_technology})")
        return full_draft