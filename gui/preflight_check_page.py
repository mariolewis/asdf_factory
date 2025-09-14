# gui/preflight_check_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QPushButton
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_preflight_check_page import Ui_PreflightCheckPage
from master_orchestrator import MasterOrchestrator
from gui.manual_change_dialog import ManualChangeDialog
from gui.worker import Worker

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
        self.threadpool = QThreadPool()
        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.proceedButton.clicked.connect(self.on_proceed_clicked)
        self.ui.manualResolveButton.clicked.connect(self.on_manual_resolve_clicked)
        self.ui.discardButton.clicked.connect(self.on_discard_clicked)
        self.ui.backButton.clicked.connect(self.project_load_failed.emit)
        self.ui.continueButton.clicked.connect(self.on_continue_clicked)
        self.ui.ignoreButton.clicked.connect(self.on_ignore_clicked)

    def _on_task_error(self, error_tuple):
        """A generic handler for errors from background worker threads."""
        main_window = self.window()
        if main_window:
            main_window.setEnabled(True)
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().clearMessage()

        error_msg = f"An unexpected error occurred in a background task:\n{error_tuple[1]}"
        logging.error(error_msg, exc_info=error_tuple)
        QMessageBox.critical(self, "Background Task Error", error_msg)

    def _handle_commit_result(self, result_tuple):
        """Handles the result of the simple commit task."""
        main_window = self.window()
        main_window.setEnabled(True)
        main_window.statusBar().clearMessage()

        success, message = result_tuple
        if success:
            # After a successful commit, now call the resume logic
            # before refreshing the main UI.
            self.orchestrator.resume_project()
            self.project_load_finalized.emit()
        else:
            QMessageBox.critical(self, "Error", f"Failed to commit changes:\n{message}")

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

        self.ui.headerLabel.setText("Continue Project")

        if status == "ALL_PASS":
            self.ui.statusLabel.setText("Status: Success")
            self.ui.statusLabel.setStyleSheet("color: green; font-weight: bold;")
            self.ui.detailsTextEdit.setText(message)
            self.ui.actionStackedWidget.setCurrentWidget(self.ui.successPage)
        elif status == "STATE_DRIFT":
            self.ui.statusLabel.setText("Status: Action Required")
            self.ui.statusLabel.setStyleSheet("color: orange; font-weight: bold;")
            self.ui.detailsTextEdit.setText(message)
            self.ui.actionStackedWidget.setCurrentWidget(self.ui.stateDriftPage)
        else: # Covers PATH_NOT_FOUND, GIT_MISSING, ERROR
            self.ui.statusLabel.setText("Status: Failed")
            self.ui.statusLabel.setStyleSheet("color: red; font-weight: bold;")
            self.ui.detailsTextEdit.setText(message)
            self.ui.actionStackedWidget.setCurrentWidget(self.ui.errorPage)

    def on_proceed_clicked(self):
        """Finalizes the project load and signals the main window."""
        self.orchestrator.resume_project()
        self.project_load_finalized.emit()

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
                # This is a blocking call. The UI will wait until it's done.
                self.orchestrator.handle_discard_changes(history_id)
                # After it's done, explicitly tell this page to refresh itself.
                self.prepare_for_display()
            else:
                QMessageBox.critical(self, "Error", "Could not identify the project to discard changes for.")

    def on_continue_clicked(self):
        """
        Handles the primary action for state drift. The behavior is now
        context-aware based on whether a sprint plan is active.
        """
        has_active_plan = self.orchestrator.preflight_check_result.get("has_active_plan", False)

        if has_active_plan:
            # SCENARIO A: A sprint was paused. Show the task list to sync state.
            try:
                uncompleted_tasks = self.orchestrator.get_uncompleted_tasks_for_manual_fix()
                if uncompleted_tasks is None:
                    QMessageBox.critical(self, "Error", "Could not retrieve the list of uncompleted tasks from the active sprint plan.")
                    return

                dialog = ManualChangeDialog(uncompleted_tasks, self)
                if dialog.exec():
                    selected_task_ids = dialog.get_selected_task_ids()
                    self.orchestrator.handle_continue_with_uncommitted_changes(selected_task_ids)
                    self.project_load_finalized.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
                logging.error(f"Failed during on_continue_clicked (active plan): {e}", exc_info=True)
        else:
            # SCENARIO B: Between sprints. Perform a simple commit.
            reply = QMessageBox.question(self, "Commit Manual Changes",
                                        "You have uncommitted changes but no active sprint. This action will commit all changes with a generic message ('feat: Apply and commit manual changes from PM').\n\nDo you want to proceed?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                main_window = self.window()
                main_window.setEnabled(False)
                main_window.statusBar().showMessage("Committing manual changes...")

                worker = Worker(self.orchestrator.commit_manual_changes_and_proceed)
                worker.signals.result.connect(self._handle_commit_result)
                worker.signals.error.connect(self._on_task_error)
                self.threadpool.start(worker)

    def on_ignore_clicked(self):
        """Proceeds with loading the project, leaving local changes as they are."""
        # This action is functionally the same as a successful check for the UI flow
        self.on_proceed_clicked()