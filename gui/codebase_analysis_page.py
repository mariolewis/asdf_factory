# gui/codebase_analysis_page.py

import logging
import threading
from PySide6.QtWidgets import QWidget, QMessageBox, QApplication
from PySide6.QtCore import Signal, QThreadPool, QTimer

from gui.ui_codebase_analysis_page import Ui_CodebaseAnalysisPage
from gui.worker import Worker
from master_orchestrator import MasterOrchestrator

class CodebaseAnalysisPage(QWidget):
    """
    The logic handler for the Codebase Analysis progress page.
    """
    analysis_complete = Signal()
    analysis_cancelled = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.ui = Ui_CodebaseAnalysisPage()
        self.ui.setupUi(self)

        self.analysis_worker = None
        self.pause_event = threading.Event()

        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.pauseButton.clicked.connect(self.on_pause_clicked)
        self.ui.resumeButton.clicked.connect(self.on_resume_clicked)
        self.ui.cancelButton.clicked.connect(self.on_cancel_clicked)
        self.ui.continueButton.clicked.connect(self.analysis_complete.emit)
        self.analysis_cancelled.connect(self.orchestrator.reset) # Connect to orchestrator

    def prepare_for_display(self):
        """Resets UI and starts the background analysis task."""
        self.ui.logOutputTextEdit.clear()
        self.ui.progressBar.setValue(0)
        self.ui.statusLabel.setText("Status: Initializing scan...")
        self.ui.continueButton.setVisible(False)
        self.ui.pauseButton.setEnabled(True)
        self.ui.resumeButton.setEnabled(False)
        self.ui.cancelButton.setEnabled(True)
        self.pause_event.clear()

        self.analysis_worker = Worker(self._task_run_analysis, self.pause_event)
        self.analysis_worker.signals.progress.connect(self.on_progress_update)
        self.analysis_worker.signals.result.connect(self._handle_analysis_result)
        self.analysis_worker.signals.error.connect(self._on_task_error)
        self.analysis_worker.signals.finished.connect(self.on_task_finished)
        self.window().threadpool.start(self.analysis_worker)

    def on_pause_clicked(self):
        """Sets the pause event to halt the background worker."""
        self.pause_event.set()
        self.ui.pauseButton.setEnabled(False)
        self.ui.resumeButton.setEnabled(True)
        self.ui.logOutputTextEdit.append("<i>--- Analysis paused by user ---</i>")

    def on_resume_clicked(self):
        """Clears the pause event to resume the background worker."""
        self.pause_event.clear()
        self.ui.pauseButton.setEnabled(True)
        self.ui.resumeButton.setEnabled(False)
        self.ui.logOutputTextEdit.append("<i>--- Resuming analysis... ---</i>")

    def on_cancel_clicked(self):
        """Cancels the analysis and cleans up the project."""
        reply = QMessageBox.question(self, "Cancel Analysis",
                                     "Are you sure you want to cancel the analysis? All progress will be lost and created records will be deleted.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.analysis_worker:
                self.analysis_worker.cancel()
            self.ui.logOutputTextEdit.append("<i>--- Cancelling analysis, please wait for the current step to finish... ---</i>")
            # Disable all action buttons to prevent further interaction
            self.ui.cancelButton.setEnabled(False)
            self.ui.pauseButton.setEnabled(False)
            self.ui.resumeButton.setEnabled(False)

    def on_progress_update(self, progress_data):
        """
        Updates the UI with structured progress from the worker thread, including
        the main window's status bar.
        """
        try:
            main_window = self.window()
            status_type, data = progress_data

            if status_type == "SCANNING":
                total_files = data.get("total_files", 0)
                status_text = f"Scanning {total_files} source files..."
                self.ui.statusLabel.setText(status_text)
                if main_window: main_window.statusBar().showMessage(status_text)

            elif status_type == "SUMMARIZING":
                total = data.get("total", 0)
                current = data.get("current", 0)
                filename = data.get("filename", "")
                progress_percent = int((current / total) * 100) if total > 0 else 0
                self.ui.progressBar.setValue(progress_percent)
                status_text = f"Summarizing file {current} of {total}..."
                self.ui.statusLabel.setText(status_text)
                self.ui.logOutputTextEdit.append(f"({current}/{total}) Summarizing {filename}...")
                if main_window: main_window.statusBar().showMessage(status_text)

            elif status_type == "SYNTHESIZING":
                status_text = "Preparing specification documents..."
                self.ui.statusLabel.setText(status_text)
                self.ui.logOutputTextEdit.append(f"\n--- {status_text} ---")
                if main_window: main_window.statusBar().showMessage(status_text)

            QApplication.processEvents()
        except Exception as e:
            logging.error(f"Failed to update progress UI: {e}")

    def on_task_finished(self):
        """Handles post-task UI cleanup, like clearing all status messages."""
        main_window = self.window()
        if main_window and hasattr(main_window, 'statusBar'):
            # Clear both the persistent widget and any temporary messages
            main_window.clear_persistent_status()
            main_window.statusBar().clearMessage()

    def _handle_analysis_result(self, result):
        """
        Handles the final result of the analysis task, performing cleanup
        if the task was cancelled or failed.
        """
        if result == "SUCCESS":
            self.ui.logOutputTextEdit.append("\n<b>--- Analysis and Specification Synthesis Complete ---</b>")
            self.ui.progressBar.setValue(100)
            self.ui.continueButton.setVisible(True)
        elif result == "CANCELLED":
            self.ui.logOutputTextEdit.append("\n<b>--- Analysis Cancelled by User ---</b>")
            self.orchestrator.cancel_and_cleanup_analysis()
            self.analysis_cancelled.emit()
        else: # FAILED
            self.ui.logOutputTextEdit.append("\n<b>--- Analysis Failed ---</b>")
            QMessageBox.critical(self, "Error", "The analysis process failed. Please check the logs.")
            self.orchestrator.cancel_and_cleanup_analysis()
            self.analysis_cancelled.emit()

        self.ui.pauseButton.setEnabled(False)
        self.ui.resumeButton.setEnabled(False)
        self.ui.cancelButton.setEnabled(False)

    def _on_task_error(self, error_tuple):
        """Handles a critical error from the worker thread."""
        error_msg = f"A critical error occurred during analysis:\n{error_tuple[1]}"
        self.ui.logOutputTextEdit.append(f"<font color='red'>{error_msg}</font>")
        logging.error(error_msg, exc_info=error_tuple)
        self.ui.pauseButton.setEnabled(False)
        self.ui.resumeButton.setEnabled(False)
        self.ui.cancelButton.setEnabled(False)
        QMessageBox.critical(self, "Analysis Failed", error_msg)

    def _task_run_analysis(self, pause_event, progress_callback, worker_instance):
        """
        Background worker task that runs the full codebase archeology process,
        now returning an explicit status string on completion or cancellation.
        """
        from agents.agent_codebase_scanner import CodebaseScannerAgent
        from agents.agent_spec_synthesis import SpecSynthesisAgent

        try:
            if worker_instance.is_cancelled: return "CANCELLED"

            project_id = self.orchestrator.project_id
            project_root = self.orchestrator.project_root_path

            if not all([project_id, project_root]):
                raise Exception("Project ID or root path is not set in the orchestrator.")

            # Step 1: Scan codebase and generate summaries
            scanner_agent = CodebaseScannerAgent(
                llm_service=self.orchestrator.llm_service,
                db_manager=self.orchestrator.db_manager
            )
            scan_successful = scanner_agent.scan_project(project_id, project_root, pause_event, progress_callback, worker_instance)

            if worker_instance.is_cancelled: return "CANCELLED"
            if not scan_successful: return "FAILED"

            if pause_event.is_set():
                pause_event.wait()

            if worker_instance.is_cancelled: return "CANCELLED"

            # Step 2: Synthesize specification documents from summaries
            progress_callback(("SYNTHESIZING", {}))
            synthesis_agent = SpecSynthesisAgent(orchestrator=self.orchestrator)
            synthesis_agent.synthesize_all_specs(project_id)

            # Step 3: Set the next phase for the main window to pick up.
            self.orchestrator.set_phase("AWAITING_BROWNFIELD_STRATEGY")

            return "SUCCESS"

        except Exception as e:
            logging.error(f"Full analysis task failed: {e}", exc_info=True)
            return "FAILED"