# main_window.py

import logging
from pathlib import Path
from datetime import datetime
import os
import subprocess
import sys

from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QStackedWidget,
                               QInputDialog, QMessageBox, QFileSystemModel, QMenu, QVBoxLayout, QHeaderView, QAbstractItemView)
from PySide6.QtGui import QAction, QStandardItemModel, QStandardItem
from PySide6.QtCore import QFile, Signal, Qt, QDir
from PySide6.QtCore import QThreadPool

from gui.ui_main_window import Ui_MainWindow
from master_orchestrator import MasterOrchestrator, FactoryPhase
from gui.settings_dialog import SettingsDialog
from gui.env_setup_page import EnvSetupPage
from gui.spec_elaboration_page import SpecElaborationPage
from gui.tech_spec_page import TechSpecPage
from gui.build_script_page import BuildScriptPage
from gui.test_env_page import TestEnvPage
from gui.coding_standard_page import CodingStandardPage
from gui.planning_page import PlanningPage
from gui.genesis_page import GenesisPage
from gui.load_project_page import LoadProjectPage
from gui.preflight_check_page import PreflightCheckPage
from gui.decision_page import DecisionPage
from gui.raise_request_dialog import RaiseRequestDialog
from gui.cr_details_dialog import CRDetailsDialog
from gui.documents_page import DocumentsPage
from gui.reports_page import ReportsPage
from gui.manual_ui_testing_page import ManualUITestingPage
from gui.project_complete_page import ProjectCompletePage
from gui.cr_management_page import CRManagementPage
from gui.worker import Worker

class ASDFMainWindow(QMainWindow):
    """
    The main window for the ASDF desktop application.
    This is the complete, architecturally corrected version.
    """
    def __init__(self, orchestrator: MasterOrchestrator):
        super().__init__()
        self.threadpool = QThreadPool()
        self.orchestrator = orchestrator
        self.last_known_phase = None
        self.previous_phase = FactoryPhase.IDLE

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._create_pages()
        self._setup_file_tree()
        self._setup_cr_register_view()
        self._create_menus_and_toolbar()
        self._connect_signals()

        self.update_ui_after_state_change()

    def _create_pages(self):
        """Creates and adds all page widgets to the stacked widget."""
        self.env_setup_page = EnvSetupPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.env_setup_page)
        self.spec_elaboration_page = SpecElaborationPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.spec_elaboration_page)
        self.tech_spec_page = TechSpecPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.tech_spec_page)
        self.build_script_page = BuildScriptPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.build_script_page)
        self.test_env_page = TestEnvPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.test_env_page)
        self.coding_standard_page = CodingStandardPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.coding_standard_page)
        self.planning_page = PlanningPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.planning_page)
        self.genesis_page = GenesisPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.genesis_page)
        self.load_project_page = LoadProjectPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.load_project_page)
        self.preflight_check_page = PreflightCheckPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.preflight_check_page)
        self.decision_page = DecisionPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.decision_page)
        self.documents_page = DocumentsPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.documents_page)
        self.reports_page = ReportsPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.reports_page)
        self.manual_ui_testing_page = ManualUITestingPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.manual_ui_testing_page)
        self.project_complete_page = ProjectCompletePage(self)
        self.ui.mainContentArea.addWidget(self.project_complete_page)
        self.cr_management_page = CRManagementPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.cr_management_page)

    def _setup_file_tree(self):
        """Initializes the file system model and view."""
        self.treeViewInfoLabel = QLabel("No active project.")
        self.treeViewInfoLabel.setAlignment(Qt.AlignCenter)
        self.treeViewInfoLabel.setWordWrap(True)

        existing_layout = self.ui.filesTab.layout()
        existing_layout.insertWidget(0, self.treeViewInfoLabel)

        self.file_system_model = QFileSystemModel()
        # This more explicit filter should hide the specified files/folders
        self.file_system_model.setNameFilters([".git", ".gitignore", "__pycache__", "*.pyc"])
        self.file_system_model.setNameFilterDisables(True) # This hides the matching names
        self.ui.projectFilesTreeView.setModel(self.file_system_model)

        # Configure the view's appearance
        self.ui.projectFilesTreeView.hideColumn(1) # Size
        self.ui.projectFilesTreeView.hideColumn(2) # Type
        self.ui.projectFilesTreeView.hideColumn(3) # Date Modified
        self.ui.projectFilesTreeView.setHeaderHidden(True)
        self.ui.projectFilesTreeView.setContextMenuPolicy(Qt.CustomContextMenu)

    def _setup_cr_register_view(self):
        """Initializes the model and view for the 'Changes' tab table."""
        self.cr_model = QStandardItemModel(self)
        self.ui.crTableView.setModel(self.cr_model)
        # Configure static properties of the view
        self.ui.crTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.crTableView.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def _create_menus_and_toolbar(self):
        """Programmatically creates dynamic menus and toolbar actions."""
        self.actionManage_CRs_Bugs = QAction("Manage CRs / Bugs", self)
        self.actionManage_CRs_Bugs.setToolTip("View and manage the CR/Bug register")
        self.ui.toolBar.addAction(self.actionManage_CRs_Bugs)

        for phase in FactoryPhase:
            if phase.name == "IDLE": continue
            action = QAction(phase.name.replace("_", " ").title(), self)
            action.triggered.connect(lambda checked=False, p=phase.name: self.on_debug_jump_to_phase(p))
            self.ui.menuDebug.addAction(action)

        self.status_project_label = QLabel("Project: N/A")
        self.status_phase_label = QLabel("Phase: Idle")
        self.status_git_label = QLabel("Branch: N/A")
        self.ui.statusbar.addPermanentWidget(self.status_project_label)
        self.ui.statusbar.addPermanentWidget(self.status_phase_label)
        self.ui.statusbar.addPermanentWidget(self.status_git_label)

    def _connect_signals(self):
        """Connects all UI signals to their corresponding slots."""
        self.ui.actionNew_Project.triggered.connect(self.on_new_project)
        self.ui.actionLoad_Archived_Project.triggered.connect(self.on_load_project)
        self.ui.actionClose_Project.triggered.connect(self.on_close_project)
        self.ui.actionStop_Export_Project.triggered.connect(self.on_stop_export_project)
        self.ui.actionSettings.triggered.connect(self.show_settings_dialog)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionAbout_ASDF.triggered.connect(self.on_about)
        self.ui.actionRaise_CR.triggered.connect(self.on_raise_cr)
        self.ui.actionView_Documents.triggered.connect(self.on_view_documents)
        self.ui.actionView_Reports.triggered.connect(self.on_view_reports)

        # Connect signals that trigger a FULL UI refresh and page transition
        for page in [self.env_setup_page, self.spec_elaboration_page, self.tech_spec_page, self.build_script_page, self.test_env_page, self.coding_standard_page, self.planning_page, self.genesis_page, self.load_project_page, self.preflight_check_page]:
            if hasattr(page, 'setup_complete'): page.setup_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'spec_elaboration_complete'): page.spec_elaboration_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'tech_spec_complete'): page.tech_spec_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'build_script_setup_complete'): page.build_script_setup_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'test_env_setup_complete'): page.test_env_setup_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'coding_standard_complete'): page.coding_standard_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'planning_complete'): page.planning_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'genesis_complete'): page.genesis_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'project_loaded'): page.project_loaded.connect(self.update_ui_after_state_change)
            if hasattr(page, 'project_load_finalized'): page.project_load_finalized.connect(self.update_ui_after_state_change)

        # Connect signals that trigger a PARTIAL UI refresh (no page transition)
        for page in [self.spec_elaboration_page, self.tech_spec_page, self.build_script_page, self.test_env_page, self.coding_standard_page, self.planning_page, self.genesis_page]:
            if hasattr(page, 'state_changed'): page.state_changed.connect(self.update_static_ui_elements)

        self.load_project_page.back_to_main.connect(self.on_back_from_load_project)
        self.preflight_check_page.project_load_failed.connect(self.reset_to_idle)
        self.decision_page.option1_selected.connect(self.on_decision_option1)
        self.decision_page.option2_selected.connect(self.on_decision_option2)
        self.decision_page.option3_selected.connect(self.on_decision_option3)
        self.ui.projectFilesTreeView.customContextMenuRequested.connect(self.on_file_tree_context_menu)
        self.ui.crTableView.doubleClicked.connect(self.on_cr_double_clicked)
        self.documents_page.back_to_workflow.connect(self.on_back_to_workflow)
        self.reports_page.back_to_workflow.connect(self.on_back_to_workflow)
        self.manual_ui_testing_page.go_to_documents.connect(self.on_view_documents)
        self.manual_ui_testing_page.testing_complete.connect(self.update_ui_after_state_change)
        self.project_complete_page.back_to_main.connect(self.on_close_project)
        self.project_complete_page.export_project.connect(self.on_stop_export_project)
        self.cr_management_page.back_to_workflow.connect(self.on_back_to_workflow)
        self.cr_management_page.edit_cr.connect(self.on_cr_edit_action)
        self.cr_management_page.delete_cr.connect(self.on_cr_delete_action)
        self.cr_management_page.analyze_cr.connect(self.on_cr_analyze_action)
        self.cr_management_page.implement_cr.connect(self.on_cr_implement_action)
        self.actionManage_CRs_Bugs.triggered.connect(self.on_manage_crs)

    def update_static_ui_elements(self):
        """
        Updates only the static parts of the UI like the status bar and file tree.
        """
        is_project_active = self.orchestrator.project_id is not None
        is_project_dirty = self.orchestrator.is_project_dirty
        project_name = self.orchestrator.project_name or "N/A"
        current_phase_enum = self.orchestrator.current_phase
        display_phase_name = self.orchestrator.PHASE_DISPLAY_NAMES.get(current_phase_enum, current_phase_enum.name)
        git_branch = self.orchestrator.get_current_git_branch()
        self.status_project_label.setText(f"Project: {project_name}")
        self.status_phase_label.setText(f"Phase: {display_phase_name}")
        self.status_git_label.setText(f"Branch: {git_branch}")
        self.ui.actionClose_Project.setEnabled(is_project_active and not is_project_dirty)
        self.ui.actionStop_Export_Project.setEnabled(is_project_active)
        genesis_complete = self.orchestrator.is_genesis_complete
        self.ui.actionManage_CRs_Bugs.setEnabled(is_project_active and genesis_complete)
        self.ui.actionManage_CRs_Bugs.setToolTip("Enabled after initial development is complete.")

        project_root = ""
        if is_project_active:
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = project_details['project_root_folder']

        if project_root and Path(project_root).exists():
            root_path_obj = Path(project_root)
            # This is the fix: Reset the model to ensure a clean refresh
            self.file_system_model.setRootPath("") # Clear the old root
            self.file_system_model.setRootPath(str(root_path_obj.parent))
            self.ui.projectFilesTreeView.setRootIndex(self.file_system_model.index(project_root))

            self.ui.projectFilesTreeView.setVisible(True)
            self.treeViewInfoLabel.setVisible(False)
        else:
            self.ui.projectFilesTreeView.setVisible(False)
            self.treeViewInfoLabel.setVisible(True)
            default_path = self.orchestrator.db_manager.get_config_value("DEFAULT_PROJECT_PATH")
            if default_path:
                self.treeViewInfoLabel.setText("No active project.\n\nPlease create a new project or load an archive.")
            else:
                self.treeViewInfoLabel.setText("No active project.\n\nPlease go to Files -> Settings to set a default project path.")

    def update_cr_register_view(self):
        """
        Fetches CRs/Bugs for the active project and populates the 'Changes' table.
        """
        self.cr_model.clear()
        self.cr_model.setHorizontalHeaderLabels(['ID', 'Type', 'Status', 'Description'])

        # Set column resizing rules
        header = self.ui.crTableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Description

        if not self.orchestrator.project_id:
            return # No project active, leave the table empty

        try:
            change_requests = self.orchestrator.get_all_change_requests()
            for cr in change_requests:
                type_display = cr['request_type'].replace('_', ' ').title()
                if type_display == "Change Request":
                    type_display = "CR"
                elif type_display == "Bug Report":
                    type_display = "Bug"

                id_item = QStandardItem(str(cr['cr_id']))
                type_item = QStandardItem(type_display)
                status_item = QStandardItem(cr['status'])
                desc_item = QStandardItem(cr['description'])
                self.cr_model.appendRow([id_item, type_item, status_item, desc_item])

        except Exception as e:
            logging.error(f"Failed to update CR register view: {e}")

    def on_cr_double_clicked(self, index):
        """
        Handles the event when a user double-clicks an item in the CR table.
        """
        if not index.isValid():
            return

        selected_row = index.row()
        cr_id_item = self.cr_model.item(selected_row, 0)
        if not cr_id_item:
            return

        try:
            cr_id = int(cr_id_item.text())
            cr_details = self.orchestrator.get_cr_details_by_id(cr_id)
            if cr_details:
                # Create and show our new, custom dialog
                dialog = CRDetailsDialog(cr_details, self)
                dialog.exec()
        except (ValueError, TypeError) as e:
            logging.error(f"Could not process CR selection: {e}")

    def on_cr_edit_action(self, cr_id: int):
        """Handles the signal to edit a CR."""
        QMessageBox.information(self, "Action Triggered", f"Received signal to EDIT Change Request: {cr_id}")
        # In the future, this will call: self.orchestrator.handle_edit_cr_action(cr_id)

    def on_cr_delete_action(self, cr_id: int):
        """Handles the signal to delete a CR."""
        QMessageBox.information(self, "Action Triggered", f"Received signal to DELETE Change Request: {cr_id}")
        # In the future, this will call: self.orchestrator.handle_delete_cr_action(cr_id)

    def on_cr_analyze_action(self, cr_id: int):
        """Handles the signal to run impact analysis on a CR in a background thread."""
        self.setEnabled(False) # Disable the main window to prevent user interaction
        self.statusBar().showMessage(f"Running impact analysis for CR-{cr_id}...")

        # Create and start the worker thread
        worker = Worker(self.orchestrator.handle_run_impact_analysis_action, cr_id)
        worker.signals.result.connect(lambda: self._handle_analysis_result(cr_id, True))
        worker.signals.error.connect(lambda err: self._handle_analysis_result(cr_id, False, err))
        self.threadpool.start(worker) # Assuming self.threadpool exists from another page

    def _handle_analysis_result(self, cr_id: int, success: bool, error=None):
        """Handles the result of the background analysis task."""
        self.setEnabled(True) # Re-enable the main window
        self.statusBar().clearMessage()

        if success:
            QMessageBox.information(self, "Success", f"Impact analysis for CR-{cr_id} completed successfully.")
        else:
            error_msg = str(error[1]) if error else "An unknown error occurred."
            QMessageBox.critical(self, "Analysis Failed", f"Failed to run impact analysis for CR-{cr_id}:\n{error_msg}")

        # Refresh the CR table to show the updated status and summary
        if self.ui.mainContentArea.currentWidget() == self.cr_management_page:
            self.cr_management_page.update_cr_table()
        self.update_cr_register_view() # Also update the side panel view

    def on_cr_implement_action(self, cr_id: int):
        """Handles the signal to implement a CR in a background thread."""
        self.setEnabled(False)
        self.statusBar().showMessage(f"Generating implementation plan for CR-{cr_id}...")

        worker = Worker(self.orchestrator.handle_implement_cr_action, cr_id)
        worker.signals.result.connect(lambda: self._handle_implementation_result(cr_id, True))
        worker.signals.error.connect(lambda err: self._handle_implementation_result(cr_id, False, err))
        self.threadpool.start(worker)

    def _handle_implementation_result(self, cr_id: int, success: bool, error=None):
        """Handles the result of the background implementation planning task."""
        self.setEnabled(True)
        self.statusBar().clearMessage()

        if success:
            QMessageBox.information(self, "Success", f"Implementation plan for CR-{cr_id} created. Transitioning to development phase.")
            # The orchestrator has changed the phase to GENESIS, so a full UI update is needed
            self.update_ui_after_state_change()
        else:
            error_msg = str(error[1]) if error else "An unknown error occurred."
            QMessageBox.critical(self, "Implementation Failed", f"Failed to create an implementation plan for CR-{cr_id}:\n{error_msg}")

    def update_ui_after_state_change(self):
        """
        Performs a full UI refresh. This is called only after a phase transition.
        """
        self.update_cr_register_view()
        self.update_static_ui_elements()

        current_phase = self.orchestrator.current_phase
        current_phase_name = current_phase.name
        is_project_active = self.orchestrator.project_id is not None

        page_display_map = {
            "ENV_SETUP_TARGET_APP": self.env_setup_page,
            "SPEC_ELABORATION": self.spec_elaboration_page,
            "TECHNICAL_SPECIFICATION": self.tech_spec_page,
            "BUILD_SCRIPT_SETUP": self.build_script_page,
            "TEST_ENVIRONMENT_SETUP": self.test_env_page,
            "CODING_STANDARD_GENERATION": self.coding_standard_page,
            "PLANNING": self.planning_page,
            "GENESIS": self.genesis_page,
            "VIEWING_PROJECT_HISTORY": self.load_project_page,
            "AWAITING_PREFLIGHT_RESOLUTION": self.preflight_check_page,
            "VIEWING_DOCUMENTS": self.documents_page,
            "VIEWING_REPORTS": self.reports_page,
            "MANUAL_UI_TESTING": self.manual_ui_testing_page,
            "DEBUG_PM_ESCALATION": self.decision_page,
            "IMPLEMENTING_CHANGE_REQUEST": self.cr_management_page,
        }

        if current_phase_name in page_display_map:
            page_to_show = page_display_map[current_phase_name]

            # This is the corrected, explicit logic that prevents regressions.
            if current_phase_name == "VIEWING_PROJECT_HISTORY":
                self.load_project_page.refresh_projects_list()
            elif current_phase_name == "AWAITING_PREFLIGHT_RESOLUTION":
                self.preflight_check_page.update_and_display()
            # --- Add this new block ---
            elif current_phase_name == "DEBUG_PM_ESCALATION":
                failure_log = self.orchestrator.task_awaiting_approval.get("failure_log", "No failure details were captured.")
                self.decision_page.configure(
                    header="Debug Escalation",
                    instruction="The factory has been unable to automatically fix a persistent bug. Please review the details and choose how to proceed.",
                    details=failure_log,
                    option1_text="Retry Automated Fix",
                    option2_text="Pause for Manual Fix",
                    option3_text="Ignore Bug & Proceed"
                )
            # --- End of new block ---
            elif hasattr(page_to_show, 'prepare_for_display'):
                page_to_show.prepare_for_display()
            elif hasattr(page_to_show, 'prepare_for_new_project'):
                page_to_show.prepare_for_new_project()

            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        elif not is_project_active:
            self.ui.mainContentArea.setCurrentWidget(self.ui.welcomePage)

        elif current_phase_name == "IDLE" and is_project_active:
            # Use our new dedicated page for the "Project Complete" screen
            self.project_complete_page.set_project_name(self.orchestrator.project_name)
            self.ui.mainContentArea.setCurrentWidget(self.project_complete_page)

        else: # Fallback for other unimplemented phases
            self.ui.mainContentArea.setCurrentWidget(self.ui.phasePage)
            self.ui.phaseLabel.setText(f"UI for phase '{current_phase_name}' is not yet implemented.")

    def on_new_project(self):
        project_name, ok = QInputDialog.getText(self, "New Project", "Enter a name for your new project:")
        if ok and project_name:
            self.orchestrator.start_new_project(project_name)
            self.update_ui_after_state_change()

    def on_load_project(self):
        self.orchestrator.set_phase("VIEWING_PROJECT_HISTORY")
        self.update_ui_after_state_change()

    def on_close_project(self):
        self.orchestrator.close_active_project()
        self.update_ui_after_state_change()

    def on_stop_export_project(self):
        if not self.orchestrator.project_id: return
        default_name = f"{self.orchestrator.project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        archive_name, ok = QInputDialog.getText(self, "Stop & Export Project", "Enter a name for the archive file:", text=default_name)
        if ok and archive_name:
            archive_path_from_db = self.orchestrator.db_manager.get_config_value("DEFAULT_ARCHIVE_PATH")
            if not archive_path_from_db or not archive_path_from_db.strip():
                QMessageBox.warning(self, "Configuration Error", "The Default Project Archive Path is not set. Please set it in the Settings dialog.")
                return

            self.orchestrator.stop_and_export_project(archive_path_from_db, archive_name)
            self.update_ui_after_state_change()

    def reset_to_idle(self):
        self.orchestrator.reset()
        self.update_ui_after_state_change()

    def show_settings_dialog(self):
        dialog = SettingsDialog(self.orchestrator, self)
        dialog.populate_fields()
        dialog.exec()
        self.update_ui_after_state_change()

    def on_about(self):
        QMessageBox.about(self, "About ASDF", "<h3>Autonomous Software Development Factory (ASDF)</h3><p>Version 0.8 (PySide6 Migration)</p><p>This application uses AI to assist in the end-to-end creation of software.</p>")

    def on_back_to_workflow(self):
        """Returns the UI to the previously active workflow phase."""
        if self.orchestrator.project_id and self.previous_phase:
            self.orchestrator.set_phase(self.previous_phase.name)
            self.update_ui_after_state_change()

    def on_back_from_load_project(self):
        self.reset_to_idle()

    def on_debug_jump_to_phase(self, phase_name: str):
        self.orchestrator.set_phase(phase_name)
        self.update_ui_after_state_change()

    def on_decision_option1(self):
        self.orchestrator.handle_pm_debug_choice("RETRY")
        self.update_ui_after_state_change()

    def on_decision_option2(self):
        self.orchestrator.handle_pm_debug_choice("MANUAL_PAUSE")
        self.update_ui_after_state_change()

    def on_decision_option3(self):
        self.orchestrator.handle_pm_debug_choice("IGNORE")
        self.update_ui_after_state_change()

    def on_proceed(self): QMessageBox.information(self, "Not Implemented", "The 'Proceed' action is not yet implemented.")
    def on_run_tests(self): QMessageBox.information(self, "Not Implemented", "The 'Run Tests' action is not yet implemented.")

    def on_raise_cr(self):
        """Opens the Raise Request dialog and processes the result."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project before raising a request.")
            return

        dialog = RaiseRequestDialog(self)
        if dialog.exec():  # This is true if the user clicks "Save" and validation passes
            data = dialog.get_data()
            request_type = data["request_type"]
            description = data["description"]
            severity = data["severity"]

            success = False
            if request_type == "CHANGE_REQUEST":
                self.orchestrator.save_new_change_request(description)
                # For CR, set_phase is handled inside the orchestrator
                success = True
            elif request_type == "BUG_REPORT":
                success = self.orchestrator.save_bug_report(description, severity)
                # For bugs, we stay in the current phase
                self.orchestrator.set_phase(self.orchestrator.current_phase.name)

            elif request_type == "SPEC_CORRECTION":
                QMessageBox.information(self, "Not Implemented", "The full workflow for 'Specification Correction' requires a dedicated editor and will be implemented separately.")
                return

            if success:
                QMessageBox.information(self, "Success", f"{request_type.replace('_', ' ').title()} has been successfully logged.")
                self.update_cr_register_view() # Refresh the Changes table
            else:
                QMessageBox.critical(self, "Error", f"Failed to save the {request_type.replace('_', ' ').title()}.")

    def on_manage_crs(self):
        """Switches to the CR Management page."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to manage requests.")
            return

        self.orchestrator.handle_view_cr_register_action()
        self.update_ui_after_state_change()

    def on_report_bug(self): QMessageBox.information(self, "Not Implemented", "The 'Report Bug' action is not yet implemented.")

    def on_view_documents(self):
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to view its documents.")
            return
        self.previous_phase = self.orchestrator.current_phase
        self.orchestrator.set_phase("VIEWING_DOCUMENTS")
        self.update_ui_after_state_change()

    def on_view_reports(self):
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to view its reports.")
            return
        self.previous_phase = self.orchestrator.current_phase
        self.orchestrator.set_phase("VIEWING_REPORTS")
        self.update_ui_after_state_change()

    def on_file_tree_context_menu(self, point):
        index = self.ui.projectFilesTreeView.indexAt(point)
        if not index.isValid(): return
        file_path = self.file_system_model.filePath(index)
        is_dir = self.file_system_model.isDir(index)

        menu = QMenu(self)
        if is_dir:
            open_folder_action = menu.addAction("See in Folder")
            open_folder_action.triggered.connect(lambda: self.on_open_file_in_tree(file_path))
        else:
            open_action = menu.addAction("Open File")
            open_action.triggered.connect(lambda: self.on_open_file_in_tree(file_path))
            open_folder_action = menu.addAction("See in Folder")
            open_folder_action.triggered.connect(lambda: self.on_open_file_in_tree(os.path.dirname(file_path)))

        menu.exec(self.ui.projectFilesTreeView.viewport().mapToGlobal(point))

    def on_open_file_in_tree(self, file_path):
        try:
            if sys.platform == "win32": os.startfile(file_path)
            elif sys.platform == "darwin": subprocess.run(["open", file_path], check=True)
            else: subprocess.run(["xdg-open", file_path], check=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file or folder:\n{e}")