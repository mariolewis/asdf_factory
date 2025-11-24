# gui/legal_dialog.py

from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
import resources
from gui.ui_legal_dialog import Ui_LegalDialog

class LegalDialog(QDialog):
    """
    A blocking dialog that forces the user to accept the EULA and Privacy Policy.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_LegalDialog()
        self.ui.setupUi(self)

        # Load texts from the protected resources file
        self.ui.eulaTextEdit.setPlainText(resources.EULA_TEXT)
        self.ui.privacyTextEdit.setPlainText(resources.PRIVACY_POLICY_TEXT)

        # Navigation Requirement Logic
        self.visited_tabs = {0} # Set of visited tab indices (starts with 0/EULA)

        # Connect signals
        self.ui.tabWidget.currentChanged.connect(self.on_tab_changed)
        self.ui.consentCheckBox.stateChanged.connect(self.on_consent_changed)
        self.ui.acceptButton.clicked.connect(self.accept)
        self.ui.exitButton.clicked.connect(self.reject)

    def on_tab_changed(self, index):
        """Tracks which tabs the user has viewed."""
        self.visited_tabs.add(index)

        # Check if both tabs (0 and 1) have been visited
        if 0 in self.visited_tabs and 1 in self.visited_tabs:
            self.ui.consentCheckBox.setEnabled(True)

            # Update label text
            self.ui.validationLabel.setText("Thank you. You may now proceed.")

            # Update style dynamically using the property defined in style.qss
            self.ui.validationLabel.setProperty("state", "success")
            self.ui.validationLabel.style().unpolish(self.ui.validationLabel)
            self.ui.validationLabel.style().polish(self.ui.validationLabel)

    def on_consent_changed(self, state):
        """Enables the Accept button only when the checkbox is checked."""
        is_checked = (state == Qt.Checked.value)
        self.ui.acceptButton.setEnabled(is_checked)