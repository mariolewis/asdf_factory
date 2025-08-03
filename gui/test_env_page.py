# gui/test_env_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool, QTimer

from gui.ui_test_env_page import Ui_TestEnvPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_verification_app_target import VerificationAgent_AppTarget

class TestEnvPage(QWidget):
    """
    The logic handler for the Test Environment Setup page.
    """
    test_env_setup_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.tasks = []
        self.current_task_index = 0

        self.ui = Ui_TestEnvPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page and schedules the fetching of tasks."""
        logging.info("Resetting TestEnvPage for a new project.")
        self.tasks = []
        self.current_task_index = 0
        self.ui.helpTextEdit.setVisible(False)
        self.ui.helpTextEdit.clear()
        self.ui.taskGroupBox.setTitle("Loading setup tasks...")
        self.ui.taskInstructionsTextEdit.clear()

        QTimer.singleShot(100, self.run_fetch_tasks)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.doneButton.clicked.connect(self.on_done_clicked)
        self.ui.helpButton.clicked.connect(self.run_help_task)
        self.ui.ignoreButton.clicked.connect(self.on_ignore_clicked)
        self.ui.finalizeButton.clicked.connect(self.on_finalize_clicked)

    def _set_ui_busy(self, is_busy):
        """Disables or enables the page while a background task runs."""
        self.setEnabled(not is_busy)

    def _execute_task(self, task_function, on_result, *args):
        """Generic method to run a task in the background."""
        self._set_ui_busy(True)
        worker = Worker(task_function, *args)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        self.threadpool.start(worker)

    def _on_task_error(self, error_tuple):
        """Handles errors from the worker thread."""
        error_msg = f"An error occurred in a background task:\n{error_tuple[2]}"
        QMessageBox.critical(self, "Error", error_msg)
        self._set_ui_busy(False)

    def run_fetch_tasks(self):
        """Initiates the background task to fetch setup tasks."""
        self._execute_task(self._task_fetch_tasks, self._handle_fetch_tasks_result)

    def run_help_task(self):
        """Initiates the background task to get help for the current step."""
        if not self.tasks or self.current_task_index >= len(self.tasks):
            return
        task = self.tasks[self.current_task_index]
        self._execute_task(self._task_get_help, self._handle_help_result, task.get('instructions', ''))

    def _handle_fetch_tasks_result(self, tasks):
        try:
            if tasks:
                self.tasks = tasks
                self.ui.stackedWidget.setCurrentWidget(self.ui.checklistPage)
                self._update_task_display()
            else:
                QMessageBox.warning(self, "No Tasks", "No specific test environment setup tasks were identified. Please confirm the test command manually.")
                self.ui.stackedWidget.setCurrentWidget(self.ui.finalConfirmPage)
                self._suggest_test_command()
        finally:
            self._set_ui_busy(False)

    def _handle_help_result(self, help_text):
        try:
            self.ui.helpTextEdit.setText(help_text)
            self.ui.helpTextEdit.setVisible(True)
        finally:
            self._set_ui_busy(False)

    def _update_task_display(self):
        """Updates the UI to show the current task."""
        if not self.tasks or self.current_task_index >= len(self.tasks):
            self._suggest_test_command()
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalConfirmPage)
            return

        task = self.tasks[self.current_task_index]
        self.ui.taskGroupBox.setTitle(f"Step {self.current_task_index + 1} of {len(self.tasks)}: {task.get('tool_name', 'Unnamed Step')}")
        self.ui.taskInstructionsTextEdit.setText(task.get('instructions', 'No instructions provided.'))
        self.ui.helpTextEdit.setVisible(False)

    def _suggest_test_command(self):
        """Suggests a test command. This is a fast operation, no thread needed."""
        try:
            with self.orchestrator.db_manager as db:
                project_details = db.get_project_by_id(self.orchestrator.project_id)
                tech_spec_text = project_details['tech_spec_text']

            if self.orchestrator.llm_service and tech_spec_text:
                agent = VerificationAgent_AppTarget(llm_service=self.orchestrator.llm_service)
                details = agent._get_test_execution_details(tech_spec_text)
                suggested_command = details.get("command") if details else "pytest"
                self.ui.testCommandLineEdit.setText(suggested_command)
        except Exception as e:
            self.ui.testCommandLineEdit.setText("pytest")

    def on_done_clicked(self):
        self.current_task_index += 1
        self._update_task_display()

    def on_ignore_clicked(self):
        task = self.tasks[self.current_task_index]
        self.orchestrator.handle_ignore_setup_task(task)
        QMessageBox.information(self, "Task Ignored", f"The task '{task.get('tool_name')}' was skipped and logged as a known issue.")
        self.current_task_index += 1
        self._update_task_display()

    def on_finalize_clicked(self):
        command = self.ui.testCommandLineEdit.text().strip()
        if not command:
            QMessageBox.warning(self, "Input Required", "The test execution command cannot be empty.")
            return

        if self.orchestrator.finalize_test_environment_setup(command):
            self.test_env_setup_complete.emit()
        else:
            QMessageBox.critical(self, "Error", "Failed to finalize setup. Please check the logs.")

    # --- Backend Logic (to be run in worker threads) ---

    def _task_fetch_tasks(self, **kwargs):
        return self.orchestrator.start_test_environment_setup()

    def _task_get_help(self, instructions, **kwargs):
        return self.orchestrator.get_help_for_setup_task(instructions)