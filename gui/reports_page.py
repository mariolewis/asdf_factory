# gui/reports_page.py

import logging
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QLabel, QHeaderView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal

from gui.ui_reports_page import Ui_ReportsPage
from master_orchestrator import MasterOrchestrator
from agents.agent_report_generator import ReportGeneratorAgent

class ReportsPage(QWidget):
    """
    The logic handler for the Project Reports page.
    """
    back_to_workflow = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.report_generator = ReportGeneratorAgent()

        self.ui = Ui_ReportsPage()
        self.ui.setupUi(self)

        self.cr_model = QStandardItemModel(self)
        self.ui.crTableView.setModel(self.cr_model)

        self.connect_signals()

    def prepare_for_display(self):
        """Called by the main window just before this page is shown."""
        self.update_all_reports()

    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.crFilterComboBox.currentIndexChanged.connect(self.update_cr_report)
        self.ui.exportProgressButton.clicked.connect(self.on_export_progress_clicked)
        self.ui.exportCrButton.clicked.connect(self.on_export_cr_clicked)
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)

    def update_all_reports(self):
        """Updates all report sections for the active project."""
        self.update_progress_summary()
        self.update_cr_report()

    def clear_layout(self, layout):
        """Removes all widgets from a layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def update_progress_summary(self):
        """Populates the development progress summary section."""
        self.clear_layout(self.ui.progressFormLayout)

        project_id = self.orchestrator.project_id
        if not project_id:
            self.ui.progressFormLayout.addRow(QLabel("No active project."))
            return

        db = self.orchestrator.db_manager
        all_artifacts = db.get_all_artifacts_for_project(project_id)
        status_counts = db.get_component_counts_by_status(project_id)

        if not all_artifacts:
            self.ui.progressFormLayout.addRow(QLabel("No components defined yet."))
            return

        total_components = len(all_artifacts)
        self.ui.progressFormLayout.addRow("Total Components Defined:", QLabel(str(total_components)))

        for status, count in status_counts.items():
            # THIS IS THE FIX: Handle cases where status might be None in the database
            display_status = status.replace('_', ' ').title() if status else "Status Not Set"
            self.ui.progressFormLayout.addRow(f"{display_status}:", QLabel(str(count)))

    def update_cr_report(self):
        """Populates the Change Requests & Bug Fixes table."""
        self.cr_model.clear()
        self.cr_model.setHorizontalHeaderLabels(['ID', 'Type', 'Status', 'Description'])

        project_id = self.orchestrator.project_id
        if not project_id:
            return

        filter_type = self.ui.crFilterComboBox.currentText()
        report_data = self.orchestrator.get_cr_and_bug_report_data(project_id, filter_type)

        for item in report_data:
            id_item = QStandardItem(str(item.get("id", "N/A")))
            type_item = QStandardItem(item.get("type", "N/A"))
            status_item = QStandardItem(item.get("status", "N/A"))
            desc_item = QStandardItem(item.get("description", "N/A"))
            self.cr_model.appendRow([id_item, type_item, status_item, desc_item])

        header = self.ui.crTableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

    def on_export_progress_clicked(self):
        """Exports the progress summary report."""
        project_id = self.orchestrator.project_id
        if not project_id:
            QMessageBox.warning(self, "No Project", "No active project to report on.")
            return

        db = self.orchestrator.db_manager
        all_artifacts = db.get_all_artifacts_for_project(project_id)
        status_counts = db.get_component_counts_by_status(project_id)

        total_components = len(all_artifacts)
        project_name = self.orchestrator.project_name
        default_filename = f"{project_name}_Progress_Summary.docx"

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Progress Summary", default_filename, "Word Documents (*.docx)")
        if file_path:
            docx_bytes = self.report_generator.generate_progress_summary_docx(total_components, status_counts)
            with open(file_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            QMessageBox.information(self, "Success", f"Successfully exported report to:\n{file_path}")

    def on_export_cr_clicked(self):
        """Exports the CR & Bug Fixes report."""
        project_id = self.orchestrator.project_id
        if not project_id:
            QMessageBox.warning(self, "No Project", "No active project to report on.")
            return

        filter_type = self.ui.crFilterComboBox.currentText()
        report_data = self.orchestrator.get_cr_and_bug_report_data(project_id, filter_type)
        project_name = self.orchestrator.project_name
        default_filename = f"{project_name}_CR_Bug_Report.docx"

        file_path, _ = QFileDialog.getSaveFileName(self, "Save CR & Bug Report", default_filename, "Word Documents (*.docx)")
        if file_path:
            docx_bytes = self.report_generator.generate_cr_bug_report_docx(report_data, filter_type)
            with open(file_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            QMessageBox.information(self, "Success", f"Successfully exported report to:\n{file_path}")