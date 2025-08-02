# gui/test_env_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QTimer

from gui.ui_test_env_page import Ui_TestEnvPage
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

        # FIX: Defer the slow network call until after the UI is shown
        QTimer.singleShot(100, self.fetch_tasks)

    def fetch_tasks(self):
        """Fetches setup tasks from the orchestrator to avoid blocking the UI thread."""
        try:
            tasks = self.orchestrator.start_test_environment_setup()
            if tasks:
                self.tasks = tasks
                self.ui.stackedWidget.setCurrentWidget(self.ui.checklistPage)
                self._update_task_display()
            else:
                QMessageBox.warning(self, "No Tasks", "No specific test environment setup tasks were identified. Please confirm the test command manually.")
                self.ui.stackedWidget.setCurrentWidget(self.ui.finalConfirmPage)
                self._suggest_test_command()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not generate setup tasks: {e}")
            self.orchestrator.set_phase("CODING_STANDARD_GENERATION") # Allow skipping on error
            self.test_env_setup_complete.emit()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.doneButton.clicked.connect(self.on_done_clicked)
        self.ui.helpButton.clicked.connect(self.on_help_clicked)
        self.ui.ignoreButton.clicked.connect(self.on_ignore_clicked)
        self.ui.finalizeButton.clicked.connect(self.on_finalize_clicked)

    def _update_task_display(self):
        """Updates the UI to show the current task."""
        if not self.tasks or self.current_task_index >= len(self.tasks):
            self._suggest_test_command()
            self.ui.stackedWidget.setCurrentWidget(self.ui.finalConfirmPage)
            return

        task = self.tasks[self.current_task_index]
        self.ui.taskGroupBox.setTitle(f"Step {self.current_task_index + 1} of {len(self.tasks)}: {task.get('tool_name', 'Unnamed Step')}")
        # FIX: Use the new QTextEdit widget which supports scrolling
        self.ui.taskInstructionsTextEdit.setText(task.get('instructions', 'No instructions provided.'))
        self.ui.helpTextEdit.setVisible(False)

    def _suggest_test_command(self):
        """Asks the VerificationAgent to suggest a test command."""
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
            logging.error(f"Failed to suggest test command: {e}")
            self.ui.testCommandLineEdit.setText("pytest")

    def on_done_clicked(self):
        self.current_task_index += 1
        self._update_task_display()

    def on_help_clicked(self):
        task = self.tasks[self.current_task_index]
        help_text = self.orchestrator.get_help_for_setup_task(task.get('instructions', ''))
        self.ui.helpTextEdit.setText(help_text)
        self.ui.helpTextEdit.setVisible(True)

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
            # This method in the orchestrator now correctly sets the next phase
            self.test_env_setup_complete.emit()
        else:
            QMessageBox.critical(self, "Error", "Failed to finalize setup. Please check the logs.")