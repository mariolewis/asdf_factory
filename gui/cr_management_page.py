# gui/cr_management_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QHeaderView, QAbstractItemView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal, QItemSelection, Qt

from gui.ui_cr_management_page import Ui_CRManagementPage
from master_orchestrator import MasterOrchestrator

class CRManagementPage(QWidget):
    """
    The logic handler for the Change Request and Bug Management page.
    """
    back_to_workflow = Signal()
    implement_cr = Signal(int)
    analyze_cr = Signal(int)
    edit_cr = Signal(int)
    delete_cr = Signal(int)

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_CRManagementPage()
        self.ui.setupUi(self)

        self.model = QStandardItemModel(self)
        self.ui.crTableView.setModel(self.model)

        self.connect_signals()
        self._configure_table_view()

    def prepare_for_display(self):
        """Called by the main window to refresh the data."""
        self.update_cr_table()

    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)
        self.ui.crTableView.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Connect action buttons to their handlers
        self.ui.editButton.clicked.connect(self.on_edit_clicked)
        self.ui.deleteButton.clicked.connect(self.on_delete_clicked)
        self.ui.analyzeButton.clicked.connect(self.on_analyze_clicked)
        self.ui.implementButton.clicked.connect(self.on_implement_clicked)


    def _configure_table_view(self):
        """Sets up the initial properties for the table view."""
        self.ui.crTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.crTableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.crTableView.setSortingEnabled(True)
        header = self.ui.crTableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Impact
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Description

        # Initially disable all action buttons
        self.on_selection_changed()

    def update_cr_table(self):
        """Populates the table with the latest CR and Bug data."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['ID', 'Type', 'Status', 'Severity/Impact', 'Description'])

        if not self.orchestrator.project_id:
            return

        try:
            requests = self.orchestrator.get_all_change_requests()
            for req in requests:
                req_type = req['request_type'].replace('_', ' ').title()

                id_item = QStandardItem(str(req['cr_id']))
                type_item = QStandardItem(req_type)
                status_item = QStandardItem(req['status'])
                impact_item = QStandardItem(req['impact_rating'] if req['impact_rating'] else "N/A")
                desc_item = QStandardItem(req['description'])

                # Store the raw data in the first item for easy retrieval
                id_item.setData(req, Qt.UserRole)

                self.model.appendRow([id_item, type_item, status_item, impact_item, desc_item])

        except Exception as e:
            logging.error(f"Failed to update CR management table: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load change requests: {e}")

    def on_selection_changed(self):
        """Enables/disables action buttons based on the selected item's status."""
        selected_cr = self._get_selected_cr_data()

        is_raised = False
        is_analyzed = False
        genesis_complete = self.orchestrator.is_genesis_complete

        if selected_cr:
            status = selected_cr['status']
            is_raised = (status == 'RAISED')
            is_analyzed = (status == 'IMPACT_ANALYZED')

        self.ui.editButton.setEnabled(is_raised)
        self.ui.deleteButton.setEnabled(is_raised)
        self.ui.analyzeButton.setEnabled(is_raised)
        self.ui.implementButton.setEnabled(is_analyzed and genesis_complete)

    def _get_selected_cr_data(self) -> dict | None:
        """Retrieves the full data dictionary for the currently selected CR."""
        selection_model = self.ui.crTableView.selectionModel()
        if not selection_model.hasSelection():
            return None

        selected_index = selection_model.selectedRows()[0]
        id_item = self.model.item(selected_index.row(), 0)
        return id_item.data(Qt.UserRole)

    def on_edit_clicked(self):
        cr_data = self._get_selected_cr_data()
        if cr_data:
            QMessageBox.information(self, "Not Implemented", f"Editing for CR-{cr_data['cr_id']} is not yet implemented.")
            # self.edit_cr.emit(cr_data['cr_id'])

    def on_delete_clicked(self):
        cr_data = self._get_selected_cr_data()
        if cr_data:
            QMessageBox.information(self, "Not Implemented", f"Deletion for CR-{cr_data['cr_id']} is not yet implemented.")
            # self.delete_cr.emit(cr_data['cr_id'])

    def on_analyze_clicked(self):
        cr_data = self._get_selected_cr_data()
        if cr_data:
            QMessageBox.information(self, "Not Implemented", f"Impact analysis for CR-{cr_data['cr_id']} is not yet implemented.")
            # self.analyze_cr.emit(cr_data['cr_id'])

    def on_implement_clicked(self):
        cr_data = self._get_selected_cr_data()
        if cr_data:
            QMessageBox.information(self, "Not Implemented", f"Implementation for CR-{cr_data['cr_id']} is not yet implemented.")
            # self.implement_cr.emit(cr_data['cr_id'])