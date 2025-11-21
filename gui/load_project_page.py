# gui/load_project_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QAbstractItemView
from PySide6.QtCore import Signal, QItemSelectionModel
from PySide6.QtGui import QStandardItemModel, QStandardItem

from gui.utils import format_timestamp_for_display
from gui.ui_load_project_page import Ui_LoadProjectPage
from master_orchestrator import MasterOrchestrator

class LoadProjectPage(QWidget):
    """
    The logic handler for the Load Archived Project page.
    """
    project_loaded = Signal()
    back_to_main = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator

        self.ui = Ui_LoadProjectPage()
        self.ui.setupUi(self)

        self.current_mode = "history"

        self.model = QStandardItemModel(self)
        self.ui.projectsTableView.setModel(self.model)
        # CORRECTED: Use QAbstractItemView for the enums
        self.ui.projectsTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.projectsTableView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.connect_signals()

    def prepare_for_display(self):
        """Fetches and populates the view based on the current orchestrator phase."""
        self.model.clear()

        phase = self.orchestrator.current_phase.name
        if phase == "VIEWING_ACTIVE_PROJECTS":
            self.current_mode = "active"
            self.ui.headerLabel.setText("Open Project")
            self.ui.instructionLabel.setText("Select a project from your active workspace to resume working on it.")
            self.ui.loadButton.setText("Open Selected Project")
            self.model.setHorizontalHeaderLabels(['Project Name', 'Project Folder (Path)', 'Created On', 'Project ID'])

            projects = self.orchestrator.db_manager.get_all_active_projects()
            for row in projects:
                self.model.appendRow([
                    QStandardItem(row['project_name']), # New Display Name
                    QStandardItem(row['project_root_folder']), # Show the path for clarity
                    QStandardItem(format_timestamp_for_display(row['creation_timestamp'])),
                    QStandardItem(row['project_id'])
                ])
            self.ui.projectsTableView.setColumnHidden(3, True) # Hide Project ID
        else: # Default to VIEWING_PROJECT_HISTORY
            self.current_mode = "history"
            self.ui.headerLabel.setText("Import Archived Project")
            self.ui.instructionLabel.setText("Select a project from the history below to import it into the factory.")
            self.ui.loadButton.setText("Import Selected Project")
            self.model.setHorizontalHeaderLabels(['Project Name', 'Project Folder (Path)', 'Archived On', 'History ID'])

            history = self.orchestrator.get_project_history()
            for row in history:
                self.model.appendRow([
                    QStandardItem(row['project_name']),
                    QStandardItem(row['project_root_folder']),
                    QStandardItem(format_timestamp_for_display(row['last_stop_timestamp'])),
                    QStandardItem(str(row['history_id']))
                ])
            self.ui.projectsTableView.setColumnHidden(3, True) # Hide History ID

        self.ui.projectsTableView.resizeColumnsToContents()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.backButton.clicked.connect(self.back_to_main.emit)
        self.ui.loadButton.clicked.connect(self.on_load_clicked)
        self.ui.deleteButton.clicked.connect(self.on_delete_clicked)

    def _get_selected_id(self):
        """Gets the relevant ID from the hidden last column of the selected row."""
        selection_model = self.ui.projectsTableView.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "Selection Required", "Please select a project from the list.")
            return None

        selected_row = selection_model.selectedRows()[0].row()
        id_item = self.model.item(selected_row, 3) # ID is always in the hidden 3rd column
        return id_item.text()

    def on_load_clicked(self):
        """Handles the load/open action based on the current mode."""
        selected_id = self._get_selected_id()
        if selected_id is None:
            return

        if self.current_mode == "active":
            self.orchestrator.resume_from_idle(selected_id)
        else: # history mode
            self.orchestrator.load_archived_project(int(selected_id))

        self.project_loaded.emit()

    def on_delete_clicked(self):
        """Handles the 'Delete Selected Project' button click for either mode."""
        selected_id = self._get_selected_id()
        if selected_id is None:
            return

        selected_row = self.ui.projectsTableView.selectionModel().selectedRows()[0].row()
        project_name_item = self.model.item(selected_row, 0) # Name is now always in the first column
        project_name = project_name_item.text()

        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to permanently delete the project '{project_name}'?\nThis action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            success = False
            message = "An unknown error occurred."

            if self.current_mode == "active":
                success, message = self.orchestrator.delete_active_project(selected_id)
            else: # history mode
                success, message = self.orchestrator.delete_archived_project(int(selected_id))

            if success:
                QMessageBox.information(self, "Success", message)
                self.prepare_for_display() # Refresh the list
            else:
                QMessageBox.critical(self, "Error", message)