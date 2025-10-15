# gui/sprint_integration_test_page.py

import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from gui.ui_sprint_integration_test_page import Ui_SprintIntegrationTestPage
from master_orchestrator import MasterOrchestrator

class SprintIntegrationTestPage(QWidget):
    """
    The logic handler for the Sprint Integration Test execution checkpoint page.
    """
    run_test_clicked = Signal(str)
    skip_clicked = Signal()
    pause_clicked = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_SprintIntegrationTestPage()
        self.ui.setupUi(self)
        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to this widget's public signals."""
        self.ui.runButton.clicked.connect(self.on_run_clicked)
        self.ui.skipButton.clicked.connect(self.skip_clicked.emit)
        self.ui.pauseButton.clicked.connect(self.pause_clicked.emit)

    def on_run_clicked(self):
        """Emits the run signal with the current command text."""
        command = self.ui.commandLineEdit.text().strip()
        self.run_test_clicked.emit(command)

    def configure(self, file_path: str, command: str):
        """
        Populates the page with the generated file path and suggested command.

        Args:
            file_path (str): The relative path to the temporary test script.
            command (str): The suggested execution command.
        """
        self.ui.filePathLineEdit.setText(file_path)
        self.ui.commandLineEdit.setText(command)