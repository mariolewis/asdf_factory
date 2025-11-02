# gui/documents_page.py

import logging
import html
import re
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QMessageBox, QFileDialog, QHeaderView,
                             QAbstractItemView, QDialog, QVBoxLayout, QTextEdit,
                             QDialogButtonBox, QListWidget, QListWidgetItem)
from PySide6.QtGui import QColor, Qt
from PySide6.QtCore import Signal, QThreadPool, QTimer

from gui.ui_documents_page import Ui_DocumentsPage
from master_orchestrator import MasterOrchestrator
from gui.worker import Worker
from gui.utils import format_timestamp_for_display, render_markdown_to_html

class DocumentViewerDialog(QDialog):
    """A simple dialog to display document content."""
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        # Use our new robust renderer
        html_content = render_markdown_to_html(content)
        text_edit.setHtml(html_content)
        layout.addWidget(text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

class DocumentsPage(QWidget):
    """
    Logic handler for the Document Hub page.
    Manages system specs (DB) and other docs (filesystem) with a review log.
    """
    back_to_workflow = Signal()

    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.threadpool = QThreadPool()
        self.current_selected_doc_path = None # Stores the relative path

        self.ui = Ui_DocumentsPage()
        self.ui.setupUi(self)

        self.connect_signals()
        self.setup_initial_state()

    def connect_signals(self):
        """Connects UI element signals to their handler slots."""
        self.ui.specDocumentsListWidget.currentItemChanged.connect(self._on_spec_document_selected)
        self.ui.otherDocumentsListWidget.currentItemChanged.connect(self._on_other_document_selected)

        # Connect double-click signals for viewing
        self.ui.specDocumentsListWidget.itemDoubleClicked.connect(self._on_document_double_clicked)
        self.ui.otherDocumentsListWidget.itemDoubleClicked.connect(self._on_document_double_clicked)

        self.ui.addOtherDocumentButton.clicked.connect(self._on_add_other_document)
        self.ui.uploadVersionButton.clicked.connect(self._on_upload_new_version)

        self.ui.saveFeedbackButton.clicked.connect(self._on_save_feedback)
        self.ui.markApprovedButton.clicked.connect(self._on_mark_approved)
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)

    def setup_initial_state(self):
        """Sets the initial state of the widgets on the page."""
        self.ui.logTextEdit.setPlaceholderText("Enter or paste feedback or review comments here...")
        self._update_review_panel_state(is_enabled=False)

    def prepare_for_display(self):
        """Called when the page is displayed. Refreshes the document lists."""
        self.refresh_document_lists()
        self._update_review_panel_state(is_enabled=False)
        self.ui.reviewLogBrowser.clear()
        self.ui.reviewLogHeaderLabel.setText("Review Log (Select a Document)")

    def refresh_document_lists(self):
        """Fetches and displays the classified lists of project documents."""
        self.ui.specDocumentsListWidget.clear()
        self.ui.otherDocumentsListWidget.clear()

        if not self.orchestrator.project_id:
            return

        spec_docs, other_docs = self.orchestrator.get_project_documents()

        for doc in spec_docs:
            item = QListWidgetItem(doc['name'])
            item.setData(Qt.UserRole, doc['path']) # Store the relative path
            item.setToolTip(doc['path'])
            self.ui.specDocumentsListWidget.addItem(item)

        for doc_path in other_docs:
            item = QListWidgetItem(doc_path)
            item.setData(Qt.UserRole, doc_path) # Store the relative path
            item.setToolTip(doc_path)
            self.ui.otherDocumentsListWidget.addItem(item)

    def _on_spec_document_selected(self, current_item: QListWidgetItem):
        """Handles selection in the Specifications list."""
        if not current_item:
            return

        # Deselect item in the other list
        self.ui.otherDocumentsListWidget.setCurrentItem(None)

        doc_path = current_item.data(Qt.UserRole)
        self._set_active_document(doc_path)

    def _on_other_document_selected(self, current_item: QListWidgetItem):
        """Handles selection in the Other Documents list."""
        if not current_item:
            return

        # Deselect item in the other list
        self.ui.specDocumentsListWidget.setCurrentItem(None)

        doc_path = current_item.data(Qt.UserRole)
        self._set_active_document(doc_path)

    def _set_active_document(self, doc_relative_path: str):
        """Sets the currently active document and loads its log."""
        self.current_selected_doc_path = doc_relative_path
        self.ui.reviewLogHeaderLabel.setText(f"Review Log for: {Path(doc_relative_path).name}")
        self._update_review_panel_state(is_enabled=True)
        self._load_review_log()

    def _update_review_panel_state(self, is_enabled: bool):
        """Enables or disables the entire review log and actions panel."""
        self.ui.reviewLogContentsWidget.setEnabled(is_enabled)
        self.ui.uploadVersionButton.setEnabled(is_enabled)

    def _load_review_log(self):
        """Loads and displays the review log for the currently selected document."""
        self.ui.reviewLogBrowser.clear()
        if not self.current_selected_doc_path or not self.orchestrator.project_id:
            return

        log_entries = self.orchestrator.db_manager.get_document_log(
            self.orchestrator.project_id, self.current_selected_doc_path
        )

        if not log_entries:
            self.ui.reviewLogBrowser.setText("No review log entries found for this document.")
            return

        html_output = ""
        for entry in log_entries:
            timestamp = format_timestamp_for_display(entry['timestamp'])
            author = entry['author']
            log_text = html.escape(entry['log_text']).replace('\n', '<br>')
            status = entry['status']

            header_color = "#A9B7C6" # Default (Developer)
            if author == 'CLIENT':
                header_color = "#FFC66D" # Amber
            elif author == 'SYSTEM':
                header_color = "#007ACC" # Blue

            status_badge = ""
            if status == "APPROVED":
                status_badge = "<b style='color:#6A8759;'> [APPROVED]</b>"
            elif status == "VERSION_UPDATE":
                status_badge = "<b style='color:#007ACC;'> [VERSION UPDATE]</b>"

            html_output += f"<p><b style='color:{header_color};'>{timestamp} | {author}</b>{status_badge}<br>{log_text}</p><hr style='border: 1px solid #3C3F41;'>"

        self.ui.reviewLogBrowser.setHtml(html_output)

    def _on_add_other_document(self):
        """Opens a file dialog to add a new generic document."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Document to Add", "", "All Files (*)")
        if not file_path:
            return

        # Run this in a worker to avoid blocking the UI
        self.setCursor(Qt.WaitCursor)
        self._set_ui_busy(True, "Adding document...")
        worker = Worker(self.orchestrator.add_other_document, Path(file_path))
        worker.signals.result.connect(self._handle_add_document_result)
        worker.signals.error.connect(self._on_task_error)
        worker.signals.finished.connect(lambda: self._set_ui_busy(False))
        worker.signals.finished.connect(lambda: self.setCursor(Qt.ArrowCursor))
        self.threadpool.start(worker)

    def _handle_add_document_result(self, destination_path: Path):
        self._set_ui_busy(False)
        if destination_path:
            QMessageBox.information(self, "Success", f"Document '{destination_path.name}' added successfully.")
            self.refresh_document_lists()
            # Find and select the new item
            self._find_and_select_item(str(destination_path).replace('\\', '/'))
        else:
            QMessageBox.critical(self, "Error", "Failed to add the document.")

    def _on_upload_new_version(self):
        """Opens a file dialog to upload a new version of the selected document."""
        if not self.current_selected_doc_path:
            return

        file_path, _ = QFileDialog.getOpenFileName(self, f"Select New Version of {self.current_selected_doc_path}", "", "All Files (*)")
        if not file_path:
            return

        # Run this in a worker
        self.setCursor(Qt.WaitCursor)
        self._set_ui_busy(True, "Uploading new version...")
        worker = Worker(self.orchestrator.upload_new_document_version, Path(file_path), self.current_selected_doc_path)
        worker.signals.result.connect(self._handle_upload_version_result)
        worker.signals.error.connect(self._on_task_error)
        worker.signals.finished.connect(lambda: self._set_ui_busy(False))
        worker.signals.finished.connect(lambda: self.setCursor(Qt.ArrowCursor))
        self.threadpool.start(worker)

    def _handle_upload_version_result(self, new_doc_path: Path):
        self._set_ui_busy(False)
        if new_doc_path:
            QMessageBox.warning(
                self,
                "Document Updated - Manual Action Required",
                f"Version '{new_doc_path.name}' has been saved.\n\n"
                "IMPORTANT: Changes in this document are NOT automatically implemented. "
                "You must review the changes and manually create new Change Requests in the project backlog to action them."
            )
            self.refresh_document_lists()
            # Auto-select the new version
            self._find_and_select_item(str(new_doc_path).replace('\\', '/'))
        else:
            QMessageBox.critical(self, "Error", "Failed to upload the new version.")

    def _find_and_select_item(self, relative_path: str):
        """Finds and selects an item in either list view by its relative path."""
        for i in range(self.ui.specDocumentsListWidget.count()):
            item = self.ui.specDocumentsListWidget.item(i)
            if item.data(Qt.UserRole) == relative_path:
                item.setSelected(True)
                self.ui.specDocumentsListWidget.scrollToItem(item)
                self._set_active_document(relative_path)
                return

        for i in range(self.ui.otherDocumentsListWidget.count()):
            item = self.ui.otherDocumentsListWidget.item(i)
            if item.data(Qt.UserRole) == relative_path:
                item.setSelected(True)
                self.ui.otherDocumentsListWidget.scrollToItem(item)
                self._set_active_document(relative_path)
                return

    def _on_save_feedback(self):
        """Saves the content of the text box as a new log entry."""
        if not self.current_selected_doc_path or not self.orchestrator.project_id:
            return

        log_text = self.ui.logTextEdit.toPlainText().strip()
        if not log_text:
            QMessageBox.warning(self, "Input Required", "Feedback text cannot be empty.")
            return

        author = self.ui.authorComboBox.currentText()
        try:
            self.orchestrator.db_manager.add_document_log_entry(
                project_id=self.orchestrator.project_id,
                document_path=self.current_selected_doc_path,
                author=author,
                log_text=log_text
            )
            self.ui.logTextEdit.clear()
            self._load_review_log()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save log entry: {e}")

    def _on_mark_approved(self):
        """Adds a special 'APPROVED' status entry to the log."""
        if not self.current_selected_doc_path or not self.orchestrator.project_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Approval",
            f"Are you sure you want to mark '{Path(self.current_selected_doc_path).name}' as APPROVED?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            author = self.ui.authorComboBox.currentText()
            try:
                self.orchestrator.db_manager.add_document_log_entry(
                    project_id=self.orchestrator.project_id,
                    document_path=self.current_selected_doc_path,
                    author=author,
                    log_text="Document has been marked as approved.",
                    status="APPROVED"
                )
                self._load_review_log()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save approval: {e}")

    def _set_ui_busy(self, is_busy: bool, message: str = "Processing..."):
        """Disables/enables the UI and shows a status message."""
        main_window = self.window()
        if main_window:
            # We don't disable the main window anymore, just the page
            # main_window.setEnabled(not is_busy)
            if hasattr(main_window, 'statusBar'):
                if is_busy:
                    main_window.statusBar().showMessage(message)
                else:
                    main_window.statusBar().clearMessage()

        self.setEnabled(not is_busy) # Disable this page only

    def _on_task_error(self, error_tuple):
        """Handles a generic error from a worker thread."""
        self._set_ui_busy(False) # Ensure UI is re-enabled on error
        self.setCursor(Qt.ArrowCursor) # Ensure cursor is reset
        logging.error(f"Error in DocumentsPage worker: {error_tuple[1]}. Traceback: {error_tuple[2]}")
        QMessageBox.critical(self, "Task Error", f"An error occurred: {error_tuple[1]}")

    # Add new handlers for viewing document content

    def _on_document_double_clicked(self, item: QListWidgetItem):
        """Handles double-click on any document to view it."""
        doc_path = item.data(Qt.UserRole)
        if not doc_path:
            return

        self.setCursor(Qt.WaitCursor)
        self._set_ui_busy(True, f"Loading {doc_path}...")
        worker = Worker(self.orchestrator.get_document_content, doc_path)
        worker.signals.result.connect(self._show_document_viewer)
        worker.signals.error.connect(self._on_doc_load_error)
        # We don't connect finished signals here, as they are handled
        # in the result/error slots specifically for this flow.
        self.threadpool.start(worker)

    def _show_document_viewer(self, result_tuple):
        """Shows the document viewer dialog with the loaded content."""
        self.setCursor(Qt.ArrowCursor)
        self._set_ui_busy(False)
        title, content = result_tuple
        dialog = DocumentViewerDialog(title, content, self)
        dialog.exec()

    def _on_doc_load_error(self, error_tuple):
        """Handles failure to load a document for viewing."""
        self.setCursor(Qt.ArrowCursor)
        self._set_ui_busy(False)
        logging.error(f"Failed to load document content: {error_tuple[1]}. Traceback: {error_tuple[2]}")
        QMessageBox.critical(self, "Error", f"Could not load document: {error_tuple[1]}")
