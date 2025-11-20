# gui/reports_page.py
import logging
from io import BytesIO
from PySide6.QtWidgets import QWidget, QMessageBox, QAbstractItemView
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from gui.ui_reports_page import Ui_ReportsPage
from master_orchestrator import MasterOrchestrator
from gui.worker import Worker
from gui.utils import show_status_message
from gui.utils import format_timestamp_for_display
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
        self.worker_thread_pool = self.window().threadpool # Get threadpool from main window
        self.report_metadata = {} # To store info about each report

        # --- New TreeView Setup ---
        self.tree_model = QStandardItemModel(self)
        self.ui.reportTreeView.setModel(self.tree_model)
        self.ui.reportTreeView.setHeaderHidden(True) # Hide the default header
        self.ui.reportTreeView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # --- Initial Details Panel State ---
        self.ui.filterGroupBox.setVisible(False)
        self.ui.statusFilterComboBox.setVisible(False)
        self.ui.statusFilterLabel.setVisible(False)
        self.ui.typeFilterComboBox.setVisible(False)
        self.ui.typeFilterLabel.setVisible(False)
        self.ui.sprintFilterComboBox.setVisible(False)
        self.ui.sprintFilterLabel.setVisible(False)
        self.ui.generateReportButton.setEnabled(False)
        self.ui.lastGeneratedLabel.setVisible(False) # Optional feature

        self.connect_signals()

    def connect_signals(self):
        """Connects all UI signals to their slots."""
        self.ui.backButton.clicked.connect(self.back_to_workflow.emit)
        # Connect the tree view selection change to the details panel update
        self.ui.reportTreeView.selectionModel().currentChanged.connect(self._on_report_selection_changed)
        # The generate button's connection will be handled dynamically

    def prepare_for_display(self):
        """Called when the page is shown, populates the report tree."""
        logging.debug("Reports Hub prepared for display. Populating tree...")
        self.tree_model.clear() # Clear previous items
        self.ui.reportTreeView.setHeaderHidden(True) # Ensure header is hidden

        # Define report structure with metadata, including the new "enabled" key
        self.report_metadata = {
            "Project Pulse": {
                "category": "Project Overview",
                "description": "A one-page visual summary of backlog completion and code quality. Ideal for stakeholder updates.",
                "file_type": ".docx",
                "generation_function": self.orchestrator.generate_health_snapshot_report,
                "filters": [],
                "enabled": True
            },
            "AI Assistance Rate": {
                "category": "Project Overview",
                "description": "Tracks the frequency of required PM intervention (Debug Escalations), indicating AI reliability. (Not implemented in this version)",
                "file_type": ".docx",
                "generation_function": self.orchestrator.generate_ai_assistance_rate_data,
                "filters": [],
                "enabled": False # <-- SET TO FALSE
            },
            "Backlog Views": {
                "category": "Backlog & Scope",
                "description": "Export the hierarchical project backlog to Excel, with optional filtering by item status and type.",
                "file_type": ".xlsx",
                "generation_function": self.orchestrator.generate_filtered_backlog_report,
                "filters": ["status", "type"],
                "enabled": True
            },
            "Workflow Efficiency": {
                "category": "Backlog & Scope",
                "description": "Visualizes the flow of backlog items through different statuses over time (Cumulative Flow Diagram) to identify bottlenecks. (Not implemented in this version)",
                "file_type": ".docx",
                "generation_function": self.orchestrator.generate_workflow_efficiency_data,
                "filters": [],
                "enabled": False # <-- SET TO FALSE
            },
            "Backlog Traceability Matrix": {
                "category": "Backlog & Scope",
                "description": "An end-to-end report mapping backlog items (using hierarchical IDs) to their implemented code artifacts.",
                "file_type": ".xlsx",
                "generation_function": self.orchestrator.generate_traceability_matrix_report,
                "filters": [],
                "enabled": True
            },
            "Complexity Point Burndown Chart": {
                "category": "Sprint Performance",
                "description": "Shows the remaining estimated complexity points versus completed tasks for a selected sprint. (Not implemented in this version)",
                "file_type": ".docx",
                "generation_function": self.orchestrator.generate_burndown_chart_data,
                "filters": ["sprint"],
                "enabled": False # <-- SET TO FALSE
            },
            "Sprint Deliverables List": {
                "category": "Sprint Performance",
                "description": "Lists the specific backlog items and the code artifacts delivered in a selected sprint.",
                "file_type": ".xlsx",
                "generation_function": self.orchestrator.generate_sprint_deliverables_report,
                "filters": ["sprint"],
                "enabled": True
            },
            "Code Quality Trend": {
                "category": "Code Quality",
                "description": "Tracks the status of component unit tests over time or across sprints. (Not implemented in this version)",
                "file_type": ".docx",
                "generation_function": self.orchestrator.generate_code_quality_trend_data,
                "filters": [],
                "enabled": False # <-- SET TO FALSE
            }
        }

        # --- New population logic to handle disabling categories ---
        root_item = self.tree_model.invisibleRootItem()
        category_order = ["Project Overview", "Backlog & Scope", "Sprint Performance", "Code Quality"]

        for category_name in category_order:
            # Find all reports for this category
            reports_in_category = []
            for report_name, meta in self.report_metadata.items():
                if meta["category"] == category_name:
                    reports_in_category.append((report_name, meta))

            if not reports_in_category:
                continue # Skip category if no reports are defined for it

            # Create the category item
            category_item = QStandardItem(category_name)
            category_item.setEditable(False)
            font = category_item.font()
            font.setBold(True)
            category_item.setFont(font)
            root_item.appendRow(category_item)

            all_children_disabled = True
            for report_name, meta in reports_in_category:
                report_item = QStandardItem(report_name)
                report_item.setEditable(False)
                report_item.setData(report_name, Qt.UserRole)

                is_enabled = meta.get("enabled", False) # Default to False if key is missing
                report_item.setEnabled(is_enabled)

                if is_enabled:
                    all_children_disabled = False # Found at least one enabled report

                category_item.appendRow(report_item)

            # Disable the category *itself* if all its children are disabled
            if all_children_disabled:
                category_item.setEnabled(False)
        # --- End of new logic ---

        self.ui.reportTreeView.expandAll()
        # Reset details panel to default state
        self._reset_details_panel()
        # Populate sprint dropdown if needed by any report
        if any("sprint" in meta["filters"] for meta in self.report_metadata.values()):
            self._populate_sprint_dropdown()

    def _reset_details_panel(self):
        """Resets the details panel to its default state."""
        self.ui.reportTitleLabel.setText("Select a Report")
        self.ui.reportDescriptionLabel.setText("Select a report from the list on the left to view its description and generate it.")
        self.ui.filterGroupBox.setVisible(False)
        self.ui.statusFilterComboBox.setVisible(False)
        self.ui.statusFilterLabel.setVisible(False)
        self.ui.typeFilterComboBox.setVisible(False)
        self.ui.typeFilterLabel.setVisible(False)
        self.ui.sprintFilterComboBox.setVisible(False)
        self.ui.sprintFilterLabel.setVisible(False)
        self.ui.generateReportButton.setEnabled(False)
        self.ui.generateReportButton.setText("Generate Report")
        # self.ui.lastGeneratedLabel.setVisible(False)
        # Disconnect any previous dynamic connection
        try:
            self.ui.generateReportButton.clicked.disconnect()
        except (TypeError, RuntimeError): # Catch if no connection exists
            pass

    def _on_report_selection_changed(self, current, previous):
        """Updates the details panel when a report is selected in the tree."""
        if not current.isValid():
            self._reset_details_panel()
            return

        item = self.tree_model.itemFromIndex(current)
        if not item or not item.parent(): # Ensure it's a report item, not a category
            self._reset_details_panel()
            return

        report_name = item.data(Qt.UserRole)
        meta = self.report_metadata.get(report_name)

        if not meta:
            self._reset_details_panel()
            logging.warning(f"No metadata found for selected report: {report_name}")
            return

        # Update Title and Description
        self.ui.reportTitleLabel.setText(report_name)
        # Use objectName for QSS styling if needed: self.ui.reportTitleLabel.setObjectName("reportTitleLabel")
        self.ui.reportDescriptionLabel.setText(meta["description"])

        # Configure Filters
        required_filters = meta["filters"]
        show_groupbox = bool(required_filters)
        self.ui.filterGroupBox.setVisible(show_groupbox)

        # Status Filter (for Backlog Views)
        show_status = "status" in required_filters
        self.ui.statusFilterLabel.setVisible(show_status)
        self.ui.statusFilterComboBox.setVisible(show_status)
        if show_status:
            # Populate if first time or if content might change
            if self.ui.statusFilterComboBox.count() == 0:
                self.ui.statusFilterComboBox.addItems(["All", "TO_DO", "IMPACT_ANALYZED", "TECHNICAL_PREVIEW_COMPLETE", "IMPLEMENTATION_IN_PROGRESS", "BLOCKED", "COMPLETED", "CANCELLED", "EXISTING", "BUG_RAISED"]) # Add all relevant statuses

        # Type Filter (for Backlog Views)
        show_type = "type" in required_filters
        self.ui.typeFilterLabel.setVisible(show_type)
        self.ui.typeFilterComboBox.setVisible(show_type)
        if show_type:
            if self.ui.typeFilterComboBox.count() == 0:
                self.ui.typeFilterComboBox.addItems(["All", "EPIC", "FEATURE", "BACKLOG_ITEM", "BUG_REPORT"])

        # Sprint Filter (for Sprint Deliverables, Burndown)
        show_sprint = "sprint" in required_filters
        self.ui.sprintFilterLabel.setVisible(show_sprint)
        self.ui.sprintFilterComboBox.setVisible(show_sprint)
        # Sprint dropdown population happens in prepare_for_display

        # Configure Generate Button
        self.ui.generateReportButton.setEnabled(True)
        self.ui.generateReportButton.setText(f"Generate {meta['file_type']}")
        # Disconnect previous slot before connecting new one
        try:
            self.ui.generateReportButton.clicked.disconnect()
        except Exception:
            pass
        # Dynamically connect the button to the correct handler based on report name
        # We use a lambda to pass the report name or necessary context if needed
        handler_method = self._request_report_generation # Use a single generic handler
        self.ui.generateReportButton.clicked.connect(lambda checked=False, rn=report_name: handler_method(rn))

        self.ui.lastGeneratedLabel.setVisible(False) # Reset last generated label

    def _populate_sprint_dropdown(self):
        """
        Fetches the list of relevant sprints from the orchestrator
        and populates the sprint filter dropdown.
        """
        logging.debug("Populating sprint dropdown...")
        self.ui.sprintFilterComboBox.clear()
        try:
            sprint_list = self.orchestrator.get_sprint_list_for_report()
            if not sprint_list:
                self.ui.sprintFilterComboBox.addItem("No completed or active sprints found", None)
                self.ui.sprintFilterComboBox.setEnabled(False)
                return

            self.ui.sprintFilterComboBox.setEnabled(True)
            self.ui.sprintFilterComboBox.addItem("Select a sprint...", None)
            for display_text, sprint_id in sprint_list:
                self.ui.sprintFilterComboBox.addItem(display_text, sprint_id)

        except Exception as e:
            logging.error(f"Failed to populate sprint dropdown: {e}", exc_info=True)
            self.ui.sprintFilterComboBox.addItem("Error loading sprints", None)
            self.ui.sprintFilterComboBox.setEnabled(False)


    def _request_report_generation(self, report_name: str):
        """
        Generic handler to request a report. It gathers filter data
        and starts the corresponding worker thread.
        """
        meta = self.report_metadata.get(report_name)
        if not meta:
            show_status_message(self.window(), "Error: Report metadata not found.", "error")
            return

        # Disable button to prevent double-clicks
        self.ui.generateReportButton.setEnabled(False)
        self.ui.generateReportButton.setText("Generating...")
        show_status_message(self.window(), f"Generating '{report_name}'... This may take a moment.", "info", duration=5000)

        # Collect filter arguments
        kwargs = {}
        if "status" in meta["filters"]:
            status_text = self.ui.statusFilterComboBox.currentText()
            if status_text != "All":
                kwargs['statuses'] = [status_text]
        if "type" in meta["filters"]:
            type_text = self.ui.typeFilterComboBox.currentText()
            if type_text != "All":
                kwargs['types'] = [type_text]
        if "sprint" in meta["filters"]:
            sprint_id = self.ui.sprintFilterComboBox.currentData()
            if not sprint_id:
                show_status_message(self.window(), "Error: Please select a sprint.", "error")
                self.ui.generateReportButton.setEnabled(True)
                self.ui.generateReportButton.setText(f"Generate {meta['file_type']}")
                return
            kwargs['sprint_id'] = sprint_id

        # Get the generation function from metadata
        generation_func = meta["generation_function"]

        # Pass the report name and file type to the success handler
        worker = Worker(generation_func, **kwargs)
        worker.signals.result.connect(lambda result, rn=report_name, ft=meta['file_type']: self._on_report_success(result, rn, ft))
        worker.signals.error.connect(self._on_report_failure)
        self.worker_thread_pool.start(worker)


    def _on_report_success(self, result: str | BytesIO, report_name: str, file_type: str):
        """
        Handles the successful generation of a report from the worker.
        Saves the file and shows a success message.
        """
        self.ui.generateReportButton.setEnabled(True)
        self.ui.generateReportButton.setText(f"Generate {file_type}")

        if isinstance(result, str) and result.startswith(("Error:", "Info:")):
            # Handle controlled errors or info messages from orchestrator
            log_level = "warning" if result.startswith("Info:") else "error"
            logging.warning(f"Report generation for '{report_name}' returned a message: {result}")
            show_status_message(self.window(), result, log_level)
            return

        if not isinstance(result, BytesIO):
            logging.error(f"Report generation for '{report_name}' returned unexpected type: {type(result)}")
            show_status_message(self.window(), f"Error generating '{report_name}': Invalid data returned.", "error")
            return

        try:
            # Save the file
            save_path = self.orchestrator.save_report_file(result, report_name, file_type)
            if not save_path:
                raise Exception("Orchestrator failed to save file.")

            logging.info(f"Successfully generated and saved report: {save_path}")
            show_status_message(self.window(), f"Success: Report '{report_name}' saved.", "success", duration=7000)
            # self.ui.lastGeneratedLabel.setText(f"Last generated: {save_path}")
            # self.ui.lastGeneratedLabel.setVisible(True)

        except Exception as e:
            logging.error(f"Failed to save report '{report_name}': {e}", exc_info=True)
            show_status_message(self.window(), f"Error saving report: {e}", "error")


    def _on_report_failure(self, error_info):
        """Handles a fatal error from the worker thread."""
        exctype, value, tb = error_info
        logging.error(f"Report generation worker failed: {value}\n{tb}")
        show_status_message(self.window(), f"Error generating report: {value}", "error", duration=10000)
        self.ui.lastGeneratedLabel.setVisible(False)

        # Re-enable the button, but we don't know which one was clicked
        # We need to re-fetch the current selection to get the file type
        current_index = self.ui.reportTreeView.currentIndex()
        if current_index.isValid():
            item = self.tree_model.itemFromIndex(current_index)
            if item and item.parent():
                report_name = item.data(Qt.UserRole)
                meta = self.report_metadata.get(report_name)
                if meta:
                    self.ui.generateReportButton.setText(f"Generate {meta['file_type']}")
                    self.ui.generateReportButton.setEnabled(True)
                    return

        # Fallback if no selection
        self.ui.generateReportButton.setText("Generate Report")
        self.ui.generateReportButton.setEnabled(True)