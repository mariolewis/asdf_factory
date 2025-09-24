# gui/manual_ui_testing_page.py

import logging
from pathlib import Path
import shutil
from datetime import datetime
import docx
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import Signal, QThreadPool

from gui.ui_manual_ui_testing_page import Ui_ManualUITestingPage
from master_orchestrator import MasterOrchestrator
from gui.worker import Worker

class ManualUITestingPage(QWidget):
    """
    The logic handler for the Manual UI Testing page.
    """
    go_to_documents = Signal()
    testing_complete = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.selected_file_path = ""

        self.ui = Ui_ManualUITestingPage()
        self.ui.setupUi(self)

        self.threadpool = QThreadPool()
        self.connect_signals()

    def prepare_for_display(self):
        """Resets the page to its initial state."""
        self.selected_file_path = ""
        self.ui.filePathLineEdit.clear()
        self.ui.processResultsButton.setEnabled(False)
        self.setEnabled(True)

    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.goToDocumentsButton.clicked.connect(self.go_to_documents.emit)
        self.ui.browseButton.clicked.connect(self.on_browse_clicked)
        self.ui.processResultsButton.clicked.connect(self.run_process_results_task)

    def on_browse_clicked(self):
        """Opens a file dialog to select the completed test plan."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Completed Test Plan", "", "Documents (*.docx *.txt *.md)")
        if file_path:
            self.selected_file_path = file_path
            self.ui.filePathLineEdit.setText(file_path)
            self.ui.processResultsButton.setEnabled(True)

    def _set_ui_busy(self, is_busy, message="Processing..."):
        """Disables or enables the page and updates the main status bar."""
        self.setEnabled(not is_busy)
        main_window = self.parent()
        if main_window and hasattr(main_window, 'statusBar'):
            if is_busy:
                main_window.statusBar().showMessage(message)
            else:
                main_window.statusBar().clearMessage()

    def run_process_results_task(self):
        """Initiates the background task to process the test results."""
        self.orchestrator.is_project_dirty = True

        self.window().statusBar().showMessage("Processing uploaded test results file...")
        self._set_ui_busy(True)

        worker = Worker(self._task_process_results, self.selected_file_path)
        worker.signals.result.connect(self._handle_processing_result)
        worker.signals.error.connect(self._handle_processing_error)
        self.threadpool.start(worker)

    def _handle_processing_result(self, success):
        """Handles the result from the worker thread."""
        try:
            if success:
                self.testing_complete.emit()
            else:
                QMessageBox.critical(self, "Error", "Failed to submit test results. Please check the logs.")
        finally:
            self._set_ui_busy(False)

    def _handle_processing_error(self, error_tuple):
        """Handles an error from the worker thread."""
        try:
            QMessageBox.critical(self, "Processing Error", f"An error occurred while processing the file:\n{error_tuple[1]}")
        finally:
            self._set_ui_busy(False)

    def _task_process_results(self, file_path, **kwargs):
        """
        Background worker task that saves a copy of the uploaded results,
        reads its content, and passes it to the orchestrator for analysis.
        """
        try:
            # Step 1: Save a copy of the uploaded file for archiving.
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise IOError("Project root folder could not be determined for archiving test results.")

            project_root = Path(project_details['project_root_folder'])
            reports_dir = project_root / "docs" / "test_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            source_path = Path(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            destination_path = reports_dir / f"manual_fe_test_results_{timestamp}{source_path.suffix}"

            shutil.copy(source_path, destination_path)
            logging.info(f"Archived uploaded test results to: {destination_path}")

            # Step 2: Read the file content for processing (existing logic).
            content = ""
            if file_path.endswith('.docx'):
                doc = docx.Document(file_path)
                content = "\n".join([p.text for p in doc.paragraphs])
            else: # For .txt and .md files
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            # Step 3: Pass content to the orchestrator.
            self.orchestrator.handle_ui_test_result_upload(content)
            return True
        except Exception as e:
            logging.error(f"Failed to process test results file: {e}", exc_info=True)
            # Re-raise the exception to be caught by the worker's error handler
            raise e