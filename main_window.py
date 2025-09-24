# main_window.py

import logging
from pathlib import Path
from datetime import datetime
import os
import subprocess
import sys
import warnings

from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QStackedWidget,
                               QInputDialog, QMessageBox, QFileSystemModel, QMenu,
                               QVBoxLayout, QHeaderView, QAbstractItemView,
                               QStyle, QToolButton, QButtonGroup, QPushButton,
                               QSpacerItem, QSizePolicy, QFileDialog)
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
from gui.import_issue_dialog import ImportIssueDialog
from gui.documents_page import DocumentsPage
from gui.reports_page import ReportsPage
from gui.manual_ui_testing_page import ManualUITestingPage
from gui.project_complete_page import ProjectCompletePage
from gui.sprint_review_page import SprintReviewPage
from gui.project_settings_dialog import ProjectSettingsDialog
from gui.cr_management_page import CRManagementPage
from gui.ux_spec_page import UXSpecPage
from gui.backlog_ratification_page import BacklogRatificationPage
from agents.agent_integration_pmt import IntegrationAgentPMT
from gui.sprint_planning_page import SprintPlanningPage
from gui.worker import Worker

from gui.import_issue_dialog import ImportIssueDialog
from agents.agent_integration_pmt import IntegrationAgentPMT

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
        self.current_tree_root_path = None

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.ui.horizontalLayout.setSpacing(0)

        # Force the layout stretch factors programmatically
        self.ui.centralwidget.layout().setStretch(0, 0) # Index 0 is verticalActionBar (no stretch)
        self.ui.centralwidget.layout().setStretch(1, 1) # Index 1 is mainSplitter (takes all stretch)
        self.ui.verticalLayout_actionBar.setContentsMargins(2, 8, 2, 8) # left, top, right, bottom

        self.ui.mainSplitter.setChildrenCollapsible(False)
        self.ui.mainSplitter.setSizes([350, 850])

        self._create_pages()
        self._setup_file_tree()
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
        self.backlog_ratification_page = BacklogRatificationPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.backlog_ratification_page)
        self.sprint_planning_page = SprintPlanningPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.sprint_planning_page)
        self.sprint_review_page = SprintReviewPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.sprint_review_page)

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
        self.file_system_model.rowsInserted.connect(self.on_directory_updated)

    def on_directory_updated(self, parent_index, first, last):
        """
        Slot to auto-expand a directory when a new item is added to it.
        """
        # The 'first' argument is the row number of the new item within its parent.
        new_item_index = self.file_system_model.index(first, 0, parent_index)
        if new_item_index.isValid() and self.file_system_model.isDir(new_item_index):
            # Use a timer to ensure the view has processed the insertion before we expand
            QTimer.singleShot(50, lambda: self.ui.projectFilesTreeView.expand(new_item_index))

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
        self.button_raise_request.setToolTip("Add a new Backlog Item or Bug Report")
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

        # --- Active Sprint Button (Initially Hidden) ---
        self.button_view_sprint = QToolButton()
        self.button_view_sprint.setToolTip("Return to Active Sprint")
        self.button_view_sprint.setIcon(QIcon(str(icons_path / "sprint_active.png"))) # We will need to add this icon
        self.button_view_sprint.setCheckable(True)
        self.button_view_sprint.setVisible(False) # Hidden by default
        # Insert it before the stretch so it's with the other buttons
        self.ui.verticalLayout_actionBar.insertWidget(self.ui.verticalLayout_actionBar.count() - 1, self.button_view_sprint)
        self.button_group_sidebar.addButton(self.button_view_sprint)

        # Configure the existing "Manage CRs / Bugs" action, add it to the menu and toolbar
        icon = QIcon(str(icons_path / "manage_crs.png"))
        icon.addFile(str(icons_path / "manage_crs.png"), QSize(), QIcon.Normal, QIcon.Off) # Ensure color is preserved
        self.ui.actionManage_CRs_Bugs.setIcon(icon)
        self.ui.menuProject.addAction(self.ui.actionManage_CRs_Bugs)
        self.ui.toolBar.addAction(self.ui.actionManage_CRs_Bugs)

        # --- Project Settings Menu Action ---
        self.actionProject_Settings = QAction("Project Settings...", self)
        self.ui.menuProject.addAction(self.actionProject_Settings)

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
        self.ui.actionOpen_Project.triggered.connect(self.on_open_project)
        self.ui.actionImport_Archived_Project.triggered.connect(self.on_load_project)
        self.ui.actionClose_Project.triggered.connect(self.on_close_project)
        self.ui.actionArchive_Project.triggered.connect(self.on_stop_export_project)
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
        self.actionProject_Settings.triggered.connect(self.on_show_project_settings)

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
        self.button_view_sprint.clicked.connect(self.on_view_sprint)

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
        self.documents_page.back_to_workflow.connect(self.on_back_to_workflow)
        self.reports_page.back_to_workflow.connect(self.on_back_to_workflow)
        self.manual_ui_testing_page.go_to_documents.connect(self.on_view_documents)
        self.manual_ui_testing_page.testing_complete.connect(self.update_ui_after_state_change)
        self.project_complete_page.export_project.connect(self.on_stop_export_project)
        self.cr_management_page.delete_cr.connect(self.on_cr_delete_action)
        self.cr_management_page.analyze_cr.connect(self.on_cr_analyze_action)
        self.cr_management_page.implement_cr.connect(self.on_cr_implement_action)
        self.cr_management_page.implement_cr.connect(self.on_cr_implement_action)
        self.cr_management_page.import_from_tool.connect(self.on_import_from_tool)
        self.cr_management_page.sync_items_to_tool.connect(self.on_sync_items_to_tool)
        self.cr_management_page.generate_technical_preview.connect(self.on_generate_tech_preview_action)
        self.cr_management_page.save_new_order.connect(self.orchestrator.handle_save_cr_order)
        self.cr_management_page.request_ui_refresh.connect(self.update_ui_after_state_change)
        self.ui.actionManage_CRs_Bugs.triggered.connect(self.on_manage_crs)
        self.backlog_ratification_page.backlog_ratified.connect(self.on_backlog_ratified)
        self.sprint_planning_page.sprint_cancelled.connect(self.on_sprint_cancelled)
        self.sprint_planning_page.sprint_started.connect(self.on_start_sprint)
        self.sprint_review_page.return_to_backlog.connect(self.on_return_to_backlog)

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
            self.ui.actionImport_Archived_Project.setEnabled(settings_are_valid)

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
            self.ui.actionImport_Archived_Project.setEnabled(False)
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

        # Disable Open/Import when a project is active, enable when idle.
        self.ui.actionOpen_Project.setEnabled(not is_project_active)
        self.ui.actionImport_Archived_Project.setEnabled(not is_project_active)

        is_project_dirty = self.orchestrator.is_project_dirty
        project_name = self.orchestrator.project_name or "N/A"
        current_phase_enum = self.orchestrator.current_phase
        display_phase_name = self.orchestrator.PHASE_DISPLAY_NAMES.get(current_phase_enum, current_phase_enum.name)
        git_branch = self.orchestrator.get_current_git_branch()
        self.actionProject_Settings.setEnabled(is_project_active)

        self.status_project_label.setText(f"Project: {project_name}")
        self.status_phase_label.setText(f"Phase: {display_phase_name}")
        self.status_git_label.setText(f"Branch: {git_branch}")
        self.ui.actionClose_Project.setEnabled(is_project_active)
        self.ui.actionArchive_Project.setEnabled(is_project_active)

        self.ui.actionManage_CRs_Bugs.setEnabled(is_project_active) # Now always enabled if project is active
        self.ui.actionManage_CRs_Bugs.setToolTip("View and manage the Project Backlog")

        project_root = ""
        if is_project_active:
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = project_details['project_root_folder']

        if project_root and Path(project_root).exists():
            if self.current_tree_root_path != project_root:
                self.current_tree_root_path = project_root
                root_path_obj = Path(project_root)
                self.file_system_model.setRootPath("")
                self.file_system_model.setRootPath(str(root_path_obj.parent))
                self.ui.projectFilesTreeView.setRootIndex(self.file_system_model.index(project_root))
                QTimer.singleShot(250, self.ui.projectFilesTreeView.expandAll)

            self.ui.projectFilesTreeView.setVisible(True)
            self.treeViewInfoLabel.setVisible(False)
        else:
            self.ui.projectFilesTreeView.setVisible(False)
            self.treeViewInfoLabel.setVisible(True)
            self.treeViewInfoLabel.setText("No active project.\n\nPlease create a new project or import an archive.")

    def on_cr_edit_action(self, cr_id: int):
        """Handles the signal to edit an item by opening a pre-populated dialog."""
        details = self.orchestrator.get_cr_details_by_id(cr_id)
        if not details:
            QMessageBox.critical(self, "Error", f"Could not retrieve details for item ID {cr_id}.")
            return

        # Create the dialog and configure it for editing using the new method
        dialog = RaiseRequestDialog(self)
        dialog.set_edit_mode(details)

        # Show the dialog and save the full results on "OK"
        if dialog.exec():
            new_data = dialog.get_data()
            success = self.orchestrator.save_edited_change_request(cr_id, new_data)

            if success:
                QMessageBox.information(self, "Success", f"Item ID {cr_id} was updated successfully.")
                self.update_ui_after_state_change() # Refresh all views
            else:
                QMessageBox.critical(self, "Error", f"Failed to update item ID {cr_id}.")

    def on_cr_delete_action(self, cr_id: int):
        """Handles the signal to delete a CR after user confirmation."""
        reply = QMessageBox.question(self, "Confirm Deletion",
                                    f"Are you sure you want to permanently delete this item (ID: {cr_id})?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.orchestrator.handle_delete_cr_action(cr_id)
            # Refresh the UI to show the item has been removed or to handle a linked-item confirmation
            self.update_ui_after_state_change()

    def on_cr_analyze_action(self, item_data: dict):
        """Handles the signal to run impact analysis on a CR in a background thread."""
        cr_id = item_data.get('cr_id')
        display_id = item_data.get('hierarchical_id', f"CR-{cr_id}")

        self.setEnabled(False)
        self.statusBar().showMessage(f"Running impact analysis for item {display_id}...")

        worker = Worker(self.orchestrator.run_full_analysis, cr_id)
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

    def on_generate_tech_preview_action(self, item_data: dict):
        """Handles the signal to generate a technical preview in a background thread."""
        cr_id = item_data.get('cr_id')
        display_id = item_data.get('hierarchical_id', f"CR-{cr_id}")

        self.setEnabled(False)
        self.statusBar().showMessage(f"Generating technical preview for item {display_id}...")

        # Have the worker task return both the cr_id and the result text
        worker = Worker(lambda cr_id, **kwargs: (cr_id, self.orchestrator.handle_generate_technical_preview(cr_id)), cr_id)
        worker.signals.result.connect(self._handle_tech_preview_result)
        worker.signals.error.connect(self._on_background_task_error)
        worker.signals.finished.connect(self._on_background_task_finished)
        self.threadpool.start(worker)

    def _handle_tech_preview_result(self, result_tuple):
        """Displays the technical preview and prompts the user to acknowledge it."""
        cr_id, preview_text = result_tuple

        # Check if the agent returned an error message
        if preview_text.strip().startswith("### Error"):
            QMessageBox.critical(self, "Preview Failed", f"Failed to generate technical preview for CR-{cr_id}:\n{preview_text}")
            return

        html_content = preview_text

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"Technical Preview for CR-{cr_id}")
        msg_box.setText("The AI has generated the following technical preview of the required changes. Please review and acknowledge to make this item eligible for a sprint.")
        msg_box.setDetailedText(html_content)

        acknowledge_button = msg_box.addButton("Acknowledge & Continue", QMessageBox.AcceptRole)
        msg_box.addButton(QMessageBox.Cancel)
        msg_box.exec()

        if msg_box.clickedButton() == acknowledge_button:
            self.orchestrator.handle_acknowledge_technical_preview(cr_id, preview_text)
            # A full UI update is needed to refresh the backlog's status colors and button states
            self.update_ui_after_state_change()

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

    def on_backlog_ratified(self, final_items: list):
        """Saves the final backlog in a background thread."""
        self.setEnabled(False)
        self.statusBar().showMessage("Saving ratified backlog items to database...")

        worker = Worker(self._task_ratify_backlog, final_items)
        worker.signals.result.connect(self._handle_ratification_result)
        worker.signals.error.connect(self._on_background_task_error) # Re-use generic error handler
        self.threadpool.start(worker)

    def _on_background_task_error(self, error_tuple):
        """A generic handler for errors from background worker threads."""
        self.setEnabled(True)
        self.statusBar().clearMessage()
        error_msg = f"An unexpected error occurred in a background task:\n{error_tuple[1]}"
        logging.error(error_msg, exc_info=False)
        QMessageBox.critical(self, "Background Task Error", error_msg)

    def _task_ratify_backlog(self, final_items, **kwargs):
        """Background worker task to save the backlog."""
        self.orchestrator.handle_backlog_ratification(final_items)
        return True

    def _handle_ratification_result(self, success):
        """Handles the result of the background ratification task."""
        self.setEnabled(True)
        self.statusBar().clearMessage()
        if success:
            self.update_ui_after_state_change()
        else:
            QMessageBox.critical(self, "Error", "Failed to save the ratified backlog.")

    def on_import_from_tool(self):
        """Handles the user's request to import an item from an external tool."""
        dialog = ImportIssueDialog(self)
        if dialog.exec():
            import_data = dialog.get_data()

            self.setEnabled(False)
            self.statusBar().showMessage("Importing item(s) from external tool...")

            worker = Worker(self._task_import_issues, import_data)
            worker.signals.result.connect(self._handle_import_result)
            worker.signals.error.connect(self._on_background_task_error)
            # This is the crucial change: connect to the robust, existing handler
            worker.signals.finished.connect(self._on_background_task_finished)
            self.threadpool.start(worker)

    def _task_import_issues(self, import_data, **kwargs):
        """Background worker task that calls the orchestrator to fetch and filter issues."""
        # This method's logic is correct and remains the same
        return self.orchestrator.handle_import_from_tool(import_data)

    def _handle_import_result(self, new_issues: list):
        """Handles the result data from the import task, but does not update the UI."""
        if new_issues is not None:
            total_found = len(new_issues)
            if total_found > 0:
                # Save the successfully fetched and filtered items to the database
                self.orchestrator.add_imported_backlog_items(new_issues)

            # Use QTimer to show the message after the event loop has had a chance to process
            QTimer.singleShot(100, lambda: QMessageBox.information(self, "Import Complete", f"Successfully imported {total_found} new item(s) into the backlog."))
        # The UI refresh is now handled by _on_background_task_finished

    def _handle_implementation_result(self, cr_id: int, success: bool, error=None):
        """Handles showing the result message of the background implementation task."""
        if success:
            # The message is now queued. The UI transition is handled by _on_background_task_finished.
            QTimer.singleShot(100, lambda: QMessageBox.information(self, "Success", f"Implementation plan for CR-{cr_id} created. Transitioning to development phase."))
        else:
            error_msg = str(error[1]) if error else "An unknown error occurred."
            QTimer.singleShot(100, lambda: QMessageBox.critical(self, "Implementation Failed", f"Failed to create an implementation plan for CR-{cr_id}:\n{error_msg}"))

    def _on_pausing_task_finished(self):
        """
        A dedicated slot that runs after a task that requires a user pause.
        It re-enables the UI but does NOT trigger a state refresh.
        """
        self.setEnabled(True)
        self.statusBar().clearMessage()
        self.orchestrator.set_task_processing_complete()

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

    def on_view_sprint(self):
        """
        Returns the UI to the previously active sprint workflow phase.
        """
        if self.orchestrator.project_id and self.previous_phase:
            self.orchestrator.set_phase(self.previous_phase.name)
            self.update_ui_after_state_change()

    def update_ui_after_state_change(self):
        logging.debug("update_ui_after_state_change: Method entered.")
        """
        Performs a full UI refresh. This is the single source of truth for mapping
        the orchestrator's state to the correct UI view.
        """
        self.update_static_ui_elements()

        current_phase = self.orchestrator.current_phase

        # --- SPRINT NAVIGATION AND PROTECTION LOGIC (CORRECTED) ---
        # Use the new reliable method to check the project's persistent state
        is_sprint_active = self.orchestrator.is_sprint_active()
        self.button_view_sprint.setVisible(is_sprint_active)

        # The button should only be "checked" if we are actively viewing the sprint page
        is_viewing_sprint = (current_phase == FactoryPhase.SPRINT_IN_PROGRESS)
        if is_sprint_active:
            self.button_view_sprint.setChecked(is_viewing_sprint)
        # --- END OF NEW LOGIC ---

        current_phase_name = current_phase.name
        logging.debug(f"update_ui_after_state_change: Detected phase: {current_phase_name}")
        is_project_active = self.orchestrator.project_id is not None

        # This is the new, corrected dictionary
        page_display_map = {
        "ENV_SETUP_TARGET_APP": self.env_setup_page, "SPEC_ELABORATION": self.spec_elaboration_page,
        "GENERATING_APP_SPEC_AND_RISK_ANALYSIS": self.spec_elaboration_page,
        "AWAITING_SPEC_REFINEMENT_SUBMISSION": self.spec_elaboration_page,
        "AWAITING_SPEC_FINAL_APPROVAL": self.spec_elaboration_page,
        "TECHNICAL_SPECIFICATION": self.tech_spec_page,
        "BUILD_SCRIPT_SETUP": self.build_script_page,
        "TEST_ENVIRONMENT_SETUP": self.test_env_page,
        "CODING_STANDARD_GENERATION": self.coding_standard_page,
        "PLANNING": self.planning_page,
        "BACKLOG_RATIFICATION": self.backlog_ratification_page,
        "GENESIS": self.genesis_page,
        "SPRINT_IN_PROGRESS": self.genesis_page,
        "BACKLOG_VIEW": self.cr_management_page,
        "VIEWING_PROJECT_HISTORY": self.load_project_page,
        "VIEWING_ACTIVE_PROJECTS": self.load_project_page,
        "AWAITING_PREFLIGHT_RESOLUTION": self.preflight_check_page,
        "VIEWING_DOCUMENTS": self.documents_page,
        "VIEWING_REPORTS": self.reports_page,
        "MANUAL_UI_TESTING": self.manual_ui_testing_page,
        "PROJECT_COMPLETED": self.project_complete_page,
        "UX_UI_DESIGN": self.ux_spec_page,
        "SPRINT_REVIEW": self.sprint_review_page,
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

        if current_phase_name in page_display_map:
            page_to_show = page_display_map[current_phase_name]
            if hasattr(page_to_show, 'prepare_for_display'):
                page_to_show.prepare_for_display()
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        elif current_phase_name == "AWAITING_UI_TEST_DECISION":
            self.statusBar().clearMessage()
            # Find this entire block and replace it
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            is_auto_test_configured = bool(project_details and project_details['ui_test_execution_command'])
            is_gui = bool(project_details and project_details['is_gui_project'] == 1)

            self.decision_page.configure(
                header="Front-end Testing Phase",
                instruction="The automated backend tests passed. Choose how to proceed with Front-end Testing for this sprint.",
                details="Select an option below to continue.",
                option1_text="Run Automated Front-end Tests",
                option1_enabled=is_auto_test_configured,
                option2_text="Run Manual Front-end Tests",
                option2_enabled=is_gui,  # This line enforces the new rule
                option3_text="Skip and Go to Sprint Review"
            )
            self.decision_page.option1_selected.connect(self.on_ui_test_decision_automated)
            self.decision_page.option2_selected.connect(self.on_ui_test_decision_manual)
            self.decision_page.option3_selected.connect(self.on_ui_test_decision_skip)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "AWAITING_SCRIPT_FAILURE_RESOLUTION":
            task_details = self.orchestrator.task_awaiting_approval or {}
            error_msg = task_details.get("error", "An unknown error occurred.")
            self.decision_page.configure(
                header="Automated Test Script Failure",
                instruction="The AI agent failed to generate the automated Front-end test scripts. Please choose a fallback option.",
                details=f"<b>Agent Error:</b><br><pre>{error_msg}</pre>",
                option1_text="Proceed with Manual Front-end Testing",
                option2_text="Skip Front-end Testing & Go to Sprint Review"
            )
            self.decision_page.option1_selected.connect(self.on_script_failure_fallback_manual)
            self.decision_page.option2_selected.connect(self.on_ui_test_decision_skip)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "GENERATING_MANUAL_TEST_PLAN":
            status_message = "Generating manual test plan documents..."
            self.statusBar().showMessage(status_message)

            # Use the new method to update the processing page display
            self.genesis_page.update_processing_display(simple_status_message=status_message)

            # Set the main UI to show the genesis page in its processing state
            self.genesis_page.ui.stackedWidget.setCurrentWidget(self.genesis_page.ui.processingPage)
            self.genesis_page.ui.logOutputTextEdit.clear()
            self.ui.mainContentArea.setCurrentWidget(self.genesis_page)

            worker = Worker(self.orchestrator._generate_manual_ui_test_plan_phase)
            worker.signals.progress.connect(self.genesis_page.on_progress_update)
            worker.signals.result.connect(self.genesis_page._handle_phase_completion_result)
            worker.signals.error.connect(self.genesis_page._on_task_error)
            worker.signals.finished.connect(self.genesis_page._on_task_finished)
            self.threadpool.start(worker)

        elif current_phase_name == "INTEGRATION_AND_VERIFICATION":
            task_info = self.orchestrator.task_awaiting_approval or {}
            task_to_run = task_info.get("task_to_run")

            # Determine the status message and worker function based on the task
            status_message = ""
            worker_function = None
            worker_args = []

            if task_to_run == "automated_ui_tests":
                status_message = "Running Front-end Testing..."
                worker_function = self.orchestrator._run_automated_ui_test_phase
            else: # Fallback for the old integration task
                status_message = "Running Backend Testing..."
                force_flag = task_info.get("force_integration", False)
                worker_function = self.orchestrator.run_integration_and_verification_phase
                worker_args = [force_flag]

            self.statusBar().showMessage(status_message)

            # Switch to the processing page and update its display using our new method
            self.genesis_page.update_processing_display(simple_status_message=status_message)
            self.genesis_page.ui.stackedWidget.setCurrentWidget(self.genesis_page.ui.processingPage)
            self.genesis_page.ui.logOutputTextEdit.clear()
            self.ui.mainContentArea.setCurrentWidget(self.genesis_page)

            # Start the worker
            worker = Worker(worker_function, *worker_args)
            worker.signals.progress.connect(self.genesis_page.on_progress_update)
            worker.signals.result.connect(self.genesis_page._handle_development_result)
            worker.signals.error.connect(self.genesis_page._on_task_error)
            worker.signals.finished.connect(self.genesis_page._on_task_finished)
            self.threadpool.start(worker)

        elif current_phase_name == "AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION":
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

        elif current_phase_name in ["AWAITING_SPEC_REFINEMENT_SUBMISSION", "AWAITING_SPEC_FINAL_APPROVAL"]:
            # These two states now correctly point to the spec elaboration page.
            # The page itself will handle which view (initial draft or 3-tab) to show.
            page_to_show = self.spec_elaboration_page
            if hasattr(page_to_show, 'prepare_for_display'):
                page_to_show.prepare_for_display()
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        elif current_phase_name in page_display_map:
            page_to_show = page_display_map[current_phase_name]
            logging.debug(f"update_ui_after_state_change: Found page in map. About to switch to: {page_to_show.__class__.__name__}")

            if hasattr(page_to_show, 'prepare_for_display'):
                page_to_show.prepare_for_display()
            if current_phase_name == "PROJECT_COMPLETED":
                 self.project_complete_page.set_project_name(self.orchestrator.project_name)
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        # Add this entire block back into the method
        elif current_phase_name == "AWAITING_RISK_ASSESSMENT_APPROVAL":
            # This block handles showing the risk assessment report.
            page_to_show = self.decision_page
            task_data = self.orchestrator.task_awaiting_approval or {}

            # Check for an error first
            error = task_data.get("error")
            if error:
                QMessageBox.critical(self, "Error", f"Failed to generate specification draft or risk analysis:\n{error}")
                self.orchestrator.set_phase("SPEC_ELABORATION") # Go back to allow retry
                return

            # Correctly parse the nested analysis and risk data from the task
            complexity_data = task_data.get("complexity_analysis", {}) or {}
            risk_data = task_data.get("risk_assessment", {}) or {}

            # Build the detailed HTML string for display
            html_parts = []
            html_parts.append("<h3>Complexity Analysis</h3>")
            for key, value in complexity_data.items():
                title = key.replace('_', ' ').title()
                rating = value.get('rating', 'N/A')
                justification = value.get('justification', 'No details provided.')
                html_parts.append(f"<p><b>{title}:</b> {rating}<br/><i>{justification}</i></p>")

            html_parts.append("<hr><h3>Risk Assessment</h3>")
            html_parts.append(f"<p><b>Overall Risk Level:</b> {risk_data.get('overall_risk_level', 'N/A')}</p>")
            html_parts.append(f"<p><b>Summary:</b> {risk_data.get('summary', 'No summary provided.')}</p>")

            recommendations = risk_data.get('recommendations', [])
            if recommendations:
                html_parts.append("<p><b>Recommendations:</b></p><ul>")
                for rec in recommendations:
                    html_parts.append(f"<li>{rec}</li>")
                html_parts.append("</ul>")

            details_text = "".join(html_parts)

            page_to_show.configure(
                header="Project Complexity & Risk Assessment",
                instruction="The AI has analyzed the project scope. Please review and approve to proceed.",
                details=details_text,
                option1_text="Accept Project & Continue to Spec Review",
                option2_text="Cancel Project"
            )
            # Connect the buttons to the correct new orchestrator methods
            page_to_show.option1_selected.connect(self.on_risk_assessment_approved)
            page_to_show.option2_selected.connect(self.on_close_project)
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

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

        elif current_phase_name == "SPRINT_PLANNING":
            page_to_show = self.sprint_planning_page
            logging.debug(f"update_ui_after_state_change: Preparing Sprint Planning page.")

            # Get the selected items from the orchestrator's pending task
            task_data = self.orchestrator.task_awaiting_approval or {}
            selected_items = task_data.get("selected_sprint_items", [])

            if not selected_items:
                logging.warning("Navigated to Sprint Planning page without any selected items (likely from Debug menu).")

            # Pass the selected items to the page, which fixes the crash
            page_to_show.prepare_for_display(selected_items)
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        elif current_phase_name == "DEBUG_PM_ESCALATION":
            task_details = self.orchestrator.task_awaiting_approval or {}
            failure_log = task_details.get("failure_log", "No details provided.")
            is_env_failure = task_details.get("is_env_failure", False)

            # Format the log as pre-formatted HTML text for monospaced display
            formatted_log = f"<pre style='color: #CC7832;'>{failure_log}</pre>"

            task_details = self.orchestrator.task_awaiting_approval or {}
            failure_log = task_details.get("failure_log", "No details provided.")
            is_env_failure = task_details.get("is_env_failure", False)
            is_final_verification_failure = task_details.get("is_final_verification_failure", False) # New variable

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
            elif is_final_verification_failure:
                self.decision_page.configure(
                    header="Backend Testing Failed",
                    instruction="The backend regression test suite failed. You can debug this issue now, or complete the sprint and log the failure as a new high-priority bug.",
                    details=f"The automated regression test failed with the following output:<br><br>{formatted_log}",
                    option1_text="Debug Manually & Re-run",
                    option2_text="Acknowledge Failures & Complete Sprint"
                )
                # "Debug Manually" connects to the existing manual pause handler
                self.decision_page.option1_selected.connect(self.on_decision_option2)
                # "Acknowledge Failures" connects to the new handler
                self.decision_page.option2_selected.connect(self.on_decision_acknowledge_failures)
            else:
                print(f"DEBUG_INFO: task_details = {task_details}")
                is_phase_failure = task_details.get("is_phase_failure", False)
                self.decision_page.configure(
                    header="Debug Escalation",
                    instruction="The factory has been unable to fix a persistent bug. Please choose how to proceed.",
                    details=f"The automated debug procedure could not resolve the following issue:<br><br>{formatted_log}",
                    option1_text="Retry Automated Fix",
                    option2_text="Pause for Manual Fix & Investigate",
                    option3_text="Skip Task && Log as Backlog Item" if not is_phase_failure else None
                )
                self.decision_page.option1_selected.connect(self.on_decision_option1)
                self.decision_page.option2_selected.connect(self.on_decision_option2)
                if not is_phase_failure:
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

    def on_open_project(self):
        """Handles the new 'Open Project' action to show recent/active projects."""
        self.orchestrator.set_phase("VIEWING_ACTIVE_PROJECTS")
        self.update_ui_after_state_change()

    def on_load_project(self):
        """Handles the 'Import Archived Project' action."""
        self.orchestrator.set_phase("VIEWING_PROJECT_HISTORY")
        self.update_ui_after_state_change()

    def on_close_project(self):
        """Handles the new 'Close Project' action which now auto-pauses."""
        logging.debug("!!! on_close_project in main_window was triggered !!!")
        self.orchestrator.close_and_save_project()
        self.update_ui_after_state_change()

    def on_risk_assessment_approved(self):
        """Handles the PM's approval of the risk assessment and proceeds."""
        self.orchestrator.handle_risk_assessment_approval()
        self.update_ui_after_state_change()

    def on_load_project(self):
        self.orchestrator.set_phase("VIEWING_PROJECT_HISTORY")
        self.update_ui_after_state_change()

    def on_stop_export_project(self):
        if not self.orchestrator.project_id: return

        reply = QMessageBox.question(self, "Stop & Export Project",
                                     "This will create a final archive of the project and then remove it from your active workspace. This action is intended for completed projects.\n\n"
                                     "To temporarily save your work, use 'Pause Project' instead.\n\n"
                                     "Do you want to proceed?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.orchestrator.stop_and_export_project()
            self.update_ui_after_state_change()

    def reset_to_idle(self):
        self.orchestrator.reset()
        self.update_ui_after_state_change()

    def show_settings_dialog(self):
        dialog = SettingsDialog(self.orchestrator, self)
        dialog.populate_fields()

        # This conditional check is the fix. The code below will now only
        # run if the user clicks "Save" (dialog is accepted).
        if dialog.exec():
            # Re-run the check and update the UI after the dialog is closed
            self._check_mandatory_settings()
            self.update_ui_after_state_change()

    def on_show_project_settings(self):
        """Opens the project-specific settings dialog."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please load a project to view its settings.")
            return

        current_settings = self.orchestrator.get_project_settings()
        dialog = ProjectSettingsDialog(current_settings, self)

        if dialog.exec():
            new_settings = dialog.get_data()
            self.orchestrator.save_project_settings(new_settings)
            # Refresh the backlog page UI in case button states need to change
            self.cr_management_page.prepare_for_display()
            QMessageBox.information(self, "Success", "Project settings have been saved.")

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
        # This handler is for the "Retry Automated Fix" button
        if not self.orchestrator.task_awaiting_approval:
            logging.warning("Retry clicked, but no failure context found.")
            return

        failure_log = self.orchestrator.task_awaiting_approval.get("failure_log", "No failure log available.")

        # Set UI to busy state and transition to the Genesis processing view
        self.setEnabled(False)
        self.statusBar().showMessage("Attempting to generate a new automated fix plan...")
        self.orchestrator.set_phase("GENESIS")
        self.update_ui_after_state_change() # This shows the Genesis Page's processing view

        # Switch the Genesis page to its processing view to show the live log
        self.genesis_page.ui.stackedWidget.setCurrentWidget(self.genesis_page.ui.processingPage)
        self.genesis_page.ui.logOutputTextEdit.clear()

        # Start the background worker to generate the fix plan
        worker = Worker(self.orchestrator.handle_retry_fix_action, failure_log)
        worker.signals.progress.connect(self.genesis_page.on_progress_update)
        worker.signals.result.connect(self._handle_retry_fix_result)
        worker.signals.error.connect(self._on_background_task_error)
        worker.signals.finished.connect(self._on_background_task_finished)
        self.threadpool.start(worker)

    def on_decision_option2(self):
        self.orchestrator.handle_pm_debug_choice("MANUAL_PAUSE")
        self.update_ui_after_state_change()

    def on_decision_option3(self):
        self.orchestrator.handle_pm_debug_choice("SKIP_TASK_AND_LOG")
        self.update_ui_after_state_change()

    def on_decision_acknowledge_failures(self):
        """Handles the PM's choice to complete the sprint with acknowledged failures."""
        self.orchestrator.handle_complete_with_failures()
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

    def on_ui_test_decision_skip(self):
        """Handles the PM's choice to skip UI testing."""
        self.orchestrator.handle_ui_test_decision("SKIP")
        self.update_ui_after_state_change()

    def on_ui_test_decision_manual(self):
        """Handles the PM's choice to run manual UI tests."""
        self.orchestrator.handle_ui_test_decision("MANUAL")
        self.update_ui_after_state_change()

    def on_ui_test_decision_automated(self):
        """Handles the PM's choice to run automated UI tests."""
        self.orchestrator.handle_ui_test_decision("AUTOMATED")
        self.update_ui_after_state_change()

    def on_script_failure_fallback_manual(self):
        """Handles the fallback to manual testing after an agent failure."""
        # Re-use the existing handler, which sets the phase to MANUAL_UI_TESTING
        self.on_ui_test_decision_manual()

    def on_pre_execution_check_proceed(self):
        """Handles the user's choice to proceed to the sprint planning workspace."""
        logging.info("PM acknowledged pre-execution report. Proceeding to Sprint Planning.")
        self.orchestrator.set_phase("SPRINT_PLANNING")
        self.update_ui_after_state_change()

    def on_pre_execution_check_cancel(self):
        """Handles the user's choice to cancel the sprint after reviewing the pre-execution check."""
        logging.info("PM cancelled sprint after pre-execution check. Returning to Backlog.")
        self.orchestrator.task_awaiting_approval = None # Clear the pending task
        self.orchestrator.set_phase("BACKLOG_VIEW")
        self.update_ui_after_state_change()

    def on_pre_execution_check_proceed(self):
        """Handles the user's choice to proceed to the sprint planning workspace."""
        logging.info("PM acknowledged pre-execution report. Proceeding to Sprint Planning.")
        self.orchestrator.set_phase("SPRINT_PLANNING")
        self.update_ui_after_state_change()

    def on_sprint_cancelled(self):
        """Handles the user cancelling the sprint planning phase."""
        logging.info("Sprint planning cancelled by user. Returning to Backlog.")
        self.orchestrator.task_awaiting_approval = None # Clear any pending data
        self.orchestrator.set_phase("BACKLOG_VIEW")
        self.update_ui_after_state_change()

    def on_start_sprint(self, sprint_items: list):
        """
        Handles the signal to start a sprint, calls the orchestrator,
        and triggers a UI update.
        """
        self.orchestrator.handle_start_sprint(sprint_items)
        # This is the missing step that forces the UI to refresh to the new phase
        self.update_ui_after_state_change()

    def on_return_to_backlog(self):
        """
        Handles the signal to complete a sprint review and triggers a UI update
        to return to the backlog view.
        """
        self.cr_management_page.clear_sprint_staging()
        self.orchestrator.handle_sprint_review_complete()
        self.update_ui_after_state_change()

    def on_save_pre_execution_report_clicked(self):
        """Handles the request to save the pre-execution report to a DOCX file."""
        try:
            report_context = self.orchestrator.task_awaiting_approval
            if not report_context:
                QMessageBox.warning(self, "No Report", "No report data is available to save.")
                return

            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            project_root = Path(project_details['project_root_folder'])
            sprint_dir = project_root / "sprint"
            sprint_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = sprint_dir / f"{self.orchestrator.project_name}_Pre-Execution_Report_{timestamp}.docx"

            file_path, _ = QFileDialog.getSaveFileName(self, "Save Pre-Execution Report", str(default_filename), "Word Documents (*.docx)")

            if file_path:
                self.setEnabled(False)
                self.statusBar().showMessage("Generating and saving report...")
                worker = Worker(self._task_save_pre_execution_report, file_path, report_context)
                worker.signals.result.connect(self._handle_save_report_result)
                worker.signals.error.connect(self._on_background_task_error)
                worker.signals.finished.connect(self._on_background_task_finished)
                self.threadpool.start(worker)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while preparing to save the report:\n{e}")

    def _task_save_pre_execution_report(self, file_path, report_context, **kwargs):
        """Background worker task to get DOCX data and save it."""
        docx_bytes = self.orchestrator.export_pre_execution_report_to_docx(report_context)
        if docx_bytes:
            with open(file_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            return (True, file_path)
        return (False, "Failed to generate report data.")

    def _handle_save_report_result(self, result):
        """Handles the result of the background save task."""
        success, message = result
        if success:
            QMessageBox.information(self, "Success", f"Successfully saved report to:\n{message}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save report: {message}")

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

    def _handle_retry_fix_result(self, result):
        """Handles the successful completion of the background retry/fix-plan task."""
        # The main UI update is handled by the generic _on_background_task_finished
        # slot. This handler is primarily for logging success.
        logging.info("Successfully completed the retry/fix-plan generation task.")

    def _handle_test_run_error(self, error_tuple):
        """Handles a system error from the test run worker."""
        self.setEnabled(True)
        self.statusBar().clearMessage()
        error_msg = f"An unexpected error occurred while running tests:\n{error_tuple[1]}"
        QMessageBox.critical(self, "Error", error_msg)

    def on_raise_cr(self):
        """Delegates the action to the dedicated handler in the CR Management page."""
        self.cr_management_page.on_add_item_clicked()

    def on_manage_crs(self):
        """Switches to the CR Management page."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to manage requests.")
            return

        self.previous_phase = self.orchestrator.current_phase
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
            # Call the new, unified orchestrator method. Parent is None as it's a top-level request.
            success, _ = self.orchestrator.add_new_backlog_item(data, parent_cr_id=None)

            if success:
                QMessageBox.information(self, "Success", "Bug Report has been successfully logged.")
                self.update_ui_after_state_change()
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

    def on_sync_items_to_tool(self, cr_ids: list):
        """Handles the request to sync a list of items to the external tool."""
        if not cr_ids:
            QMessageBox.warning(self, "No Items to Sync", "No valid, unsynced items were selected.")
            return

        reply = QMessageBox.question(self, "Confirm Sync",
                                     f"You have selected {len(cr_ids)} item(s) to create in the external tool. Proceed?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.setEnabled(False)
            self.statusBar().showMessage(f"Syncing {len(cr_ids)} item(s)...")

            worker = Worker(self._task_sync_items, cr_ids)
            worker.signals.result.connect(self._handle_sync_result)
            worker.signals.error.connect(self._on_background_task_error)
            worker.signals.finished.connect(self._on_background_task_finished)
            self.threadpool.start(worker)

    def _task_sync_items(self, cr_ids: list, **kwargs):
        """Background worker task that calls the orchestrator to sync issues."""
        return self.orchestrator.handle_sync_to_tool(cr_ids)

    def _handle_sync_result(self, result_dict: dict):
        """Handles the summary report from the background sync task."""
        succeeded = result_dict.get('succeeded', 0)
        failed = result_dict.get('failed', 0)
        errors = result_dict.get('errors', [])
        synced_items = result_dict.get('synced_items', [])

        summary_message = ""
        # --- NEW: Custom message for single vs. multiple items ---
        if succeeded == 1 and failed == 0:
            key = synced_items[0]['external_key'] if synced_items else 'N/A'
            summary_message = f"Sync complete.\n\nSuccessfully created Jira issue: {key}"
        else:
            summary_message = f"Sync complete.\n\nSuccessfully created: {succeeded} item(s)\nFailed to create: {failed} item(s)"
        # --- END NEW ---

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Sync Report")
        msg_box.setText(summary_message)

        details = ""
        # Only add synced items to details if there were more than one, or if there were failures.
        if len(synced_items) > 1 or failed > 0:
            created_keys = "\n".join([f"- {item['external_key']} (ASDF ID: {item['id']})" for item in synced_items])
            details += f"Successfully Created Issues:\n{created_keys}\n\n"

        if errors:
            detailed_errors = "\n".join([f"- Item ID {e['id']}: {e['reason']}" for e in errors])
            details += f"Failure Details:\n{detailed_errors}"

        if details:
            msg_box.setDetailedText(details.strip())

        QTimer.singleShot(100, lambda: msg_box.exec())
