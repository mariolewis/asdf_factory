# gui/reports_page.py
import logging
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal
from gui.ui_reports_page import Ui_ReportsPage
from master_orchestrator import MasterOrchestrator
from gui.worker import Worker
import os # Import os for showing the file

class ReportsPage(QWidget):
    """
    Manages the new "Reports Hub" card-based UI.
    Each report generation is handled on a background thread.
    """
    back_to_workflow = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.ui = Ui_ReportsPage()
        self.ui.setupUi(self)
        self.orchestrator = orchestrator
        self.worker_thread_pool = self.window().threadpool

        self.connect_signals()

    def connect_signals(self):
        """Connects all UI signals to their slots."""
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)

        # Connect the Health Snapshot button
        self.ui.generateHealthSnapshotButton.clicked.connect(
            lambda: self._on_report_requested(
                self.ui.generateHealthSnapshotButton,
                "Generate .docx",
                self.orchestrator.generate_health_snapshot_report
            )
        )

        # Connect the Traceability Matrix button
        self.ui.generateTraceabilityMatrixButton.clicked.connect(
            lambda: self._on_report_requested(
                self.ui.generateTraceabilityMatrixButton,
                "Generate .xlsx",
                self.orchestrator.generate_traceability_matrix_report
            )
        )

    def prepare_for_display(self):
        """Called when the page is shown, resets button states."""
        logging.debug("Reports Hub prepared for display.")
        # Reset button states
        self.ui.generateHealthSnapshotButton.setEnabled(True)
        self.ui.generateHealthSnapshotButton.setText("Generate .docx")
        self.ui.generateTraceabilityMatrixButton.setEnabled(True)
        self.ui.generateTraceabilityMatrixButton.setText("Generate .xlsx")

    def _on_report_requested(self, button, original_text, generation_function):
        """
        Handles the button click to generate a report on a worker thread.
        """
        button.setEnabled(False)
        button.setText("Generating...")

        worker = Worker(generation_function)
        worker.signals.result.connect(
            lambda path_or_error: self._on_report_success(button, original_text, path_or_error)
        )
        worker.signals.error.connect(
            lambda error_tuple: self._on_report_failure(button, original_text, str(error_tuple[1]))
        )
        self.worker_thread_pool.start(worker)

    def _on_report_success(self, button, original_text, path_or_error: str):
        """Handles the successful generation of a report."""
        button.setEnabled(True)
        button.setText(original_text)

        if path_or_error.startswith("Error:"):
            logging.error(f"Report generation failed: {path_or_error}")
            QMessageBox.critical(self, "Export Failed", f"Could not generate the report:\n{path_or_error}")
        elif os.path.exists(path_or_error):
            QMessageBox.information(self, "Export Successful", f"Report saved successfully to:\n{path_or_error}")
        else:
            logging.error(f"Report generation returned an invalid path: {path_or_error}")
            QMessageBox.critical(self, "Export Failed", "Report generation returned an empty or invalid path.")

    def _on_report_failure(self, button, original_text, error_message):
        """Shows an error message if report generation fails."""
        button.setEnabled(True)
        button.setText(original_text)
        logging.error(f"Report generation failed: {error_message}")
        QMessageBox.critical(self, "Export Failed", f"Could not generate the report.\nSee logs for details.")