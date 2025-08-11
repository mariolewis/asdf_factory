# gui/cr_management_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QHeaderView, QAbstractItemView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal, Qt

from gui.ui_cr_management_page import Ui_CRManagementPage
from master_orchestrator import MasterOrchestrator
from gui.cr_details_dialog import CRDetailsDialog

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
        # Ensure buttons are in a reasonable default state
        is_project_active = self.orchestrator.project_id is not None
        self.ui.editButton.setEnabled(is_project_active)
        self.ui.deleteButton.setEnabled(is_project_active)
        self.ui.analyzeButton.setEnabled(is_project_active)
        self.ui.implementButton.setEnabled(is_project_active)


    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)
        self.ui.crTableView.doubleClicked.connect(self.on_cr_double_clicked)
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
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

    def update_cr_table(self):
        """Populates the table with the latest CR and Bug data."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['ID', 'Type', 'Status', 'Severity/Impact', 'Description', 'Analysis Summary'])
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
                analysis_item = QStandardItem(req['impact_analysis_details'] if req['impact_analysis_details'] else "")
                self.model.appendRow([id_item, type_item, status_item, impact_item, desc_item, analysis_item])
        except Exception as e:
            logging.error(f"Failed to update CR management table: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load change requests: {e}")

    def _get_selected_cr_id_and_details(self):
        """Gets the ID and full details of the selected row. Returns (None, None) if no selection."""
        selection_model = self.ui.crTableView.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "No Selection", "Please select an item from the table first.")
            return None, None

        selected_index = selection_model.selectedRows()[0]
        id_item = self.model.item(selected_index.row(), 0)
        if not id_item:
            return None, None

        try:
            cr_id = int(id_item.text())
            details = self.orchestrator.get_cr_details_by_id(cr_id)
            return cr_id, details
        except (ValueError, TypeError):
            return None, None

    def on_cr_double_clicked(self, index):
        """Handles double-clicking a row to show the details dialog."""
        if not index.isValid():
            return

        cr_id, cr_details = self._get_selected_cr_id_and_details()
        if cr_details:
            dialog = CRDetailsDialog(cr_details, self)
            dialog.exec()

    def on_edit_clicked(self):
        cr_id, details = self._get_selected_cr_id_and_details()
        if not cr_id:
            return
        if details.get('status') == 'RAISED':
            self.edit_cr.emit(cr_id)
        else:
            QMessageBox.warning(self, "Action Not Allowed", "Items can only be edited when their status is 'RAISED'.")

    def on_delete_clicked(self):
        cr_id, details = self._get_selected_cr_id_and_details()
        if not cr_id:
            return
        if details.get('status') == 'RAISED':
            self.delete_cr.emit(cr_id)
        else:
            QMessageBox.warning(self, "Action Not Allowed", "Items can only be deleted when their status is 'RAISED'.")

    def on_analyze_clicked(self):
        cr_id, details = self._get_selected_cr_id_and_details()
        if not cr_id:
            return
        if details.get('status') == 'RAISED':
            self.analyze_cr.emit(cr_id)
        else:
            QMessageBox.warning(self, "Action Not Allowed", "Impact analysis can only be run on items with a 'RAISED' status.")

    def on_implement_clicked(self):
        cr_id, details = self._get_selected_cr_id_and_details()
        if not cr_id:
            return

        genesis_complete = self.orchestrator.is_genesis_complete
        if not genesis_complete:
            QMessageBox.warning(self, "Action Not Allowed", "Implementation is only available after the main development plan is complete.")
            return

        if details.get('status') == 'IMPACT_ANALYZED':
            self.implement_cr.emit(cr_id)
        else:
            QMessageBox.warning(self, "Action Not Allowed", "Items can only be implemented when their status is 'IMPACT_ANALYZED'.")