# gui/sprint_review_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal

from gui.ui_sprint_review_page import Ui_SprintReviewPage
from master_orchestrator import MasterOrchestrator

class SprintReviewPage(QWidget):
    """
    The logic handler for the Sprint Review page.
    """
    return_to_backlog = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_SprintReviewPage()
        self.ui.setupUi(self)

        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.returnToBacklogButton.clicked.connect(self.return_to_backlog.emit)
        self.ui.exportSummaryButton.clicked.connect(self.on_export_summary_clicked)

    def prepare_for_display(self):
        """Populates the summary view when the page is shown."""
        # This will be implemented in a later step.
        self.ui.summaryTextEdit.setText("Sprint summary will be displayed here.")

    def on_export_summary_clicked(self):
        """Handles the export summary button click."""
        # This will be implemented in a later step.
        QMessageBox.information(self, "Not Implemented", "Exporting the sprint summary will be implemented shortly.")