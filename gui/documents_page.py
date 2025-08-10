# gui/documents_page.py

import logging
import re
from PySide6.QtWidgets import QWidget, QMessageBox, QFileDialog, QHeaderView, QAbstractItemView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal, QItemSelection, QItemSelectionModel

from gui.ui_documents_page import Ui_DocumentsPage
from master_orchestrator import MasterOrchestrator
from agents.agent_report_generator import ReportGeneratorAgent

class DocumentsPage(QWidget):
    """
    The logic handler for the Project Documents page.
    """
    back_to_workflow = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.report_generator = ReportGeneratorAgent()
        self.project_docs_cache = {}

        self.ui = Ui_DocumentsPage()
        self.ui.setupUi(self)

        self.ui.projectSelectorComboBox.setVisible(False)
        self.ui.instructionLabel.setText("Showing all available documents for the currently active project.")
        self.ui.exportButton.setEnabled(False)
        self.ui.documentsTableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.documentsTableView.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.model = QStandardItemModel(self)
        self.ui.documentsTableView.setModel(self.model)

        self.connect_signals()

    def prepare_for_display(self):
        """Called by the main window just before this page is shown."""
        self.update_documents_list()

    def connect_signals(self):
        """Connects widget signals to the appropriate slots."""
        self.ui.exportButton.clicked.connect(self.on_export_clicked)
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)
        self.ui.documentsTableView.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        """Enables or disables the export button based on table selection."""
        is_selection = self.ui.documentsTableView.selectionModel().hasSelection()
        self.ui.exportButton.setEnabled(is_selection)

    def _get_version_from_text(self, content: str) -> str:
        """Parses document content to find a version number."""
        match = re.search(r'(?:v|Version\s|Version number:\s)(\d+\.\d+)', content, re.IGNORECASE)
        if match:
            return match.group(1)
        return "N/A"

    def update_documents_list(self):
        """Populates the table with documents and their versions for the active project."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Document Name', 'Version', 'Content Key'])
        self.ui.documentsTableView.setColumnHidden(2, True)

        project_id = self.orchestrator.project_id
        if not project_id:
            return

        # Corrected: Direct call to the db_manager
        project_docs = self.orchestrator.db_manager.get_project_by_id(project_id)

        if not project_docs:
            return

        self.project_docs_cache = dict(project_docs)

        doc_map = {
            "Application Specification": "final_spec_text",
            "UX/UI Specification": "ux_spec_text",
            "Technical Specification": "tech_spec_text",
            "Coding Standard": "coding_standard_text",
            "Development Plan": "development_plan_text",
            "Complexity & Risk Assessment": "complexity_assessment_text",
            "Integration Plan": "integration_plan_text",
            "UI Test Plan": "ui_test_plan_text",
        }

        for name, key in doc_map.items():
            content = self.project_docs_cache.get(key)
            if content:
                version = self._get_version_from_text(content)
                name_item = QStandardItem(name)
                version_item = QStandardItem(version)
                key_item = QStandardItem(key)
                self.model.appendRow([name_item, version_item, key_item])

        header = self.ui.documentsTableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

    def on_export_clicked(self):
        """Handles exporting the selected document to a .docx file."""
        selection_model = self.ui.documentsTableView.selectionModel()
        if not selection_model.hasSelection():
            return

        selected_row = selection_model.selectedRows()[0].row()
        doc_name_item = self.model.item(selected_row, 0)
        doc_key_item = self.model.item(selected_row, 2)

        doc_name = doc_name_item.text()
        doc_key = doc_key_item.text()
        content = self.project_docs_cache.get(doc_key)

        project_name = self.orchestrator.project_name
        default_filename = f"{project_name}_{doc_name.replace(' ', '_')}.docx"

        file_path, _ = QFileDialog.getSaveFileName(self, f"Save {doc_name}", default_filename, "Word Documents (*.docx)")

        if file_path and content:
            try:
                is_code = doc_key in ["development_plan_text", "integration_plan_text", "complexity_assessment_text"]
                docx_bytes = self.report_generator.generate_text_document_docx(f"{doc_name} - {project_name}", content, is_code=is_code)
                with open(file_path, 'wb') as f:
                    f.write(docx_bytes.getbuffer())
                QMessageBox.information(self, "Success", f"Successfully exported '{doc_name}' to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export document: {e}")