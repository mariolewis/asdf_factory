# gui/new_project_dialog.py

from PySide6.QtWidgets import QDialog

# This import is created by the pyside6-uic command you will run
from gui.ui_new_project_dialog import Ui_NewProjectDialog

class NewProjectDialog(QDialog):
    """
    The logic handler for the initial project workflow selection dialog.
    This dialog prompts the user to choose between creating a project
    from a new specification or (in the future) from an existing codebase.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_NewProjectDialog()
        self.ui.setupUi(self)

        self.connect_signals()
        self.setup_initial_state()

    def connect_signals(self):
        """Connects the dialog's buttons to their handler slots."""
        # Connect the "Create from a New Specification" button to accept the dialog.
        self.ui.fromSpecButton.clicked.connect(self.accept)
        # The QDialogButtonBox's "Cancel" button is auto-connected to reject()
        self.ui.buttonBox.rejected.connect(self.reject)

    def setup_initial_state(self):
        """Sets the initial state of the dialog's widgets."""
        # The "Work with an Existing Codebase" button is disabled as it is a future feature.
        self.ui.fromCodebaseButton.setEnabled(False) #
        self.ui.fromCodebaseButton.setToolTip("This feature will be enabled in a future version.")