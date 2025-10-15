# gui/new_project_dialog.py

from PySide6.QtWidgets import QDialog

from gui.ui_new_project_dialog import Ui_NewProjectDialog

class NewProjectDialog(QDialog):
    """
    The logic handler for the initial project workflow selection dialog.
    This dialog prompts the user to choose between creating a project
    from a new specification or from an existing codebase.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_NewProjectDialog()
        self.ui.setupUi(self)

        self.connect_signals()
        self.setup_initial_state()

    def connect_signals(self):
        """Connects the dialog's buttons to their handler slots."""
        # Connect the new "Create..." button to accept the dialog.
        self.ui.createGreenfieldButton.clicked.connect(self.accept)
        # Connect the new "Onboard..." button to the custom codebase slot.
        self.ui.onboardBrownfieldButton.clicked.connect(self.on_codebase_clicked)
        # The QDialogButtonBox's "Cancel" button is auto-connected to reject()
        self.ui.buttonBox.rejected.connect(self.reject)

    def on_codebase_clicked(self):
        """A custom slot to set a result property before accepting."""
        self.result = "codebase"
        self.accept()

    def setup_initial_state(self):
        """Sets the initial state of the dialog's widgets."""
        self.result = "spec" # Default result

        # Set object names for styling
        self.ui.headerLabel.setObjectName("headerLabel")
        self.ui.greenfieldTitleLabel.setObjectName("reviewHeaderLabel")
        self.ui.brownfieldTitleLabel.setObjectName("reviewHeaderLabel")
        self.ui.instructionLabel.setObjectName("instructionLabel")
        self.ui.greenfieldDescLabel.setObjectName("instructionLabel")
        self.ui.brownfieldDescLabel.setObjectName("instructionLabel")