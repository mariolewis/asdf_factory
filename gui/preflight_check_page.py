# gui/preflight_check_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QPushButton
from PySide6.QtCore import Signal

# We will create this file in the next step
from gui.ui_preflight_check_page import Ui_PreflightCheckPage
from master_orchestrator import MasterOrchestrator

class PreflightCheckPage(QWidget):
    """
    The logic handler for the Pre-flight Check Resolution page.
    """
    project_load_finalized = Signal()
    project_load_failed = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator

        self.ui = Ui_PreflightCheckPage()
        self.ui.setupUi(self)

    def update_and_display(self):
        """
        Updates the page with the results from the orchestrator's
        pre-flight check and configures the appropriate action buttons.
        """
        result = self.orchestrator.preflight_check_result
        if not result:
            self.ui.statusLabel.setText("Error")
            self.ui.messageTextEdit.setText("Pre-flight check result not found in the orchestrator.")
            return

        status = result.get("status")
        message = result.get("message")

        self.ui.statusLabel.setText(f"Status: {status.replace('_', ' ').title()}")
        self.ui.messageTextEdit.setText(message)

        # Clear any existing buttons from the layout
        while self.ui.buttonLayout.count():
            child = self.ui.buttonLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add buttons based on the status
        if status == "ALL_PASS":
            proceed_button = QPushButton("▶️ Proceed to Project")
            proceed_button.clicked.connect(self.on_proceed_clicked)
            self.ui.buttonLayout.addWidget(proceed_button)

        elif status in ["PATH_NOT_FOUND", "GIT_MISSING"]:
            resolve_button = QPushButton("Go to Environment Setup to Resolve")
            resolve_button.clicked.connect(self.on_resolve_manually_clicked)
            self.ui.buttonLayout.addWidget(resolve_button)

        elif status == "STATE_DRIFT":
            manual_button = QPushButton("I Will Resolve Manually")
            discard_button = QPushButton("Discard All Local Changes (Expert)")
            manual_button.clicked.connect(self.on_manual_resolve_drift_clicked)
            discard_button.clicked.connect(self.on_discard_changes_clicked)
            self.ui.buttonLayout.addWidget(manual_button)
            self.ui.buttonLayout.addWidget(discard_button)

        self.ui.stackedWidget.setCurrentWidget(self.ui.resultsPage)

    def on_proceed_clicked(self):
        """Finalizes the project load and signals completion."""
        self.orchestrator.set_phase(self.orchestrator.resume_phase_after_load.name)
        self.orchestrator.resume_phase_after_load = None
        self.project_load_finalized.emit()

    def on_resolve_manually_clicked(self):
        """Handles fatal errors by guiding the user back to the setup phase."""
        self.project_load_failed.emit() # Signal to main window to reset
        self.orchestrator.set_phase("ENV_SETUP_TARGET_APP")
        self.project_load_finalized.emit() # Re-signal to trigger UI update

    def on_manual_resolve_drift_clicked(self):
        """Acknowledges manual resolution and returns to the welcome screen."""
        self.orchestrator.project_id = None
        self.orchestrator.set_phase("IDLE")
        self.project_load_finalized.emit()

    def on_discard_changes_clicked(self):
        """Triggers the orchestrator to discard local git changes."""
        reply = QMessageBox.warning(
            self, "Confirm Discard",
            "This will permanently delete all uncommitted changes in your local repository. This cannot be undone.\n\nAre you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # The orchestrator handles the git logic and re-triggers the load
            self.orchestrator.handle_discard_changes(self.orchestrator.preflight_check_result['history_id'])
            self.project_load_finalized.emit()