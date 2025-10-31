# gui/build_script_page.py

import logging
import json
import markdown
import html
import warnings
from pathlib import Path
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QListWidgetItem
from PySide6.QtCore import Signal, QThreadPool, Qt, QTimer
from PySide6.QtGui import QColor

from gui.ui_build_script_page import Ui_BuildScriptPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_build_script_generator import BuildScriptGeneratorAgent
from agents.agent_project_bootstrap import ProjectBootstrapAgent

class BuildScriptPage(QWidget):
    """
    The logic handler for the Build Script Generation page.
    This page now manages a multi-technology build script workflow.
    """
    state_changed = Signal()
    build_script_setup_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.build_script_draft = ""
        self.selected_files = []
        self.current_technology = ""
        self.tech_status = {} # Holds "Pending" or "Completed"
        self.review_is_error_state = False
        self.last_failed_action = None # 'generation' or 'guidelines'
        self.script_filename = ""
        self.script_content = ""
        self.build_script_not_required = [
            "Shell Script", "Bash", "PowerShell", "cmd",
            "SQL", "JSON", "Markdown", "HTML", "CSS"
        ]

        self.ui = Ui_BuildScriptPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()
        self.ui.reviewTabWidget.setTabVisible(1, False) # Hide AI Analysis
        self.ui.reviewTabWidget.setTabVisible(2, False) # Hide Feedback
        self.ui.refineButton.setVisible(False) # Hide refine button

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.aiProposedButton.clicked.connect(self.on_ai_proposed_clicked)
        self.ui.pmGuidedButton.clicked.connect(self.on_pm_guided_clicked)
        self.ui.browseFilesButton.clicked.connect(self.on_browse_files_clicked)
        self.ui.generateFromGuidelinesButton.clicked.connect(self.run_generate_from_guidelines_task)
        self.ui.cancelButton_1.clicked.connect(self.on_cancel_clicked)
        self.ui.approveButton.clicked.connect(self.on_approve_or_retry_clicked)
        self.ui.cancelButton_2.clicked.connect(self.on_cancel_clicked)
        self.ui.techListWidget.itemSelectionChanged.connect(self._on_tech_selection_changed)
        self.ui.skipTechButton.clicked.connect(self.on_skip_tech_clicked)

    def on_approve_or_retry_clicked(self):
        """Handles the main action on the review page (Approve or Retry)."""
        if self.review_is_error_state:
            if self.last_failed_action == 'generation':
                self.run_generation_task()
            elif self.last_failed_action == 'guidelines':
                self.run_generate_from_guidelines_task()
        else:
            self.on_approve_clicked()

    def prepare_for_display(self):
        """Prepares the page by reading the pre-populated technologies list."""
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
        self.ui.techListWidget.clear()
        self.ui.aiProposedButton.setEnabled(False)
        self.ui.pmGuidedButton.setEnabled(False)
        self.ui.skipTechButton.setEnabled(False)

        try:
            db = self.orchestrator.db_manager
            project_details_row = db.get_project_by_id(self.orchestrator.project_id)
            project_details = dict(project_details_row) if project_details_row else None
            technologies_json = project_details.get('detected_technologies') if project_details else None

            if technologies_json:
                all_techs = json.loads(technologies_json)
                # Filter out techs that don't need build scripts
                required_techs = [tech for tech in all_techs if tech not in self.build_script_not_required]
                logging.info(f"Found {len(required_techs)} techs requiring build scripts: {required_techs}")
                # Call the handler directly, no task needed
                self._handle_tech_detection_result(required_techs)
            else:
                logging.error("Build script page loaded, but no technologies were found in the database.")
                QMessageBox.critical(self, "Error", "Could not find detected technologies. Please check the logs.")
                self.ui.techListWidget.addItem("Error: No technologies found.")

        except Exception as e:
            logging.error(f"Error in prepare_for_display: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to prepare page: {e}")

    def _handle_tech_detection_result(self, technologies):
        """Populates the tech list widget with filtered technologies."""
        try:
            self.ui.techListWidget.clear()
            self.tech_status = {tech: "Pending" for tech in technologies}

            if not self.tech_status:
                logging.info("No technologies require a build script. Skipping this phase.")
                # All "required" techs are done (i.e., zero of them)
                QTimer.singleShot(0, self.build_script_setup_complete.emit)
                return

            self._update_tech_list_widget()
            self.ui.aiProposedButton.setEnabled(False)
            self.ui.pmGuidedButton.setEnabled(False)
        finally:
            self._set_ui_busy(False)

    def _update_tech_list_widget(self):
        """Updates the list widget items with their current status."""
        self.ui.techListWidget.clear()
        for tech, status in self.tech_status.items():
            item = QListWidgetItem(f"{tech} [{status}]")
            if status == "Completed":
                item.setForeground(QColor("#888888")) # Muted Text
            self.ui.techListWidget.addItem(item)

    def _on_tech_selection_changed(self):
        """Enables buttons only if a 'Pending' item is selected."""
        selected_items = self.ui.techListWidget.selectedItems()
        if not selected_items:
            self.ui.aiProposedButton.setEnabled(False)
            self.ui.pmGuidedButton.setEnabled(False)
            self.ui.skipTechButton.setEnabled(False)
            return

        selected_text = selected_items[0].text()
        self.current_technology = selected_text.split(" ")[0]

        if self.tech_status.get(self.current_technology) == "Pending":
            self.ui.aiProposedButton.setEnabled(True)
            self.ui.pmGuidedButton.setEnabled(True)
            self.ui.skipTechButton.setEnabled(True)
        else:
            self.ui.aiProposedButton.setEnabled(False)
            self.ui.pmGuidedButton.setEnabled(False)
            self.ui.skipTechButton.setEnabled(False)

    def prepare_for_new_project(self):
        """Resets the page to its initial state."""
        logging.info("Resetting BuildScriptPage for a new project.")
        self.build_script_draft = ""
        self.selected_files = []
        self.current_technology = ""
        self.tech_status = {}
        self.review_is_error_state = False
        self.last_failed_action = None
        self.script_filename = ""
        self.script_content = ""

        self.ui.techListWidget.clear()
        self.ui.pmGuidelinesTextEdit.clear()
        self.ui.uploadPathLineEdit.clear()
        self.ui.standardTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
        self.setEnabled(True)

    def on_ai_proposed_clicked(self):
        """Handles AI proposal for the selected technology."""
        if not self.current_technology: return
        self.run_generation_task()

    def on_pm_guided_clicked(self):
        """Switches to the PM guidelines page for the selected technology."""
        if not self.current_technology: return
        self.ui.pmDefineHeaderLabel.setText(f"Define Guidelines for {self.current_technology} Build Script")
        self.ui.pmGuidelinesTextEdit.setPlaceholderText(f"Enter the full, desired build script content for {self.current_technology} (e.g., paste your requirements.txt or package.json here).")
        self.ui.stackedWidget.setCurrentWidget(self.ui.pmDefinePage)

    def on_browse_files_clicked(self):
        """Allows user to select build script files."""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Build Script File(s)", "", "All Files (*)")
        if files:
            self.selected_files = files
            self.ui.uploadPathLineEdit.setText("; ".join(files))

    def on_cancel_clicked(self):
        """Returns to the technology list page."""
        self.build_script_draft = ""
        self.current_technology = ""
        self.review_is_error_state = False
        self.last_failed_action = None
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)
        self._on_tech_selection_changed() # Reset button states

    def on_skip_tech_clicked(self):
        """Skips the selected technology."""
        if not self.current_technology:
            return

        logging.info(f"PM skipped build script generation for: {self.current_technology}")
        self.tech_status[self.current_technology] = "Completed"
        self._update_tech_list_widget()
        self._on_tech_selection_changed() # This will disable the buttons

        # Check if all techs are now complete
        if all(status == "Completed" for status in self.tech_status.values()):
            logging.info("All build scripts (or skips) are complete. Proceeding to Dockerization.")
            # We must still call the orchestrator's finalize method
            self.orchestrator.finalize_build_script()
            self.build_script_setup_complete.emit()

    def on_approve_clicked(self):
        """Finalizes the build script and checks if all techs are done."""
        try:
            self.script_content = self.ui.standardTextEdit.toPlainText()

            db = self.orchestrator.db_manager
            project_details = db.get_project_by_id(self.orchestrator.project_id)
            project_root = Path(project_details['project_root_folder'])

            (project_root / self.script_filename).write_text(self.script_content, encoding='utf-8')

            # Update the main build_script_file_name field
            # This is imperfect for multi-tech, but we'll set it to the *last* one.
            db.update_project_field(self.orchestrator.project_id, "build_script_file_name", self.script_filename)
            # We set this flag to true since we generated at least one.
            db.update_project_field(self.orchestrator.project_id, "is_build_automated", 1)

            QMessageBox.information(self, "Success", f"Success: Generated and saved '{self.script_filename}' to the project root.")
            self.orchestrator.is_project_dirty = True

            # Update status and check for completion
            self.tech_status[self.current_technology] = "Completed"
            self._update_tech_list_widget()

            if all(status == "Completed" for status in self.tech_status.values()):
                logging.info("All build scripts generated. Proceeding to Dockerization.")
                self.orchestrator.finalize_build_script() # This just sets the next phase
                self.build_script_setup_complete.emit()
            else:
                logging.info(f"Build script for {self.current_technology} complete. Returning to list.")
                self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save build script:\n{e}")
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
                if hasattr(main_window, 'show_persistent_status'):
                    main_window.show_persistent_status(message)
                else:
                    main_window.statusBar().showMessage(message)
            else:
                if hasattr(main_window, 'clear_persistent_status'):
                    main_window.clear_persistent_status()
                else:
                    main_window.statusBar().clearMessage()

    def _execute_task(self, task_function, on_result, *args, status_message="Processing..."):
        self._set_ui_busy(True, status_message)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        # This lambda ensures _set_ui_busy(False) is called *after* result/error handlers
        worker.signals.finished.connect(lambda: self._set_ui_busy(False))
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        try:
            QMessageBox.critical(self, "Error", f"An error occurred: {error_tuple[1]}")
        finally:
            # self._set_ui_busy(False) # Handled by 'finished' signal
            self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

    def run_generation_task(self):
        """Initiates AI generation for the build script."""
        self.last_failed_action = 'generation'
        self._execute_task(self._task_auto_generate, self._handle_generation_result,
                           status_message=f"Generating build script for {self.current_technology}...")

    def _task_auto_generate(self, **kwargs):
        """Background task that calls the build script agent."""
        db = self.orchestrator.db_manager
        project_details_row = db.get_project_by_id(self.orchestrator.project_id)
        project_details = dict(project_details_row) if project_details_row else {}
        tech_spec_text = project_details.get('tech_spec_text')
        target_os = project_details.get('target_os')

        if not tech_spec_text:
            raise Exception("Technical Specification not found.")

        # Create a modified tech spec context for the agent
        tech_spec_context = f"Full Tech Spec:\n{tech_spec_text}\n\n--- TASK ---\nGenerate a build script *only* for the '{self.current_technology}' part of the stack."

        agent = BuildScriptGeneratorAgent(llm_service=self.orchestrator.llm_service)
        return agent.generate_script(tech_spec_context, target_os)

    def _handle_generation_result(self, script_info):
        """Handles the result from the generation worker."""
        if script_info:
            filename, content = script_info
            self.script_filename = filename
            self.script_content = content
            self.review_is_error_state = False
            self.ui.approveButton.setText(f"Approve {filename}")
            self.ui.standardTextEdit.setPlainText(content) # Show as plain text
        else:
            self.review_is_error_state = True
            self.script_filename = ""
            self.script_content = ""
            self.ui.standardTextEdit.setText("Error: The AI was unable to generate a build script for this technology.")
            self.ui.approveButton.setText("Retry Generation")

        self.ui.reviewHeaderLabel.setText(f"Review Build Script for {self.current_technology}")
        self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
        self.ui.reviewTabWidget.setCurrentIndex(0)

    def run_generate_from_guidelines_task(self):
        """Uses PM-provided text/files as the build script."""
        self.last_failed_action = 'guidelines'
        guidelines = self.ui.pmGuidelinesTextEdit.toPlainText().strip()

        if not guidelines and not self.selected_files:
            QMessageBox.warning(self, "Input Required", "Please provide the script content or upload a script file.")
            return

        self._execute_task(self._task_generate_from_guidelines, self._handle_generation_result, guidelines, self.selected_files,
                           status_message=f"Processing script for {self.current_technology}...")

    def _task_generate_from_guidelines(self, guidelines, uploaded_files, **kwargs):
        """Background task that uses PM's text or file as the script."""
        content = ""
        filename = ""

        if uploaded_files:
            # If files are uploaded, use the first one
            source_path = Path(uploaded_files[0])
            filename = source_path.name
            content = source_path.read_text(encoding='utf-8')
        elif guidelines:
            # If text is entered, we must ask the AI for the filename
            db = self.orchestrator.db_manager
            project_details_row = db.get_project_by_id(self.orchestrator.project_id)
            project_details = dict(project_details_row) if project_details_row else {}
            tech_spec_text = project_details.get('tech_spec_text')
            target_os = project_details.get('target_os')

            # Create a context to help the agent *name* the file
            tech_spec_context = f"Full Tech Spec:\n{tech_spec_text}\n\n--- TASK ---\nDetermine the correct filename for a build script containing the following content for {self.current_technology}:\n\n{guidelines[:500]}..."

            agent = BuildScriptGeneratorAgent(llm_service=self.orchestrator.llm_service)
            script_info = agent.generate_script(tech_spec_context, target_os)
            if script_info:
                filename = script_info[0]
            else:
                filename = f"build_script_{self.current_technology.lower()}" # Fallback
            content = guidelines

        if not filename or not content:
            return None

        return filename, content