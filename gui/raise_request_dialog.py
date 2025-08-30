# gui/raise_request_dialog.py

from PySide6.QtWidgets import QDialog, QMessageBox
from gui.ui_raise_request_dialog import Ui_RaiseRequestDialog

class RaiseRequestDialog(QDialog):
    """
    The logic handler for the Raise Request dialog.
    """
    def __init__(self, parent=None, initial_request_type="CHANGE_REQUEST"):
        super().__init__(parent)
        self.ui = Ui_RaiseRequestDialog()
        self.ui.setupUi(self)

        if initial_request_type == "BUG_REPORT":
            self.ui.bugRadioButton.setChecked(True)
        else: # Default to Change Request
            self.ui.crRadioButton.setChecked(True)

        self.connect_signals()
        # Initial UI state setup is now handled by the logic above
        self._update_ui_for_type()

    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.buttonBox.accepted.connect(self.on_save)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.bugRadioButton.toggled.connect(self._update_ui_for_type)
        self.ui.crRadioButton.toggled.connect(self._update_ui_for_type)

    def set_edit_mode(self, details: dict):
        """Configures the dialog for editing an existing item."""
        self.setWindowTitle("Edit Backlog Item")
        self.ui.headerLabel.setText("Edit Backlog Item")

        # Pre-populate fields
        self.ui.descriptionTextEdit.setText(details.get('description', ''))
        self.ui.complexityComboBox.setCurrentText(details.get('complexity', ''))

        # Handle priority/severity pre-population
        request_type = details.get('request_type')
        if request_type == 'BUG_REPORT':
            self.ui.bugRadioButton.setChecked(True)
            priority_value = details.get('impact_rating', '')
            self.ui.severityComboBox.setCurrentText(priority_value)
        else:
            self.ui.crRadioButton.setChecked(True)
            priority_value = details.get('priority', '')
            # We need to make the severity widget visible and set its value
            self.ui.severityWidget.setVisible(True)
            self.ui.severityLabel.setText("Priority:")
            self.ui.severityComboBox.setCurrentText(priority_value)

        # Disable the type-switching radio buttons during an edit
        self.ui.typeGroupBox.setEnabled(False)

    def _update_ui_for_type(self):
        """Shows the priority/severity dropdown and updates its label."""
        self.ui.severityWidget.setVisible(True) # Always visible now
        if self.ui.bugRadioButton.isChecked():
            self.ui.severityLabel.setText("Severity:")
        else:
            self.ui.severityLabel.setText("Priority:")

    def on_save(self):
        """Validates input before accepting the dialog."""
        if not self.ui.descriptionTextEdit.toPlainText().strip():
            QMessageBox.warning(self, "Input Required", "The description cannot be empty.")
            return # Prevent the dialog from closing

        # If all validation passes, accept the dialog
        self.accept()

    def get_data(self) -> dict:
        """Returns the data entered into the dialog."""
        request_type = "CHANGE_REQUEST"
        if self.ui.bugRadioButton.isChecked():
            request_type = "BUG_REPORT"

        return {
            "request_type": request_type,
            "description": self.ui.descriptionTextEdit.toPlainText().strip(),
            "severity": self.ui.severityComboBox.currentText(), # Always get the current text
            "complexity": self.ui.complexityComboBox.currentText()
        }