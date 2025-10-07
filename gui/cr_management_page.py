import logging
from PySide6.QtWidgets import (QWidget, QMessageBox, QHeaderView, QAbstractItemView, QMenu, QTreeView,
                               QDialog, QVBoxLayout, QLineEdit, QTextEdit, QDialogButtonBox, QComboBox, QFileDialog)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction, QColor
from PySide6.QtCore import Signal, Qt, QItemSelectionModel, QThreadPool
from datetime import datetime
from pathlib import Path

from gui.ui_cr_management_page import Ui_CRManagementPage
from master_orchestrator import MasterOrchestrator, FactoryPhase
from gui.raise_request_dialog import RaiseRequestDialog
from gui.cr_details_dialog import CRDetailsDialog
from gui.worker import Worker
from gui.utils import format_timestamp_for_display
from master_orchestrator import FactoryPhase

# Note: The EditItemDialog is now handled by the more capable RaiseRequestDialog in edit mode.

class CRManagementPage(QWidget):
    sync_items_to_tool = Signal(list)
    implement_cr = Signal(int)
    analyze_cr = Signal(dict)
    delete_cr = Signal(int)
    import_from_tool = Signal()
    save_new_order = Signal(list)
    generate_technical_preview = Signal(dict)
    request_ui_refresh = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_CRManagementPage()
        self.ui.setupUi(self)
        self.threadpool = QThreadPool()
        self.staged_sprint_items = set()
        self.is_reorder_mode = False
        self.model = QStandardItemModel(self)
        self.ui.crTreeView.setModel(self.model)
        self._create_more_actions_menu()
        self._configure_tree_view()
        self.connect_signals()
        self._exit_reorder_mode(refresh=False)

    def clear_sprint_staging(self):
        """Public method to allow the main window to clear the staging set."""
        logging.info("Clearing sprint staging set for new sprint planning session.")
        self.staged_sprint_items.clear()

    def _create_more_actions_menu(self):
        self.more_actions_menu = QMenu(self)
        self.edit_action = self.more_actions_menu.addAction("Edit Item")
        self.delete_action = self.more_actions_menu.addAction("Delete Item")
        self.more_actions_menu.addSeparator()
        self.analyze_action = self.more_actions_menu.addAction("Run Impact Analysis")
        self.implement_action = self.more_actions_menu.addAction("Implement Item")
        self.tech_preview_action = self.more_actions_menu.addAction("Generate Technical Preview")
        self.more_actions_menu.addSeparator()
        self.import_action = self.more_actions_menu.addAction("Import from Tool...")
        self.sync_action = self.more_actions_menu.addAction("Sync to Tool")
        self.ui.moreActionsButton.setMenu(self.more_actions_menu)

    def _configure_tree_view(self):
        self.model.setHorizontalHeaderLabels(['#', 'Title', 'Type', 'Status', 'Priority/Severity', 'Complexity', 'Last Modified'])
        self.ui.crTreeView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.crTreeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.crTreeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.crTreeView.setSortingEnabled(False)
        self.ui.crTreeView.header().setStretchLastSection(False)

        # Set specific widths for columns for better default layout
        self.ui.crTreeView.setColumnWidth(0, 100)    # Number
        self.ui.crTreeView.setColumnWidth(1, 350)   # Title
        self.ui.crTreeView.setColumnWidth(2, 100)   # Type
        self.ui.crTreeView.setColumnWidth(3, 120)   # Status
        self.ui.crTreeView.setColumnWidth(4, 110)   # Priority/Severity
        self.ui.crTreeView.setColumnWidth(5, 100)   # Complexity
        self.ui.crTreeView.setColumnWidth(6, 120)   # Last Modified

        # Allow the Title column to be resized by the user, which enables the scrollbar
        self.ui.crTreeView.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)

        # Allow the Title column to be resized by the user, which enables the scrollbar
        self.ui.crTreeView.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)

    def connect_signals(self):
        self.ui.primaryActionButton.clicked.connect(self.on_primary_action_clicked)
        self.ui.addNewItemButton.clicked.connect(self.on_add_item_clicked)
        self.ui.reorderButton.clicked.connect(self.on_reorder_clicked)
        self.ui.cancelReorderButton.clicked.connect(self.on_cancel_reorder_clicked)
        self.ui.saveOrderButton.clicked.connect(self.on_save_order_clicked)
        self.ui.moveUpButton.clicked.connect(self.on_move_up_clicked)
        self.ui.moveDownButton.clicked.connect(self.on_move_down_clicked)
        self.ui.crTreeView.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.ui.crTreeView.doubleClicked.connect(self.on_item_double_clicked)
        self.ui.crTreeView.customContextMenuRequested.connect(self.show_context_menu)
        self.ui.saveBacklogButton.clicked.connect(self.on_save_backlog_clicked)
        self.edit_action.triggered.connect(self.on_edit_clicked)
        self.delete_action.triggered.connect(self.on_delete_item)
        self.analyze_action.triggered.connect(self.on_run_full_analysis_clicked)
        self.implement_action.triggered.connect(self.on_implement_clicked)
        self.tech_preview_action.triggered.connect(self.on_generate_tech_preview_clicked)
        self.import_action.triggered.connect(self.import_from_tool.emit)
        self.sync_action.triggered.connect(self.on_sync_clicked)
        self.ui.backButton.clicked.connect(self.on_back_clicked)

    def prepare_for_display(self):
        """
        Updates the backlog view and dynamically shows or hides the 'Back' button
        based on the previous workflow phase.
        """
        self.update_backlog_view()

        # Show the back button only if we navigated here from the dashboard.
        prev_phase = getattr(self.window(), 'previous_phase', FactoryPhase.IDLE)
        is_from_dashboard = (prev_phase == FactoryPhase.AWAITING_BROWNFIELD_STRATEGY)
        self.ui.backButton.setVisible(is_from_dashboard)

    def update_backlog_view(self):
        selection_model = self.ui.crTreeView.selectionModel()
        selection_model.blockSignals(True)
        self.model.clear()
        self._configure_tree_view()
        self.ui.crTreeView.header().setVisible(True)

        try:
            full_hierarchy = self.orchestrator.get_full_backlog_hierarchy()
            if full_hierarchy:
                self._populate_from_dict(self.model.invisibleRootItem(), full_hierarchy)
                self.ui.crTreeView.expandAll()
        except Exception as e:
            logging.error(f"Failed to populate backlog tree view: {e}", exc_info=True)

        self.model.layoutChanged.emit()
        selection_model.blockSignals(False)
        self._on_selection_changed()

    def _populate_from_dict(self, parent_item, items, prefix=""):
        status_colors = { "IMPACT_ANALYZED": QColor("#007ACC"), "IMPLEMENTATION_IN_PROGRESS": QColor("#FFC66D"), "COMPLETED": QColor("#6A8759"), "DEBUG_PM_ESCALATION": QColor("#CC7832"), "KNOWN_ISSUE": QColor("#CC7832"), "BLOCKED": QColor("#CC7832") }
        priority_colors = { "High": QColor("#CC7832"), "Major": QColor("#CC7832"), "Medium": QColor("#FFC66D"), "Low": QColor("#6A8759"), "Minor": QColor("#6A8759") }
        complexity_colors = {"Large": QColor("#CC7832"), "Medium": QColor("#FFC66D"), "Small": QColor("#6A8759")}

        for i, item_data in enumerate(items, 1):
            current_prefix = f"{prefix}{i}"
            item_data['hierarchical_id'] = current_prefix
            full_title_tooltip = item_data.get('title', 'N/A')

            num_item = QStandardItem(current_prefix)
            num_item.setData(item_data, Qt.UserRole)

            title_item = QStandardItem(item_data['title'])

            timestamp_str = item_data.get('last_modified_timestamp') or item_data.get('creation_timestamp')
            formatted_date = format_timestamp_for_display(timestamp_str)
            last_modified_item = QStandardItem(formatted_date)

            type_item = QStandardItem(item_data['request_type'].replace('_', ' ').title())
            status_item = QStandardItem(item_data['status'])
            priority = item_data.get('priority') or item_data.get('impact_rating') or ''
            priority_item = QStandardItem(priority)
            complexity = item_data.get('complexity') or ''
            complexity_item = QStandardItem(complexity)

            # Highlight the row if the item is staged for the sprint
            if item_data['cr_id'] in self.staged_sprint_items:
                amber_color = QColor("#FFAB00") # As per GUI Design System: Warning Color
                for cell_item in [num_item, title_item, type_item, status_item, priority_item, complexity_item, last_modified_item]:
                    cell_item.setBackground(amber_color)

            # gui/cr_management_page.py

            # Set colors
            if item_data['status'] == 'EXISTING':
                muted_color = QColor("#888888") # Muted Text color from Design System
                for cell_item in [num_item, title_item, type_item, status_item, priority_item, complexity_item, last_modified_item]:
                    cell_item.setForeground(muted_color)
            else:
                if item_data['status'] in status_colors: status_item.setForeground(status_colors[item_data['status']])
                if priority in priority_colors: priority_item.setForeground(priority_colors[priority])
                if complexity in complexity_colors: complexity_item.setForeground(complexity_colors[complexity])

            # Add Tooltips
            for cell_item in [num_item, title_item, type_item, status_item, priority_item, complexity_item, last_modified_item]:
                cell_item.setToolTip(full_title_tooltip)

            parent_item.appendRow([num_item, title_item, type_item, status_item, priority_item, complexity_item, last_modified_item])

            if "features" in item_data and item_data["features"]:
                self._populate_from_dict(num_item, item_data["features"], prefix=f"{current_prefix}.")
            elif "user_stories" in item_data and item_data["user_stories"]:
                self._populate_from_dict(num_item, item_data["user_stories"], prefix=f"{current_prefix}.")

    def _get_selected_item_and_data(self):
        selection_model = self.ui.crTreeView.selectionModel()
        if not selection_model.hasSelection(): return None, None
        index = selection_model.selectedRows()[0]
        num_item = self.model.itemFromIndex(index.siblingAtColumn(0))
        if not num_item: return None, None
        return num_item, num_item.data(Qt.UserRole)

    def on_change_status_clicked(self, new_status: str):
        """Handles the context menu action to manually change an item's status."""
        item, data = self._get_selected_item_and_data()
        if not data:
            return

        cr_id = data['cr_id']
        hierarchical_id = data.get('hierarchical_id', f'CR-{cr_id}')
        reply = QMessageBox.question(self, "Confirm Status Change",
                                     f"Are you sure you want to manually change the status of item {hierarchical_id} to '{new_status}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Use the new generic orchestrator method
            self.orchestrator.manually_update_cr_status(cr_id, new_status)
            self.update_backlog_view() # Refresh the UI to show the change

    # In gui/cr_management_page.py

    def show_context_menu(self, position):
        """Creates and shows a context menu on right-click."""
        index = self.ui.crTreeView.indexAt(position)
        menu = QMenu()

        if index.isValid():
            item, item_data = self._get_selected_item_and_data()
            if item_data:
                item_type = item_data.get("request_type")
                item_status = item_data.get("status")
                cr_id = item_data.get("cr_id")

                is_actionable = item_status != 'EXISTING'

                # --- Sprint Actions (only for actionable items) ---
                if is_actionable:
                    is_eligible_for_sprint = item_status in ["TO_DO", "IMPACT_ANALYZED"]
                    is_staged_for_sprint = cr_id in self.staged_sprint_items

                    add_sprint_action = QAction("Add to Sprint Scope", self)
                    add_sprint_action.triggered.connect(self.on_add_to_sprint_scope)
                    add_sprint_action.setEnabled(is_eligible_for_sprint and not is_staged_for_sprint)
                    menu.addAction(add_sprint_action)

                    remove_sprint_action = QAction("Remove from Sprint Scope", self)
                    remove_sprint_action.triggered.connect(self.on_remove_from_sprint_scope)
                    remove_sprint_action.setEnabled(is_staged_for_sprint)
                    menu.addAction(remove_sprint_action)
                    menu.addSeparator()

                # --- Add Child Actions (always enabled) ---
                if item_type == "EPIC":
                    add_feature_action = QAction("Add Feature to this Epic...", self)
                    add_feature_action.triggered.connect(lambda: self.on_add_item_clicked("FEATURE"))
                    menu.addAction(add_feature_action)
                elif item_type == "FEATURE":
                    add_story_action = QAction("Add Backlog Item to this Feature...", self)
                    add_story_action.triggered.connect(lambda: self.on_add_item_clicked("BACKLOG_ITEM"))
                    menu.addAction(add_story_action)

                if item_type in ["EPIC", "FEATURE"]:
                    menu.addSeparator()

                # --- Modification Actions (only for actionable items) ---
                if is_actionable:
                    if item_type == "BUG_REPORT" or item_status == "BLOCKED":
                        status_menu = QMenu("Change Status", self)
                        set_completed_action = QAction("Set as Completed", self)
                        set_completed_action.triggered.connect(lambda: self.on_change_status_clicked("COMPLETED"))
                        status_menu.addAction(set_completed_action)

                        set_cancelled_action = QAction("Set as Cancelled", self)
                        set_cancelled_action.triggered.connect(lambda: self.on_change_status_clicked("CANCELLED"))
                        status_menu.addAction(set_cancelled_action)
                        menu.addMenu(status_menu)
                        menu.addSeparator()

                    edit_action = QAction("Edit Item...", self)
                    edit_action.triggered.connect(self.on_edit_clicked)
                    menu.addAction(edit_action)

                    delete_action = QAction("Delete Selected Item(s)", self)
                    delete_action.triggered.connect(self.on_delete_item)
                    menu.addAction(delete_action)
        else:
            add_epic_action = QAction("Add New Epic...", self)
            add_epic_action.triggered.connect(lambda: self.on_add_item_clicked("EPIC"))
            menu.addAction(add_epic_action)

        menu.exec(self.ui.crTreeView.viewport().mapToGlobal(position))

    def on_add_to_sprint_scope(self):
        """Adds all selected, eligible items to the sprint staging set."""
        selection_model = self.ui.crTreeView.selectionModel()
        if not selection_model.hasSelection():
            return

        for index in selection_model.selectedRows():
            num_item = self.model.itemFromIndex(index.siblingAtColumn(0))
            if num_item:
                data = num_item.data(Qt.UserRole)
                if data and data.get('cr_id'):
                    self.staged_sprint_items.add(data['cr_id'])

        self.update_backlog_view()

    def on_remove_from_sprint_scope(self):
        """Removes all selected items from the sprint staging set."""
        selection_model = self.ui.crTreeView.selectionModel()
        if not selection_model.hasSelection():
            return

        for index in selection_model.selectedRows():
            num_item = self.model.itemFromIndex(index.siblingAtColumn(0))
            if num_item:
                data = num_item.data(Qt.UserRole)
                if data and data.get('cr_id'):
                    self.staged_sprint_items.discard(data['cr_id'])

        self.update_backlog_view()

    def _get_parent_candidates_for_dialog(self):
        """Traverses the model to get formatted names and IDs for parent selection."""
        candidates = {"epics": [], "features": []}
        root = self.model.invisibleRootItem()
        for i in range(root.rowCount()):
            epic_item = root.child(i, 0)
            epic_data = epic_item.data(Qt.UserRole)
            epic_text = f"{epic_item.text()}: {epic_data['title']}"
            candidates["epics"].append((epic_text, epic_data['cr_id']))
            for j in range(epic_item.rowCount()):
                feature_item = epic_item.child(j, 0)
                feature_data = feature_item.data(Qt.UserRole)
                feature_text = f"{feature_item.text()}: {feature_data['title']}"
                candidates["features"].append((feature_text, feature_data['cr_id']))
        return candidates

    def on_item_double_clicked(self, index):
        """Handles opening the edit dialog when an item is double-clicked."""
        self.on_edit_clicked()

    def on_add_item_clicked(self, item_type_to_add=None):
        """Handles creating a new backlog item by launching a non-blocking dialog."""
        parent_candidates = self.orchestrator._get_backlog_with_hierarchical_numbers()
        initial_type = item_type_to_add if item_type_to_add else "BACKLOG_ITEM"

        # FIX: Make the dialog an instance variable to prevent garbage collection.
        self.dialog = RaiseRequestDialog(self, orchestrator=self.orchestrator, parent_candidates=parent_candidates, initial_request_type=initial_type)

        if item_type_to_add:
            item, data = self._get_selected_item_and_data()
            if data:
                parent_id_to_select = data.get("cr_id")
                for i in range(self.dialog.ui.parentComboBox.count()):
                    if self.dialog.ui.parentComboBox.itemData(i) == parent_id_to_select:
                        self.dialog.ui.parentComboBox.setCurrentIndex(i)
                        break

        self.dialog.accepted.connect(self._on_dialog_accepted)
        self.dialog.open()

    def _on_dialog_accepted(self):
        """Handles the logic after the RaiseRequestDialog is successfully saved."""
        # FIX: Get data from the persistent instance variable self.dialog.
        new_data = self.dialog.get_data()

        final_parent_id = new_data.get("parent_id")

        success, _ = self.orchestrator.add_new_backlog_item(new_data)

        if success:
            self.update_backlog_view()
        else:
            QMessageBox.critical(self, "Error", "Failed to save the new item.")

    def on_delete_item(self):
        selection_model = self.ui.crTreeView.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "No Selection", "Please select item(s) to delete.")
            return

        selected_rows = selection_model.selectedRows()
        item_names = [self.model.itemFromIndex(index.siblingAtColumn(1)).text() for index in selected_rows]

        reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to permanently delete {len(item_names)} item(s) and all their children?\n - {', '.join(item_names)}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            ids_to_delete = []
            for index in selected_rows:
                num_item = self.model.itemFromIndex(index.siblingAtColumn(0))
                if num_item and num_item.data(Qt.UserRole):
                    ids_to_delete.append(num_item.data(Qt.UserRole)['cr_id'])

            for cr_id in ids_to_delete:
                self.orchestrator.delete_backlog_item(cr_id)
            self.update_backlog_view()

    def on_edit_clicked(self):
        item, data = self._get_selected_item_and_data()
        if not data: return

        parent_candidates = self.orchestrator._get_backlog_with_hierarchical_numbers()
        dialog = RaiseRequestDialog(self, orchestrator=self.orchestrator, parent_candidates=parent_candidates)
        dialog.set_edit_mode(data)

        if dialog.exec():
            new_data = dialog.get_data()
            if self.orchestrator.save_edited_change_request(data['cr_id'], new_data):
                self.update_backlog_view()
            else:
                QMessageBox.critical(self, "Error", "Failed to save changes.")

    def on_run_full_analysis_clicked(self):
        """Handles the new 'Run Full Analysis' action."""
        item, data = self._get_selected_item_and_data()
        if data:
            # Re-using the existing analyze_cr signal for this enhanced action
            self.analyze_cr.emit(data)

    def on_analyze_clicked(self):
        item, data = self._get_selected_item_and_data()
        if data and data.get('request_type') in ["BACKLOG_ITEM", "BUG_REPORT"]: self.analyze_cr.emit(data)

    def on_implement_clicked(self):
        item, data = self._get_selected_item_and_data()
        if data and data.get('request_type') in ["BACKLOG_ITEM", "BUG_REPORT"]: self.implement_cr.emit(data['cr_id'])

    def on_generate_tech_preview_clicked(self):
        """Handles the signal to generate a technical preview for a CR."""
        item, data = self._get_selected_item_and_data()
        if data:
            self.generate_technical_preview.emit(data)

    def on_sync_clicked(self):
        selection_model = self.ui.crTreeView.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "No Selection", "Please select one or more items to sync.")
            return

        cr_ids_to_sync = []
        for index in selection_model.selectedRows():
            num_item = self.model.itemFromIndex(index.siblingAtColumn(0))
            data = num_item.data(Qt.UserRole)
            if data and not data.get('external_id'):
                cr_ids_to_sync.append(data['cr_id'])

        if cr_ids_to_sync:
            self.sync_items_to_tool.emit(cr_ids_to_sync)
        else:
            QMessageBox.information(self, "Already Synced", "All selected items have already been synced to the external tool.")

    def on_reorder_clicked(self):
        self.is_reorder_mode = True
        self.ui.actionButtonStackedWidget.setCurrentWidget(self.ui.reorderModePage)
        self.ui.crTreeView.setDragDropMode(QAbstractItemView.InternalMove)
        self.ui.crTreeView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.crTreeView.setSortingEnabled(False)
        self._on_selection_changed()

    def _exit_reorder_mode(self, refresh=True):
        self.is_reorder_mode = False
        self.ui.actionButtonStackedWidget.setCurrentWidget(self.ui.normalModePage)
        self.ui.crTreeView.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.ui.crTreeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.ui.crTreeView.setSortingEnabled(False) # Keep sorting disabled to preserve order
        if refresh: self.update_backlog_view()

    def on_cancel_reorder_clicked(self):
        self._exit_reorder_mode(refresh=True)

    def on_save_order_clicked(self):
        if not self.is_reorder_mode: return
        order_mapping = []

        def recurse_and_map(parent_item):
            for i in range(parent_item.rowCount()):
                child_item = parent_item.child(i, 0)
                child_data = child_item.data(Qt.UserRole)
                order_mapping.append((i + 1, child_data['cr_id']))
                if child_item.hasChildren():
                    recurse_and_map(child_item)

        recurse_and_map(self.model.invisibleRootItem())
        self.orchestrator.handle_save_cr_order(order_mapping)
        self._exit_reorder_mode(refresh=True)
        QMessageBox.information(self, "Success", "The new backlog order has been saved.")

    def on_move_up_clicked(self):
        selection_model = self.ui.crTreeView.selectionModel()
        if not selection_model.hasSelection(): return
        index = selection_model.selectedRows()[0]
        if not index.isValid() or index.row() == 0: return
        parent_index = index.parent()
        parent_item = self.model.itemFromIndex(parent_index) if parent_index.isValid() else self.model.invisibleRootItem()
        row = index.row()
        row_items = parent_item.takeRow(row)
        parent_item.insertRow(row - 1, row_items)
        new_index = self.model.index(row - 1, 0, parent_index)
        selection_model.select(new_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    def on_move_down_clicked(self):
        selection_model = self.ui.crTreeView.selectionModel()
        if not selection_model.hasSelection(): return
        index = selection_model.selectedRows()[0]
        if not index.isValid(): return
        parent_index = index.parent()
        parent_item = self.model.itemFromIndex(parent_index) or self.model.invisibleRootItem()
        row = index.row()
        if row >= parent_item.rowCount() - 1: return
        row_items = parent_item.takeRow(row)
        parent_item.insertRow(row + 1, row_items)
        new_index = self.model.index(row + 1, 0, parent_index)
        selection_model.select(new_index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    def on_primary_action_clicked(self):
        """
        Handles the click event for the "Plan Sprint" button. It uses the
        staged items set as the source of truth.
        """
        if not self.staged_sprint_items:
            QMessageBox.warning(self, "No Items Staged", "Please add one or more eligible items to the sprint scope using the right-click menu before planning.")
            return

        eligible_ids = list(self.staged_sprint_items)

        # The rest of the logic proceeds as before, but with the staged IDs
        self.window().setEnabled(False)
        self.window().statusBar().showMessage("Initiating sprint planning...")
        worker = Worker(self.orchestrator.initiate_sprint_planning, eligible_ids)
        worker.signals.finished.connect(self._on_pre_execution_check_finished)
        self.threadpool.start(worker)

        # Clear the staging set now that the sprint plan is being generated
        # self.staged_sprint_items.clear()

    def _on_pre_execution_check_finished(self):
        """Called when the background pre-execution check is complete."""
        self.window().setEnabled(True)
        self.window().statusBar().clearMessage()
        # The orchestrator's state has now changed, so we trigger a UI refresh
        self.request_ui_refresh.emit()

    def _on_selection_changed(self):
        """
        Updates the enabled/disabled state of all action buttons based on the
        current selection in the tree view and the overall sprint status.
        """
        has_items = self.model.rowCount() > 0
        self.ui.reorderButton.setEnabled(has_items)

        # --- Sprint Action Button Logic ---
        is_sprint_active = self.orchestrator.is_sprint_active()
        if is_sprint_active:
            self.ui.primaryActionButton.setEnabled(False)
            self.ui.primaryActionButton.setToolTip("Cannot plan a new sprint while another is in progress.")
        else:
            self.ui.primaryActionButton.setEnabled(bool(self.staged_sprint_items))
            self.ui.primaryActionButton.setToolTip("Plan a new sprint with the staged items.")

        # --- More Actions Menu Logic ---
        selection_model = self.ui.crTreeView.selectionModel()
        has_selection = selection_model.hasSelection()

        # The "More Actions" button itself is always enabled to allow access to "Import".
        self.ui.moreActionsButton.setEnabled(True)
        # The "Import" action is always enabled.
        self.import_action.setEnabled(True)

        # By default, disable all selection-dependent actions.
        self.edit_action.setEnabled(False)
        self.delete_action.setEnabled(False)
        self.analyze_action.setEnabled(False)
        self.tech_preview_action.setEnabled(False)
        self.sync_action.setEnabled(False)
        self.implement_action.setEnabled(False)

        if not has_selection:
            return # No more logic needed if nothing is selected.

        # Logic for actions that require at least ONE item to be selected
        can_delete = False
        can_sync = False
        for index in selection_model.selectedRows():
            num_item = self.model.itemFromIndex(index.siblingAtColumn(0))
            if num_item:
                data = num_item.data(Qt.UserRole)
                if data and data.get('status') != 'EXISTING':
                    can_delete = True
                if data and not data.get('external_id'):
                    can_sync = True
        self.delete_action.setEnabled(can_delete)
        self.sync_action.setEnabled(can_sync)

        # Logic for actions that require exactly ONE item to be selected
        if len(selection_model.selectedRows()) == 1:
            item, data = self._get_selected_item_and_data()
            if data and data.get('status') != 'EXISTING':
                item_status = data.get("status", "")
                self.edit_action.setEnabled(True)

                can_analyze = item_status in ["CHANGE_REQUEST", "BUG_RAISED", "BLOCKED", "TO_DO"]
                self.analyze_action.setEnabled(can_analyze)

                # "Implement" is only available after analysis is complete.
                can_implement = item_status in ["IMPACT_ANALYZED", "TECHNICAL_PREVIEW_COMPLETE"]
                self.implement_action.setEnabled(can_implement)

                # "Generate Technical Preview" is available once analysis is done.
                self.tech_preview_action.setEnabled(item_status == "IMPACT_ANALYZED")

    def on_save_backlog_clicked(self):
        """Handles the user's request to save the backlog to an XLSX file."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "An active project is required to save the backlog.")
            return

        try:
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise ValueError("Project root folder is not set.")

            project_root = Path(project_details['project_root_folder'])
            backlog_dir = project_root / "backlog"
            backlog_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = backlog_dir / f"{self.orchestrator.project_name}_Backlog_{timestamp}.xlsx"

            file_path, _ = QFileDialog.getSaveFileName(self, "Save Backlog As", str(default_filename), "Excel Files (*.xlsx)")

            if file_path:
                self.window().setEnabled(False)
                self.window().statusBar().showMessage("Generating and saving backlog report...")
                worker = Worker(self._task_save_backlog, file_path)
                worker.signals.result.connect(self._handle_save_backlog_result)
                worker.signals.error.connect(self._on_pre_execution_check_finished) # Can reuse this handler for errors
                self.threadpool.start(worker)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to prepare for backlog export:\n{e}")

    def _task_save_backlog(self, file_path, **kwargs):
        """Background worker task to get XLSX data and save it."""
        xlsx_bytes_io = self.orchestrator.export_backlog_to_xlsx()
        if xlsx_bytes_io:
            with open(file_path, 'wb') as f:
                f.write(xlsx_bytes_io.getbuffer())
            return (True, file_path)
        return (False, "Failed to generate backlog data.")

    def _handle_save_backlog_result(self, result):
        """Handles the result of the background save task."""
        self.window().setEnabled(True)
        self.window().statusBar().clearMessage()
        success, message = result
        if success:
            QMessageBox.information(self, "Success", f"Successfully saved backlog to:\n{message}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save backlog: {message}")

    def on_back_clicked(self):
        """Returns the UI to the brownfield project dashboard."""
        self.orchestrator.set_phase("AWAITING_BROWNFIELD_STRATEGY")
        self.request_ui_refresh.emit()