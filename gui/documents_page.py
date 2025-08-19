# gui/documents_page.py

import logging
import re
from PySide6.QtWidgets import (QWidget, QMessageBox, QFileDialog, QHeaderView,
                               QAbstractItemView, QDialog, QVBoxLayout, QTextEdit,
                               QDialogButtonBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal, QItemSelection

from gui.ui_documents_page import Ui_DocumentsPage
from master_orchestrator import MasterOrchestrator
from agents.agent_report_generator import ReportGeneratorAgent

class DocumentViewerDialog(QDialog):
    """A simple dialog to display document content."""
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(content) # Use setHtml to render formatted content
        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

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

        # Initial UI state setup
        self.ui.exportButton.setEnabled(False)
        self.ui.viewButton.setEnabled(False)
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
        self.ui.viewButton.clicked.connect(self.on_view_clicked)
        self.ui.exportButton.clicked.connect(self.on_export_clicked)
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)
        self.ui.documentsTableView.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        """Enables or disables buttons based on table selection."""
        is_selection = self.ui.documentsTableView.selectionModel().hasSelection()
        self.ui.viewButton.setEnabled(is_selection)
        self.ui.exportButton.setEnabled(is_selection)

    def _format_content_for_viewing(self, content: str, doc_key: str) -> str:
        """Converts document content to HTML for rich text display."""
        # Simple check for JSON content
        if doc_key in ["development_plan_text", "complexity_assessment_text", "integration_plan_text"]:
            try:
                parsed_json = json.loads(content)
                pretty_json = json.dumps(parsed_json, indent=4)
                return f"<pre>{pretty_json}</pre>"
            except json.JSONDecodeError:
                pass # Fallback to plain text
        # For Markdown or plain text, convert newlines to <br> for HTML
        return content.replace('\n', '<br>')

    def _get_selected_doc_info(self) -> dict | None:
        """Helper to get all info for the selected document."""
        selection_model = self.ui.documentsTableView.selectionModel()
        if not selection_model.hasSelection():
            return None

        selected_row = selection_model.selectedRows()[0].row()
        doc_name = self.model.item(selected_row, 0).text()
        doc_key = self.model.item(selected_row, 2).text()
        content = self.project_docs_cache.get(doc_key)

        return {"name": doc_name, "key": doc_key, "content": content}

    def on_view_clicked(self):
        """Handles viewing the selected document in a dialog."""
        doc_info = self._get_selected_doc_info()
        if not doc_info or not doc_info["content"]:
            QMessageBox.warning(self, "No Content", "Could not retrieve content for the selected document.")
            return

        formatted_content = self._format_content_for_viewing(doc_info["content"], doc_info["key"])

        viewer = DocumentViewerDialog(f"Viewing: {doc_info['name']}", formatted_content, self)
        viewer.exec()

    def update_documents_list(self):
        """Populates the table with documents and their versions for the active project."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Document Name', 'Version', 'Content Key'])
        self.ui.documentsTableView.setColumnHidden(2, True)

        project_id = self.orchestrator.project_id
        if not project_id:
            return

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

    def _get_version_from_text(self, content: str) -> str:
        """Parses document content to find a version number."""
        match = re.search(r'(?:v|Version\s|Version number:\s)(\d+\.\d+)', content, re.IGNORECASE)
        if match:
            return match.group(1)
        return "N/A"

    def on_export_clicked(self):
        """Handles exporting the selected document to a .docx file."""
        doc_info = self._get_selected_doc_info()
        if not doc_info or not doc_info["content"]:
            QMessageBox.warning(self, "No Content", "Could not retrieve content to export.")
            return

        # Use the simplified filename as requested
        default_filename = f"{doc_info['name'].replace(' ', '_')}.docx"

        file_path, _ = QFileDialog.getSaveFileName(self, f"Export {doc_info['name']}", default_filename, "Word Documents (*.docx)")

        if file_path:
            try:
                # The ReportGeneratorAgent can handle both text and JSON-like content
                docx_bytes = self.report_generator.generate_text_document_docx(
                    title=f"{doc_info['name']} - {self.orchestrator.project_name}",
                    content=doc_info['content'],
                    is_code=doc_info['key'] in ["development_plan_text", "integration_plan_text", "complexity_assessment_text"]
                )
                with open(file_path, 'wb') as f:
                    f.write(docx_bytes.getbuffer())
                QMessageBox.information(self, "Success", f"Successfully exported '{doc_info['name']}' to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export document: {e}")