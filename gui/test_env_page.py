# gui/test_env_page.py

import logging
import markdown
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
from PySide6.QtWidgets import QWidget, QMessageBox, QLabel, QVBoxLayout, QScrollArea, QFileDialog
from PySide6.QtCore import Signal, QThreadPool, QTimer
from PySide6.QtGui import QPalette, QColor
from pathlib import Path

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
        # Render the Markdown content as formatted HTML
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
        self.ui = Ui_TestEnvPage()
        self.ui.setupUi(self)
        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_display(self):
        """Checks if a manual build script name is needed before showing the page."""
        project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
        if project_details and project_details['is_build_automated'] == 0:
            self.ui.stackedWidget.setCurrentWidget(self.ui.manualBuildScriptPage)
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.standbyPage)

    def prepare_for_new_project(self):
        self.setup_tasks = []
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
        """Saves the manually entered build script filename and proceeds."""
        filename = self.ui.manualBuildScriptLineEdit.text().strip()
        if not filename:
            QMessageBox.warning(self, "Input Required", "Please enter the filename for your build script.")
            return

        try:
            db = self.orchestrator.db_manager
            db.update_project_field(self.orchestrator.project_id, "build_script_file_name", filename)
            self.orchestrator.is_project_dirty = True
            # Proceed to the next logical step in this page's workflow
            self.ui.stackedWidget.setCurrentWidget(self.ui.standbyPage)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save build script filename:\n{e}")

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the main window and updates the status bar."""
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
        """Generic method to run a task in the background."""
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
                           status_message="Analyzing specifications for test environment...")

    def _handle_analysis_result(self, tasks):
        try:
            if tasks is None:
                QMessageBox.critical(self, "Error", "Could not generate setup tasks.")
                return

            self.setup_tasks = tasks
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

        for i, task in enumerate(self.setup_tasks):
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            page = QWidget()
            page.setProperty("class", "contentPanel")

            layout = QVBoxLayout(page)
            header = QLabel(f"<b>Step {i+1} of {len(self.setup_tasks)}: {task.get('tool_name')}</b>")
            instructions = QLabel(task.get('instructions'))
            instructions.setWordWrap(True)
            layout.addWidget(header)
            layout.addWidget(instructions)
            layout.addStretch()
            scroll_area.setWidget(page)
            self.ui.stepsStackedWidget.addWidget(scroll_area)

    def _update_step_view(self):
        self.ui.stepsStackedWidget.setCurrentIndex(self.current_step_index)
        self.ui.doneButton.setText("Finish && Proceed" if self.current_step_index == len(self.setup_tasks) - 1 else "Done, Next Step")
        self.ui.previousButton.setEnabled(self.current_step_index > 0)

    def on_previous_clicked(self):
        """Navigates to the previous setup step."""
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

    def on_export_clicked(self):
        """Exports all setup steps to a single .docx file in the project's docs folder."""
        if not self.setup_tasks:
            QMessageBox.warning(self, "No Content", "There are no setup steps to export.")
            return

        try:
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise IOError("Project root folder not found.")

            project_root = Path(project_details['project_root_folder'])
            docs_dir = project_root / "docs"
            docs_dir.mkdir(exist_ok=True) # Ensure the directory exists

            project_name = self.orchestrator.project_name or "project"
            file_path = docs_dir / f"{project_name}_Test_Environment_Setup.docx"

            full_content = []
            for i, task in enumerate(self.setup_tasks):
                full_content.append(f"Step {i+1}: {task.get('tool_name')}\n")
                full_content.append(f"{task.get('instructions')}\n\n")

            report_generator = ReportGeneratorAgent()
            docx_bytes = report_generator.generate_text_document_docx(
                title=f"Test Environment Setup - {self.orchestrator.project_name}",
                content="\n".join(full_content)
            )
            with open(file_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())

            QMessageBox.information(self, "Success", f"Successfully exported setup instructions to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export document: {e}")

    def on_help_clicked(self):
        """Gets detailed help for the current setup task."""
        if not self.setup_tasks or self.current_step_index >= len(self.setup_tasks):
            return

        current_task = self.setup_tasks[self.current_step_index]
        instructions = current_task.get('instructions', 'No instructions available.')

        # We can run this in a background thread to avoid blocking if the help generation is slow
        self._execute_task(self.orchestrator.get_help_for_setup_task, self._handle_help_result, instructions,
                           status_message="Getting help...")

    def _handle_help_result(self, help_text):
        """Displays the help text in a custom, scrollable dialog."""
        try:
            dialog = HelpDialog("Help", help_text, self)
            dialog.exec()
        finally:
            self._set_ui_busy(False)

    def on_ignore_clicked(self):
        """Acknowledges the user wants to skip the current step, logs it,
        and proceeds to the final step of this phase."""
        if not self.setup_tasks or self.current_step_index >= len(self.setup_tasks):
            return

        current_task = self.setup_tasks[self.current_step_index]
        task_name = current_task.get('tool_name', 'Unnamed Task')

        reply = QMessageBox.question(self, "Confirm Ignore",
                                     f"Are you sure you want to ignore the setup for '{task_name}'?\nThis may cause issues later. A 'KNOWN_ISSUE' will be logged.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.orchestrator.handle_ignore_setup_task(current_task)
            # --- THIS IS THE FIX ---
            # Transition to the final page of THIS phase, not the next one.
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalizePage)
            self._populate_test_command()
            # --- END OF FIX ---

    def on_finalize_clicked(self):
        command = self.ui.testCommandLineEdit.text().strip()
        if not command:
            QMessageBox.warning(self, "Input Required", "The test execution command cannot be empty.")
            return
        if self.orchestrator.finalize_test_environment_setup(command):
            self.test_env_setup_complete.emit()
        else:
            QMessageBox.critical(self, "Error", "Failed to finalize setup.")

    def _populate_test_command(self):
        """Gets a suggested test command from the backend."""
        self._execute_task(self._task_get_test_command, self._handle_command_result,
                           status_message="Generating test command...")

    def _handle_command_result(self, command_text):
        """Safely sets the text of the command line edit."""
        try:
            if command_text and command_text.strip():
                self.ui.testCommandLineEdit.setText(command_text)
            else:
                self.ui.testCommandLineEdit.setText("pytest")
        finally:
            self._set_ui_busy(False)

    def _task_get_test_command(self, **kwargs):
        """Background task to get the suggested test command."""
        try:
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            tech_spec_text = project_details['tech_spec_text'] if project_details else ""
            if self.orchestrator.llm_service and tech_spec_text:
                agent = VerificationAgent_AppTarget(llm_service=self.orchestrator.llm_service)
                details = agent._get_test_execution_details(tech_spec_text)
                command = details.get("command") if details else ""
                return command if command and command.strip() else "pytest"
            return "pytest"
        except Exception as e:
            logging.error(f"Failed to get suggested test command: {e}")
            return "pytest"