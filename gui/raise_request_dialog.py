# gui/raise_request_dialog.py

from PySide6.QtWidgets import QDialog, QMessageBox
from gui.ui_raise_request_dialog import Ui_RaiseRequestDialog

class RaiseRequestDialog(QDialog):
    """
    The logic handler for the Raise Request dialog.
    """
    def __init__(self, parent=None, orchestrator=None, parent_candidates=None, initial_request_type="BACKLOG_ITEM"):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.parent_candidates = parent_candidates or {}
        self.ui = Ui_RaiseRequestDialog()
        self.ui.setupUi(self)

        self.type_map = {
            "Backlog Item": "BACKLOG_ITEM",
            "Bug Report": "BUG_REPORT",
            "Feature": "FEATURE",
            "Epic": "EPIC"
        }

        # FIX: Clear static items from the UI file before adding them programmatically
        self.ui.typeComboBox.clear()
        self.ui.typeComboBox.addItems(self.type_map.keys())

        initial_text = [k for k, v in self.type_map.items() if v == initial_request_type][0]
        if initial_text:
            self.ui.typeComboBox.setCurrentText(initial_text)

        self.connect_signals()
        self._update_ui_for_type()

    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.buttonBox.accepted.connect(self.on_save)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.typeComboBox.currentTextChanged.connect(self._update_ui_for_type)

    def set_edit_mode(self, details: dict):
        """Configures the dialog for editing an existing item."""
        self.setWindowTitle("Edit Backlog Item")
        self.ui.headerLabel.setText(f"Edit Item: {details.get('title')}")

        request_type = details.get('request_type')
        type_text = [k for k, v in self.type_map.items() if v == request_type][0]
        if type_text:
            self.ui.typeComboBox.setCurrentText(type_text)

        self._update_ui_for_type()

        # --- NEW: Combine description and impact analysis for display ---
        description = details.get('description', 'No description provided.')
        analysis = details.get('impact_analysis_details')

        display_text = description
        if analysis and analysis.strip():
            display_text += f"\n\n---\n**Impact Analysis Summary**\n{analysis}"

        self.ui.descriptionTextEdit.setText(display_text)
        # --- END NEW ---

        priority_value = details.get('priority') or details.get('impact_rating', '')
        self.ui.priorityComboBox.setCurrentText(priority_value)
        self.ui.complexityComboBox.setCurrentText(details.get('complexity', ''))

        self.ui.typeComboBox.setEnabled(False)
        self.ui.parentComboBox.setVisible(False)
        self.ui.parentLabel.setVisible(False)

    def _update_ui_for_type(self):
        """Shows or hides fields and populates parent dropdown."""
        selected_type = self.ui.typeComboBox.currentText()
        is_epic = (selected_type == "Epic")
        is_feature = (selected_type == "Feature")
        is_item = (selected_type in ["Backlog Item", "Bug Report"])

        self.ui.parentLabel.setVisible(is_feature or is_item)
        self.ui.parentComboBox.setVisible(is_feature or is_item)
        self.ui.priorityLabel.setVisible(is_item)
        self.ui.priorityComboBox.setVisible(is_item)
        self.ui.complexityLabel.setVisible(is_item)
        self.ui.complexityComboBox.setVisible(is_item)

        if selected_type == "Bug Report":
            self.ui.priorityLabel.setText("Severity:")
            if self.ui.priorityComboBox.count() != 3 or self.ui.priorityComboBox.itemText(0) != "Minor":
                self.ui.priorityComboBox.clear()
                self.ui.priorityComboBox.addItems(["Minor", "Medium", "Major"])
        else:
            self.ui.priorityLabel.setText("Priority:")
            if self.ui.priorityComboBox.count() != 3 or self.ui.priorityComboBox.itemText(0) != "Low":
                self.ui.priorityComboBox.clear()
                self.ui.priorityComboBox.addItems(["Low", "Medium", "High"])

        self.ui.parentComboBox.clear()
        if is_feature:
            self.ui.parentLabel.setText("Parent Epic:")
            # Use the pre-formatted list passed into the constructor
            for text, cr_id in self.parent_candidates.get("epics", []):
                self.ui.parentComboBox.addItem(text, userData=cr_id)
        elif is_item:
            self.ui.parentLabel.setText("Parent Feature:")
            # Use the pre-formatted list passed into the constructor
            for text, cr_id in self.parent_candidates.get("features", []):
                self.ui.parentComboBox.addItem(text, userData=cr_id)

    def on_save(self):
        """Validates input before accepting the dialog."""
        if not self.ui.descriptionTextEdit.toPlainText().strip():
            QMessageBox.warning(self, "Input Required", "The description cannot be empty.")
            return

        selected_type = self.ui.typeComboBox.currentText()
        if selected_type in ["Feature", "Backlog Item", "Bug Report"]:
            if self.ui.parentComboBox.currentIndex() == -1:
                QMessageBox.warning(self, "Input Required", f"A parent must be selected for a {selected_type}.")
                return
        self.accept()

    def get_data(self) -> dict:
        """Returns the data entered into the dialog."""
        selected_type = self.type_map.get(self.ui.typeComboBox.currentText())
        data = {
            "request_type": selected_type,
            "description": self.ui.descriptionTextEdit.toPlainText().strip(),
            "parent_id": self.ui.parentComboBox.currentData()
        }
        if selected_type in ["BACKLOG_ITEM", "BUG_REPORT"]:
            data["complexity"] = self.ui.complexityComboBox.currentText()
            data["severity"] = self.ui.priorityComboBox.currentText()
        return data