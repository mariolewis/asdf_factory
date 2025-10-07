# gui/project_dashboard_page.py

import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from gui.ui_project_dashboard_page import Ui_ProjectDashboardPage
from master_orchestrator import MasterOrchestrator

class ProjectDashboardPage(QWidget):
    """
    The logic handler for the Project Dashboard (strategic checkpoint) page.
    """
    maintain_selected = Signal()
    quickfix_selected = Signal()
    modernize_selected = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_ProjectDashboardPage()
        self.ui.setupUi(self)

        self.connect_signals()
        self.ui.modernizeButton.setEnabled(False) # Disabled as per CR

    def connect_signals(self):
        """Connects UI element signals to this widget's public signals."""
        self.ui.maintainButton.clicked.connect(self.maintain_selected.emit)
        self.ui.quickFixButton.clicked.connect(self.quickfix_selected.emit)
        self.ui.modernizeButton.clicked.connect(self.modernize_selected.emit)

    def prepare_for_display(self):
        """
        Fetches analysis metrics and sets the enabled state of the action
        buttons based on whether a reference backlog exists.
        """
        logging.info("Populating Project Dashboard with analysis metrics.")
        # Always enable the button to generate/re-generate the reference backlog.
        self.ui.maintainButton.setEnabled(True)
        self.ui.maintainButton.setToolTip("Generate a reference backlog by analyzing the codebase's structure and specs.")

        try:
            project_id = self.orchestrator.project_id
            if not project_id:
                raise ValueError("No active project ID found.")

            db = self.orchestrator.db_manager
            project_details = db.get_project_by_id(project_id)
            tech_spec_text = project_details['tech_spec_text'] if project_details else ''

            all_artifacts = db.get_all_artifacts_for_project(project_id)
            file_count = len(all_artifacts)

            languages = self.orchestrator.detect_technologies_in_spec(tech_spec_text)
            languages_str = ", ".join(languages) if languages else "Not detected"

            self.ui.languagesValueLabel.setText(languages_str)
            self.ui.filesValueLabel.setText(str(file_count))

            # Check if a reference backlog exists to enable the other buttons.
            all_crs = db.get_all_change_requests_for_project(project_id)
            has_existing_items = any(cr['status'] == 'EXISTING' for cr in all_crs)

            self.ui.quickFixButton.setEnabled(has_existing_items)
            if not has_existing_items:
                self.ui.quickFixButton.setToolTip("This option requires a reference backlog. Use 'Maintain & Enhance' first.")
            else:
                self.ui.quickFixButton.setToolTip("Go to the Project Backlog to add new work items.")

        except Exception as e:
            logging.error(f"Failed to populate project dashboard: {e}", exc_info=True)
            self.ui.languagesValueLabel.setText("Error")
            self.ui.filesValueLabel.setText("Error")
            # Disable buttons on error for safety
            self.ui.maintainButton.setEnabled(False)
            self.ui.quickFixButton.setEnabled(False)