# gui/project_complete_page.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from gui.ui_project_complete_page import Ui_ProjectCompletePage

class ProjectCompletePage(QWidget):
    export_project = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ProjectCompletePage()
        self.ui.setupUi(self)
        self.connect_signals()

    def set_project_name(self, name):
        self.ui.projectNameLabel.setText(f"Project '{name}' has been completed successfully.")

    def connect_signals(self):
        self.ui.exportButton.clicked.connect(self.export_project.emit)