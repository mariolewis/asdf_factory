import logging
from datetime import datetime
from PySide6.QtWidgets import QWidget, QMessageBox, QHeaderView, QAbstractItemView, QMenu
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Signal, Qt, QItemSelectionModel

from gui.ui_cr_management_page import Ui_CRManagementPage
from master_orchestrator import MasterOrchestrator
from gui.cr_details_dialog import CRDetailsDialog

class CRManagementPage(QWidget):
    """
    The logic handler for the Project Backlog page.
    """
    back_to_workflow = Signal()
    add_new_item = Signal()
    sync_items_to_tool = Signal(list) # Changed from single to list
    implement_cr = Signal(int)
    analyze_cr = Signal(int)
    edit_cr = Signal(int)
    delete_cr = Signal(int)
    proceed_to_tech_spec = Signal()
    import_from_tool = Signal()
    save_new_order = Signal(list)

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_CRManagementPage()
        self.ui.setupUi(self)
        self.is_reorder_mode = False
        self.cached_model_state = []

        self.model = QStandardItemModel(self)
        self.ui.crTableView.setModel(self.model)

        self._create_more_actions_menu()
        self._configure_table_view()
        self.connect_signals()

    def _create_more_actions_menu(self):
        """Creates the QMenu and QActions for the 'More Actions...' button."""
        self.more_actions_menu = QMenu(self)
        self.edit_action = self.more_actions_menu.addAction("Edit Item")
        self.delete_action = self.more_actions_menu.addAction("Delete Item")
        self.more_actions_menu.addSeparator()
        self.analyze_action = self.more_actions_menu.addAction("Run Impact Analysis")
        self.implement_action = self.more_actions_menu.addAction("Implement Item")
        self.more_actions_menu.addSeparator()
        self.import_action = self.more_actions_menu.addAction("Import from Tool...")
        self.sync_action = self.more_actions_menu.addAction("Sync to Tool") # Text is now dynamic

        self.ui.moreActionsButton.setMenu(self.more_actions_menu)

    def prepare_for_display(self):
        """Called by the main window to refresh the data and set button states."""
        self.update_cr_table()

        project_settings = self.orchestrator.get_project_integration_settings()
        provider = project_settings.get("provider", "None")
        is_integration_configured = provider != "None"

        # Dynamically set menu text
        self.import_action.setText(f"Import from {provider}..." if is_integration_configured else "Import from Tool...")
        self.sync_action.setText(f"Sync to {provider}" if is_integration_configured else "Sync to Tool")

        self.import_action.setEnabled(is_integration_configured)
        self._on_selection_changed(None, None)

    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)
        self.ui.crTableView.clicked.connect(self.on_table_clicked)
        self.ui.crTableView.doubleClicked.connect(self.on_cr_double_clicked)
        self.ui.crTableView.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # Page-level buttons
        self.ui.addNewItemButton.clicked.connect(self.add_new_item.emit)
        self.ui.reorderButton.clicked.connect(self.on_reorder_clicked)
        self.ui.clearSelectionButton.clicked.connect(self.on_clear_selection_clicked)
        self.ui.proceedToTechSpecButton.clicked.connect(self.proceed_to_tech_spec.emit)

        # Actions from the "More Actions..." menu
        self.edit_action.triggered.connect(self.on_edit_clicked)
        self.delete_action.triggered.connect(self.on_delete_clicked)
        self.analyze_action.triggered.connect(self.on_analyze_clicked)
        self.implement_action.triggered.connect(self.on_implement_clicked)
        self.import_action.triggered.connect(self.import_from_tool.emit)
        self.sync_action.triggered.connect(self.on_sync_clicked)

        # Reorder Mode Buttons
        self.ui.cancelReorderButton.clicked.connect(self.on_cancel_reorder_clicked)
        self.ui.saveOrderButton.clicked.connect(self.on_save_order_clicked)
        self.ui.moveUpButton.clicked.connect(self.on_move_up_clicked)
        self.ui.moveDownButton.clicked.connect(self.on_move_down_clicked)

    def on_clear_selection_clicked(self):
        """Clears the current table selection."""
        self.ui.crTableView.clearSelection()

    def on_table_clicked(self, index):
        """Clears the selection if the user clicks on an empty area of the table."""
        if not index.isValid():
            self.ui.crTableView.clearSelection()

    def _configure_table_view(self):
        """Sets up the initial properties for the table view."""
        self.ui.crTableView.setSelectionMode(QAbstractItemView.ExtendedSelection) # Enable multi-select
        self.ui.crTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.crTableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.crTableView.horizontalHeader().setVisible(True)
        self.ui.crTableView.verticalHeader().setVisible(False)

    def _on_selection_changed(self, selected, deselected):
        """Enables/disables actions based on selection and the current UI mode."""
        selection_model = self.ui.crTableView.selectionModel()
        has_selection = selection_model.hasSelection()

        if self.is_reorder_mode:
            # Handle button states for reorder mode
            if not has_selection:
                self.ui.moveUpButton.setEnabled(False)
                self.ui.moveDownButton.setEnabled(False)
            else:
                selected_row = selection_model.selectedRows()[0].row()
                # Boundary check: Only enable move up if not the first item
                self.ui.moveUpButton.setEnabled(selected_row > 0)
                # Boundary check: Only enable move down if not the last item
                self.ui.moveDownButton.setEnabled(selected_row < self.model.rowCount() - 1)
        else:
            # Handle button states for normal mode
            self.ui.moreActionsButton.setEnabled(True)

            # Default item-specific actions to disabled
            self.edit_action.setEnabled(False)
            self.delete_action.setEnabled(False)
            self.analyze_action.setEnabled(False)
            self.implement_action.setEnabled(False)
            self.sync_action.setEnabled(False)

            if has_selection:
                selected_rows = selection_model.selectedRows()

                # Edit is only enabled for a single selection
                if len(selected_rows) == 1:
                    details = self._get_selected_cr_details(suppress_warning=True)
                    if details:
                        is_raised = details.get('status') == 'RAISED'
                        is_analyzed = details.get('status') == 'IMPACT_ANALYZED'
                        genesis_complete = self.orchestrator.is_genesis_complete

                        if is_raised or is_analyzed:
                            self.edit_action.setEnabled(True)
                        self.analyze_action.setEnabled(True)
                        if is_analyzed and genesis_complete:
                            self.implement_action.setEnabled(True)

                # Delete and Sync can work on multiple items
                self.delete_action.setEnabled(True)

                can_sync = False
                for index in selected_rows:
                    details = self._get_cr_details_for_row(index.row())
                    if details and not details.get('external_id'):
                        can_sync = True
                        break

                project_settings = self.orchestrator.get_project_integration_settings()
                provider = project_settings.get("provider", "None")
                if provider != "None":
                    self.sync_action.setEnabled(can_sync)

    def on_reorder_clicked(self):
        """Enters the UI reordering mode."""
        self._enter_reorder_mode()

    def _enter_reorder_mode(self):
        """Switches the UI to reorder mode."""
        self.ui.crTableView.clearSelection()
        self.is_reorder_mode = True
        self.ui.actionButtonStackedWidget.setCurrentWidget(self.ui.reorderModePage)
        self.ui.crTableView.setDragDropMode(QAbstractItemView.InternalMove)
        self.ui.crTableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.crTableView.setSortingEnabled(False) # Disable sorting during reorder

        # Cache the current order
        self.cached_model_state = []
        for row in range(self.model.rowCount()):
            row_items = [self.model.item(row, col).clone() for col in range(self.model.columnCount())]
            self.cached_model_state.append(row_items)

        # Initial button state
        self.ui.moveUpButton.setEnabled(False)
        self.ui.moveDownButton.setEnabled(False)

    def _exit_reorder_mode(self, restore_state=False):
        """Switches the UI back to normal mode."""
        if restore_state:
            self.model.clear()
            # Re-apply header labels after clearing the model
            self.model.setHorizontalHeaderLabels(['#', 'Type', 'Status', 'Description', 'Priority', 'Complexity', 'External ID', 'Last Modified'])
            self._configure_table_view()
            for row_items in self.cached_model_state:
                self.model.appendRow(row_items)

        self.is_reorder_mode = False
        self.cached_model_state = []
        self.ui.actionButtonStackedWidget.setCurrentWidget(self.ui.normalModePage)
        self.ui.crTableView.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.ui.crTableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.crTableView.setSortingEnabled(True)

    def on_move_up_clicked(self):
        """Moves the selected item up one row."""
        selection_model = self.ui.crTableView.selectionModel()
        if not selection_model.hasSelection():
            return

        current_row = selection_model.selectedRows()[0].row()
        if current_row > 0:
            row_items = self.model.takeRow(current_row)
            self.model.insertRow(current_row - 1, row_items)
            # Re-select the moved item
            new_index = self.model.index(current_row - 1, 0)
            selection_model.setCurrentIndex(new_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    def on_move_down_clicked(self):
        """Moves the selected item down one row."""
        selection_model = self.ui.crTableView.selectionModel()
        if not selection_model.hasSelection():
            return

        current_row = selection_model.selectedRows()[0].row()
        if current_row < self.model.rowCount() - 1:
            row_items = self.model.takeRow(current_row)
            self.model.insertRow(current_row + 1, row_items)
            # Re-select the moved item
            new_index = self.model.index(current_row + 1, 0)
            selection_model.setCurrentIndex(new_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    def on_cancel_reorder_clicked(self):
        """Cancels reordering and restores the original table state."""
        self._exit_reorder_mode(restore_state=True)

    def on_save_order_clicked(self):
        """Saves the new item order to the database."""
        if not self.is_reorder_mode:
            return

        order_mapping = []
        for row in range(self.model.rowCount()):
            cr_id_item = self.model.item(row, 0)
            cr_id = cr_id_item.data(Qt.UserRole) # Use data role instead of text
            # display_order is 1-based, row is 0-based
            order_mapping.append((row + 1, cr_id))

        self.save_new_order.emit(order_mapping)
        self._exit_reorder_mode()
        self.update_cr_table()
        QMessageBox.information(self, "Success", "The new backlog order has been saved.")

    def update_cr_table(self):
        """
        Fetches all CRs/Bugs for the active project and populates the table.
        """
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['#', 'Title', 'Type', 'Status', 'Description', 'Priority', 'Complexity', 'External ID', 'Last Modified'])

        project_id = self.orchestrator.project_id
        if not project_id:
            return

        try:
            change_requests = self.orchestrator.get_all_change_requests()
            for i, cr in enumerate(change_requests, 1):
                type_display = cr['request_type'].replace('_', ' ').title()
                if type_display == "Change Request":
                    type_display = "CR"
                elif type_display == "Bug Report":
                    type_display = "Bug"

                ts_string = cr['last_modified_timestamp'] or cr['creation_timestamp']
                formatted_date = "N/A"
                if ts_string:
                    try:
                        dt_obj = datetime.fromisoformat(ts_string)
                        formatted_date = dt_obj.astimezone().strftime('%x')
                    except (ValueError, TypeError):
                        formatted_date = "Invalid Date"

                display_id_item = QStandardItem(str(i))
                display_id_item.setData(cr['cr_id'], Qt.UserRole)

                title_item = QStandardItem(cr['title'])
                type_item = QStandardItem(type_display)
                status_item = QStandardItem(cr['status'])
                desc_item = QStandardItem(cr['description'])
                priority_to_display = cr['priority'] or cr['impact_rating'] or 'N/A'
                priority_item = QStandardItem(priority_to_display)
                complexity_item = QStandardItem(cr['complexity'] or 'N/A')
                external_id_item = QStandardItem(cr['external_id'] or '')
                modified_item = QStandardItem(formatted_date)

                self.model.appendRow([display_id_item, title_item, type_item, status_item, desc_item, priority_item, complexity_item, external_id_item, modified_item])

        except Exception as e:
            logging.error(f"Failed to update CR Management table: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load project backlog:\n{e}")

        # Configure column resizing rules
        header = self.ui.crTableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # '#'
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # Description
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Priority
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Complexity
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # External ID
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents) # Last Modified

        # Set reasonable initial widths for the interactive columns
        self.ui.crTableView.setColumnWidth(1, 250) # Title
        self.ui.crTableView.setColumnWidth(4, 350) # Description

    def _get_cr_details_for_row(self, row):
        """Helper to get CR details for a specific row index."""
        if row < 0 or row >= self.model.rowCount():
            return None
        id_item = self.model.item(row, 0)
        if not id_item:
            return None
        try:
            cr_id = id_item.data(Qt.UserRole) # Use data role instead of text
            return self.orchestrator.get_cr_details_by_id(cr_id)
        except (ValueError, TypeError):
            return None

    def _get_selected_cr_details(self, suppress_warning=False):
        """Gets the full details of the first selected row."""
        selection_model = self.ui.crTableView.selectionModel()
        if not selection_model.hasSelection():
            if not suppress_warning:
                QMessageBox.warning(self, "No Selection", "Please select an item from the table first.")
            return None
        return self._get_cr_details_for_row(selection_model.selectedRows()[0].row())

    def on_cr_double_clicked(self, index):
        """
        Handles the event when a user double-clicks an item in the CR table.
        """
        if not index.isValid():
            return

        selected_row = index.row()
        cr_id_item = self.model.item(selected_row, 0)
        if not cr_id_item:
            return

        try:
            cr_id = cr_id_item.data(Qt.UserRole) # Use the stored real ID
            if cr_id is None: return

            cr_details = self.orchestrator.get_cr_details_by_id(cr_id)
            if cr_details:
                dialog = CRDetailsDialog(cr_details, self)
                dialog.exec()
        except Exception as e:
            logging.error(f"Could not process CR double-click: {e}")

    def on_edit_clicked(self):
        details = self._get_selected_cr_details()
        if details: self.edit_cr.emit(details['cr_id'])

    def on_delete_clicked(self):
        selection_model = self.ui.crTableView.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "No Selection", "Please select item(s) to delete.")
            return

        ids_to_delete = [self.model.item(index.row(), 0).data(Qt.UserRole) for index in selection_model.selectedRows()]
        for cr_id in ids_to_delete:
            self.delete_cr.emit(cr_id)

    def on_analyze_clicked(self):
        details = self._get_selected_cr_details()
        if details: self.analyze_cr.emit(details['cr_id'])

    def on_implement_clicked(self):
        details = self._get_selected_cr_details()
        if details: self.implement_cr.emit(details['cr_id'])

    def on_sync_clicked(self):
        """Gathers all selected, unsynced items and emits a signal."""
        selection_model = self.ui.crTableView.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "No Selection", "Please select item(s) to sync.")
            return

        ids_to_sync = []
        for index in selection_model.selectedRows():
            details = self._get_cr_details_for_row(index.row())
            if details and not details.get('external_id'):
                ids_to_sync.append(details['cr_id'])

        if ids_to_sync:
            self.sync_items_to_tool.emit(ids_to_sync)
        else:
            QMessageBox.information(self, "Already Synced", "All selected items have already been synced.")

