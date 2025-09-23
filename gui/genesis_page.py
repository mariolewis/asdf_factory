# gui/genesis_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool, QTimer

from gui.ui_genesis_page import Ui_GenesisPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator

class GenesisPage(QWidget):
    """
    The logic handler for the Iterative Component Development (Genesis) page.
    """
    genesis_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_GenesisPage()
        self.ui.setupUi(self)
        # self.threadpool = QThreadPool()

        self.ui.continueButton.setVisible(False)
        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.proceedButton.clicked.connect(self.run_development_step)
        self.ui.continueButton.clicked.connect(self.on_continue_clicked)
        self.ui.acknowledgeButton.clicked.connect(self.on_acknowledge_manual_fix_clicked)
        self.ui.retryButton.clicked.connect(self.on_retry_automated_fix_clicked)
        self.ui.skipButton.clicked.connect(self.on_skip_task_clicked)

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting GenesisPage for a new project.")
        self.ui.stackedWidget.setCurrentWidget(self.ui.checkpointPage)
        self.ui.progressBar.setValue(0)
        self.ui.nextTaskLabel.setText("No development plan loaded yet.")
        self.ui.logOutputTextEdit.clear()
        self.setEnabled(True)
        self.ui.continueButton.setVisible(False)

    def prepare_for_display(self):
        """
        This is the standard refresh method called by the main window before the
        page is shown. It ensures the UI is always up-to-date.
        """
        logging.info("Preparing GenesisPage for display.")
        if self.orchestrator.is_task_processing:
            self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.checkpointPage)
        self.update_checkpoint_display()

    def _set_ui_busy(self, is_busy):
        """Disables or enables the page's buttons while a background task runs."""
        self.ui.proceedButton.setEnabled(not is_busy)
        # The decision to show the continue button or switch pages is now handled
        # by the methods that call this one.

    def on_continue_clicked(self):
        """Hides the continue button, resets the view, and triggers the main UI update."""
        self.ui.continueButton.setVisible(False)
        # Switch back to the checkpoint page view before the main window updates.
        self.ui.stackedWidget.setCurrentWidget(self.ui.checkpointPage)
        # Emit the signal to have the main window show the correct next page.
        self.genesis_complete.emit()

    # In file: gui/genesis_page.py

    # Add this new method to the GenesisPage class
    def _handle_acknowledgement_result(self, success):
        """Handles the result of the manual fix acknowledgement task."""
        try:
            if success:
                # This call forces the page to refresh itself with the new state
                # from the orchestrator (which now has an advanced cursor).
                self.prepare_for_display()
            else:
                QMessageBox.critical(self, "Error", "The acknowledgement process failed.")
        finally:
            self._set_ui_busy(False)
            self.ui.stackedWidget.setCurrentWidget(self.ui.checkpointPage)

    def on_acknowledge_manual_fix_clicked(self):
        """Triggers the orchestrator to accept the manual fix and proceed."""
        self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
        self.ui.logOutputTextEdit.setText("Acknowledging manual fix and updating project records...")
        self._set_ui_busy(True)

        worker = Worker(self.orchestrator.acknowledge_manual_fix_and_advance)
        worker.signals.result.connect(self._handle_acknowledgement_result)
        worker.signals.error.connect(self._on_task_error)
        worker.signals.finished.connect(self._on_task_finished)
        self.window().threadpool.start(worker)

    def on_retry_automated_fix_clicked(self):
        """Triggers the orchestrator to attempt a new automated fix."""
        self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
        self.ui.logOutputTextEdit.clear()
        self._set_ui_busy(True)

        failure_log = self.orchestrator.task_awaiting_approval.get("failure_log", "No failure log available.")
        worker = Worker(self.orchestrator.handle_retry_fix_action, failure_log)
        worker.signals.progress.connect(self.on_progress_update)
        worker.signals.result.connect(self._handle_development_result)
        worker.signals.error.connect(self._on_task_error)
        worker.signals.finished.connect(self._on_task_finished)
        self.window().threadpool.start(worker)

    def on_skip_task_clicked(self):
        """Triggers the orchestrator to skip the manually handled task and log it."""
        # This is now a synchronous call that updates the state.
        success = self.orchestrator.skip_and_log_manually_handled_task()
        if success:
            # The orchestrator has advanced the cursor. A full UI refresh is needed
            # to show the dashboard for the next task.
            self.genesis_complete.emit()
        else:
            QMessageBox.critical(self, "Error", "Failed to skip the task and log the bug. Please check the logs.")

    def on_progress_update(self, progress_data):
        """
        Appends a progress message to the log in a thread-safe manner,
        applying color based on the status.
        """
        try:
            if isinstance(progress_data, tuple) and len(progress_data) == 2:
                status, message = progress_data
            else:
                status, message = "INFO", str(progress_data)

            color_map = {
                "SUCCESS": "#6A8759", # Green
                "INFO": "#A9B7C6",    # Light Gray
                "WARNING": "#FFC66D", # Amber
                "ERROR": "#CC7832"     # Red/Orange
            }

            color = color_map.get(status, "#A9B7C6")
            # Ensure message is properly escaped for HTML
            escaped_message = message.replace('<', '&lt;').replace('>', '&gt;')
            html_message = f'<font color="{color}">{escaped_message}</font>'
            QTimer.singleShot(0, lambda: self.ui.logOutputTextEdit.append(html_message))

        except Exception as e:
            # Fallback for any unexpected data format
            QTimer.singleShot(0, lambda: self.ui.logOutputTextEdit.append(str(progress_data)))
            logging.error(f"Error processing progress update: {e}")

    def update_processing_display(self, simple_status_message: str = None):
        """
        Updates the labels on the processing page with dynamic information.
        Can be called with a simple string for phase-level status, or will
        get detailed task info from the orchestrator if called without arguments.
        """
        # If a simple message is provided, use it. This is for testing phases.
        if simple_status_message:
            self.ui.statusLabel.setText(f"<b>{simple_status_message}</b>")
            # Get all user story titles for the sprint context
            sprint_stories = self.orchestrator.get_sprint_goal()
            self.ui.contextLabel.setText(f"<b>User Stories:</b> {sprint_stories}")
            return

        # Otherwise, it's a development/fix task. Get the full details.
        details = self.orchestrator.get_current_task_details()
        if not details or not details.get("task") or "micro_spec_id" not in details.get("task"):
            self.ui.statusLabel.setText("<b>All development tasks complete.</b>")
            self.ui.contextLabel.setText("")
            return

        task = details.get("task", {})
        cursor = details.get("cursor", 0)
        total = details.get("total", 0)
        is_fix = details.get("is_fix_mode", False)
        task_name = task.get('component_name', 'Unnamed Task')
        parent_cr_ids = task.get('parent_cr_ids', [])

        # Format the status line
        mode_prefix = "Executing fix for" if is_fix else "Executing"
        status_text = f"<b>{mode_prefix} task {cursor + 1}/{total}:</b> {task_name}"
        self.ui.statusLabel.setText(status_text)

        # Get and set the user story context
        story_context = self.orchestrator._get_user_story_context_for_task(parent_cr_ids)
        self.ui.contextLabel.setText(f"<b>User Story:</b> {story_context}")

    def run_development_step(self):
        """Initiates the background task to run the next development step."""
        self.update_processing_display()
        # Explicitly set the UI to the processing state before starting the worker.
        self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
        self.ui.logOutputTextEdit.clear()
        self.ui.continueButton.setVisible(False)
        self._set_ui_busy(True)

        worker = Worker(self.orchestrator.handle_proceed_action)
        worker.signals.progress.connect(self.on_progress_update)
        worker.signals.result.connect(self._handle_development_result)
        worker.signals.error.connect(self._on_task_error)
        worker.signals.finished.connect(self._on_task_finished)
        self.window().threadpool.start(worker)

    def _handle_development_result(self, result: str):
        """
        Handles the completion of the development step, checking if the
        result indicates a success or a handled failure.
        """
        # On either a success or a handled failure, just show the appropriate
        # message and the continue button. Do not emit a signal here.
        if result and result.strip().startswith("Error"):
            self.ui.logOutputTextEdit.append(f"\n--- TASK FAILED ---")
            self.ui.continueButton.setVisible(True)
        else:
            self.ui.logOutputTextEdit.append(f"\n--- TASK COMPLETE ---")
            self.ui.continueButton.setVisible(True)

    def _on_task_error(self, error_tuple):
        """Handles an error from the worker and shows the continue button."""
        error_msg = f"A critical error occurred in a background task:\n{error_tuple[1]}"
        self.ui.logOutputTextEdit.append(f"\n--- ERROR ---\n{error_msg}")
        self.ui.continueButton.setVisible(True)

    def _on_task_finished(self):
        """Re-enables the UI after any background task is complete."""
        self.orchestrator.set_task_processing_complete()
        self._set_ui_busy(False)

    def update_checkpoint_display(self):
        """
        Updates the PM Checkpoint screen (now the Sprint Progress Dashboard)
        with the current progress and status.
        """
        sprint_goal_text = self.orchestrator.get_sprint_goal()
        self.ui.sprintGoalLabel.setText(f"<b>Sprint Goal:</b> {sprint_goal_text}")

        mode = self.orchestrator.get_current_mode()
        # The sprintStatusIndicatorLabel was removed from the UI, so all references are gone.

        details = self.orchestrator.get_current_task_details()

        if details:
            task = details.get("task", {})
            cursor = details.get("cursor", 0)
            total = details.get("total", 0)
            is_fix = details.get("is_fix_mode", False)
            confidence = details.get("confidence_score", 0)
            task_name = task.get('component_name', 'Unnamed Task')
            progress_percent = int((cursor / total) * 100) if total > 0 else 0

            self.ui.progressBar.setValue(progress_percent)
            self.ui.aiConfidenceGauge.setValue(confidence)

            if self.orchestrator.is_resuming_from_manual_fix:
                self.ui.actionButtonStackedWidget.setCurrentWidget(self.ui.manualFixModePage)
                self.ui.nextTaskLabel.setText(f"<b>Resuming from manual fix for task ({cursor + 1}/{total}):</b> {task_name}")
                self.ui.aiConfidenceLabel.setVisible(True)
                self.ui.aiConfidenceGauge.setVisible(True)
            else:
                self.ui.actionButtonStackedWidget.setCurrentWidget(self.ui.normalModePage)
                self.ui.aiConfidenceLabel.setVisible(not is_fix)
                self.ui.aiConfidenceGauge.setVisible(not is_fix)

                if cursor >= total and total > 0:
                    self.ui.progressBar.setValue(100)
                    self.ui.nextTaskLabel.setText("Sprint development tasks complete.")
                    self.ui.proceedButton.setText("▶️ Run Backend Testing") # CORRECTED TEXT
                    self.ui.aiConfidenceLabel.setVisible(False) # HIDE GAUGE
                    self.ui.aiConfidenceGauge.setVisible(False) # HIDE GAUGE
                else:
                    mode_prefix = "FIX: " if is_fix else ""
                    self.ui.nextTaskLabel.setText(f"Next task ({cursor + 1}/{total}): {mode_prefix}{task_name}")
                    self.ui.proceedButton.setText(f"▶️ Proceed with: {mode_prefix}{task_name}")
        else:
            self.ui.progressBar.setValue(0)
            self.ui.aiConfidenceGauge.setValue(0)
            self.ui.aiConfidenceLabel.setVisible(False)
            self.ui.aiConfidenceGauge.setVisible(False)
            self.ui.nextTaskLabel.setText("No development plan loaded yet.")
            self.ui.proceedButton.setText("▶️ Proceed")

