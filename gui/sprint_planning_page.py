# gui/sprint_planning_page.py

import logging
import json
import markdown
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QMessageBox, QMenu, QListWidgetItem,
                               QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QFileDialog, QLabel)
from PySide6.QtCore import Signal, Qt, QThreadPool
from PySide6.QtGui import QAction, QColor

from gui.ui_sprint_planning_page import Ui_SprintPlanningPage
from master_orchestrator import MasterOrchestrator
from gui.worker import Worker

class DetailsDialog(QDialog):
    """A custom, resizable dialog with a scrollable text area for showing details."""
    def __init__(self, title, content_html, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(content_html)
        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class SprintPlanningPage(QWidget):
    """
    The logic handler for the Sprint Planning Workspace page.
    """
    sprint_started = Signal(list)
    sprint_cancelled = Signal()

    # In gui/sprint_planning_page.py

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.sprint_scope_items = []
        self.implementation_plan_json = ""
        self.threadpool = QThreadPool()

        self.ui = Ui_SprintPlanningPage()
        self.ui.setupUi(self)

        self.ui.mainSplitter.setChildrenCollapsible(False)
        self.ui.mainSplitter.setSizes([350, 450])

        self.complexity_colors = {
            "Large": QColor("#CC7832"),
            "Medium": QColor("#FFC66D"),
            "Small": QColor("#6A8759")
        }

        self.ui.sprintScopeListWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self._create_audit_menu() # Create the menu
        self.connect_signals()   # Connect all signals

        self.ui.incorporateFeedbackButton.setEnabled(False)
        self.ui.runAuditButton.setEnabled(False) # New button is disabled initially

    def _create_audit_menu(self):
        """Creates the QMenu and QActions for the audit button."""
        self.audit_menu = QMenu(self)
        self.security_audit_action = QAction("Security Audit", self)
        self.scalability_audit_action = QAction("Scalability Audit", self)
        self.readability_audit_action = QAction("Readability Audit", self)
        self.best_practices_audit_action = QAction("Best Practices Audit", self)

        self.audit_menu.addAction(self.security_audit_action)
        self.audit_menu.addAction(self.scalability_audit_action)
        self.audit_menu.addAction(self.readability_audit_action)
        self.audit_menu.addAction(self.best_practices_audit_action)

        self.ui.runAuditButton.setMenu(self.audit_menu)

    def connect_signals(self):
        """Connects UI element signals to their handler methods."""
        self.ui.cancelSprintButton.clicked.connect(self.sprint_cancelled.emit)
        self.ui.removeFromSprintButton.clicked.connect(self.on_remove_item_triggered)
        self.ui.sprintScopeListWidget.customContextMenuRequested.connect(self.show_sprint_scope_context_menu)
        self.ui.sprintScopeListWidget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.ui.savePlanButton.clicked.connect(self.on_save_plan_clicked)
        self.ui.sprintScopeListWidget.itemSelectionChanged.connect(self._on_selection_changed)

        # Connect the new QActions instead of the old buttons
        self.security_audit_action.triggered.connect(self.on_security_audit_clicked)
        self.scalability_audit_action.triggered.connect(self.on_scalability_audit_clicked)
        self.readability_audit_action.triggered.connect(self.on_readability_audit_clicked)
        self.best_practices_audit_action.triggered.connect(self.on_best_practices_audit_clicked)

        self.ui.incorporateFeedbackButton.clicked.connect(self.on_incorporate_feedback_clicked)

    def _on_selection_changed(self):
        """Enables or disables the 'Remove from Sprint' button based on selection."""
        has_selection = len(self.ui.sprintScopeListWidget.selectedItems()) > 0
        self.ui.removeFromSprintButton.setEnabled(has_selection)

    def on_item_double_clicked(self, item: QListWidgetItem):
        """Displays the full details of a double-clicked item in a custom dialog."""
        item_data = item.data(Qt.UserRole)
        if not item_data:
            return

        hierarchical_id = item_data.get('hierarchical_id', '')
        title = item_data.get('title', 'No Title')
        display_title = f"{hierarchical_id}: {title}" if hierarchical_id else title
        description = item_data.get('description', 'No description provided.')
        analysis = item_data.get('technical_preview_text', '')

        md_text = f"### {display_title}\n\n**Description:**\n\n{description}"
        if analysis:
            md_text += f"\n\n---\n\n**Technical Preview:**\n\n{analysis}"

        details_html = markdown.markdown(md_text)

        dialog = DetailsDialog(f"Details for: {display_title}", details_html, self)
        dialog.exec()

    def show_sprint_scope_context_menu(self, position):
        """Creates and shows a context menu on right-click."""
        item = self.ui.sprintScopeListWidget.itemAt(position)
        if not item:
            return

        menu = QMenu()
        remove_action = QAction("Remove from Sprint", self)
        remove_action.triggered.connect(self.on_remove_item_triggered)
        menu.addAction(remove_action)

        menu.exec(self.ui.sprintScopeListWidget.viewport().mapToGlobal(position))

    def on_remove_item_triggered(self):
        """Removes the currently selected item(s) from the sprint scope and regenerates the plan."""
        selected_list_items = self.ui.sprintScopeListWidget.selectedItems()
        if not selected_list_items:
            return

        rows_to_remove = sorted([self.ui.sprintScopeListWidget.row(item) for item in selected_list_items], reverse=True)

        for row in rows_to_remove:
            self.ui.sprintScopeListWidget.takeItem(row)
            if row < len(self.sprint_scope_items):
                del self.sprint_scope_items[row]

        if not self.sprint_scope_items:
            self.ui.implementationPlanTextEdit.clear()
            self._update_metrics()
            self.ui.startSprintButton.setEnabled(False)
            self.ui.savePlanButton.setEnabled(False)
        else:
            self.run_plan_generation_task()

        self._on_selection_changed()

    def prepare_for_display(self, selected_items: list = None):
        """Loads sprint data into the UI and triggers plan generation."""
        self.ui.planTabWidget.setCurrentWidget(self.ui.planTab)
        if selected_items is None:
            selected_items = []

        logging.info(f"Loading {len(selected_items)} items into Sprint Planning workspace.")
        self.sprint_scope_items = selected_items
        self.ui.savePlanButton.setEnabled(False)

        self.ui.sprintScopeListWidget.clear()
        for item_data in self.sprint_scope_items:
            title = item_data.get('title', 'Untitled Item')
            complexity = item_data.get('complexity', '')

            list_item = QListWidgetItem(title)
            list_item.setData(Qt.UserRole, item_data)

            if complexity in self.complexity_colors:
                list_item.setForeground(self.complexity_colors[complexity])

            self.ui.sprintScopeListWidget.addItem(list_item)

        if self.sprint_scope_items:
            self.run_plan_generation_task()
        else:
            self.ui.implementationPlanTextEdit.setText("No items in sprint scope.")
            self._update_metrics()

        self._on_selection_changed()

    def run_plan_generation_task(self):
        """Initiates the background task to generate the implementation plan."""
        self.ui.implementationPlanTextEdit.setText("<b>Generating implementation plan...</b>")
        self.ui.startSprintButton.setEnabled(False)
        self.ui.savePlanButton.setEnabled(False)
        self.window().setEnabled(False)

        worker = Worker(self._task_generate_plan, self.sprint_scope_items)
        worker.signals.result.connect(self._handle_plan_generation_result)
        self.threadpool.start(worker)

    def _task_generate_plan(self, sprint_items, **kwargs):
        """Background worker task that calls the orchestrator."""
        return self.orchestrator.generate_sprint_implementation_plan(sprint_items)

    def _handle_plan_generation_result(self, plan_json_str: str):
        """Handles the result from the plan generation worker."""
        self.window().setEnabled(True)
        self.window().statusBar().clearMessage()
        self.implementation_plan_json = plan_json_str
        self.ui.planTabWidget.setCurrentWidget(self.ui.planTab)

        try:
            plan_data = json.loads(plan_json_str)
            if isinstance(plan_data, list) and plan_data and plan_data[0].get("error"):
                error_details = plan_data[0].get("error", "Unknown error.")
                self.ui.implementationPlanTextEdit.setText(f"Error generating plan:\n\n{error_details}")
                self.ui.startSprintButton.setEnabled(False)
                self.ui.savePlanButton.setEnabled(False)
                self.ui.runAuditButton.setEnabled(False)
            else:
                formatted_plan = self._format_plan_for_display(plan_data)
                self.ui.implementationPlanTextEdit.setHtml(formatted_plan)
                self.ui.startSprintButton.setEnabled(True)
                self.ui.savePlanButton.setEnabled(True)
                self.ui.runAuditButton.setEnabled(True)
            self._update_metrics(plan_data)
        except json.JSONDecodeError:
            self.ui.implementationPlanTextEdit.setText(f"Error: Could not parse the generated plan.\n\n{plan_json_str}")
            self.ui.startSprintButton.setEnabled(False)
            self.ui.savePlanButton.setEnabled(False)
            self._update_metrics()

    def on_save_plan_clicked(self):
        """Handles exporting the current sprint plan to a .docx file."""
        if not self.implementation_plan_json:
            QMessageBox.warning(self, "No Plan", "There is no implementation plan to save.")
            return

        try:
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            project_root = Path(project_details['project_root_folder'])
            sprint_dir = project_root / "sprint"
            sprint_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = sprint_dir / f"{self.orchestrator.project_name}_Sprint_Plan_{timestamp}.docx"

            file_path, _ = QFileDialog.getSaveFileName(self, "Save Sprint Plan", str(default_filename), "Word Documents (*.docx)")

            if file_path:
                docx_bytes = self.orchestrator.export_sprint_plan_to_docx(self.sprint_scope_items, self.implementation_plan_json)
                if docx_bytes:
                    with open(file_path, 'wb') as f:
                        f.write(docx_bytes.getbuffer())
                    QMessageBox.information(self, "Success", f"Successfully saved sprint plan to:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to generate the document data.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while saving the plan:\n{e}")

    def _format_plan_for_display(self, plan_data: list) -> str:
        """Converts the JSON development plan into a formatted HTML string."""
        if not plan_data:
            return "<p>No development steps were generated.</p>"

        html = ["<ol>"]
        for task in plan_data:
            html.append("<li>")
            html.append(f"<b>Component:</b> {task.get('component_name', 'N/A')}<br/>")
            html.append(f"<b>File Path:</b> {task.get('component_file_path', 'N/A')}<br/>")
            html.append(f"<b>Description:</b> <i>{task.get('task_description', 'No description.')}</i>")
            html.append("</li><br/>")
        html.append("</ol>")

        return "".join(html)

    def _update_metrics(self, plan_data: list = None):
        """Updates the metrics label based on current scope and plan."""
        if plan_data is None:
            plan_data = []

        item_count = len(self.sprint_scope_items)

        task_count = 0
        if isinstance(plan_data, list) and plan_data:
            if "error" not in plan_data[0]:
                task_count = len(plan_data)

        complexity_map = {"Small": 1, "Medium": 3, "Large": 5}
        total_complexity = 0
        for item in self.sprint_scope_items:
            complexity_str = item.get('complexity', '')
            total_complexity += complexity_map.get(complexity_str, 0)

        self.ui.metricsLabel.setText(f"Items: {item_count} | Total Complexity: {total_complexity} story points | Development Tasks: {task_count}")

    # In gui/sprint_planning_page.py ... replace these three methods

    def _run_audit_task(self, audit_type: str):
        """Generic handler to run a specific audit in a background thread."""
        if not self.implementation_plan_json:
            QMessageBox.warning(self, "No Plan", "An implementation plan must be generated before running an audit.")
            return

        self.ui.runAuditButton.setEnabled(False)
        self.ui.incorporateFeedbackButton.setEnabled(False)

        self.window().setEnabled(False)
        self.window().statusBar().showMessage(f"Running {audit_type} Audit...")
        self.ui.planTabWidget.setCurrentWidget(self.ui.advisoryTab)
        self.ui.auditResultTextEdit.setText(f"Running {audit_type} Audit...")

        worker = Worker(self.orchestrator.run_sprint_plan_audit, audit_type, self.implementation_plan_json)
        worker.signals.result.connect(self._handle_audit_result)
        worker.signals.error.connect(self._on_background_task_error)
        self.threadpool.start(worker)

    def _on_background_task_error(self, error_tuple):
        """A generic handler for errors from background worker threads."""
        self.window().setEnabled(True)
        self.window().statusBar().clearMessage()
        error_msg = f"An unexpected error occurred in a background task:\n{error_tuple[1]}"
        logging.error(error_msg, exc_info=error_tuple)
        QMessageBox.critical(self, "Background Task Error", error_msg)
        self.ui.auditResultTextEdit.setText(error_msg)

        self.ui.runAuditButton.setEnabled(True)

    def _handle_audit_result(self, report_markdown: str):
        """Displays the audit result in the text edit."""
        self.window().setEnabled(True)
        self.window().statusBar().clearMessage()
        self.ui.auditResultTextEdit.setHtml(markdown.markdown(report_markdown))

        self.ui.incorporateFeedbackButton.setEnabled(True)
        self.ui.runAuditButton.setEnabled(True)

    def on_security_audit_clicked(self):
        self._run_audit_task("Security")

    def on_scalability_audit_clicked(self):
        self._run_audit_task("Scalability")

    def on_readability_audit_clicked(self):
        self._run_audit_task("Readability")

    def on_best_practices_audit_clicked(self):
        self._run_audit_task("Best Practices")

    def on_incorporate_feedback_clicked(self):
        """Opens a dialog for the PM to enter refinement instructions."""
        dialog = IncorporateFeedbackDialog(self)
        if dialog.exec():
            feedback = dialog.get_feedback()
            if feedback:
                self.run_refinement_task(feedback)

    def run_refinement_task(self, feedback: str):
        """Initiates the background task to refine the implementation plan."""
        self.ui.planTabWidget.setCurrentWidget(self.ui.planTab)
        self.ui.implementationPlanTextEdit.setText("<b>Refining implementation plan based on feedback...</b>")
        self.window().setEnabled(False)
        self.window().statusBar().showMessage("Refining implementation plan based on feedback...")

        worker = Worker(self._task_refine_plan, feedback)
        # We can reuse the same result handler as the initial plan generation
        worker.signals.result.connect(self._handle_plan_generation_result)
        worker.signals.error.connect(self._on_background_task_error)
        self.threadpool.start(worker)

    def _task_refine_plan(self, pm_feedback, **kwargs):
        """Background worker task that calls the orchestrator to refine the plan."""
        return self.orchestrator.refine_sprint_implementation_plan(
            current_plan_json=self.implementation_plan_json,
            pm_feedback=pm_feedback
        )


class IncorporateFeedbackDialog(QDialog):
    """A simple dialog to get refinement instructions from the PM."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Incorporate Audit Feedback")
        self.setMinimumSize(500, 300)

        self.layout = QVBoxLayout(self)
        self.label = QLabel("Enter your instructions for the AI to refine the plan based on the audit findings:")
        self.label.setWordWrap(True)
        self.text_edit = QTextEdit()
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_feedback(self):
        return self.text_edit.toPlainText().strip()