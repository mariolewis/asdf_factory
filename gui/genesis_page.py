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
        """Resets the page to its initial state."""
        logging.info("Resetting GenesisPage for a new project.")
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

    def _execute_task(self, task_function, on_result, *args):
        """Generic method to run a task in the background."""
        self.ui.logOutputTextEdit.clear()
        self._set_ui_busy(True)
        worker = Worker(task_function, *args)
        worker.signals.progress.connect(self.on_progress_update)
        worker.signals.result.connect(on_result)
        worker.signals.error.connect(self._on_task_error)
        self.threadpool.start(worker)

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
        self._execute_task(self._task_run_development_step, self._handle_development_result)

    def _handle_development_result(self, result):
        """Handles the successful completion of the development step."""
        self.ui.logOutputTextEdit.append(f"\n--- SUCCESS ---\n{result}")
        self._set_ui_busy(False)
        self.update_checkpoint_display()
        # Check if the orchestrator's phase has changed away from GENESIS
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

    # --- Backend Logic (to be run in worker thread) ---

    def _task_run_development_step(self, **kwargs):
        """The actual function that runs in the background."""
        progress_callback = kwargs.get('progress_callback')
        self.orchestrator.handle_proceed_action(progress_callback=progress_callback)
        return "Step complete."