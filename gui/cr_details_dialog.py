# gui/cr_details_dialog.py

from PySide6.QtWidgets import QDialog
from gui.ui_cr_details_dialog import Ui_CRDetailsDialog

class CRDetailsDialog(QDialog):
    """
    The logic handler for the CR Details viewing dialog.
    """
    def __init__(self, cr_details: dict, parent=None):
        super().__init__(parent)
        self.ui = Ui_CRDetailsDialog()
        self.ui.setupUi(self)

        self.connect_signals()
        self.set_details(cr_details)

    def connect_signals(self):
        """Connects the close button to the dialog's reject slot."""
        # The QDialogButtonBox automatically connects standard buttons.
        # Connecting rejected signal to the dialog's reject slot is the default.
        self.ui.buttonBox.rejected.connect(self.reject)

    def set_details(self, cr_details: dict):
        """Populates the dialog's widgets with the CR data."""
        if not cr_details:
            self.ui.headerLabel.setText("Error: Details not found.")
            return

        cr_id = cr_details.get('cr_id', 'N/A')
        request_type = cr_details.get('request_type', 'REQUEST').replace('_', ' ').title()
        status = cr_details.get('status', 'N/A')
        description = cr_details.get('description', 'No description provided.')
        analysis = cr_details.get('impact_analysis_details', '')

        # Set the main header
        self.ui.headerLabel.setText(f"{request_type} (CR-{cr_id})")

        # Build the full details text for the text box
        full_details = f"Status: {status}\n\n"
        full_details += "--- Description ---\n"
        full_details += f"{description}\n"

        if analysis:
            full_details += "\n--- Impact Analysis ---\n"
            full_details += analysis

        self.ui.detailsTextEdit.setText(full_details)