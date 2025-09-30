# gui/new_project_dialog.py

from PySide6.QtWidgets import QDialog
from gui.ui_new_project_dialog import Ui_NewProjectDialog

class NewProjectDialog(QDialog):
    """
    The logic handler for the new project creation dialog, which allows the user
    to choose the starting point for their project.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_NewProjectDialog()
        self.ui.setupUi(self)

        self.selection = ""  # Will store the user's choice

        self._connect_signals()

        # Disable the "from codebase" button as it's a future feature
        self.ui.fromCodebaseButton.setEnabled(False)
        self.ui.fromCodebaseButton.setToolTip("This feature will be enabled in a future version.")

    def _connect_signals(self):
        """Connects the dialog's buttons to their handler methods."""
        self.ui.fromSpecButton.clicked.connect(self._on_from_spec_clicked)
        # self.ui.fromCodebaseButton.clicked.connect(self._on_from_codebase_clicked)
        self.ui.buttonBox.rejected.connect(self.reject)

    def _on_from_spec_clicked(self):
        """Handles the 'From Specification' button click."""
        self.selection = "spec"
        self.accept()

    def _on_from_codebase_clicked(self):
        """Handles the 'From Codebase' button click (currently disabled)."""
        self.selection = "codebase"
        self.accept()

    def get_selection(self) -> str:
        """Returns the user's workflow choice."""
        return self.selection