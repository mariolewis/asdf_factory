# main_window.py

import logging
from pathlib import Path
from datetime import datetime
import os
import subprocess
import sys
import warnings

from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QStackedWidget,
                               QInputDialog, QMessageBox, QFileSystemModel, QMenu, QVBoxLayout, QHeaderView, QAbstractItemView, QStyle, QToolButton, QButtonGroup)
from PySide6.QtGui import QAction, QStandardItemModel, QStandardItem, QIcon
from PySide6.QtCore import QFile, Signal, Qt, QDir, QSize, QTimer
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
from gui.ux_spec_page import UXSpecPage
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
        self.ui.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.ui.horizontalLayout.setSpacing(0)

        # Force the layout stretch factors programmatically
        self.ui.centralwidget.layout().setStretch(0, 0) # Index 0 is verticalActionBar (no stretch)
        self.ui.centralwidget.layout().setStretch(1, 1) # Index 1 is mainSplitter (takes all stretch)
        self.ui.verticalLayout_actionBar.setContentsMargins(2, 8, 2, 8) # left, top, right, bottom

        self._create_pages()
        self._setup_file_tree()
        self._setup_cr_register_view()
        self._create_menus_and_toolbar()
        self._connect_signals()

        self.update_ui_after_state_change()
        self._check_mandatory_settings()

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
        self.ux_spec_page = UXSpecPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.ux_spec_page)

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
        # Define the path to the custom icons directory
        icons_path = Path(__file__).parent / "gui" / "icons"

        # Add custom icons to top toolbar actions
        self.ui.actionProceed.setIcon(QIcon(str(icons_path / "proceed.png")))
        self.ui.actionRun_Tests.setIcon(QIcon(str(icons_path / "run_tests.png")))
        # The other top toolbar actions will remain without icons for now

        # Create QToolButtons with custom icons for the Vertical Action Bar
        self.button_group_sidebar = QButtonGroup(self)
        self.button_group_sidebar.setExclusive(True)

        self.button_view_explorer = QToolButton()
        self.button_view_explorer.setToolTip("Show Project Explorer")
        self.button_view_explorer.setIcon(QIcon(str(icons_path / "explorer.png")))
        self.button_view_explorer.setCheckable(True)
        self.button_view_explorer.setChecked(True)
        self.ui.verticalLayout_actionBar.addWidget(self.button_view_explorer)
        self.button_group_sidebar.addButton(self.button_view_explorer)

        self.button_raise_request = QToolButton()
        self.button_raise_request.setToolTip("Raise a new Change Request or Bug Report")
        self.button_raise_request.setIcon(QIcon(str(icons_path / "add_request.png")))
        self.ui.verticalLayout_actionBar.addWidget(self.button_raise_request)

        self.button_view_reports = QToolButton()
        self.button_view_reports.setToolTip("View Project Reports")
        self.button_view_reports.setIcon(QIcon(str(icons_path / "reports.png")))
        self.button_view_reports.setCheckable(True)
        self.ui.verticalLayout_actionBar.addWidget(self.button_view_reports)
        self.button_group_sidebar.addButton(self.button_view_reports)

        self.button_view_documents = QToolButton()
        self.button_view_documents.setToolTip("View Project Documents")
        self.button_view_documents.setIcon(QIcon(str(icons_path / "documents.png")))
        self.button_view_documents.setCheckable(True)
        self.ui.verticalLayout_actionBar.addWidget(self.button_view_documents)
        self.button_group_sidebar.addButton(self.button_view_documents)

        self.ui.verticalLayout_actionBar.addStretch()

        # Configure the existing "Manage CRs / Bugs" action, add it to the menu and toolbar
        icon = QIcon(str(icons_path / "manage_crs.png"))
        icon.addFile(str(icons_path / "manage_crs.png"), QSize(), QIcon.Normal, QIcon.Off) # Ensure color is preserved
        self.ui.actionManage_CRs_Bugs.setIcon(icon)
        self.ui.menuProject.addAction(self.ui.actionManage_CRs_Bugs)
        self.ui.toolBar.addAction(self.ui.actionManage_CRs_Bugs)

        # Debug menu setup
        for phase in FactoryPhase:
            if phase.name == "IDLE": continue
            action = QAction(phase.name.replace("_", " ").title(), self)
            action.triggered.connect(lambda checked=False, p=phase.name: self.on_debug_jump_to_phase(p))
            self.ui.menuDebug.addAction(action)

        # Status bar setup
        self.status_project_label = QLabel("Project: N/A")
        self.status_phase_label = QLabel("Phase: Idle")
        self.status_git_label = QLabel("Branch: N/A")
        self.ui.statusbar.addPermanentWidget(self.status_project_label)
        self.ui.statusbar.addPermanentWidget(self.status_phase_label)
        self.ui.statusbar.addPermanentWidget(self.status_git_label)

    def _connect_signals(self):
        """Connects all UI signals to their corresponding slots."""
        # File Menu & Top Toolbar Actions
        self.ui.actionNew_Project.triggered.connect(self.on_new_project)
        self.ui.actionLoad_Exported_Project.triggered.connect(self.on_load_project)
        self.ui.actionClose_Project.triggered.connect(self.on_close_project)
        self.ui.actionStop_Export_Project.triggered.connect(self.on_stop_export_project)
        self.ui.actionSettings.triggered.connect(self.show_settings_dialog)
        self.ui.actionExit.triggered.connect(self.close)

        # Edit Menu Connections
        self.ui.actionUndo.triggered.connect(self.on_undo)
        self.ui.actionRedo.triggered.connect(self.on_redo)
        self.ui.actionCut.triggered.connect(self.on_cut)
        self.ui.actionCopy.triggered.connect(self.on_copy)
        self.ui.actionPaste.triggered.connect(self.on_paste)

        # --- NEW: View Menu Connections ---
        self.ui.actionToggleProjectPanel.triggered.connect(self.on_view_explorer) # Re-uses existing handler
        self.ui.actionToggleNotificationPanel.triggered.connect(self.on_toggle_notification_panel)
        # --- End of New Section ---

        # Project Menu Actions
        self.ui.actionView_Documents.triggered.connect(self.on_view_documents)
        self.ui.actionView_Reports.triggered.connect(self.on_view_reports)

        # Run Menu & Top Toolbar Actions
        self.ui.actionProceed.triggered.connect(self.on_proceed)
        self.ui.actionRun_Tests.triggered.connect(self.on_run_tests)
        self.ui.actionReport_Bug.triggered.connect(self.on_report_bug)

        # Help Menu
        self.ui.actionAbout_ASDF.triggered.connect(self.on_about)

        # --- CORRECTED: Vertical Action Bar Connections ---
        self.button_view_explorer.clicked.connect(self.on_view_explorer)
        self.button_raise_request.clicked.connect(self.on_raise_cr)
        self.button_view_reports.clicked.connect(self.on_view_reports)
        self.button_view_documents.clicked.connect(self.on_view_documents)
        # --- End of Corrected Section ---

        # Connect signals that trigger a FULL UI refresh and page transition
        for page in [self.env_setup_page, self.spec_elaboration_page, self.tech_spec_page, self.build_script_page, self.test_env_page, self.coding_standard_page, self.planning_page, self.genesis_page, self.load_project_page, self.preflight_check_page, self.ux_spec_page]:
            if hasattr(page, 'setup_complete'): page.setup_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'spec_elaboration_complete'): page.spec_elaboration_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'project_cancelled'): page.project_cancelled.connect(self.update_ui_after_state_change)
            if hasattr(page, 'tech_spec_complete'): page.tech_spec_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'build_script_setup_complete'): page.build_script_setup_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'test_env_setup_complete'): page.test_env_setup_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'coding_standard_complete'): page.coding_standard_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'planning_complete'): page.planning_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'genesis_complete'): page.genesis_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'project_loaded'): page.project_loaded.connect(self.update_ui_after_state_change)
            if hasattr(page, 'project_load_finalized'): page.project_load_finalized.connect(self.update_ui_after_state_change)
            if hasattr(page, 'ux_spec_complete'): page.ux_spec_complete.connect(self.update_ui_after_state_change)

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
        self.project_complete_page.export_project.connect(self.on_stop_export_project)
        self.cr_management_page.back_to_workflow.connect(self.on_back_to_workflow)
        self.cr_management_page.edit_cr.connect(self.on_cr_edit_action)
        self.cr_management_page.delete_cr.connect(self.on_cr_delete_action)
        self.cr_management_page.analyze_cr.connect(self.on_cr_analyze_action)
        self.cr_management_page.implement_cr.connect(self.on_cr_implement_action)
        self.ui.actionManage_CRs_Bugs.triggered.connect(self.on_manage_crs)

    def _reset_all_pages_for_new_project(self):
        """Iterates through all page widgets and calls their reset method if it exists."""
        logging.info("Resetting all UI pages for new project.")
        pages = [
            self.env_setup_page,
            self.spec_elaboration_page,
            self.tech_spec_page,
            self.build_script_page,
            self.test_env_page,
            self.coding_standard_page,
            self.planning_page,
            self.genesis_page,
            self.preflight_check_page,
            self.decision_page,
            self.manual_ui_testing_page,
            self.cr_management_page
        ]
        for page in pages:
            if hasattr(page, 'prepare_for_new_project'):
                page.prepare_for_new_project()

    def _check_mandatory_settings(self):
        """
        Checks for mandatory global settings and enables/disables project actions.
        Returns True if settings are valid, False otherwise.
        """
        try:
            db = self.orchestrator.db_manager
            config = db.get_all_config_values()

            provider = config.get("SELECTED_LLM_PROVIDER")
            api_key_valid = False
            if provider == "Gemini" and config.get("GEMINI_API_KEY"):
                api_key_valid = True
            elif provider == "ChatGPT" and config.get("OPENAI_API_KEY"):
                api_key_valid = True
            elif provider == "Claude" and config.get("ANTHROPIC_API_KEY"):
                api_key_valid = True
            elif provider == "Phi-3 (Local)":
                api_key_valid = True # No key needed
            elif provider == "Any Other" and config.get("CUSTOM_ENDPOINT_API_KEY") and config.get("CUSTOM_ENDPOINT_URL"):
                api_key_valid = True

            paths_valid = bool(config.get("DEFAULT_PROJECT_PATH") and config.get("DEFAULT_ARCHIVE_PATH"))

            settings_are_valid = api_key_valid and paths_valid

            # Enable/disable actions
            self.ui.actionNew_Project.setEnabled(settings_are_valid)
            # The Load_Exported_Project action is only available when no project is active anyway
            # but we can disable it here for consistency.
            self.ui.actionLoad_Exported_Project.setEnabled(settings_are_valid)

            # Update status bar AND the main info label
            if not settings_are_valid:
                message = "Configuration incomplete. \n\nPlease go to File > Settings to set the LLM API key and default paths."
                self.statusBar().showMessage(message, 0)
                if self.treeViewInfoLabel:
                    self.treeViewInfoLabel.setText(message)
            else:
                # Clear any persistent message if settings are now valid
                if "Configuration incomplete" in self.statusBar().currentMessage():
                    self.statusBar().clearMessage()
                if self.treeViewInfoLabel and "Configuration incomplete" in self.treeViewInfoLabel.text():
                    self.treeViewInfoLabel.setText("No active project.\n\nPlease create a new project or load an archive.")

            return settings_are_valid
        except Exception as e:
            logging.error(f"Failed to check mandatory settings: {e}")
            self.ui.actionNew_Project.setEnabled(False)
            self.ui.actionLoad_Exported_Project.setEnabled(False)
            self.statusBar().showMessage("Error checking settings. Please see logs.", 5000)
            return False

    def on_view_explorer(self):
        """Toggles the visibility of the left project/navigation panel."""
        self.ui.leftPanelWidget.setVisible(not self.ui.leftPanelWidget.isVisible())

    def _get_focused_text_widget(self):
        """Helper to get the currently focused text input widget."""
        widget = QApplication.focusWidget()
        if isinstance(widget, (QTextEdit, QLineEdit, QPlainTextEdit)):
            return widget
        return None

    def on_undo(self):
        widget = self._get_focused_text_widget()
        if widget:
            widget.undo()

    def on_redo(self):
        widget = self._get_focused_text_widget()
        if widget:
            widget.redo()

    def on_cut(self):
        widget = self._get_focused_text_widget()
        if widget:
            widget.cut()

    def on_copy(self):
        widget = self._get_focused_text_widget()
        if widget:
            widget.copy()

    def on_paste(self):
        widget = self._get_focused_text_widget()
        if widget:
            widget.paste()

    def on_toggle_notification_panel(self):
        """Toggles the visibility of the bottom notification/log panel."""
        # The actual panel does not exist yet and will be added in a future task.
        # This handler serves as a placeholder.
        QMessageBox.information(self, "Not Implemented", "The notification panel will be implemented in a future update.")

    def update_static_ui_elements(self):
        """
        Updates only the static parts of the UI like the status bar and file tree.
        """
        is_project_active = self.orchestrator.project_id is not None
        is_project_dirty = self.orchestrator.is_project_dirty
        self.ui.actionLoad_Exported_Project.setEnabled(not is_project_active)
        project_name = self.orchestrator.project_name or "N/A"
        current_phase_enum = self.orchestrator.current_phase
        display_phase_name = self.orchestrator.PHASE_DISPLAY_NAMES.get(current_phase_enum, current_phase_enum.name)
        git_branch = self.orchestrator.get_current_git_branch()

        # Access is_genesis_complete as a property (no parentheses)
        genesis_complete = self.orchestrator.is_genesis_complete

        self.status_project_label.setText(f"Project: {project_name}")
        self.status_phase_label.setText(f"Phase: {display_phase_name}")
        self.status_git_label.setText(f"Branch: {git_branch}")
        self.ui.actionClose_Project.setEnabled(is_project_active and not is_project_dirty)
        self.ui.actionStop_Export_Project.setEnabled(is_project_active)

        self.ui.actionManage_CRs_Bugs.setEnabled(is_project_active) # Now always enabled if project is active
        self.ui.actionManage_CRs_Bugs.setToolTip("View and manage the CR/Bug register")

        project_root = ""
        if is_project_active:
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = project_details['project_root_folder']

        if project_root and Path(project_root).exists():
            root_path_obj = Path(project_root)
            self.file_system_model.setRootPath("")
            self.file_system_model.setRootPath(str(root_path_obj.parent))
            self.ui.projectFilesTreeView.setRootIndex(self.file_system_model.index(project_root))
            self.ui.projectFilesTreeView.setVisible(True)
            self.treeViewInfoLabel.setVisible(False)
        else:
            self.ui.projectFilesTreeView.setVisible(False)
            self.treeViewInfoLabel.setVisible(True)
            self.treeViewInfoLabel.setText("No active project.\n\nPlease create a new project or load an archive.")

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
        self.setEnabled(False)
        self.statusBar().showMessage(f"Running impact analysis for CR-{cr_id}...")

        worker = Worker(self.orchestrator.handle_run_impact_analysis_action, cr_id)
        # Connect the result/error signals to the data handler
        worker.signals.result.connect(lambda: self._handle_analysis_result(cr_id, True))
        worker.signals.error.connect(lambda err: self._handle_analysis_result(cr_id, False, err))
        # Connect the FINISHED signal to the UI re-enabling handler
        worker.signals.finished.connect(self._on_background_task_finished)
        self.threadpool.start(worker)

    def _handle_analysis_result(self, cr_id: int, success: bool, error=None):
        """Handles showing the result message of the background analysis task."""
        if success:
            QTimer.singleShot(100, lambda: QMessageBox.information(self, "Success", f"Impact analysis for CR-{cr_id} completed successfully."))
        else:
            error_msg = str(error[1]) if error else "An unknown error occurred."
            QTimer.singleShot(100, lambda: QMessageBox.critical(self, "Analysis Failed", f"Failed to run impact analysis for CR-{cr_id}:\n{error_msg}"))

    def _handle_integration_result(self):
        """Called when the integration worker is finished. Triggers a final UI update."""
        # The orchestrator's phase will have been updated, so a full UI refresh
        # will show the correct next page (e.g., MANUAL_UI_TESTING or an error).
        # The re-enabling of the UI is now handled by the _on_background_task_finished slot.
        self.update_ui_after_state_change()

    def on_cr_implement_action(self, cr_id: int):
        """Handles the signal to implement a CR in a background thread."""
        self.setEnabled(False)
        self.statusBar().showMessage(f"Generating implementation plan for CR-{cr_id}...")

        worker = Worker(self.orchestrator.handle_implement_cr_action, cr_id)
        # Connect the result/error signals to the data handler
        worker.signals.result.connect(lambda: self._handle_implementation_result(cr_id, True))
        worker.signals.error.connect(lambda err: self._handle_implementation_result(cr_id, False, err))
        # This is the crucial change: connect the FINISHED signal
        worker.signals.finished.connect(self._on_background_task_finished)
        self.threadpool.start(worker)

    def _handle_implementation_result(self, cr_id: int, success: bool, error=None):
        """Handles showing the result message of the background implementation task."""
        if success:
            # The message is now queued. The UI transition is handled by _on_background_task_finished.
            QTimer.singleShot(100, lambda: QMessageBox.information(self, "Success", f"Implementation plan for CR-{cr_id} created. Transitioning to development phase."))
        else:
            error_msg = str(error[1]) if error else "An unknown error occurred."
            QTimer.singleShot(100, lambda: QMessageBox.critical(self, "Implementation Failed", f"Failed to create an implementation plan for CR-{cr_id}:\n{error_msg}"))

    def _on_background_task_finished(self):
        """
        A dedicated slot that runs AFTER a background task is completely finished.
        It re-enables the UI and then refreshes the data tables.
        """
        self.setEnabled(True)
        self.statusBar().clearMessage()

        # --- THIS IS THE FIX ---
        # The orchestrator's state is now final. A single call here will now
        # correctly read the new phase (GENESIS) and transition the page.
        self.update_ui_after_state_change()
        # --- END OF FIX ---

    def update_ui_after_state_change(self):
        logging.debug("update_ui_after_state_change: Method entered.")
        """
        Performs a full UI refresh. This is the single source of truth for mapping
        the orchestrator's state to the correct UI view.
        """
        #is_project_active = self.orchestrator.project_id is not None
        #if not is_project_active:
        #    self.ui.mainContentArea.setCurrentWidget(self.ui.welcomePage)
        #    return
        self.update_cr_register_view()
        self.update_static_ui_elements()

        current_phase = self.orchestrator.current_phase
        current_phase_name = current_phase.name
        logging.debug(f"update_ui_after_state_change: Detected phase: {current_phase_name}")
        is_project_active = self.orchestrator.project_id is not None

        # This map now includes all standard pages
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
            "IMPLEMENTING_CHANGE_REQUEST": self.cr_management_page,
            "PROJECT_COMPLETED": self.project_complete_page,
            "UX_UI_DESIGN": self.ux_spec_page,
        }

        # Disconnect all signals from the generic decision page to prevent multiple triggers
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            try:
                self.decision_page.option1_selected.disconnect()
                self.decision_page.option2_selected.disconnect()
                self.decision_page.option3_selected.disconnect()
            except TypeError:
                pass # Still catch TypeError for other potential issues

        if current_phase_name == "AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION":
            task = self.orchestrator.task_awaiting_approval or {}
            analysis = task.get("analysis", {})
            error = task.get("analysis_error")

            if error:
                details_text = f"The UX Triage Agent failed to process the brief.<br><br>--- ERROR ---<br><pre>{error}</pre>"
                self.decision_page.configure(
                    header="Triage Analysis Failed",
                    instruction="An error occurred during the initial analysis.",
                    details=details_text,
                    option1_text="Proceed to Specification Anyway",
                    option2_text="Cancel Project"
                )
                self.decision_page.option1_selected.connect(self.on_ux_phase_decision_skip)
                self.decision_page.option2_selected.connect(self.on_cancel_project)
            else:
                necessity = analysis.get('ux_phase_necessity', 'N/A')
                justification = analysis.get('justification', 'No details provided.')
                details_text = f"<b>AI Recommendation:</b> {necessity}<br><br><b>Justification:</b><br>{justification}"

                is_start_button_enabled = (necessity != "Not Recommended")

                self.decision_page.configure(
                    header="UX/UI Phase Recommendation",
                    instruction="The AI has analyzed the project brief and recommends the following course of action.",
                    details=details_text,
                    option1_text="Start Dedicated UX/UI Phase",
                    option1_enabled=is_start_button_enabled,
                    option2_text="Skip and Proceed to Application Specification"
                )
                self.decision_page.option1_selected.connect(self.on_ux_phase_decision_start)
                self.decision_page.option2_selected.connect(self.on_ux_phase_decision_skip)

            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name in page_display_map:
            page_to_show = page_display_map[current_phase_name]
            logging.debug(f"update_ui_after_state_change: Found page in map. About to switch to: {page_to_show.__class__.__name__}")

            if hasattr(page_to_show, 'prepare_for_display'):
                page_to_show.prepare_for_display()
            if current_phase_name == "PROJECT_COMPLETED":
                 self.project_complete_page.set_project_name(self.orchestrator.project_name)
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        elif current_phase_name == "INTEGRATION_AND_VERIFICATION":
            self.setEnabled(False)
            self.statusBar().showMessage("Running integration and verification phase...")
            self.genesis_page.ui.stackedWidget.setCurrentWidget(self.genesis_page.ui.processingPage)
            self.genesis_page.ui.processingLabel.setText("Running Integration & Verification...")
            self.genesis_page.ui.logOutputTextEdit.clear()
            self.ui.mainContentArea.setCurrentWidget(self.genesis_page)

            task_info = self.orchestrator.task_awaiting_approval or {}
            force_flag = task_info.get("force_integration", False)

            worker = Worker(self.orchestrator.run_integration_and_verification_phase, force_proceed=force_flag)
            worker.signals.progress.connect(self.genesis_page.on_progress_update)
            worker.signals.result.connect(self._handle_integration_result)
            worker.signals.error.connect(self._handle_integration_result) # Can be handled by the same logic
            worker.signals.finished.connect(self._on_background_task_finished) # Re-enables the UI
            self.threadpool.start(worker)

        elif current_phase_name == "AWAITING_INTEGRATION_CONFIRMATION":
            task = self.orchestrator.task_awaiting_approval or {}
            known_issues = task.get("known_issues", [])
            issue_list_str = "\n".join([f"- {issue['artifact_name']} (Status: {issue['status']})" for issue in known_issues])
            details_text = (
                "The system has detected that one or more components have a non-passing status (e.g., 'KNOWN_ISSUE').\n\n"
                f"--- Components with Issues ---\n{issue_list_str}\n\n"
                "Proceeding with integration is not recommended. Do you wish to proceed anyway?"
            )
            self.decision_page.configure(
                header="Pre-Integration Checkpoint",
                instruction="Components with known issues were detected.",
                details=details_text,
                option1_text="Proceed Anyway",
                option2_text="Stop && Export Project"
            )
            self.decision_page.option1_selected.connect(self.on_integration_confirmed)
            self.decision_page.option2_selected.connect(self.on_stop_export_project)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "DEBUG_PM_ESCALATION":
            task_details = self.orchestrator.task_awaiting_approval or {}
            failure_log = task_details.get("failure_log", "No details provided.")
            is_env_failure = task_details.get("is_env_failure", False)

            # Format the log as pre-formatted HTML text for monospaced display
            formatted_log = f"<pre style='color: #CC7832;'>{failure_log}</pre>"

            if is_env_failure:
                self.decision_page.configure(
                    header="Environment Failure",
                    instruction="The process is paused. Please resolve the environment issue.",
                    details=f"The factory has encountered an unrecoverable ENVIRONMENT error:<br><br>--- ERROR LOG ---{formatted_log}",
                    option1_text="I have fixed the issue, Retry",
                    option2_text="Stop && Export Project"
                )
                self.decision_page.option1_selected.connect(self.on_decision_option1)
                self.decision_page.option2_selected.connect(self.on_stop_export_project)
            else:
                self.decision_page.configure(
                    header="Debug Escalation",
                    instruction="The factory has been unable to fix a persistent bug. Please choose how to proceed.",
                    details=f"The automated debug procedure could not resolve the following issue:<br><br>{formatted_log}",
                    option1_text="Retry Automated Fix",
                    option2_text="Pause for Manual Fix",
                    option3_text="Ignore Bug && Proceed"
                )
                self.decision_page.option1_selected.connect(self.on_decision_option1)
                self.decision_page.option2_selected.connect(self.on_decision_option2)
                self.decision_page.option3_selected.connect(self.on_decision_option3)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "AWAITING_IMPACT_ANALYSIS_CHOICE":
            self.decision_page.configure(
                header="Stale Impact Analysis",
                instruction="The project's code has changed since the impact analysis was last run.",
                details="Do you want to re-run the analysis, or proceed with the existing (stale) analysis?",
                option1_text="Re-run Analysis",
                option2_text="Proceed Anyway"
            )
            self.decision_page.option1_selected.connect(self.on_stale_analysis_rerun)
            self.decision_page.option2_selected.connect(self.on_stale_analysis_proceed)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "AWAITING_PM_DECLARATIVE_CHECKPOINT":
            task = self.orchestrator.task_awaiting_approval
            details_text = (
                f"High-risk change for: <b>{task.get('component_name')}</b>\nFile: <b>{task.get('component_file_path')}</b>\n\n<pre>{task.get('task_description')}</pre>"
            )
            self.decision_page.configure(
                header="High-Risk Change Approval",
                instruction="A high-risk change requires your explicit approval before execution.",
                details=details_text,
                option1_text="Execute Change Automatically",
                option2_text="I Will Apply Manually && Skip"
            )
            self.decision_page.option1_selected.connect(self.on_declarative_execute_auto)
            self.decision_page.option2_selected.connect(self.on_declarative_execute_manual)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "IDLE" or not is_project_active:
            self.ui.mainContentArea.setCurrentWidget(self.ui.welcomePage)
        else:
            self.ui.mainContentArea.setCurrentWidget(self.ui.phasePage)
            self.ui.phaseLabel.setText(f"UI for phase '{current_phase_name}' is not yet implemented.")
        logging.debug("update_ui_after_state_change: Method finished.")

    def on_new_project(self):
        project_name, ok = QInputDialog.getText(self, "New Project", "Enter a name for your new project:")
        if ok and project_name:
            # The orchestrator now returns the suggested path
            suggested_path = self.orchestrator.start_new_project(project_name)

            # This is the new line that fixes the state bug
            self._reset_all_pages_for_new_project()

            # We now explicitly tell the setup page what path to display
            self.env_setup_page.set_initial_path(suggested_path)

            # This call will now show the page with the pre-populated path
            self.update_ui_after_state_change()

    def on_load_project(self):
        self.orchestrator.set_phase("VIEWING_PROJECT_HISTORY")
        self.update_ui_after_state_change()

    def on_close_project(self):
        logging.debug("!!! on_close_project in main_window was triggered !!!")
        self.orchestrator.close_active_project()
        self.update_ui_after_state_change()

    def on_stop_export_project(self):
        if not self.orchestrator.project_id: return
        default_name = f"{self.orchestrator.project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        archive_name, ok = QInputDialog.getText(self, "Stop && Export Project", "Enter a name for the archive file:", text=default_name)
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
        # Re-run the check and update the UI after the dialog is closed
        self._check_mandatory_settings()
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

    def on_stale_analysis_rerun(self):
        """Handles the user's choice to re-run a stale analysis."""
        cr_id = self.orchestrator.task_awaiting_approval.get("cr_id_for_reanalysis")
        if cr_id:
            self.orchestrator.handle_stale_analysis_choice("RE-RUN", cr_id)
            # After re-running, the orchestrator flow will continue, so we just update the UI
            self.update_ui_after_state_change()

    def on_stale_analysis_proceed(self):
        """Handles the user's choice to proceed with a stale analysis."""
        cr_id = self.orchestrator.task_awaiting_approval.get("cr_id_for_reanalysis")
        if cr_id:
            self.orchestrator.handle_stale_analysis_choice("PROCEED", cr_id)
            # The orchestrator will set the phase back to the CR manager, so we update the UI
            self.update_ui_after_state_change()

    def on_declarative_execute_auto(self):
        """Handles the user's choice to have the factory execute the declarative change."""
        self.orchestrator.handle_declarative_checkpoint_decision("EXECUTE_AUTOMATICALLY")
        self.update_ui_after_state_change()

    def on_declarative_execute_manual(self):
        """Handles the user's choice to apply the change manually and skip automated execution."""
        self.orchestrator.handle_declarative_checkpoint_decision("WILL_EXECUTE_MANUALLY")
        self.update_ui_after_state_change()

    def on_ux_phase_decision_start(self):
        """Handles the PM's choice to start the UX/UI phase."""
        self.orchestrator.handle_ux_ui_phase_decision("START_UX_UI_PHASE")
        self.update_ui_after_state_change()

    def on_ux_phase_decision_skip(self):
        """Handles the PM's choice to skip the UX/UI phase."""
        self.orchestrator.handle_ux_ui_phase_decision("SKIP_TO_SPEC")
        self.update_ui_after_state_change()

    def on_proceed(self):
        """Triggers the primary 'proceed' action for the active page, if applicable."""
        if self.orchestrator.current_phase == FactoryPhase.GENESIS:
            # The genesis page has its own logic to run the step in a background thread
            self.genesis_page.run_development_step()
        else:
            QMessageBox.information(self, "Action Not Applicable", "The 'Proceed' action is not applicable in the current phase.")

    def on_run_tests(self):
        """Runs the full test suite for the active project in a background thread."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to run tests.")
            return

        self.setEnabled(False)
        self.statusBar().showMessage("Running full test suite...")

        # We will create the 'run_full_test_suite' method in the orchestrator next.
        worker = Worker(self.orchestrator.run_full_test_suite)
        worker.signals.result.connect(self._handle_test_run_result)
        worker.signals.error.connect(self._handle_test_run_error)
        self.threadpool.start(worker)

    def _handle_test_run_result(self, result):
        """Handles the result of the background test run task."""
        self.setEnabled(True)
        self.statusBar().clearMessage()
        success, output = result
        if success:
            QMessageBox.information(self, "Tests Passed", "The full test suite passed successfully.")
        else:
            # Use a detailed text message box for long error logs
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Test Run Failed")
            msg_box.setText("One or more tests failed. See details below.")
            msg_box.setDetailedText(output)
            msg_box.exec()

    def _handle_test_run_error(self, error_tuple):
        """Handles a system error from the test run worker."""
        self.setEnabled(True)
        self.statusBar().clearMessage()
        error_msg = f"An unexpected error occurred while running tests:\n{error_tuple[1]}"
        QMessageBox.critical(self, "Error", error_msg)

    def on_raise_cr(self):
        """Opens the Raise Request dialog and processes the result."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project before raising a request.")
            return

        dialog = RaiseRequestDialog(self, initial_request_type="CHANGE_REQUEST")
        if dialog.exec():
            data = dialog.get_data()
            request_type = data["request_type"]
            description = data["description"]
            severity = data["severity"]

            success = False
            if request_type == "CHANGE_REQUEST":
                self.orchestrator.save_new_change_request(description)
                success = True
            elif request_type == "BUG_REPORT":
                success = self.orchestrator.save_bug_report(description, severity)

            if success:
                QMessageBox.information(self, "Success", f"{request_type.replace('_', ' ').title()} has been successfully logged.")
                # --- THIS IS THE FIX ---
                # Trigger a full UI update to refresh all tables and state.
                self.update_ui_after_state_change()
                # --- END OF FIX ---
            else:
                QMessageBox.critical(self, "Error", f"Failed to save the {request_type.replace('_', ' ').title()}.")

    def on_manage_crs(self):
        """Switches to the CR Management page."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to manage requests.")
            return

        self.orchestrator.handle_view_cr_register_action()
        self.update_ui_after_state_change()

    def on_report_bug(self):
        """Opens the Raise Request dialog with the Bug Report option pre-selected."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project before reporting a bug.")
            return

        dialog = RaiseRequestDialog(self, initial_request_type="BUG_REPORT")
        if dialog.exec():
            data = dialog.get_data()
            success = self.orchestrator.save_bug_report(data["description"], data["severity"])
            if success:
                QMessageBox.information(self, "Success", "Bug Report has been successfully logged.")
                self.update_cr_register_view()
            else:
                QMessageBox.critical(self, "Error", "Failed to save the Bug Report.")

    def on_view_documents(self):
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to view its documents.")
            return
        # --- THIS IS THE FIX ---
        self.previous_phase = self.orchestrator.current_phase
        # --- END OF FIX ---
        self.orchestrator.set_phase("VIEWING_DOCUMENTS")
        self.update_ui_after_state_change()

    def on_view_reports(self):
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to view its reports.")
            return
        # --- THIS IS THE FIX ---
        self.previous_phase = self.orchestrator.current_phase
        # --- END OF FIX ---
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

    def on_integration_confirmed(self):
        """Handles the user's choice to proceed with integration despite known issues."""
        self.orchestrator.handle_integration_confirmation("PROCEED")
        # The orchestrator will now re-trigger the integration task in the background,
        # so we just need to update the UI to show its progress.
        self.update_ui_after_state_change()