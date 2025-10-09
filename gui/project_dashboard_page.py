# gui/project_dashboard_page.py

import logging
import json
from PySide6.QtWidgets import QWidget, QMessageBox
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
        self.ui.maintainButton.clicked.connect(self.on_maintainButton_clicked)
        self.ui.quickFixButton.clicked.connect(self.quickfix_selected.emit)
        self.ui.modernizeButton.clicked.connect(self.modernize_selected.emit)

    def on_maintainButton_clicked(self):
        """
        Auto-connected slot for the 'Maintain & Enhance' button.
        If a reference backlog already exists, it prompts for confirmation before
        emitting the maintain_selected signal.
        """
        try:
            db = self.orchestrator.db_manager
            project_id = self.orchestrator.project_id

            all_crs = db.get_all_change_requests_for_project(project_id)
            has_existing_items = any(cr['status'] == 'EXISTING' for cr in all_crs)

            proceed = True
            if has_existing_items:
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText("This action will result in a complete refresh of the backlog items corresponding to the implemented codebase. Continue?")
                msg_box.setWindowTitle("Confirm Backlog Refresh")
                msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

                if msg_box.exec() != QMessageBox.Ok:
                    proceed = False

            if proceed:
                self.maintain_selected.emit()

        except Exception as e:
            logging.error(f"Error in on_maintainButton_clicked: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

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
            project_details_row = db.get_project_by_id(project_id)
            if not project_details_row:
                 raise ValueError("Could not retrieve project details.")

            project_details = dict(project_details_row)

            # Read cached file count
            file_count = project_details.get('scanned_file_count', 0)
            self.ui.filesValueLabel.setText(str(file_count))

            # Read and parse cached technologies
            languages_json = project_details.get('detected_technologies')
            if languages_json:
                languages = json.loads(languages_json)
                languages_str = ", ".join(languages) if languages else "Not detected"
            else:
                languages_str = "Not yet calculated"
            self.ui.languagesValueLabel.setText(languages_str)

            # Logic to enable/disable buttons remains the same
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
