# gui/planning_page.py

import logging
import json
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_planning_page import Ui_PlanningPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator
from agents.agent_planning_app_target import PlanningAgent_AppTarget

class PlanningPage(QWidget):
    """
    The logic handler for the Strategic Development Planning page.
    """
    planning_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.development_plan_json = ""

        self.ui = Ui_PlanningPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page to its initial state."""
        logging.info("Resetting PlanningPage for a new project.")
        self.development_plan_json = ""
        self.ui.planTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.generatePage)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.generateButton.clicked.connect(self.run_generation_task)
        self.ui.regenerateButton.clicked.connect(self.run_generation_task)
        self.ui.approveButton.clicked.connect(self.on_approve_clicked)

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

    def run_generation_task(self):
        """Initiates the background task to generate the development plan."""
        self._execute_task(self._task_generate_plan, self._handle_generation_result)

    def _handle_generation_result(self, plan_json_str):
        """Handles the result from the worker thread."""
        try:
            self.development_plan_json = plan_json_str
            parsed_json = json.loads(plan_json_str)
            pretty_json = json.dumps(parsed_json, indent=4)
            self.ui.planTextEdit.setText(pretty_json)
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
        finally:
            self._set_ui_busy(False)

    def on_approve_clicked(self):
        """Saves the final plan and proceeds to the next phase."""
        if not self.development_plan_json:
            QMessageBox.warning(self, "Approval Failed", "There is no development plan to approve.")
            return

        success, message = self.orchestrator.finalize_and_save_dev_plan(self.development_plan_json)
        if success:
            QMessageBox.information(self, "Success", "Development Plan approved and saved.")
            self.planning_complete.emit()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save the development plan:\n{message}")

    # --- Backend Logic (to be run in worker thread) ---

    def _task_generate_plan(self, **kwargs):
        """The actual function that runs in the background."""
        with self.orchestrator.db_manager as db:
            project_details = db.get_project_by_id(self.orchestrator.project_id)
            final_spec = project_details['final_spec_text']
            tech_spec = project_details['tech_spec_text']

        if not all([final_spec, tech_spec]):
            raise Exception("Missing Final or Technical Specification. Cannot generate a plan.")

        agent = PlanningAgent_AppTarget(
            llm_service=self.orchestrator.llm_service,
            db_manager=self.orchestrator.db_manager
        )
        response_json_str = agent.generate_development_plan(final_spec, tech_spec)

        response_data = json.loads(response_json_str)
        main_executable = response_data.get("main_executable_file")
        if main_executable:
            with self.orchestrator.db_manager as db:
                db.update_project_apex_file(self.orchestrator.project_id, main_executable)

        return response_json_str