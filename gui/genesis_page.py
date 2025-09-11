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

    def on_progress_update(self, progress_data):
        """
        Appends a progress message to the log in a thread-safe manner,
        applying color based on the status.
        """
        try:
            status, message = progress_data

            color_map = {
                "SUCCESS": "#00C853", # Bright Green
                "INFO": "#A9B7C6",    # Light Gray (Secondary Text)
                "WARNING": "#FFAB00", # Bright Amber
                "ERROR": "#D50000"     # Bright Red
            }

            color = color_map.get(status, "#A9B7C6")
            html_message = f'<font color="{color}">{message}</font>'
            QTimer.singleShot(0, lambda: self.ui.logOutputTextEdit.append(html_message))

        except Exception as e:
            QTimer.singleShot(0, lambda: self.ui.logOutputTextEdit.append(str(progress_data)))
            logging.error(f"Error processing progress update: {e}")

    def run_development_step(self):
        """Initiates the background task to run the next development step."""
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
        self._set_ui_busy(False)

    def update_checkpoint_display(self):
        """
        Updates the PM Checkpoint screen (now the Sprint Progress Dashboard)
        with the current progress and status.
        """
        sprint_goal_text = self.orchestrator.get_sprint_goal()
        self.ui.sprintGoalLabel.setText(f"<b>Sprint Goal:</b> {sprint_goal_text}")
        self.ui.sprintGoalValueLabel.setText(sprint_goal_text)

        mode = self.orchestrator.get_current_mode()
        self.ui.sprintStatusIndicatorLabel.setText(f"MODE: {mode}")

        if mode == "FIXING":
            self.ui.sprintStatusIndicatorLabel.setStyleSheet("color: #FFC66D; font-weight: bold;")
        else:
            self.ui.sprintStatusIndicatorLabel.setStyleSheet("color: #007ACC; font-weight: bold;")

        details = self.orchestrator.get_current_task_details()

        if details:
            task = details.get("task", {})
            cursor = details.get("cursor", 0)
            total = details.get("total", 0)
            is_fix = details.get("is_fix_mode", False)

            show_confidence = not is_fix
            self.ui.aiConfidenceLabel.setVisible(show_confidence)
            self.ui.aiConfidenceGauge.setVisible(show_confidence)

            if show_confidence:
                confidence_score = details.get("confidence_score", 0)
                self.ui.aiConfidenceGauge.setValue(confidence_score)

                if confidence_score > 80:
                    self.ui.aiConfidenceGauge.setStyleSheet("QProgressBar::chunk { background-color: #6A8759; }")
                    self.ui.aiConfidenceGauge.setToolTip("High Confidence: The AI had a clear and complete view of this task. The generated output is likely to be highly accurate.")
                elif confidence_score > 40:
                    self.ui.aiConfidenceGauge.setStyleSheet("QProgressBar::chunk { background-color: #FFC66D; }")
                    self.ui.aiConfidenceGauge.setToolTip("Medium Confidence: The AI used summaries for some related files to understand the context. A standard review of the generated output is recommended.")
                else:
                    self.ui.aiConfidenceGauge.setStyleSheet("QProgressBar::chunk { background-color: #CC7832; }")
                    self.ui.aiConfidenceGauge.setToolTip("Low Confidence - Review Required: This is a complex task that touches many parts of the project, and the AI's view was limited. Thorough manual review and testing are required.")

            if cursor >= total and total > 0:
                progress_percent = 100
                self.ui.nextTaskLabel.setText("All development tasks are complete.")
                self.ui.proceedButton.setText("▶️ Run Final Verification")
            else:
                progress_percent = int((cursor / total) * 100) if total > 0 else 0
                mode_prefix = "FIX: " if is_fix else ""
                task_name = task.get('component_name', 'Unnamed Task')
                self.ui.nextTaskLabel.setText(f"Next task ({cursor + 1}/{total}): {mode_prefix}{task_name}")
                self.ui.proceedButton.setText(f"▶️ Proceed with: {mode_prefix}{task_name}")

            self.ui.progressBar.setValue(progress_percent)
        else:
            self.ui.progressBar.setValue(0)
            self.ui.aiConfidenceGauge.setValue(0)
            self.ui.aiConfidenceLabel.setVisible(False)
            self.ui.aiConfidenceGauge.setVisible(False)
            self.ui.nextTaskLabel.setText("No development plan loaded yet.")
            self.ui.proceedButton.setText("▶️ Proceed")