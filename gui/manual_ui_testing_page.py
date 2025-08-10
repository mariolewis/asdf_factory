# gui/manual_ui_testing_page.py

import logging
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

    def run_process_results_task(self):
        """Initiates the background task to process the test results."""
        # Mark the project as dirty immediately, before starting the task
        self.orchestrator.is_project_dirty = True

        # Show confirmation message IMMEDIATELY
        QMessageBox.information(self, "Processing Started", "Your test results have been submitted and are being processed in the background. The application will advance to the next step when complete.")

        self.ui.processResultsButton.setEnabled(False)
        self.ui.processResultsButton.setText("Processing...")

        worker = Worker(self._task_process_results, self.selected_file_path)
        worker.signals.result.connect(self._handle_processing_result)
        worker.signals.error.connect(self._handle_processing_error)
        self.threadpool.start(worker)

    def _handle_processing_result(self, success):
        """Handles the result from the worker thread."""
        self.ui.processResultsButton.setText("Process Test Results")
        # The success message is no longer needed here.
        # We just emit the signal to trigger the UI refresh to the next phase.
        if success:
            self.testing_complete.emit()
        else:
            QMessageBox.critical(self, "Error", "Failed to submit test results. Please check the logs.")
            self.ui.processResultsButton.setEnabled(True)

    def _handle_processing_error(self, error_tuple):
        """Handles an error from the worker thread."""
        self.ui.processResultsButton.setText("Process Test Results")
        self.ui.processResultsButton.setEnabled(True)
        QMessageBox.critical(self, "Processing Error", f"An error occurred while processing the file:\n{error_tuple[1]}")

    def _task_process_results(self, file_path, **kwargs):
        """The actual function that runs in the background to read the file and pass it to the orchestrator."""
        content = ""
        try:
            if file_path.endswith('.docx'):
                doc = docx.Document(file_path)
                content = "\n".join([p.text for p in doc.paragraphs])
            else: # For .txt and .md files
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            self.orchestrator.handle_ui_test_result_upload(content)
            return True
        except Exception as e:
            logging.error(f"Failed to process test results file: {e}", exc_info=True)
            # Re-raise the exception to be caught by the worker's error handler
            raise e