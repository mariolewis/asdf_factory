# gui/genesis_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QThreadPool

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

    def on_progress_update(self, message):
        """Appends a progress message to the log."""
        self.ui.logOutputTextEdit.append(message)

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
        Updates the PM Checkpoint screen with the current progress, now fully
        aware of the orchestrator's normal vs. fix mode.
        """
        details = self.orchestrator.get_current_task_details()

        if details:
            task = details.get("task", {})
            cursor = details.get("cursor", 0)
            total = details.get("total", 0)
            is_fix = details.get("is_fix_mode", False)

            # Handle plan completion display
            if cursor >= total and total > 0:
                progress_percent = 100
                self.ui.nextTaskLabel.setText("All development tasks are complete.")
                self.ui.proceedButton.setText("▶️ Proceed to Integration")
            else:
                progress_percent = int((cursor / total) * 100) if total > 0 else 0

                mode_prefix = "FIX: " if is_fix else ""
                task_name = task.get('component_name', 'Unnamed Task')

                self.ui.nextTaskLabel.setText(f"Next task ({cursor + 1}/{total}): {mode_prefix}{task_name}")
                self.ui.proceedButton.setText(f"▶️ Proceed with: {mode_prefix}{task_name}")

            self.ui.progressBar.setValue(progress_percent)
        else:
            # Fallback for when no plan is loaded
            self.ui.progressBar.setValue(0)
            self.ui.nextTaskLabel.setText("No development plan loaded yet.")
            self.ui.proceedButton.setText("▶️ Proceed")