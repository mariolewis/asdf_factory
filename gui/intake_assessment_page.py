# gui/intake_assessment_page.py

import logging
import markdown
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from gui.ui_intake_assessment_page import Ui_IntakeAssessmentPage
from master_orchestrator import MasterOrchestrator

class IntakeAssessmentPage(QWidget):
    """
    The logic handler for the "Informed Choice" page, which displays the
    AI's summary and allows the PM to choose a strategic lifecycle path.
    """
    full_lifecycle_selected = Signal()
    direct_to_development_selected = Signal()
    back_selected = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_IntakeAssessmentPage()
        self.ui.setupUi(self)
        self.connect_signals()

    def connect_signals(self):
        """Connects the page's buttons to its public signals."""
        self.ui.directToDevelopmentButton.clicked.connect(self.direct_to_development_selected.emit)
        self.ui.fullLifecycleButton.clicked.connect(self.full_lifecycle_selected.emit)
        self.ui.backButton.clicked.connect(self.back_selected.emit)

    def configure(self, assessment_data: dict):
        """
        Populates the page with the AI's summary and assessment.

        Args:
            assessment_data (dict): The data from the ProjectIntakeAdvisorAgent.
        """
        summary_markdown = assessment_data.get("project_summary_markdown", "No summary was generated.")
        assessment_text = assessment_data.get("completeness_assessment", "No assessment was provided.")

        # Render the markdown summary into the QTextEdit widget
        summary_html = markdown.markdown(summary_markdown, extensions=['fenced_code', 'extra'])
        self.ui.summaryTextEdit.setHtml(summary_html)

        # Display the assessment text in the appropriate QLabel
        self.ui.completenessAssessmentLabel.setText(assessment_text)