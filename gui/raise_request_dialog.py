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
        elif initial_request_type == "SPEC_CORRECTION":
            self.ui.specRadioButton.setChecked(True)
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
        self.ui.specRadioButton.toggled.connect(self._update_ui_for_type)

    def _update_ui_for_type(self):
        """Shows or hides the severity dropdown based on the selected request type."""
        is_bug_report = self.ui.bugRadioButton.isChecked()
        self.ui.severityWidget.setVisible(is_bug_report)

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
        elif self.ui.specRadioButton.isChecked():
            request_type = "SPEC_CORRECTION"

        return {
            "request_type": request_type,
            "description": self.ui.descriptionTextEdit.toPlainText().strip(),
            "severity": self.ui.severityComboBox.currentText() if request_type == "BUG_REPORT" else None
        }