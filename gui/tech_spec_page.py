# gui/tech_spec_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal

from gui.ui_tech_spec_page import Ui_TechSpecPage
from master_orchestrator import MasterOrchestrator
from agents.agent_tech_stack_proposal import TechStackProposalAgent

class TechSpecPage(QWidget):
    """
    The logic handler for the Technical Specification page.
    """
    tech_spec_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.tech_spec_draft = ""

        self.ui = Ui_TechSpecPage()
        self.ui.setupUi(self)

        # Programmatically set the layout stretch factors
        self.ui.verticalLayout_3.setStretch(1, 1)

        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting TechSpecPage for a new project.")
        self.tech_spec_draft = ""
        self.ui.techSpecTextEdit.clear()
        self.ui.feedbackTextEdit.clear()
        self.ui.pmGuidelinesTextEdit.clear()
        self.ui.osComboBox.setCurrentIndex(0)
        self.ui.stackedWidget.setCurrentWidget(self.ui.initialChoicePage)

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.proposeStackButton.clicked.connect(self.on_propose_stack_clicked)
        self.ui.pmDefineButton.clicked.connect(self.on_pm_define_clicked)
        self.ui.generateFromGuidelinesButton.clicked.connect(self.on_generate_from_guidelines_clicked)
        self.ui.refineButton.clicked.connect(self.on_refine_clicked)
        self.ui.approveButton.clicked.connect(self.on_approve_clicked)

    def on_propose_stack_clicked(self):
        """Handles the 'Let ASDF Propose a Tech Stack' button click."""
        try:
            target_os = self.ui.osComboBox.currentText()
            with self.orchestrator.db_manager as db:
                project_details = db.get_project_by_id(self.orchestrator.project_id)
                final_spec_text = project_details['final_spec_text']

            if not final_spec_text:
                QMessageBox.critical(self, "Error", "Could not retrieve the application specification.")
                return

            agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)
            self.tech_spec_draft = agent.propose_stack(final_spec_text, target_os)

            self._display_review_page()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while proposing the tech stack:\n{e}")

    def on_pm_define_clicked(self):
        """Handles the 'I Will Provide Technology Guidelines' button click."""
        self.ui.stackedWidget.setCurrentWidget(self.ui.pmDefinePage)

    def on_generate_from_guidelines_clicked(self):
        """Handles the 'Generate Full Specification from My Input' button click."""
        guidelines = self.ui.pmGuidelinesTextEdit.toPlainText().strip()
        if not guidelines:
            QMessageBox.warning(self, "Input Required", "Please provide your technology guidelines.")
            return

        try:
            target_os = self.ui.osComboBox.currentText()
            with self.orchestrator.db_manager as db:
                project_details = db.get_project_by_id(self.orchestrator.project_id)
                final_spec_text = project_details['final_spec_text']

            context = f"{final_spec_text}\n\n--- PM Directive for Technology Stack ---\n{guidelines}"
            agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)
            self.tech_spec_draft = agent.propose_stack(context, target_os)

            self._display_review_page()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while generating the specification:\n{e}")

    def _display_review_page(self):
        """Helper method to show the review page."""
        self.ui.techSpecTextEdit.setText(self.tech_spec_draft)
        self.ui.feedbackTextEdit.clear()
        self.ui.stackedWidget.setCurrentWidget(self.ui.reviewPage)

    def on_refine_clicked(self):
        """Handles the 'Submit Feedback & Refine' button click."""
        feedback = self.ui.feedbackTextEdit.toPlainText().strip()
        if not feedback:
            QMessageBox.warning(self, "Input Required", "Please provide feedback to refine the draft.")
            return

        try:
            target_os = self.ui.osComboBox.currentText()
            with self.orchestrator.db_manager as db:
                project_details = db.get_project_by_id(self.orchestrator.project_id)
                final_spec_text = project_details['final_spec_text']

            # Update the draft in the text edit before sending for refinement
            self.tech_spec_draft = self.ui.techSpecTextEdit.toPlainText()

            context = (
                f"{final_spec_text}\n\n"
                f"--- Current Draft to Refine ---\n{self.tech_spec_draft}\n\n"
                f"--- PM Feedback for Refinement ---\n{feedback}"
            )
            agent = TechStackProposalAgent(llm_service=self.orchestrator.llm_service)
            self.tech_spec_draft = agent.propose_stack(context, target_os)

            self._display_review_page()
            QMessageBox.information(self, "Success", "The technical specification has been refined based on your feedback.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during refinement:\n{e}")

    def on_approve_clicked(self):
        """Handles the 'Approve Technical Specification' button click."""
        final_tech_spec = self.ui.techSpecTextEdit.toPlainText()
        if not final_tech_spec.strip():
            QMessageBox.warning(self, "Approval Failed", "The technical specification cannot be empty.")
            return

        target_os = self.ui.osComboBox.currentText()
        self.orchestrator.finalize_and_save_tech_spec(final_tech_spec, target_os)
        QMessageBox.information(self, "Success", "Technical Specification approved and saved.")
        self.tech_spec_complete.emit()