import logging
import json
from PySide6.QtWidgets import (QWidget, QMessageBox, QHeaderView, QAbstractItemView, QTreeView,
                               QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox, QMenu)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction
from PySide6.QtCore import Signal, Qt

from gui.ui_backlog_ratification_page import Ui_BacklogRatificationPage
from master_orchestrator import MasterOrchestrator

# A self-contained dialog for editing items
class EditItemDialog(QDialog):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Backlog Item")
        self.setMinimumWidth(500)

        self.layout = QVBoxLayout(self)
        self.formLayout = QFormLayout()

        self.titleEdit = QLineEdit(item_data.get("title", ""))
        self.descriptionEdit = QTextEdit(item_data.get("description", ""))
        self.descriptionEdit.setMinimumHeight(100)

        self.formLayout.addRow("Title:", self.titleEdit)
        self.formLayout.addRow("Description:", self.descriptionEdit)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addLayout(self.formLayout)
        self.layout.addWidget(self.buttonBox)

    def get_data(self):
        return {
            "title": self.titleEdit.text().strip(),
            "description": self.descriptionEdit.toPlainText().strip()
        }


class BacklogRatificationPage(QWidget):
    """
    The logic handler for the new, tree-based Backlog Ratification page.
    """
    backlog_ratified = Signal(list)

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_BacklogRatificationPage()
        self.ui.setupUi(self)

        self.model = QStandardItemModel(self)
        self.ui.backlogTreeView.setModel(self.model)
        self._configure_tree_view()
        self.connect_signals()

    def _configure_tree_view(self):
        """Sets the tree view headers and column resizing behavior."""
        self.model.setHorizontalHeaderLabels(['Title', 'Description', 'Priority', 'Complexity'])
        self.ui.backlogTreeView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.backlogTreeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Enable custom context menus (for right-click)
        self.ui.backlogTreeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.backlogTreeView.setColumnWidth(0, 300) # Title
        self.ui.backlogTreeView.setColumnWidth(1, 450) # Description

    def connect_signals(self):
        """Connects the page's buttons and signals to their handler methods."""
        self.ui.addEpicButton.clicked.connect(self.on_add_epic)
        self.ui.deleteItemButton.clicked.connect(self.on_delete_item)
        self.ui.ratifyButton.clicked.connect(self.on_ratify_clicked)
        self.ui.backlogTreeView.doubleClicked.connect(self.on_item_double_clicked)
        self.ui.backlogTreeView.customContextMenuRequested.connect(self.show_context_menu)

    def on_item_double_clicked(self, index):
        """Handles opening the edit dialog when an item is double-clicked."""
        if not index.isValid():
            return
        title_item = self.model.itemFromIndex(index.siblingAtColumn(0))
        if not title_item:
            return
        item_data = title_item.data(Qt.UserRole)
        if not item_data:
            return

        dialog = EditItemDialog(item_data, self)
        if dialog.exec():
            new_data = dialog.get_data()

            item_data["title"] = new_data["title"]
            item_data["description"] = new_data["description"]
            title_item.setData(item_data, Qt.UserRole)

            title_item.setText(new_data["title"])
            desc_item = self.model.itemFromIndex(index.siblingAtColumn(1))
            if desc_item:
                desc_item.setText(new_data["description"])

    def prepare_for_display(self):
        """Loads the AI-generated nested backlog and populates the tree."""
        self.model.clear()
        self._configure_tree_view()

        task = self.orchestrator.task_awaiting_approval or {}
        items_json_str = task.get("generated_backlog_items", "[]")
        try:
            items = json.loads(items_json_str)
            self._populate_model_recursive(self.model.invisibleRootItem(), items)
            self.ui.backlogTreeView.expandAll()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse or display the backlog hierarchy: {e}")

    def _populate_model_recursive(self, parent_item, items_list):
        """Recursively populates the model from a nested list of dicts."""
        for item_data in items_list:
            title_item = QStandardItem(item_data.get('title', ''))
            title_item.setData(item_data, Qt.UserRole)
            row_items = [
                title_item,
                QStandardItem(item_data.get('description', '')),
                QStandardItem(item_data.get('priority', '')),
                QStandardItem(item_data.get('complexity', ''))
            ]
            parent_item.appendRow(row_items)
            if "features" in item_data:
                self._populate_model_recursive(title_item, item_data["features"])
            elif "user_stories" in item_data:
                self._populate_model_recursive(title_item, item_data["user_stories"])

    def show_context_menu(self, position):
        """Creates and shows a context menu on right-click."""
        index = self.ui.backlogTreeView.indexAt(position)
        menu = QMenu()

        if index.isValid():
            item = self.model.itemFromIndex(index)
            item_data = item.data(Qt.UserRole)
            item_type = item_data.get("type")

            if item_type == "EPIC":
                add_feature_action = QAction("Add Feature to this Epic", self)
                add_feature_action.triggered.connect(lambda: self.on_add_feature(item))
                menu.addAction(add_feature_action)
            elif item_type == "FEATURE":
                add_story_action = QAction("Add User Story to this Feature", self)
                add_story_action.triggered.connect(lambda: self.on_add_user_story(item))
                menu.addAction(add_story_action)

            menu.addSeparator()
            delete_action = QAction("Delete Selected Item", self)
            delete_action.triggered.connect(self.on_delete_item)
            menu.addAction(delete_action)
        else:
            add_epic_action = QAction("Add New Epic", self)
            add_epic_action.triggered.connect(self.on_add_epic)
            menu.addAction(add_epic_action)

        menu.exec(self.ui.backlogTreeView.viewport().mapToGlobal(position))

    def on_add_epic(self):
        self._add_new_item(self.model.invisibleRootItem(), "EPIC")

    def on_add_feature(self, parent_item):
        self._add_new_item(parent_item, "FEATURE")

    def on_add_user_story(self, parent_item):
        self._add_new_item(parent_item, "BACKLOG_ITEM")

    def _add_new_item(self, parent_item, item_type):
        """Generic handler for adding a new item to the tree."""
        new_item_data = {
            "type": item_type,
            "title": f"New {item_type.replace('_', ' ').title()}",
            "description": ""
        }
        if item_type == "BACKLOG_ITEM":
            new_item_data["priority"] = "Medium"
            new_item_data["complexity"] = "Medium"

        dialog = EditItemDialog(new_item_data, self)
        if dialog.exec():
            final_data = dialog.get_data()
            new_item_data.update(final_data)

            title_item = QStandardItem(new_item_data["title"])
            title_item.setData(new_item_data, Qt.UserRole)

            row_items = [
                title_item,
                QStandardItem(new_item_data["description"]),
                QStandardItem(new_item_data.get("priority", "")),
                QStandardItem(new_item_data.get("complexity", ""))
            ]
            parent_item.appendRow(row_items)
            self.ui.backlogTreeView.expand(parent_item.index())

    def on_delete_item(self):
        """Deletes the selected item from the tree."""
        index = self.ui.backlogTreeView.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "No Selection", "Please select an item to delete.")
            return

        item = self.model.itemFromIndex(index)
        reply = QMessageBox.question(self, "Confirm Deletion", f"Are you sure you want to delete '{item.text()}' and all its children?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.model.removeRow(index.row(), index.parent())

    def _traverse_model_to_json(self, parent_item):
        """Recursively traverses the model to build the final JSON list."""
        items_list = []
        for row in range(parent_item.rowCount()):
            title_item = parent_item.child(row, 0)
            item_data = title_item.data(Qt.UserRole).copy() # Work on a copy

            # Recursively get children and update the dictionary
            if item_data.get("type") == "EPIC":
                item_data["features"] = self._traverse_model_to_json(title_item)
            elif item_data.get("type") == "FEATURE":
                item_data["user_stories"] = self._traverse_model_to_json(title_item)

            items_list.append(item_data)
        return items_list

    def on_ratify_clicked(self):
        """Traverses the tree, rebuilds the nested list, and emits the signal."""
        final_backlog_hierarchy = self._traverse_model_to_json(self.model.invisibleRootItem())

        if not final_backlog_hierarchy:
            QMessageBox.warning(self, "Empty Backlog", "Cannot ratify an empty backlog.")
            return

        self.backlog_ratified.emit(final_backlog_hierarchy)