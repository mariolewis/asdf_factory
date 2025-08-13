# gui/preflight_check_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QPushButton
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor

from gui.ui_preflight_check_page import Ui_PreflightCheckPage
from master_orchestrator import MasterOrchestrator

class PreflightCheckPage(QWidget):
    """
    The logic handler for the Project Resumption (Pre-flight Check) page.
    """
    project_load_finalized = Signal()
    project_load_failed = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator

        self.ui = Ui_PreflightCheckPage()
        self.ui.setupUi(self)
        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.proceedButton.clicked.connect(self.on_proceed_clicked)
        self.ui.manualResolveButton.clicked.connect(self.on_manual_resolve_clicked)
        self.ui.discardButton.clicked.connect(self.on_discard_clicked)
        self.ui.backButton.clicked.connect(self.project_load_failed.emit)
        self.ui.continueButton.clicked.connect(self.on_continue_clicked)

    def prepare_for_display(self):
        """Updates the page content based on the pre-flight check result."""
        result = self.orchestrator.preflight_check_result
        if not result:
            self.ui.statusLabel.setText("Status: Error")
            self.ui.detailsTextEdit.setText("Could not retrieve project resumption check results.")
            self.ui.actionStackedWidget.setCurrentWidget(self.ui.errorPage)
            return

        status = result.get("status")
        message = result.get("message")

        self.ui.detailsTextEdit.setText(message)
        self.ui.headerLabel.setText("Continue Project") # Rename the page header

        if status == "ALL_PASS":
            self.ui.statusLabel.setText("Status: Success")
            self.ui.statusLabel.setStyleSheet("color: green; font-weight: bold;")
            self.ui.actionStackedWidget.setCurrentWidget(self.ui.successPage)
        elif status == "STATE_DRIFT":
            self.ui.statusLabel.setText("Status: Action Required")
            self.ui.statusLabel.setStyleSheet("color: orange; font-weight: bold;")
            self.ui.actionStackedWidget.setCurrentWidget(self.ui.stateDriftPage)
        else: # Covers PATH_NOT_FOUND, GIT_MISSING, ERROR
            self.ui.statusLabel.setText("Status: Failed")
            self.ui.statusLabel.setStyleSheet("color: red; font-weight: bold;")
            self.ui.actionStackedWidget.setCurrentWidget(self.ui.errorPage)

    def on_proceed_clicked(self):
        """Finalizes the project load and signals the main window."""
        resume_phase = self.orchestrator.resume_phase_after_load
        if resume_phase:
            self.orchestrator.set_phase(resume_phase.name)
            self.orchestrator.resume_phase_after_load = None
            self.project_load_finalized.emit()
        else:
            QMessageBox.critical(self, "Error", "Could not determine the project's resume phase.")
            self.project_load_failed.emit()

    def on_manual_resolve_clicked(self):
        """Instructs the user to resolve manually and returns to the project list."""
        QMessageBox.information(self, "Manual Resolution",
                                "The application will now return to the main screen. "
                                "Please use your own tools (e.g., git commit, git stash) to clean the repository, "
                                "then try loading the project again.")
        self.project_load_failed.emit()

    def on_discard_clicked(self):
        """Shows a final confirmation before discarding all local changes."""
        reply = QMessageBox.warning(self, "Confirm Discard",
                                    "<b>This will permanently delete all uncommitted changes in your local repository.</b>"
                                    "<br><br>This action cannot be undone. Are you sure you want to proceed?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            history_id = self.orchestrator.preflight_check_result.get("history_id")
            if history_id:
                self.orchestrator.handle_discard_changes(history_id)
                # The orchestrator will re-trigger the load, so this page will be updated automatically.
            else:
                QMessageBox.critical(self, "Error", "Could not identify the project to discard changes for.")

    def on_continue_clicked(self):
        """Handles the primary action for state drift: committing changes and resuming."""
        history_id = self.orchestrator.preflight_check_result.get("history_id")
        if history_id:
            # We will create this orchestrator method in the next step
            self.orchestrator.handle_continue_with_uncommitted_changes(history_id)
            self.project_load_finalized.emit()
        else:
            QMessageBox.critical(self, "Error", "Could not identify the project to continue.")