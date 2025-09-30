# gui/intake_assessment_page.py

import logging
from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtCore import Signal
from PySide6.QtGui import QPalette, QColor

from gui.ui_intake_assessment_page import Ui_IntakeAssessmentPage
from master_orchestrator import MasterOrchestrator

class IntakeAssessmentPage(QWidget):
    """
    The logic handler for the new Intake Assessment page, which displays the
    AI's proposed workflow plan for PM approval.
    """
    proposal_accepted = Signal()
    override_selected = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_IntakeAssessmentPage()
        self.ui.setupUi(self)
        self.connect_signals()

    def connect_signals(self):
        """Connects the page's buttons to its public signals."""
        self.ui.acceptProposalButton.clicked.connect(self.proposal_accepted.emit)
        self.ui.overrideButton.clicked.connect(self.override_selected.emit)

    def _clear_layout(self, layout):
        """Removes all widgets from a layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def configure(self, assessment_data: dict):
        """
        Dynamically populates the page's widgets from the agent's JSON output.
        """
        # Clear any previous plan from the form layout
        self._clear_layout(self.ui.planFormLayout)

        summary = assessment_data.get("assessment_summary", "No summary provided.")
        self.ui.summaryTextEdit.setText(summary)

        if assessment_data.get("is_trivial"):
            justification = assessment_data.get("justification", "Project assessed as trivial.")
            self.ui.planGroupBox.setTitle("Trivial Project Detected: Direct-to-Plan Fast Track")
            self.ui.planFormLayout.addRow(QLabel(justification))
            return

        # If not trivial, populate the proposed plan
        self.ui.planGroupBox.setTitle("Proposed Plan")
        proposed_plan = assessment_data.get("proposed_plan", [])

        action_colors = {
            "SKIP": "#6A8759",    # Green
            "ADOPT": "#6A8759",   # Green
            "REFINE": "#FFC66D",  # Amber
            "ELABORATE": "#CC7832" # Red/Orange
        }

        for item in proposed_plan:
            phase_label = QLabel(f"{item.get('phase', 'Unknown Phase')}:")

            action = item.get('action', 'N/A')
            justification = item.get('justification', 'No details.')

            action_label = QLabel(f"<b>{action}</b> - <i>{justification}</i>")
            action_label.setWordWrap(True)

            color = action_colors.get(action, "#A9B7C6") # Default to secondary text color
            action_label.setStyleSheet(f"color: {color};")

            self.ui.planFormLayout.addRow(phase_label, action_label)