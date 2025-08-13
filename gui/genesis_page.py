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
        """Updates the PM Checkpoint screen with the current progress."""
        task = self.orchestrator.get_current_task_details()
        total_tasks = len(self.orchestrator.active_plan) if self.orchestrator.active_plan else 0
        cursor = self.orchestrator.active_plan_cursor

        if self.orchestrator.active_plan and cursor < total_tasks:
            progress_percent = int((cursor / total_tasks) * 100)
            self.ui.progressBar.setValue(progress_percent)
            self.ui.nextTaskLabel.setText(f"Next component to build ({cursor + 1}/{total_tasks}): {task.get('component_name')}")
        else:
            self.ui.progressBar.setValue(100)
            self.ui.nextTaskLabel.setText("All development tasks are complete. Click 'Proceed' to begin integration.")