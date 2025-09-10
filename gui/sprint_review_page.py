# gui/sprint_review_page.py

import logging
import markdown
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog
from PySide6.QtCore import Signal, QThreadPool, QTimer

from gui.ui_sprint_review_page import Ui_SprintReviewPage
from master_orchestrator import MasterOrchestrator
from agents.agent_report_generator import ReportGeneratorAgent
from gui.worker import Worker

class SprintReviewPage(QWidget):
    """
    The logic handler for the Sprint Review page.
    """
    return_to_backlog = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.report_generator = ReportGeneratorAgent()
        self.threadpool = QThreadPool()

        self.ui = Ui_SprintReviewPage()
        self.ui.setupUi(self)

        self.connect_signals()

    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        self.ui.returnToBacklogButton.clicked.connect(self.return_to_backlog.emit)
        self.ui.exportSummaryButton.clicked.connect(self.on_export_summary_clicked)

    def prepare_for_display(self):
        """Populates the summary view when the page is shown by running a background task."""
        self.ui.summaryTextEdit.setText("Generating sprint summary...")
        worker = Worker(self._task_generate_summary)
        worker.signals.result.connect(self._handle_summary_result)
        worker.signals.error.connect(self._handle_summary_error)
        self.threadpool.start(worker)

    def _task_generate_summary(self, **kwargs):
        """Background task to get and format the sprint summary."""
        summary_data = self.orchestrator.get_sprint_summary_data()
        return self.report_generator.generate_sprint_summary_text(summary_data)

    def _handle_summary_result(self, summary_markdown: str):
        """Displays the generated summary in the text edit."""
        html = markdown.markdown(summary_markdown)
        self.ui.summaryTextEdit.setHtml(html)

    def _handle_summary_error(self, error_tuple):
        """Handles an error during summary generation."""
        error_msg = f"Failed to generate sprint summary:\n{error_tuple[1]}"
        self.ui.summaryTextEdit.setText(error_msg)
        logging.error(error_msg, exc_info=error_tuple)

    def on_export_summary_clicked(self):
        """Handles exporting the sprint summary to a .docx file."""
        try:
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise ValueError("Project root folder not found.")

            project_root = Path(project_details['project_root_folder'])
            sprint_dir = project_root / "sprints"
            sprint_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = sprint_dir / f"{self.orchestrator.project_name}_Sprint_Summary_{timestamp}.docx"

            file_path, _ = QFileDialog.getSaveFileName(self, "Save Sprint Summary", str(default_filename), "Word Documents (*.docx)")

            if file_path:
                self.window().setEnabled(False)
                self.window().statusBar().showMessage("Generating and saving sprint summary...")
                worker = Worker(self._task_export_summary, file_path)
                worker.signals.result.connect(self._handle_export_result)
                worker.signals.error.connect(self._handle_export_error)
                self.threadpool.start(worker)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to prepare for export:\n{e}")

    def _task_export_summary(self, file_path, **kwargs):
        """Background worker task to get and save the sprint summary."""
        summary_data = self.orchestrator.get_sprint_summary_data()
        docx_bytes = self.report_generator.generate_sprint_summary_docx(summary_data, self.orchestrator.project_name)
        if docx_bytes:
            with open(file_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            return (True, file_path)
        return (False, "Failed to generate report data.")

    def _handle_export_result(self, result):
        """Handles the result of the background export task."""
        self.window().setEnabled(True)
        self.window().statusBar().clearMessage()
        success, message = result
        if success:
            QMessageBox.information(self, "Success", f"Successfully saved sprint summary to:\n{message}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save report: {message}")

    def _handle_export_error(self, error_tuple):
        """Handles a system error from the export worker."""
        self.window().setEnabled(True)
        self.window().statusBar().clearMessage()
        error_msg = f"An unexpected error occurred during export:\n{error_tuple[1]}"
        QMessageBox.critical(self, "Export Error", error_msg)