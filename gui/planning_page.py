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
    state_changed = Signal()
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
        self.setEnabled(True)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.generateButton.clicked.connect(self.run_generation_task)
        self.ui.refineButton.clicked.connect(self.run_refinement_task)
        self.ui.approveButton.clicked.connect(self.on_approve_clicked)

    def _format_plan_for_display(self, plan_json_str: str) -> str:
        """Converts the JSON development plan data into a formatted HTML string."""
        try:
            plan_data = json.loads(plan_json_str)
            if not plan_data or "development_plan" not in plan_data:
                return "<p>Could not parse the development plan.</p>"

            html = []
            main_exe = plan_data.get("main_executable_file", "Not specified")
            html.append(f"<h3>Main Executable File: {main_exe}</h3>")
            html.append("<hr>")
            html.append("<h3>Development Plan Steps:</h3>")

            plan_steps = plan_data.get("development_plan", [])
            if not plan_steps:
                html.append("<p>No development steps were generated.</p>")
            else:
                html.append("<ol>")
                for task in plan_steps:
                    html.append("<li>")
                    html.append(f"<b>ID:</b> {task.get('micro_spec_id', 'N/A')}<br/>")
                    html.append(f"<b>Component:</b> {task.get('component_name', 'N/A')}<br/>")
                    html.append(f"<b>Type:</b> {task.get('component_type', 'N/A')}<br/>")
                    html.append(f"<b>Description:</b> <i>{task.get('task_description', 'No description.')}</i>")
                    html.append("</li><br/>")
                html.append("</ol>")

            return "".join(html)
        except json.JSONDecodeError:
            return f"<p>Error: Could not parse the development plan JSON.</p><pre>{plan_json_str}</pre>"


    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the main window and updates the status bar."""
        main_window = self.window() # Get the top-level window
        if not main_window:
            self.setEnabled(not is_busy) # Fallback if parent isn't found
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
        """Handles errors from the worker thread."""
        try:
            error_msg = f"An error occurred in a background task:\n{error_tuple[1]}"
            QMessageBox.critical(self, "Error", error_msg)
        finally:
            self._set_ui_busy(False)

    def run_generation_task(self):
        """Initiates the background task to generate the development plan."""
        self._execute_task(self._task_generate_plan, self._handle_generation_result,
                           status_message="Generating development plan...")

    def _handle_generation_result(self, plan_json_str):
        """Handles the result from the worker thread."""
        try:
            self.development_plan_json = plan_json_str
            plan_for_display = self._format_plan_for_display(plan_json_str)
            self.ui.planTextEdit.setHtml(plan_for_display)
            self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def on_approve_clicked(self):
        """Saves the final plan and proceeds to the next phase."""
        if not self.development_plan_json:
            QMessageBox.warning(self, "Approval Failed", "There is no development plan to approve.")
            return

        success, message = self.orchestrator.finalize_and_save_dev_plan(self.development_plan_json)
        if success:
            QMessageBox.information(self, "Success", "Success: Development Plan approved and saved.")
            self.orchestrator.is_project_dirty = True
            self.planning_complete.emit()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save the development plan:\n{message}")

    def _task_generate_plan(self, **kwargs):
        """The actual function that runs in the background."""
        db = self.orchestrator.db_manager
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

        # Check for error before trying to parse, to avoid crashing on agent error
        try:
            response_data = json.loads(response_json_str)
            main_executable = response_data.get("main_executable_file")
            if main_executable:
                db.update_project_field(self.orchestrator.project_id, "apex_executable_name", main_executable)
        except json.JSONDecodeError:
            logging.error(f"Could not parse development plan JSON from agent: {response_json_str}")
            # The error will be displayed in the text box for the user to see.

        return response_json_str

    def run_refinement_task(self):
        """Initiates the background task to refine the development plan."""
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback for refinement.")
            return

        current_plan_json = self.development_plan_json
        self._execute_task(self._task_refine_plan, self._handle_refinement_result, current_plan_json, feedback,
                           status_message="Refining development plan...")

    def _handle_refinement_result(self, new_plan_json_str):
        """Handles the result from the refinement worker thread."""
        try:
            self.development_plan_json = new_plan_json_str
            plan_for_display = self._format_plan_for_display(new_plan_json_str)
            self.ui.planTextEdit.setHtml(plan_for_display)
            self.ui.feedbackTextEdit.clear()
            QMessageBox.information(self, "Success", "Success: The development plan has been refined based on your feedback.")
            self.state_changed.emit()
        finally:
            self._set_ui_busy(False)

    def _task_refine_plan(self, current_plan_json, feedback, **kwargs):
        """The actual function that runs in the background to refine the plan."""
        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        final_spec = project_details['final_spec_text']
        tech_spec = project_details['tech_spec_text']

        agent = PlanningAgent_AppTarget(
            llm_service=self.orchestrator.llm_service,
            db_manager=db
        )
        return agent.refine_plan(current_plan_json, feedback, final_spec, tech_spec)