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
        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_new_project(self):
        """Resets the page to its initial state for a new project."""
        logging.info("Resetting GenesisPage for a new project.")
        self.ui.stackedWidget.setCurrentWidget(self.ui.checkpointPage)
        self.ui.progressBar.setValue(0)
        self.ui.nextTaskLabel.setText("No development plan loaded yet.")
        self.ui.logOutputTextEdit.clear()
        self.setEnabled(True)

    def prepare_for_display(self):
        """
        This is the standard refresh method called by the main window before the
        page is shown. It ensures the UI is always up-to-date.
        """
        logging.info("Preparing GenesisPage for display.")
        self.ui.stackedWidget.setCurrentWidget(self.ui.checkpointPage)
        self.update_checkpoint_display()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.proceedButton.clicked.connect(self.run_development_step)

    def _set_ui_busy(self, is_busy):
        """Disables or enables the page while a background task runs."""
        self.ui.proceedButton.setEnabled(not is_busy)
        if is_busy:
            self.ui.stackedWidget.setCurrentWidget(self.ui.processingPage)
        else:
            self.ui.stackedWidget.setCurrentWidget(self.ui.checkpointPage)

    def on_progress_update(self, progress_data):
        """
        Appends a progress message to the log in a thread-safe manner,
        applying color based on the status.
        """
        try:
            # The signal now emits a tuple (status, message)
            status, message = progress_data

            # New, brighter color map for better visibility in the log
            color_map = {
                "SUCCESS": "#00C853", # Bright Green
                "INFO": "#A9B7C6",    # Light Gray (Secondary Text)
                "WARNING": "#FFAB00", # Bright Amber
                "ERROR": "#D50000"     # Bright Red
            }

            # Default to the secondary text color if status is unknown
            color = color_map.get(status, "#A9B7C6")

            # Format the message as HTML to apply the color
            html_message = f'<font color="{color}">{message}</font>'

            # Use a QTimer to ensure the append operation runs on the main GUI thread
            QTimer.singleShot(0, lambda: self.ui.logOutputTextEdit.append(html_message))

        except Exception as e:
            # Fallback for any unexpected data format
            QTimer.singleShot(0, lambda: self.ui.logOutputTextEdit.append(str(progress_data)))
            logging.error(f"Error processing progress update: {e}")

    def _on_task_error(self, error_tuple):
        """Handles errors from the worker thread."""
        error_msg = f"An error occurred in a background task:\n{error_tuple[2]}"
        self.ui.logOutputTextEdit.append(f"\n--- ERROR ---\n{error_msg}")
        QMessageBox.critical(self, "Error", error_msg)
        self._set_ui_busy(False)
        self.update_checkpoint_display()

    def run_development_step(self):
        """Initiates the background task to run the next development step."""
        worker = Worker(self.orchestrator.handle_proceed_action)
        worker.signals.progress.connect(self.on_progress_update)
        worker.signals.result.connect(self._handle_development_result)
        worker.signals.error.connect(self._on_task_error)
        self._set_ui_busy(True)
        self.ui.logOutputTextEdit.clear()
        self.threadpool.start(worker)

    def _handle_development_result(self, result):
        """Handles the successful completion of the development step."""
        self.ui.logOutputTextEdit.append(f"\n--- SUCCESS ---\n{result}")
        self._set_ui_busy(False)
        self.update_checkpoint_display()
        if self.orchestrator.current_phase.name != "GENESIS":
            self.genesis_complete.emit()

    def update_checkpoint_display(self):
        """
        Updates the PM Checkpoint screen (now the Sprint Progress Dashboard)
        with the current progress and status.
        """
        # Set static text first
        sprint_goal_text = self.orchestrator.get_sprint_goal()
        self.ui.sprintGoalLabel.setText(f"<b>Sprint Goal:</b> {sprint_goal_text}")
        # Also update the label on the processing page for consistency
        self.ui.sprintGoalValueLabel.setText(sprint_goal_text)

        mode = self.orchestrator.get_current_mode()
        self.ui.sprintStatusIndicatorLabel.setText(f"MODE: {mode}")

        # Set status indicator color based on mode
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

            # --- AI Confidence Gauge Logic ---
            # As per your suggestion, only show the confidence gauge in normal development mode.
            show_confidence = not is_fix
            self.ui.aiConfidenceLabel.setVisible(show_confidence)
            self.ui.aiConfidenceGauge.setVisible(show_confidence)

            if show_confidence:
                confidence_score = details.get("confidence_score", 0)
                self.ui.aiConfidenceGauge.setValue(confidence_score)

                if confidence_score > 80: # High Confidence
                    self.ui.aiConfidenceGauge.setStyleSheet("QProgressBar::chunk { background-color: #6A8759; }") # Green
                    self.ui.aiConfidenceGauge.setToolTip("High Confidence: The AI had a clear and complete view of this task. The generated output is likely to be highly accurate.")
                elif confidence_score > 40: # Medium Confidence
                    self.ui.aiConfidenceGauge.setStyleSheet("QProgressBar::chunk { background-color: #FFC66D; }") # Yellow
                    self.ui.aiConfidenceGauge.setToolTip("Medium Confidence: The AI used summaries for some related files to understand the context. A standard review of the generated output is recommended.")
                else: # Low Confidence
                    self.ui.aiConfidenceGauge.setStyleSheet("QProgressBar::chunk { background-color: #CC7832; }") # Red/Orange
                    self.ui.aiConfidenceGauge.setToolTip("Low Confidence - Review Required: This is a complex task that touches many parts of the project, and the AI's view was limited. Thorough manual review and testing are required.")
            # --- End of Logic ---

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