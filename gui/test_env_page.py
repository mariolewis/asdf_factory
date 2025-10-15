# gui/test_env_page.py

import logging
import markdown
import re
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox,
                               QWidget, QMessageBox, QLabel, QScrollArea)
from PySide6.QtCore import Signal, QThreadPool
from PySide6.QtGui import QPalette, QColor

from agents.agent_report_generator import ReportGeneratorAgent
from gui.ui_test_env_page import Ui_TestEnvPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_verification_app_target import VerificationAgent_AppTarget

class HelpDialog(QDialog):
    """A custom dialog to display scrollable help content."""
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(markdown.markdown(content, extensions=['fenced_code', 'extra']))
        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class TestEnvPage(QWidget):
    state_changed = Signal()
    test_env_setup_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.setup_tasks = []
        self.current_step_index = 0
        self.dev_tasks = [] # NEW: To hold only development tasks
        self.test_tasks = [] # NEW: To hold only test tasks

        self.ui = Ui_TestEnvPage()
        self.ui.setupUi(self)
        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_display(self):
        project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
        if project_details and project_details['is_build_automated'] == 0 and not project_details['build_script_file_name']:
            self.ui.stackedWidget.setCurrentWidget(self.ui.manualBuildScriptPage)
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.standbyPage)

    def prepare_for_new_project(self):
        self.setup_tasks = []
        self.dev_tasks = [] # NEW
        self.test_tasks = [] # NEW
        self.current_step_index = 0
        self.ui.stackedWidget.setCurrentWidget(self.ui.standbyPage)
        self.setEnabled(True)

    def connect_signals(self):
        self.ui.startButton.clicked.connect(self.run_analysis_task)
        self.ui.doneButton.clicked.connect(self.on_done_clicked)
        self.ui.previousButton.clicked.connect(self.on_previous_clicked)
        self.ui.exportButton.clicked.connect(self.on_export_clicked)
        self.ui.helpButton.clicked.connect(self.on_help_clicked)
        self.ui.ignoreButton.clicked.connect(self.on_ignore_clicked)
        self.ui.finalizeButton.clicked.connect(self.on_finalize_clicked)
        self.ui.confirmBuildScriptButton.clicked.connect(self.on_confirm_build_script_clicked)

    def on_confirm_build_script_clicked(self):
        filename = self.ui.manualBuildScriptLineEdit.text().strip()
        if not filename:
            QMessageBox.warning(self, "Input Required", "Please enter the filename for your build script.")
            return

        try:
            db = self.orchestrator.db_manager
            db.update_project_field(self.orchestrator.project_id, "build_script_file_name", filename)
            self.orchestrator.is_project_dirty = True
            self.ui.stackedWidget.setCurrentWidget(self.ui.standbyPage)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save build script filename:\n{e}")

    def _set_ui_busy(self, is_busy, message="Processing..."):
        main_window = self.window()
        if not main_window:
            self.setEnabled(not is_busy)
            return

        main_window.setEnabled(not is_busy)
        if hasattr(main_window, 'statusBar'):
            if is_busy:
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

    def run_analysis_task(self):
        self._execute_task(self.orchestrator.start_test_environment_setup, self._handle_analysis_result,
                           status_message="Analyzing specifications for environment setup...")

    # MODIFIED: This method now handles the combined list
    def _handle_analysis_result(self, combined_tasks):
        try:
            if combined_tasks is None:
                QMessageBox.critical(self, "Error", "Could not generate setup tasks.")
                return

            # NEW: Separate combined list into dev and test lists for UI logic
            self.setup_tasks = combined_tasks
            self.dev_tasks = [t for t in combined_tasks if t.get('type') == 'development']
            self.test_tasks = [t for t in combined_tasks if t.get('type') == 'test']

            if not self.setup_tasks:
                self.ui.stackedWidget.setCurrentWidget(self.ui.finalizePage)
                self._populate_test_command()
            else:
                self._populate_steps_widget()
                self._update_step_view()
                self.ui.stackedWidget.setCurrentWidget(self.ui.checklistPage)
        finally:
            self._set_ui_busy(False)

    def _populate_steps_widget(self):
        while self.ui.stepsStackedWidget.count() > 0:
            widget = self.ui.stepsStackedWidget.widget(0)
            self.ui.stepsStackedWidget.removeWidget(widget)
            widget.deleteLater()

        for task in self.setup_tasks: # Iterate through the combined list
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            page = QWidget()
            page.setProperty("class", "contentPanel")

            layout = QVBoxLayout(page)
            header = QLabel()

            instructions = QTextEdit()
            instructions.setReadOnly(True)
            # Use setMarkdown to render the formatted text from the agent as rich text.
            instruction_text = task.get('instructions', '')
            # Replace H1/H2 markdown with simple bolding to prevent large fonts
            instruction_text = re.sub(r'^\s*#{1,2}\s*(.*)', r'<b>\1</b>', instruction_text, flags=re.MULTILINE)
            instructions.setMarkdown(instruction_text)

            layout.addWidget(header)
            layout.addWidget(instructions, 1)

            scroll_area.setWidget(page)
            self.ui.stepsStackedWidget.addWidget(scroll_area)

    def _update_step_view(self):
        if not self.setup_tasks:
            return

        self.ui.stepsStackedWidget.setCurrentIndex(self.current_step_index)
        current_task = self.setup_tasks[self.current_step_index]
        current_widget = self.ui.stepsStackedWidget.currentWidget().widget()
        header_label = current_widget.findChild(QLabel)

        # NEW: Dynamic header logic
        if current_task.get('type') == 'development':
            dev_step_num = self.current_step_index + 1
            header_text = f"<b>Development Setup: Step {dev_step_num} of {len(self.dev_tasks)}: {current_task.get('tool_name')}</b>"
            self.ui.checklistHeaderLabel.setText("Please follow the steps below to set up the development environment:")
        else: # It's a test task
            test_step_num = (self.current_step_index - len(self.dev_tasks)) + 1
            header_text = f"<b>Test Setup: Step {test_step_num} of {len(self.test_tasks)}: {current_task.get('tool_name')}</b>"
            self.ui.checklistHeaderLabel.setText("Development setup complete. Now, please set up the testing environment:")

        if header_label:
            header_label.setText(header_text)

        self.ui.doneButton.setText("Finish & Proceed" if self.current_step_index == len(self.setup_tasks) - 1 else "Done, Next Step")
        self.ui.previousButton.setEnabled(self.current_step_index > 0)

    def on_previous_clicked(self):
        if self.current_step_index > 0:
            self.current_step_index -= 1
            self._update_step_view()

    def on_done_clicked(self):
        if self.current_step_index < len(self.setup_tasks) - 1:
            self.current_step_index += 1
            self._update_step_view()
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalizePage)
            self._populate_test_command()

    # MODIFIED: Export now includes structured headers
    def on_export_clicked(self):
        if not self.setup_tasks:
            QMessageBox.warning(self, "No Content", "There are no setup steps to export.")
            return
        try:
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise IOError("Project root folder not found.")

            project_root = Path(project_details['project_root_folder'])
            docs_dir = project_root / "docs"
            docs_dir.mkdir(exist_ok=True)
            project_name = self.orchestrator.project_name or "project"
            file_path = docs_dir / f"{project_name}_Environment_Setup_Guide.docx"

            # NEW: Build structured content for the report
            full_content = []
            if self.dev_tasks:
                full_content.append("## Development Environment Setup\n")
                for i, task in enumerate(self.dev_tasks, 1):
                    full_content.append(f"### Step {i}: {task.get('tool_name')}\n")
                    full_content.append(f"{task.get('instructions')}\n")
            if self.test_tasks:
                full_content.append("\n## Test Environment Setup\n")
                for i, task in enumerate(self.test_tasks, 1):
                    full_content.append(f"### Step {i}: {task.get('tool_name')}\n")
                    full_content.append(f"{task.get('instructions')}\n")

            report_generator = ReportGeneratorAgent()
            docx_bytes = report_generator.generate_text_document_docx(
                title=f"Environment Setup Guide - {self.orchestrator.project_name}",
                content="\n".join(full_content)
            )
            with open(file_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            QMessageBox.information(self, "Success", f"Successfully exported setup instructions to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export document: {e}")

    def on_help_clicked(self):
        if not self.setup_tasks or self.current_step_index >= len(self.setup_tasks):
            return
        current_task = self.setup_tasks[self.current_step_index]
        instructions = current_task.get('instructions', 'No instructions available.')
        self._execute_task(self.orchestrator.get_help_for_setup_task, self._handle_help_result, instructions,
                           status_message="Getting help...")

    def _handle_help_result(self, help_text):
        try:
            dialog = HelpDialog("Help", help_text, self)
            dialog.exec()
        finally:
            self._set_ui_busy(False)

    def on_ignore_clicked(self):
        if not self.setup_tasks or self.current_step_index >= len(self.setup_tasks):
            return
        current_task = self.setup_tasks[self.current_step_index]
        task_name = current_task.get('tool_name', 'Unnamed Task')
        reply = QMessageBox.question(self, "Confirm Ignore",
                                     f"Are you sure you want to ignore the setup for '{task_name}'?\nThis may cause issues later. A 'KNOWN_ISSUE' will be logged.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.orchestrator.handle_ignore_setup_task(current_task)
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalizePage)
            self._populate_test_command()

    def on_finalize_clicked(self):
        backend_command = self.ui.testCommandLineEdit.text().strip()
        ui_command = self.ui.uiTestCommandLineEdit.text().strip()
        if not backend_command:
            QMessageBox.warning(self, "Input Required", "The Backend Test Command cannot be empty.")
            return
        if self.orchestrator.finalize_test_environment_setup(backend_command, ui_command):
            self.test_env_setup_complete.emit()
        else:
            QMessageBox.critical(self, "Error", "Failed to finalize setup.")

    def _populate_test_command(self):
        self._execute_task(self._task_get_test_command, self._handle_command_result,
                           status_message="Generating test command...")

    def _handle_command_result(self, command_text):
        try:
            if command_text and command_text.strip():
                self.ui.testCommandLineEdit.setText(command_text)
            else:
                self.ui.testCommandLineEdit.setText("pytest")
        finally:
            self._set_ui_busy(False)

    def _task_get_test_command(self, **kwargs):
        """
        Gets the test command, prioritizing a user-saved value from the database
        before falling back to LLM generation.
        """
        try:
            project_details_row = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            if not project_details_row:
                return "pytest" # Fallback

            project_details = dict(project_details_row)

            # First, check for an existing, user-saved command
            existing_command = project_details.get("test_execution_command")
            if existing_command and existing_command.strip():
                logging.info(f"Found existing test command in database: '{existing_command}'")
                return existing_command

            # If no command exists, proceed with LLM generation
            tech_spec_text = project_details.get('tech_spec_text', "")
            if self.orchestrator.llm_service and tech_spec_text:
                logging.info("No existing command found. Generating new test command via LLM.")
                agent = VerificationAgent_AppTarget(llm_service=self.orchestrator.llm_service)
                details = agent._get_test_execution_details(tech_spec_text)
                command = details.get("command") if details else ""
                return command if command and command.strip() else "pytest"

            return "pytest" # Final fallback
        except Exception as e:
            logging.error(f"Failed to get suggested test command: {e}")
            return "pytest"