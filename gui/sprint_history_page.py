# gui/sprint_history_page.py

import logging
import json
import markdown
from PySide6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QTextEdit,
                               QDialogButtonBox, QAbstractItemView, QHeaderView)
from PySide6.QtCore import Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem

from gui.ui_sprint_history_page import Ui_SprintHistoryPage
from master_orchestrator import MasterOrchestrator
from gui.utils import format_timestamp_for_display

class SprintDetailsDialog(QDialog):
    """A simple dialog to display the sprint's implementation plan."""
    def __init__(self, title, plan_json, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        try:
            plan_data = json.loads(plan_json)
            pretty_json = json.dumps(plan_data, indent=4)
            text_edit.setPlainText(pretty_json)
        except Exception:
            text_edit.setPlainText("Could not parse the implementation plan.")

        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class SprintHistoryPage(QWidget):
    """
    The logic handler for the Sprint History page.
    """
    back_to_workflow = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator

        self.ui = Ui_SprintHistoryPage()
        self.ui.setupUi(self)

        self.model = QStandardItemModel(self)
        self.ui.sprintsTableView.setModel(self.model)
        self.ui.sprintsTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.sprintsTableView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.connect_signals()

    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)
        self.ui.viewDetailsButton.clicked.connect(self.on_view_details_clicked)
        self.ui.sprintsTableView.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def prepare_for_display(self):
        """Fetches and populates the view with the project's sprint history."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Sprint ID', 'Status', 'Start Time', 'End Time', 'Goal'])

        try:
            sprints = self.orchestrator.db_manager.get_all_sprints_for_project(self.orchestrator.project_id)
            for sprint in sprints:
                self.model.appendRow([
                    QStandardItem(sprint['sprint_id']),
                    QStandardItem(sprint['status']),
                    QStandardItem(format_timestamp_for_display(sprint['start_timestamp'])),
                    QStandardItem(format_timestamp_for_display(sprint['end_timestamp'])),
                    QStandardItem(sprint['sprint_goal'])
                ])
        except Exception as e:
            logging.error(f"Failed to populate sprint history: {e}")

        header = self.ui.sprintsTableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._on_selection_changed()

    def _on_selection_changed(self):
        """Enables or disables the 'View Details' button based on selection."""
        is_selection = self.ui.sprintsTableView.selectionModel().hasSelection()
        self.ui.viewDetailsButton.setEnabled(is_selection)

    def on_view_details_clicked(self):
        """Shows the implementation plan for the selected sprint."""
        selection_model = self.ui.sprintsTableView.selectionModel()
        if not selection_model.hasSelection():
            return

        selected_row = selection_model.selectedRows()[0].row()
        sprint_id_item = self.model.item(selected_row, 0)

        sprints = self.orchestrator.db_manager.get_all_sprints_for_project(self.orchestrator.project_id)
        selected_sprint = next((s for s in sprints if s['sprint_id'] == sprint_id_item.text()), None)

        if selected_sprint:
            dialog = SprintDetailsDialog(f"Details for {selected_sprint['sprint_id']}", selected_sprint['sprint_plan_json'], self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Not Found", "Could not retrieve details for the selected sprint.")