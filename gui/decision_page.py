# gui/decision_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QPushButton
from PySide6.QtCore import Signal

from gui.ui_decision_page import Ui_DecisionPage
from master_orchestrator import MasterOrchestrator

class DecisionPage(QWidget):
    """
    The logic handler for the generic PM Decision page.
    """
    # Define signals for up to 3 different actions
    option1_selected = Signal()
    option2_selected = Signal()
    option3_selected = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator

        self.ui = Ui_DecisionPage()
        self.ui.setupUi(self)

        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page to its initial state."""
        logging.info("Resetting DecisionPage for a new project.")
        # No specific state to reset, but the method is here for consistency.
        pass

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.option1Button.clicked.connect(self.option1_selected.emit)
        self.ui.option2Button.clicked.connect(self.option2_selected.emit)
        self.ui.option3Button.clicked.connect(self.option3_selected.emit)

    def configure(self, header: str, instruction: str, details: str,
                option1_text: str = None, option1_enabled: bool = True,
                option2_text: str = None, option2_enabled: bool = True,
                option3_text: str = None, option3_enabled: bool = True):
        """
        Configures the page content and buttons for a specific decision.
        """
        self.ui.headerLabel.setText(header)
        self.ui.instructionLabel.setText(instruction)
        self.ui.detailsTextEdit.setHtml(details)

        if option1_text:
            self.ui.option1Button.setText(option1_text)
            self.ui.option1Button.setVisible(True)
            self.ui.option1Button.setEnabled(option1_enabled)
        else:
            self.ui.option1Button.setVisible(False)

        if option2_text:
            self.ui.option2Button.setText(option2_text)
            self.ui.option2Button.setVisible(True)
            self.ui.option2Button.setEnabled(option2_enabled)
        else:
            self.ui.option2Button.setVisible(False)

        if option3_text:
            self.ui.option3Button.setText(option3_text)
            self.ui.option3Button.setVisible(True)
            self.ui.option3Button.setEnabled(option3_enabled)
        else:
            self.ui.option3Button.setVisible(False)