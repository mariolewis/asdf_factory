# gui/raise_request_dialog.py

from PySide6.QtWidgets import (QApplication, QDialog, QMessageBox, QTextEdit,
                               QSizePolicy, QComboBox, QFormLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem

from gui.ui_raise_request_dialog import Ui_RaiseRequestDialog

class RaiseRequestDialog(QDialog):
    """
    The logic handler for the Raise Request dialog.
    """
    def __init__(self, parent=None, orchestrator=None, parent_candidates=None, initial_request_type="BACKLOG_ITEM"):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.parent_candidates = parent_candidates or []
        self.ui = Ui_RaiseRequestDialog()
        self.ui.setupUi(self)

        # FIX: Create our own lookup map to bypass the buggy currentData()
        self.parent_id_map = {}

        # --- Configure Layout and Sizing ---
        self.ui.headerLabel.setWordWrap(True)
        self.ui.parentComboBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ui.formLayout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        screen = QApplication.primaryScreen()
        if screen:
            available_width = screen.availableGeometry().width()
            self.setMaximumWidth(int(available_width * 0.6))
        self.setMinimumWidth(650)

        self.type_map = {
            "Backlog Item": "BACKLOG_ITEM",
            "Change Request": "CHANGE_REQUEST_ITEM",
            "Bug Report": "BUG_REPORT",
            "Feature": "FEATURE",
            "Epic": "EPIC"
        }
        self.ui.typeComboBox.clear()
        self.ui.typeComboBox.addItems(self.type_map.keys())

        initial_text_list = [k for k, v in self.type_map.items() if v == initial_request_type]
        if initial_text_list:
            self.ui.typeComboBox.setCurrentText(initial_text_list[0])

        self.connect_signals()
        self._update_ui_for_type()

    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.buttonBox.accepted.connect(self.on_save)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.typeComboBox.currentTextChanged.connect(self._update_ui_for_type)

    def _populate_parent_combobox(self, valid_parent_types: list):
        """Populates the parent dropdown and our manual ID map."""
        self.ui.parentComboBox.clear()
        self.parent_id_map.clear()

        # Add "(No Parent)" at index 0
        self.ui.parentComboBox.addItem("(No Parent)")
        self.parent_id_map[0] = None

        def recurse_and_add(items, indent_level=0):
            for item in items:
                item_type = item.get("request_type")
                if item_type in valid_parent_types:
                    indent = "  " * indent_level
                    display_text = f"{indent}{item['hierarchical_id']}: {item['title']}"

                    self.ui.parentComboBox.addItem(display_text)
                    # Manually map the new index to its cr_id
                    current_index = self.ui.parentComboBox.count() - 1
                    self.parent_id_map[current_index] = item['cr_id']

                    if "features" in item and item["features"]:
                        recurse_and_add(item["features"], indent_level + 1)

        recurse_and_add(self.parent_candidates)

    def set_edit_mode(self, details: dict):
        self.setWindowTitle("Edit Backlog Item")
        #... (rest of the method is unchanged)
        self.ui.headerLabel.setText(f"Edit Item: {details.get('title')}")

        request_type = details.get('request_type')
        type_text_list = [k for k, v in self.type_map.items() if v == request_type]
        if type_text_list:
            self.ui.typeComboBox.setCurrentText(type_text_list[0])

        self._update_ui_for_type()
        self.ui.descriptionTextEdit.setText(details.get('description', ''))

        priority_value = details.get('priority') or details.get('impact_rating', '')
        self.ui.priorityComboBox.setCurrentText(priority_value)
        self.ui.complexityComboBox.setCurrentText(details.get('complexity', ''))

        self.ui.typeComboBox.setEnabled(False)
        self.ui.parentComboBox.setVisible(False)
        self.ui.parentLabel.setVisible(False)


    def _update_ui_for_type(self):
        """Shows or hides fields and populates parent dropdown based on the selected item type."""
        selected_type = self.ui.typeComboBox.currentText()
        is_epic = (selected_type == "Epic")
        is_feature = (selected_type == "Feature")
        is_item = (selected_type in ["Backlog Item", "Change Request", "Bug Report"])

        # Control visibility of fields
        self.ui.priorityLabel.setVisible(is_item)
        self.ui.priorityComboBox.setVisible(is_item)
        self.ui.complexityLabel.setVisible(is_item)
        self.ui.complexityComboBox.setVisible(is_item)

        parent_visible = not is_epic
        self.ui.parentLabel.setVisible(parent_visible)
        self.ui.parentComboBox.setVisible(parent_visible)

        # Filter and populate parent combobox
        if is_feature:
            self._populate_parent_combobox(valid_parent_types=["EPIC"])
        elif is_item:
            self._populate_parent_combobox(valid_parent_types=["EPIC", "FEATURE"])

        if selected_type == "Bug Report":
            self.ui.priorityLabel.setText("Severity:")
            if self.ui.priorityComboBox.count() != 3 or self.ui.priorityComboBox.itemText(0) != "Minor":
                self.ui.priorityComboBox.clear()
                self.ui.priorityComboBox.addItems(["Minor", "Medium", "Major"])
            self.ui.descriptionLabel.setText("Bug Details (Observed/Expected/Steps):")
        else:
            self.ui.priorityLabel.setText("Priority:")
            if self.ui.priorityComboBox.count() != 3 or self.ui.priorityComboBox.itemText(0) != "Low":
                self.ui.priorityComboBox.clear()
                self.ui.priorityComboBox.addItems(["Low", "Medium", "High"])
            self.ui.descriptionLabel.setText("Description:")

    def on_save(self):
        """Validates input before accepting the dialog."""
        if not self.ui.descriptionTextEdit.toPlainText().strip():
            QMessageBox.warning(self, "Input Required", "The description cannot be empty.")
            return

        self.accept()

    def get_data(self) -> dict:
        """Returns the data entered into the dialog."""
        selected_type = self.type_map.get(self.ui.typeComboBox.currentText())

        # Get the correct parent_id from our reliable map.
        parent_id = self.parent_id_map.get(self.ui.parentComboBox.currentIndex())

        data = {
            "request_type": selected_type,
            "description": self.ui.descriptionTextEdit.toPlainText().strip(),
            # THIS IS THE FIX: Instead of the unreliable isVisible(), we check the item type.
            "parent_id": parent_id if selected_type != "EPIC" else None
        }

        if selected_type in ["BACKLOG_ITEM", "CHANGE_REQUEST_ITEM", "BUG_REPORT"]:
            data["complexity"] = self.ui.complexityComboBox.currentText()
            if selected_type == "Bug Report":
                data["severity"] = self.ui.priorityComboBox.currentText()
            else:
                data["priority"] = self.ui.priorityComboBox.currentText()

        return data