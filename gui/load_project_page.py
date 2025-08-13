# gui/load_project_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QAbstractItemView
from PySide6.QtCore import Signal, QItemSelectionModel
from PySide6.QtGui import QStandardItemModel, QStandardItem

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

        self.model = QStandardItemModel(self)
        self.ui.projectsTableView.setModel(self.model)
        # CORRECTED: Use QAbstractItemView for the enums
        self.ui.projectsTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.projectsTableView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.connect_signals()

    def prepare_for_display(self):
        """Fetches the project history and populates the table view."""
        logging.info("Refreshing archived projects list.")
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['ID', 'Project Name', 'Project ID', 'Archived On', 'Archive Path'])

        try:
            history = self.orchestrator.get_project_history()
            if not history:
                return

            for row in history:
                self.model.appendRow([
                    QStandardItem(str(row['history_id'])),
                    QStandardItem(row['project_name']),
                    QStandardItem(row['project_id']),
                    QStandardItem(row['last_stop_timestamp']),
                    QStandardItem(row['archive_file_path'])
                ])
            self.ui.projectsTableView.resizeColumnsToContents()
            self.ui.projectsTableView.setColumnHidden(2, True) # Hide Project ID
            self.ui.projectsTableView.setColumnHidden(4, True) # Hide Archive Path
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project history:\n{e}")

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.backButton.clicked.connect(self.back_to_main.emit)
        self.ui.loadButton.clicked.connect(self.on_load_clicked)
        self.ui.deleteButton.clicked.connect(self.on_delete_clicked)

    def _get_selected_history_id(self):
        """Gets the history_id from the selected row in the table."""
        selection_model = self.ui.projectsTableView.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "Selection Required", "Please select a project from the list.")
            return None

        selected_row = selection_model.selectedRows()[0].row()
        history_id_item = self.model.item(selected_row, 0) # ID is in the first column
        return int(history_id_item.text())

    def on_load_clicked(self):
        """Handles the 'Load Selected Project' button click."""
        history_id = self._get_selected_history_id()
        if history_id is None:
            return

        self.orchestrator.load_archived_project(history_id)
        self.project_loaded.emit()

    def on_delete_clicked(self):
        """Handles the 'Delete Selected Project' button click."""
        history_id = self._get_selected_history_id()
        if history_id is None:
            return

        selected_row = self.ui.projectsTableView.selectionModel().selectedRows()[0].row()
        project_name_item = self.model.item(selected_row, 1)
        project_name = project_name_item.text()

        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to permanently delete the project '{project_name}'?\nThis action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            success, message = self.orchestrator.delete_archived_project(history_id)
            if success:
                QMessageBox.information(self, "Success", message)
                self.prepare_for_display()
            else:
                QMessageBox.critical(self, "Error", message)