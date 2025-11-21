# main_window.py

import logging
from pathlib import Path
from datetime import datetime
import os
import subprocess
import sys
import warnings
import base64
from io import BytesIO

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QStackedWidget,
                               QInputDialog, QMessageBox, QFileSystemModel, QMenu, QStatusBar,
                               QHBoxLayout, QVBoxLayout, QHeaderView, QAbstractItemView,
                               QStyle, QToolButton, QButtonGroup, QPushButton,
                               QSpacerItem, QSizePolicy, QFileDialog)
from PySide6.QtGui import QAction, QStandardItemModel, QStandardItem, QIcon
from PySide6.QtCore import QFile, Signal, Qt, QDir, QSize, QTimer, QEvent
from PySide6.QtCore import QThreadPool

from gui.ui_main_window import Ui_MainWindow
from master_orchestrator import MasterOrchestrator, FactoryPhase
from gui.settings_dialog import SettingsDialog
from gui.new_project_dialog import NewProjectDialog
from gui.intake_assessment_page import IntakeAssessmentPage
from gui.env_setup_page import EnvSetupPage
from gui.spec_elaboration_page import SpecElaborationPage
from gui.tech_spec_page import TechSpecPage
from gui.build_script_page import BuildScriptPage
from gui.test_env_page import TestEnvPage
from gui.dockerization_page import DockerizationPage
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
from gui.sprint_planning_page import SprintPlanningPage
from gui.sprint_validation_page import SprintValidationPage
from gui.sprint_review_page import SprintReviewPage
from gui.sprint_history_page import SprintHistoryPage
from gui.project_settings_dialog import ProjectSettingsDialog
from gui.cr_management_page import CRManagementPage
from gui.ux_spec_page import UXSpecPage
from gui.backlog_ratification_page import BacklogRatificationPage
from agents.agent_integration_pmt import IntegrationAgentPMT
from gui.worker import Worker
from gui.import_issue_dialog import ImportIssueDialog
from agents.agent_integration_pmt import IntegrationAgentPMT
from gui.delivery_assessment_page import DeliveryAssessmentPage
from gui.codebase_analysis_page import CodebaseAnalysisPage
from gui.project_dashboard_page import ProjectDashboardPage
from gui.sprint_integration_test_page import SprintIntegrationTestPage

class KlyveMainWindow(QMainWindow):
    """
    The main window for the Klyve desktop application.
    This is the complete, architecturally corrected version.
    """
    STABLE_CHECKPOINT_PHASES = {
        FactoryPhase.IDLE,
        FactoryPhase.BACKLOG_VIEW,
        FactoryPhase.AWAITING_BROWNFIELD_STRATEGY,
        FactoryPhase.PROJECT_INTAKE_ASSESSMENT,
        FactoryPhase.AWAITING_DELIVERY_ASSESSMENT_APPROVAL,
        FactoryPhase.AWAITING_SPEC_REFINEMENT_SUBMISSION,
        FactoryPhase.AWAITING_SPEC_FINAL_APPROVAL,
        FactoryPhase.TECHNICAL_SPECIFICATION,
        FactoryPhase.TEST_ENVIRONMENT_SETUP,
        FactoryPhase.BUILD_SCRIPT_SETUP,
        FactoryPhase.DOCKERIZATION_SETUP,
        FactoryPhase.CODING_STANDARD_GENERATION,
        FactoryPhase.AWAITING_BACKLOG_GATEWAY_DECISION,
        FactoryPhase.PLANNING,
        FactoryPhase.SPRINT_REVIEW,
        FactoryPhase.MANUAL_UI_TESTING,
        FactoryPhase.DEBUG_PM_ESCALATION,
        FactoryPhase.AWAITING_SPRINT_INTEGRATION_TEST_APPROVAL,
        FactoryPhase.AWAITING_INTEGRATION_TEST_RESULT_ACK,
        FactoryPhase.AWAITING_UI_TEST_DECISION
    }
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

        #self._add_permanent_branding()

        self.setWindowTitle(f"Klyve - Autonomous Software Factory")

        self.update_ui_after_state_change()
        self._check_mandatory_settings()
        # Add instance variable for the status widget
        self.persistent_status_widget = None

        # Install event filters to protect the persistent status widget
        self.ui.menubar.installEventFilter(self)
        self.ui.toolBar.installEventFilter(self)
        self.ui.verticalActionBar.installEventFilter(self)

    def eventFilter(self, watched, event):
        # If a persistent status widget is active, intercept and ignore
        # any status tip events from the menu, toolbar, or action bar
        # that would normally clear our message.
        if self.persistent_status_widget and event.type() == QEvent.Type.StatusTip:
            return True # Event is handled and should be ignored

        # For all other events, let them pass through to the default handler.
        return super().eventFilter(watched, event)

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
        self.dockerization_page = DockerizationPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.dockerization_page)
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
        self.sprint_validation_page = SprintValidationPage(self)
        self.ui.mainContentArea.addWidget(self.sprint_validation_page)
        self.sprint_review_page = SprintReviewPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.sprint_review_page)
        self.sprint_history_page = SprintHistoryPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.sprint_history_page)
        self.sprint_integration_test_page = SprintIntegrationTestPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.sprint_integration_test_page)
        self.delivery_assessment_page = DeliveryAssessmentPage(self)
        self.ui.mainContentArea.addWidget(self.delivery_assessment_page)
        self.codebase_analysis_page = CodebaseAnalysisPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.codebase_analysis_page)
        self.project_dashboard_page = ProjectDashboardPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.project_dashboard_page)
        self.intake_assessment_page = IntakeAssessmentPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.intake_assessment_page)

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
        Slot to auto-expand a directory when new items are added, and also
        to expand any newly created subdirectories.
        """
        # Always expand the parent directory where items were just inserted.
        if parent_index.isValid():
            QTimer.singleShot(50, lambda: self.ui.projectFilesTreeView.expand(parent_index))

        # Also, if the new item is itself a directory, expand it as well.
        new_item_index = self.file_system_model.index(first, 0, parent_index)
        if new_item_index.isValid() and self.file_system_model.isDir(new_item_index):
            QTimer.singleShot(100, lambda: self.ui.projectFilesTreeView.expand(new_item_index))

    def _create_menus_and_toolbar(self):
        """Programmatically creates dynamic menus and toolbar actions."""
        # Define the path to the custom icons directory
        icons_path = Path(__file__).parent / "gui" / "icons"

        # Add custom icons to top toolbar actions
        self.ui.actionProceed.setIcon(QIcon(str(icons_path / "proceed.png")))
        # NOTE: The old actionRun_Tests is removed from the toolbar later, so we don't set its icon here.

        # Create QToolButtons with custom icons for the Vertical Action Bar
        self.button_group_sidebar = QButtonGroup(self)
        self.button_group_sidebar.setExclusive(True)

        self.button_view_explorer = QToolButton()
        self.button_view_explorer.setToolTip("Show Project Files")
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
        self.ui.actionNew_Project.setIcon(QIcon(str(icons_path / "new_project.png")))
        self.ui.actionOpen_Project.setIcon(QIcon(str(icons_path / "open_project.png")))
        self.ui.actionSettings.setIcon(QIcon(str(icons_path / "settings.png")))
        self.ui.actionRun_Tests.setIcon(QIcon(str(icons_path / "run_tests.png")))
        self.ui.menuProject.addAction(self.ui.actionManage_CRs_Bugs)
        self.ui.toolBar.addAction(self.ui.actionManage_CRs_Bugs)

        # --- Testing Submenu & Toolbar Button ---
        self.menuTesting = QMenu("Testing", self)
        self.actionRunBackendRegression = QAction("Run Backend Regression Tests", self)
        self.actionRunBackendIntegration = QAction("Run Backend Integration Tests", self)
        self.actionInitiateManualUI = QAction("Initiate Manual UI Testing", self)
        self.actionInitiateAutomatedUI = QAction("Initiate Automated UI Testing", self)

        self.menuTesting.addAction(self.actionRunBackendRegression)
        self.menuTesting.addAction(self.actionRunBackendIntegration)
        self.menuTesting.addSeparator()
        self.menuTesting.addAction(self.actionInitiateManualUI)
        self.menuTesting.addAction(self.actionInitiateAutomatedUI)

        self.ui.menuProject.addMenu(self.menuTesting)
        self.ui.menuProject.addSeparator()

        self.ui.toolBar.removeAction(self.ui.actionRun_Tests) # Remove the old direct action
        self.test_tool_button = QToolButton(self)
        self.test_tool_button.setIcon(QIcon(str(icons_path / "run_tests.png")))
        self.test_tool_button.setToolTip("Run Tests")
        self.test_tool_button.setMenu(self.menuTesting)
        self.test_tool_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.ui.toolBar.addWidget(self.test_tool_button)

        # --- Project Settings Menu Action ---
        self.actionProject_Settings = QAction("Project Settings...", self)
        self.ui.menuProject.addAction(self.actionProject_Settings)

        self.actionView_Sprint_History = QAction("View Sprint History...", self)
        self.ui.menuProject.addAction(self.actionView_Sprint_History)

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

        # Display the initial 'Ready' state on startup
        self.statusBar().showMessage("Ready", 5000)

        # --- EULA Action Definition ---
        self.ui.actionLicense = QAction(QIcon(), "License Agreement", self)
        self.ui.actionLicense.setObjectName("actionLicense")

        # 1. Safely find the Help Menu object using the parent of the About action
        help_menu = self.ui.actionAbout_Klyve.parent()

        # 2. Insert the new License action BEFORE the existing About action
        if isinstance(help_menu, QMenu):
             # This is the safest way to insert: use the existing action as a marker
             help_menu.insertAction(self.ui.actionAbout_Klyve, self.ui.actionLicense)
        # --- END EULA Action Definition ---

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

        # --- View Menu Connections ---
        self.ui.actionToggleProjectPanel.triggered.connect(self.on_view_explorer) # Re-uses existing handler
        self.ui.actionToggleNotificationPanel.triggered.connect(self.on_toggle_notification_panel)

        # Project Menu Actions
        self.ui.actionView_Documents.triggered.connect(self.on_view_documents)
        self.ui.actionView_Reports.triggered.connect(self.on_view_reports)
        self.actionProject_Settings.triggered.connect(self.on_show_project_settings)
        self.actionView_Sprint_History.triggered.connect(self.on_view_sprint_history)

        # Run Menu & Top Toolbar Actions
        self.ui.actionProceed.triggered.connect(self.on_proceed)

        # Testing Actions
        self.actionRunBackendRegression.triggered.connect(self.on_run_backend_regression)
        self.actionRunBackendIntegration.triggered.connect(self.on_run_backend_integration)
        self.actionInitiateManualUI.triggered.connect(self.on_initiate_manual_ui)
        self.actionInitiateAutomatedUI.triggered.connect(self.on_initiate_automated_ui)

        self.ui.actionReport_Bug.triggered.connect(self.on_report_bug)

        # --- Help Menu and License Insertion (Final Clean Version) ---

        # 1. Define the License Action (Must be done in self.ui)
        self.ui.actionLicense = QAction(QIcon(), "License Agreement", self)
        self.ui.actionLicense.setObjectName("actionLicense")

        # 2. Find the Help Menu object by accessing the QMenuBar
        # We iterate over the top-level menu actions to find the correct menu
        help_menu = None
        for action in self.menuBar().actions():
            if action.text() == "&Help" and action.menu():
                help_menu = action.menu()
                break

        # 3. Insert the new License action BEFORE the existing About action
        if help_menu:
            help_menu.insertAction(self.ui.actionAbout_Klyve, self.ui.actionLicense)

        # 4. Connect the actions (Must be done whether or not the insertion worked)
        self.ui.actionLicense.triggered.connect(self._show_license_agreement)
        self.ui.actionAbout_Klyve.triggered.connect(self.on_about)
        # --- END Help Menu Fix ---

        # --- Vertical Action Bar Connections ---
        self.button_view_explorer.clicked.connect(self.on_view_explorer)
        self.button_raise_request.clicked.connect(self.on_raise_cr)
        self.button_view_reports.clicked.connect(self.on_view_reports)
        self.button_view_documents.clicked.connect(self.on_view_documents)
        self.button_view_sprint.clicked.connect(self.on_unified_return_clicked)

        # Connect signals that trigger a FULL UI refresh and page transition
        for page in [self.env_setup_page, self.spec_elaboration_page, self.tech_spec_page, self.build_script_page, self.test_env_page, self.coding_standard_page, self.planning_page, self.genesis_page, self.load_project_page, self.preflight_check_page, self.ux_spec_page]:
            if hasattr(page, 'setup_complete'): page.setup_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'spec_elaboration_complete'): page.spec_elaboration_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'project_cancelled'): page.project_cancelled.connect(self.update_ui_after_state_change)
            if hasattr(page, 'tech_spec_complete'): page.tech_spec_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'build_script_setup_complete'): page.build_script_setup_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'test_env_setup_complete'): page.test_env_setup_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'coding_standard_complete'): page.coding_standard_complete.connect(self.on_coding_standard_complete)
            if hasattr(page, 'planning_complete'): page.planning_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'genesis_complete'): page.genesis_complete.connect(self.update_ui_after_state_change)
            if hasattr(page, 'project_loaded'): page.project_loaded.connect(self.update_ui_after_state_change)
            if hasattr(page, 'project_load_finalized'): page.project_load_finalized.connect(self.update_ui_after_state_change)
            if hasattr(page, 'ux_spec_complete'): page.ux_spec_complete.connect(self.update_ui_after_state_change)

        self.dockerization_page.dockerization_complete.connect(self.update_ui_after_state_change)

        self.codebase_analysis_page.analysis_complete.connect(self.update_ui_after_state_change)
        self.project_dashboard_page.maintain_selected.connect(self.on_brownfield_maintain_selected)
        self.project_dashboard_page.quickfix_selected.connect(self.on_brownfield_quickfix_selected)

        self.intake_assessment_page.full_lifecycle_selected.connect(self.on_intake_full_lifecycle_selected)
        self.intake_assessment_page.direct_to_development_selected.connect(self.on_intake_direct_to_dev_selected)
        self.intake_assessment_page.back_selected.connect(self.on_intake_back_selected)

        # Connect signals that trigger a PARTIAL UI refresh (no page transition)
        for page in [self.spec_elaboration_page, self.tech_spec_page, self.build_script_page, self.test_env_page, self.coding_standard_page, self.planning_page, self.genesis_page]:
            if hasattr(page, 'state_changed'): page.state_changed.connect(self.update_static_ui_elements)

        self.load_project_page.back_to_main.connect(self.on_back_from_load_project)
        self.preflight_check_page.project_load_failed.connect(self.reset_to_idle)
        self.decision_page.option1_selected.connect(self.on_decision_option1)
        self.decision_page.option2_selected.connect(self.on_decision_option2)
        self.decision_page.option3_selected.connect(self.on_decision_option3)
        self.delivery_assessment_page.assessment_approved.connect(self.on_assessment_approved)
        self.delivery_assessment_page.project_cancelled.connect(self.on_close_project)
        self.ui.projectFilesTreeView.customContextMenuRequested.connect(self.on_file_tree_context_menu)
        self.documents_page.back_to_workflow.connect(self.on_back_to_workflow)
        self.reports_page.back_to_workflow.connect(self.on_back_to_workflow)
        self.sprint_history_page.back_to_workflow.connect(self.on_back_to_workflow)
        self.manual_ui_testing_page.go_to_documents.connect(self.on_view_documents)
        self.manual_ui_testing_page.testing_complete.connect(self.update_ui_after_state_change)
        self.project_complete_page.export_project.connect(self.on_stop_export_project)
        self.cr_management_page.delete_cr.connect(self.on_cr_delete_action)
        self.cr_management_page.analyze_cr.connect(self.on_cr_analyze_action)
        self.cr_management_page.implement_cr.connect(self.on_cr_implement_action)
        self.cr_management_page.implement_cr.connect(self.on_cr_implement_action)
        self.cr_management_page.import_from_tool.connect(self.on_import_from_tool)
        self.cr_management_page.sync_items_to_tool.connect(self.on_sync_items_to_tool)
        self.cr_management_page.save_new_order.connect(self.orchestrator.handle_save_cr_order)
        self.cr_management_page.request_ui_refresh.connect(self.update_ui_after_state_change)
        self.ui.actionManage_CRs_Bugs.triggered.connect(self.on_manage_crs)
        self.backlog_ratification_page.backlog_ratified.connect(self.on_backlog_ratified)
        self.sprint_planning_page.sprint_cancelled.connect(self.on_sprint_cancelled)
        self.sprint_planning_page.sprint_started.connect(self.on_start_sprint)
        self.sprint_review_page.return_to_backlog.connect(self.on_return_to_backlog)

        # --- Sprint Integration Test Connections ---
        self.sprint_integration_test_page.run_test_clicked.connect(self.on_sprint_integration_run)
        self.sprint_integration_test_page.skip_clicked.connect(self.on_sprint_integration_skip)
        self.sprint_integration_test_page.pause_clicked.connect(self.on_sprint_integration_pause)

        # --- Sprint Validation Connections ---
        self.sprint_validation_page.proceed_to_planning.connect(self.on_validation_proceed)
        self.sprint_validation_page.return_to_backlog.connect(self.on_validation_cancel)
        self.sprint_validation_page.rerun_stale_analysis.connect(self.on_validation_rerun_stale)

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
        self.menuTesting.setEnabled(is_project_active)
        self.test_tool_button.setEnabled(is_project_active)

        self.status_project_label.setText(f"Project: {project_name}")
        self.status_phase_label.setText(f"Phase: {display_phase_name}")
        self.status_git_label.setText(f"Branch: {git_branch}")
        self.ui.actionClose_Project.setEnabled(is_project_active)
        self.ui.actionArchive_Project.setEnabled(is_project_active)

        # --- Backlog Manager Button & File Tree Logic ---
        project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id) if is_project_active else None

        # Conditionally enable UI testing options
        is_sprint_active = self.orchestrator.is_sprint_active()
        is_gui = is_project_active and bool(project_details and project_details['is_gui_project'] == 1)
        is_auto_ui_configured = is_gui and bool(project_details and project_details['ui_test_execution_command'])

        self.actionInitiateManualUI.setEnabled(is_gui and not is_sprint_active)
        self.actionInitiateAutomatedUI.setEnabled(is_auto_ui_configured and not is_sprint_active)

        if is_sprint_active:
            self.actionInitiateManualUI.setToolTip("Cannot start on-demand testing while a sprint is in progress.")
            self.actionInitiateAutomatedUI.setToolTip("Cannot start on-demand testing while a sprint is in progress.")
        elif not is_gui:
            self.actionInitiateManualUI.setToolTip("This action is only available for GUI projects.")
            self.actionInitiateAutomatedUI.setToolTip("This action is only available for GUI projects.")
        elif not is_auto_ui_configured:
            self.actionInitiateAutomatedUI.setToolTip("Configure the 'Automated UI Test Command' in Project Settings to enable this action.")
        else:
            self.actionInitiateManualUI.setToolTip("Generate a plan for manual UI testing.")
            self.actionInitiateAutomatedUI.setToolTip("Generate and run automated UI tests.")
        project_root = project_details['project_root_folder'] if project_details and project_details['project_root_folder'] else ""

        is_backlog_ready = is_project_active and bool(project_details and project_details['is_backlog_generated'])
        self.ui.actionManage_CRs_Bugs.setEnabled(is_backlog_ready)
        if is_backlog_ready:
            self.ui.actionManage_CRs_Bugs.setToolTip("View and manage the Project Backlog")
        else:
            self.ui.actionManage_CRs_Bugs.setToolTip("The project backlog must be generated before it can be managed.")

        self.button_raise_request.setToolTip("Add a new Backlog Item or Bug Report")

        if project_root and Path(project_root).exists():
            if self.current_tree_root_path != project_root or self.orchestrator.current_phase == FactoryPhase.AWAITING_BROWNFIELD_STRATEGY:
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
            self.treeViewInfoLabel.setText("No active project.\n\nPlease create a new project or open an existing project.")

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

    def _handle_backlog_gen_error(self, error_tuple):
        """Handles the failure of the background backlog generation task."""
        logging.error(f"Brownfield backlog generation failed: {error_tuple[1]}", exc_info=error_tuple)

        QMessageBox.critical(self, "Generation Failed",
                             f"Failed to generate the project backlog:\n{error_tuple[1]}")

        # Reset the orchestrator to the state before generation was attempted
        self.orchestrator.set_phase("AWAITING_BROWNFIELD_STRATEGY")
        self.update_ui_after_state_change()

    def _handle_intake_direct_gen_error(self, error_tuple):
        """Handles the failure of the direct-to-development backlog generation task."""
        logging.error(f"Direct-to-dev backlog generation failed: {error_tuple[1]}", exc_info=error_tuple)

        QMessageBox.critical(self, "Generation Failed",
                             f"Failed to generate the project backlog:\n{error_tuple[1]}")

        # Reset the orchestrator to the state before generation was attempted
        self.orchestrator.set_phase("PROJECT_INTAKE_ASSESSMENT")
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
        self.clear_persistent_status()
        self.orchestrator.set_task_processing_complete()

    def _on_background_task_finished(self):
        """
        A dedicated slot that runs AFTER a background task is completely finished.
        It re-enables the UI, clears the persistent status, and conditionally shows the ready message.
        """
        self.setEnabled(True)
        self.statusBar().clearMessage()
        self.clear_persistent_status()

        # The orchestrator's state is now final.
        self.update_ui_after_state_change()

        # Display 'Ready' only if the final state is a stable user checkpoint.
        if self.orchestrator.current_phase in self.STABLE_CHECKPOINT_PHASES:
            self._show_ready_status()

    def on_coding_standard_complete(self):
        """
        Handles the completion of the coding standard phase by updating
        the orchestrator's state and then refreshing the UI.
        """
        self.orchestrator.handle_coding_standard_complete()
        self.update_ui_after_state_change()

    def on_view_sprint(self):
        """
        Navigates the UI to the active sprint's main page (GenesisPage).
        """
        if self.orchestrator.is_sprint_active():
            # This is the correct phase to show when a sprint is running
            self.orchestrator.set_phase("SPRINT_IN_PROGRESS")
            self.update_ui_after_state_change()
        else:
            # Fallback in case the button was visible by mistake
            logging.warning("on_view_sprint clicked, but no sprint is active.")
            self.orchestrator.set_phase("BACKLOG_VIEW") # Go to a safe place
            self.update_ui_after_state_change()

    def on_return_to_last_phase(self):
        """
        Returns the user to the persistent last_operational_phase checkpoint.
        This handles all non-sprint returns (Specifications, Setup, Backlog).
        """
        return_phase = self.orchestrator.last_operational_phase

        # Guardrail: Only return if the current phase is a viewing phase
        if self.orchestrator.project_id and return_phase != FactoryPhase.IDLE:
            self.orchestrator.set_phase(return_phase.name)
            self.update_ui_after_state_change()
        else:
            # Fallback if no specific checkpoint was saved (e.g., just opened project)
            self.orchestrator.set_phase(FactoryPhase.BACKLOG_VIEW.name)
            self.update_ui_after_state_change()

    def on_unified_return_clicked(self):
        """
        Delegates the return action:
        1. If sprint is active, call the ORIGINAL on_view_sprint (must not be modified).
        2. Otherwise, call the new handler to return to the last general workflow phase.
        """
        if self.orchestrator.is_sprint_active():
            # Delegate to the ORIGINAL, unmodified sprint logic
            self.on_view_sprint()
        else:
            # Delegate to the new general workflow return logic
            self.on_return_to_last_phase()

    def update_ui_after_state_change(self):
        logging.debug("update_ui_after_state_change: Method entered.")
        """
        Performs a full UI refresh. This is the single source of truth for mapping
        the orchestrator's state to the correct UI view.
        """
        # Set of phases where the system is stable and awaiting user action.
        STABLE_CHECKPOINT_PHASES = {
            FactoryPhase.IDLE,
            FactoryPhase.BACKLOG_VIEW,
            FactoryPhase.AWAITING_BROWNFIELD_STRATEGY,
            FactoryPhase.PROJECT_INTAKE_ASSESSMENT,
            FactoryPhase.AWAITING_DELIVERY_ASSESSMENT_APPROVAL,
            FactoryPhase.AWAITING_SPEC_REFINEMENT_SUBMISSION,
            FactoryPhase.AWAITING_SPEC_FINAL_APPROVAL,
            FactoryPhase.TECHNICAL_SPECIFICATION,
            FactoryPhase.AWAITING_TECH_SPEC_RECTIFICATION,
            FactoryPhase.TEST_ENVIRONMENT_SETUP,
            FactoryPhase.BUILD_SCRIPT_SETUP,
            FactoryPhase.DOCKERIZATION_SETUP,
            FactoryPhase.CODING_STANDARD_GENERATION,
            FactoryPhase.AWAITING_BACKLOG_GATEWAY_DECISION,
            FactoryPhase.PLANNING,
            FactoryPhase.SPRINT_REVIEW,
            FactoryPhase.MANUAL_UI_TESTING,
            FactoryPhase.DEBUG_PM_ESCALATION, # System is waiting for PM decision
            FactoryPhase.AWAITING_SPRINT_INTEGRATION_TEST_APPROVAL,
            FactoryPhase.AWAITING_INTEGRATION_TEST_RESULT_ACK,
            # Add other known user checkpoint phases as needed
        }

        self.update_static_ui_elements()

        current_phase = self.orchestrator.current_phase

        # --- SPRINT NAVIGATION AND PROTECTION LOGIC (CORRECTED) ---
        # Use the new reliable method to check the project's persistent state
        # is_sprint_active = self.orchestrator.is_sprint_active()
        # self.button_view_sprint.setVisible(is_sprint_active)

        # The button should only be "checked" if we are actively viewing the sprint page
        # is_viewing_sprint = (current_phase == FactoryPhase.SPRINT_IN_PROGRESS)
        # if is_sprint_active:
        #     self.button_view_sprint.setChecked(is_viewing_sprint)
        # --- END OF NEW LOGIC ---

        # MODIFIED: Control the visibility of the unified Return to Workflow button
        is_project_active = self.orchestrator.project_id is not None
        current_phase = self.orchestrator.current_phase

        # Phases where the button should be visible (i.e., when user is viewing ancillary page)
        is_on_ancillary_page = current_phase in [FactoryPhase.VIEWING_DOCUMENTS, FactoryPhase.VIEWING_REPORTS, FactoryPhase.VIEWING_SPRINT_HISTORY]

        # Check if a non-IDLE operational phase was saved before navigation
        has_return_phase = self.orchestrator.last_operational_phase != FactoryPhase.IDLE

        # The button is visible if the project is active AND we are currently on an ancillary page,
        # AND we have a valid return point saved.
        should_be_visible = is_project_active and is_on_ancillary_page and has_return_phase

        # The button is functionally now the "Return to Workflow" button.
        self.button_view_sprint.setVisible(should_be_visible)
        self.button_view_sprint.setChecked(should_be_visible) # Check/Highlight when visible

        # If visible, update the tooltip to indicate the return phase (helpful for the user)
        if should_be_visible:
             return_phase_name = self.orchestrator.PHASE_DISPLAY_NAMES.get(self.orchestrator.last_operational_phase, 'Workflow')
             self.button_view_sprint.setToolTip(f"Return to Active Task: {return_phase_name}")

        # --- END OF MODIFIED LOGIC ---

        current_phase_name = current_phase.name
        logging.debug(f"update_ui_after_state_change: Detected phase: {current_phase_name}")
        is_project_active = self.orchestrator.project_id is not None

        # This is the new, corrected dictionary
        page_display_map = {
        "ENV_SETUP_TARGET_APP": self.env_setup_page,
        "SPEC_ELABORATION": self.spec_elaboration_page,
        "GENERATING_APP_SPEC_AND_RISK_ANALYSIS": self.spec_elaboration_page,
        "AWAITING_SPEC_REFINEMENT_SUBMISSION": self.spec_elaboration_page,
        "AWAITING_SPEC_FINAL_APPROVAL": self.spec_elaboration_page,
        "TECHNICAL_SPECIFICATION": self.tech_spec_page,
        "AWAITING_TECH_SPEC_GUIDELINES": self.tech_spec_page,
        "AWAITING_TECH_SPEC_RECTIFICATION": self.tech_spec_page,
        "BUILD_SCRIPT_SETUP": self.build_script_page,
        "TEST_ENVIRONMENT_SETUP": self.test_env_page,
        "DOCKERIZATION_SETUP": self.dockerization_page,
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
        "VIEWING_SPRINT_HISTORY": self.sprint_history_page,
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

        if current_phase_name == "ANALYZING_CODEBASE":
            self.show_persistent_status("Analyzing codebase...")
            page_to_show = self.codebase_analysis_page
            if hasattr(page_to_show, 'prepare_for_display'):
                page_to_show.prepare_for_display()
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        elif current_phase_name == "AWAITING_BROWNFIELD_STRATEGY":
            page_to_show = self.project_dashboard_page
            if hasattr(page_to_show, 'prepare_for_display'):
                page_to_show.prepare_for_display()
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        elif current_phase_name == "GENERATING_BACKLOG":
            self.show_persistent_status("Generating project backlog...")
            self.ui.mainContentArea.setCurrentWidget(self.project_dashboard_page) # Stay on the dashboard
            QTimer.singleShot(100, self._task_generate_backlog) # Start task async

        elif current_phase_name in page_display_map:
            page_to_show = page_display_map[current_phase_name]
            if hasattr(page_to_show, 'prepare_for_display'):
                page_to_show.prepare_for_display()
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        elif current_phase_name == "AWAITING_BACKLOG_GATEWAY_DECISION":
            self.decision_page.configure(
                header="Specification Phase Complete",
                instruction="All required project specifications have been finalized. The next major step is to generate the initial project backlog from these documents.",
                option1_text="Generate Project Backlog Now",
                option2_text="Pause Project & Continue Later"
            )
            self.decision_page.option1_selected.connect(self.on_gateway_generate_backlog)
            self.decision_page.option2_selected.connect(self.on_gateway_pause_project)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "PROJECT_INTAKE_ASSESSMENT":
            task_data = self.orchestrator.task_awaiting_approval or {}
            assessment_data = task_data.get("assessment_data", {})
            self.intake_assessment_page.configure(assessment_data)
            self.ui.mainContentArea.setCurrentWidget(self.intake_assessment_page)

        elif current_phase_name == "AWAITING_SPRINT_INTEGRATION_TEST_DECISION":
            # Correctly use the Genesis page for the processing UI
            status_message = "Generating sprint-specific integration test..."
            self.genesis_page.update_processing_display(simple_status_message=status_message)
            self.genesis_page.ui.stackedWidget.setCurrentWidget(self.genesis_page.ui.processingPage)
            self.genesis_page.ui.logOutputTextEdit.clear()
            self.ui.mainContentArea.setCurrentWidget(self.genesis_page)

            # The worker logic remains the same, but we add robust error handling
            worker = Worker(self.orchestrator._run_sprint_integration_test_generation, progress_callback=self.genesis_page.on_progress_update)
            worker.signals.progress.connect(self.genesis_page.on_progress_update)
            worker.signals.result.connect(self.genesis_page._handle_development_result)
            worker.signals.error.connect(self.genesis_page._on_task_error)
            worker.signals.finished.connect(self.genesis_page._on_task_finished)
            self.threadpool.start(worker)

        elif current_phase_name == "AWAITING_INTEGRATION_TEST_RESULT_ACK":
            task_data = self.orchestrator.task_awaiting_approval or {}
            status = task_data.get("sprint_test_status", "UNKNOWN")
            output = task_data.get("sprint_test_output", "No output captured.")

            header = "Integration Test Passed" if status == "SUCCESS" else "Integration Test Failed"
            instruction = "Review the test output below and click 'Continue' to proceed to the next step."

            # Format the output for better readability in the details section
            formatted_output = f"<pre style='color: #FFFFFF; background-color: #333333; padding: 10px; border-radius: 5px;'>{output}</pre>"

            self.decision_page.configure(
                header=header,
                instruction=instruction,
                details=formatted_output,
                option1_text="Continue",
                option2_text=None, # Hide the other buttons
                option3_text=None
            )
            # Connect the button to the new handler in the orchestrator
            self.decision_page.option1_selected.connect(self.on_sprint_test_result_ack)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "AWAITING_SPRINT_INTEGRATION_TEST_APPROVAL":
            page_to_show = self.sprint_integration_test_page
            task_data = self.orchestrator.task_awaiting_approval or {}
            script_path = task_data.get("sprint_integ_script_path", "N/A")
            command = task_data.get("sprint_integ_command", "")
            page_to_show.configure(script_path, command)
            self.ui.mainContentArea.setCurrentWidget(page_to_show)

        elif current_phase_name == "SPRINT_INTEGRATION_TEST_EXECUTION":
            self.genesis_page.update_processing_display(simple_status_message="Running Sprint Integration Test...")
            self.genesis_page.ui.stackedWidget.setCurrentWidget(self.genesis_page.ui.processingPage)
            self.genesis_page.ui.logOutputTextEdit.clear()
            self.ui.mainContentArea.setCurrentWidget(self.genesis_page)

            worker = Worker(self.orchestrator._task_run_sprint_integration_test, progress_callback=self.genesis_page.on_progress_update)
            worker.signals.progress.connect(self.genesis_page.on_progress_update)
            worker.signals.result.connect(self.genesis_page._handle_development_result)
            worker.signals.error.connect(self.genesis_page._on_task_error)
            worker.signals.finished.connect(self._on_background_task_finished)
            self.threadpool.start(worker)

        elif current_phase_name == "AWAITING_UI_TEST_DECISION":
            self.statusBar().clearMessage()
            # Find this entire block and replace it
            project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id)
            is_auto_test_configured = bool(project_details and project_details['ui_test_execution_command'])
            is_gui = bool(project_details and project_details['is_gui_project'] == 1)

            self.decision_page.configure(
                header="Front-end Testing Phase",
                instruction="The automated backend tests passed. Choose how to proceed with Front-end Testing for this sprint.<br><br>Select an option below to continue.",
                details="",
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

        elif current_phase_name == "GENERATING_UX_UI_SPEC_DRAFT":
            status_message = "Generating initial UX/UI specification draft..."

            # Use the correct, non-blocking persistent status message
            self.show_persistent_status(status_message)

            # Use the simpler processing page from the Spec Elaboration screen
            self.spec_elaboration_page.ui.processingLabel.setText(status_message)
            self.spec_elaboration_page.ui.stackedWidget.setCurrentWidget(self.spec_elaboration_page.ui.processingPage)
            self.ui.mainContentArea.setCurrentWidget(self.spec_elaboration_page)

            # The worker now calls the new wrapper method in the orchestrator
            worker = Worker(self.orchestrator._task_generate_ux_spec_draft)
            worker.signals.error.connect(self._on_background_task_error)
            worker.signals.finished.connect(self._on_background_task_finished) # This handler correctly calls clear_persistent_status()
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

        elif current_phase_name == "POST_SPRINT_DOC_UPDATE":
            status_message = "Finalizing sprint: Updating project documents..."
            self.genesis_page.update_processing_display(simple_status_message=status_message)
            self.genesis_page.ui.stackedWidget.setCurrentWidget(self.genesis_page.ui.processingPage)
            self.genesis_page.ui.logOutputTextEdit.clear()
            self.ui.mainContentArea.setCurrentWidget(self.genesis_page)

            worker = Worker(self.orchestrator._run_post_implementation_doc_update)
            worker.signals.progress.connect(self.genesis_page.on_progress_update)
            # When the doc update is done, the orchestrator phase will be BACKLOG_VIEW.
            # The _on_background_task_finished handler will then trigger a UI update,
            # which will correctly show the backlog page.
            worker.signals.error.connect(self.genesis_page._on_task_error)
            worker.signals.finished.connect(self._on_background_task_finished)
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

        elif current_phase_name == "AWAITING_DELIVERY_ASSESSMENT_APPROVAL":
            page_to_show = self.delivery_assessment_page
            task_data = self.orchestrator.task_awaiting_approval or {}

            # The page's logic now handles parsing and display
            page_to_show.populate_data(task_data)
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
                option2_text="Stop & Export Project"
            )
            self.decision_page.option1_selected.connect(self.on_integration_confirmed)
            self.decision_page.option2_selected.connect(self.on_stop_export_project)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "AWAITING_SPRINT_VALIDATION_CHECK":
            self.sprint_validation_page.show_processing()
            self.ui.mainContentArea.setCurrentWidget(self.sprint_validation_page)
            self.setEnabled(False) # Disable main window during processing
            worker = Worker(self.orchestrator._task_run_sprint_validation_checks)
            worker.signals.error.connect(self._on_background_task_error)
            worker.signals.finished.connect(self._on_background_task_finished)
            self.threadpool.start(worker)

        elif current_phase_name == "AWAITING_SPRINT_VALIDATION_APPROVAL":
            task_data = self.orchestrator.task_awaiting_approval or {}
            report_data = task_data.get("sprint_validation_report", {})
            self.sprint_validation_page.populate_report(report_data)
            self.ui.mainContentArea.setCurrentWidget(self.sprint_validation_page)

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
                    option2_text="Stop & Export Project"
                )
                self.decision_page.option1_selected.connect(self.on_retry_environment_failure)
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
                    option3_text="Skip Task & Log as Backlog Item" if not is_phase_failure else None
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
                option2_text="I Will Apply Manually & Skip"
            )
            self.decision_page.option1_selected.connect(self.on_declarative_execute_auto)
            self.decision_page.option2_selected.connect(self.on_declarative_execute_manual)
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)

        elif current_phase_name == "IDLE" or not is_project_active:
            self.ui.mainContentArea.setCurrentWidget(self.ui.welcomePage)
        else:
            self.ui.mainContentArea.setCurrentWidget(self.ui.phasePage)
            self.ui.phaseLabel.setText(f"UI for phase '{current_phase_name}' is not yet implemented.")

        # Check if the final state is a user checkpoint (IDLE or BACKLOG_VIEW)
        if current_phase in STABLE_CHECKPOINT_PHASES:
            self._show_ready_status()
        logging.debug("update_ui_after_state_change: Method finished.")

    def show_persistent_status(self, message: str):
        """Adds or updates a persistent QLabel in the status bar."""
        # Remove the old widget if it exists
        if self.persistent_status_widget:
            self.ui.statusbar.removeWidget(self.persistent_status_widget)
            self.persistent_status_widget.deleteLater()
            self.persistent_status_widget = None

        if message:
            self.persistent_status_widget = QLabel(message)
            self.ui.statusbar.addWidget(self.persistent_status_widget)

    def clear_persistent_status(self):
        """Removes the persistent status widget from the status bar."""
        if self.persistent_status_widget:
            self.ui.statusbar.removeWidget(self.persistent_status_widget)
            self.persistent_status_widget.deleteLater()
            self.persistent_status_widget = None

    def _show_ready_status(self):
        """Displays a transient 'Ready' status message on the status bar."""
        # This uses the default transient message mechanism on the far left.
        self.statusBar().showMessage("Ready", 5000) # Message lasts 5 seconds

    def on_new_project(self):
        """Handles the 'New Project' dialog and routes to the correct workflow."""
        dialog = NewProjectDialog(self)
        if dialog.exec():
            # Check the custom result property we set in the dialog
            if getattr(dialog, 'result', 'spec') == 'codebase':
                project_name, ok = QInputDialog.getText(self, "New Project", "Enter a name for your new project:")
                if ok and project_name:
                    # Pass the acquired name to the brownfield path sequence
                    self.on_start_brownfield_project(project_name)
            else: # Default is to create from spec (greenfield)
                project_name, ok = QInputDialog.getText(self, "New Project", "Enter a name for your new project:")
                if ok and project_name:
                    suggested_path = self.orchestrator.start_new_project(project_name)
                    self._reset_all_pages_for_new_project()
                    self.env_setup_page.prepare_for_greenfield(suggested_path)
                    self.update_ui_after_state_change()

    def on_start_brownfield_project(self, project_name: str): # MODIFIED: Added project_name argument
        """Gets a directory from the user and prepares the EnvSetupPage for the brownfield workflow."""
        repo_path = QFileDialog.getExistingDirectory(self, "Select Existing Project Folder")
        if repo_path:
            # Call the orchestrator method with the user-entered name and the path
            self.orchestrator.start_brownfield_project(project_name, repo_path)
            self._reset_all_pages_for_new_project()
            # This configures the EnvSetupPage for the BROWNFIELD flow
            self.env_setup_page.prepare_for_brownfield(repo_path)
            self.update_ui_after_state_change()

    def on_brownfield_maintain_selected(self):
        """Handles the PM's choice to enter the Maintain & Enhance path."""
        self.previous_phase = self.orchestrator.current_phase
        self.orchestrator.handle_brownfield_maintain_path()
        self.update_ui_after_state_change()

    def on_brownfield_quickfix_selected(self):
        """Handles the PM's choice to enter the Quick Fix path."""
        self.orchestrator.handle_brownfield_quickfix_path()
        # The orchestrator will trigger a dialog, then set the phase,
        # so the UI update is handled after the user provides input.
        self.update_ui_after_state_change()

    def _task_generate_backlog(self):
        """Wrapper to run the orchestrator's backlog generation in a background thread."""
        worker = Worker(self.orchestrator.run_backlog_generation_task)
        # When the worker is done, it will have set the phase to BACKLOG_VIEW,
        # so we just need to trigger a UI refresh.
        worker.signals.finished.connect(self.update_ui_after_state_change)
        worker.signals.finished.connect(self.clear_persistent_status)
        worker.signals.error.connect(self._handle_backlog_gen_error)
        self.threadpool.start(worker)

    def on_open_project(self):
        """Handles the new 'Open Project' action to show recent/active projects."""
        self.orchestrator.set_phase("VIEWING_ACTIVE_PROJECTS")
        self.update_ui_after_state_change()

    def on_load_project(self):
        """Handles the 'Import Exported Project' action."""
        self.orchestrator.set_phase("VIEWING_PROJECT_HISTORY")
        self.update_ui_after_state_change()

    def on_close_project(self):
        """Handles the new 'Close Project' action which now auto-pauses."""
        logging.debug("!!! on_close_project in main_window was triggered !!!")
        self.orchestrator.close_and_save_project()
        self.update_ui_after_state_change()

    def on_assessment_approved(self):
        """
        Handles the PM's approval of the delivery assessment and proceeds.
        This is now asynchronous to allow for .docx generation.
        """
        self.setEnabled(False)
        self.show_persistent_status("Finalizing assessment and saving report...")

        worker = Worker(self.orchestrator.handle_risk_assessment_approval)
        worker.signals.error.connect(self._on_background_task_error)
        # Connect to the existing finished handler, which will re-enable
        # the UI and call update_ui_after_state_change.
        worker.signals.finished.connect(self._on_background_task_finished)
        self.threadpool.start(worker)

    # def on_risk_assessment_approved(self):
    #    """Handles the PM's approval of the risk assessment and proceeds."""
    #    self.orchestrator.handle_risk_assessment_approval()
    #    self.update_ui_after_state_change()

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

        if dialog.exec():
            # This block runs after the user clicks "Save" and the dialog closes.
            self._check_mandatory_settings()
            self.update_ui_after_state_change()

            if getattr(dialog, 'provider_changed', False):
                reply = QMessageBox.question(self, "Confirm LLM Change",
                                            "Changing the LLM provider requires a connection test and may trigger auto-calibration. This could yield unpredictable results in ongoing projects. Proceed?",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                            QMessageBox.StandardButton.Yes)

                if reply == QMessageBox.StandardButton.Yes:
                    self.setEnabled(False) # Disable main window
                    worker = Worker(self._task_connect_and_calibrate)
                    worker.signals.progress.connect(self._on_calibration_progress)
                    worker.signals.result.connect(self._handle_calibration_complete)
                    worker.signals.error.connect(self._on_background_task_error)
                    worker.signals.finished.connect(self._on_calibration_finished)
                    self.threadpool.start(worker)

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

    def get_app_version(self):
        """Helper method to retrieve the application version (Placeholder)."""
        # NOTE: This should eventually read from a central config file.
        return "1.0 Beta"

    def _show_license_agreement(self):
        """
        Displays the content of the EULA/License Agreement from an external file.
        """
        try:
            eula_file = Path(__file__).parent / "EULA.txt"
            if not eula_file.exists():
                 eula_file = Path(__file__).parent / "data" / "EULA.txt"

            if not eula_file.exists():
                text = "The License Agreement file (EULA.txt) was not found. Please ensure it is in the application directory."
                QMessageBox.warning(self, "License File Not Found", text)
                return
            else:
                with open(eula_file, 'r', encoding='utf-8') as f:
                    text = f.read()

            # Use a QMessageBox with Detailed Text area for the full license body
            msg = QMessageBox(self)
            msg.setWindowTitle("Klyve License Agreement")
            msg.setText("Please review the full terms of service:")
            msg.setInformativeText("By using Klyve, you agree to the terms below.")
            msg.setDetailedText(text)
            msg.setIcon(QMessageBox.Information)
            msg.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error Loading License", f"Could not load license file: {e}")

    def on_about(self):
        """Displays the 'About Klyve' dialog with branding, version, and copyright info."""

        version = self.get_app_version()

        # Use high-contrast colors suitable for the dark dialog background (#2A2A2B)
        about_html = f"""
        <html>
        <head>
            <style>
                /* Dialog Text Colors: Inverted for Dark Mode */
                body {{ color: #F0F0F0; }} /* Sets all default text to bright white */
                h3 {{ margin-bottom: 8px; color: #007ACC; font-weight: bold; }} /* Bright blue for the main heading */
                p {{ margin: 0 0 5px 0; }}
                .version {{ font-weight: bold; color: #FFC66D; }} /* Soft amber/yellow for version number */
                .corevalue {{ margin-top: 15px; margin-bottom: 15px; color: #CCCCCC; }} /* Core value label */
            </style>
        </head>
        <body>
            <center>
                <h3>KLYVE: Your Expertise. Scaled.</h3>

                <p>The Orchestrated Software Development Assistant</p><br>
                <p class="version">Version: {version}</p>

                <!-- <p class="corevalue">Your implementation partner in software development.</p> -->
                <hr style="border-top: 1px solid #4A4A4A;">

                <p style="font-size: 10pt;">&copy; 2025 Mario J. Lewis. All Rights Reserved.</p>
                <p style="font-size: 8pt; color: #888888;">Protected by the Klyve License Agreement (EULA).</p>
            </center>
        </body>
        </html>
        """

        # Use a custom QMessageBox instance to assign an objectName for surgical QSS targeting.
        msg = QMessageBox(self)
        msg.setWindowTitle("About Klyve")
        msg.setText(about_html)

        # Set a unique objectName for surgical QSS styling
        msg.setObjectName("aboutKlyveDialog")

        # The icon type must be explicitly set to Information or NoIcon to ensure the title bar icon appears.
        # We use NoIcon to prevent the native icon type from overriding the app icon.
        msg.setIcon(QMessageBox.NoIcon)

        msg.exec()


    def on_back_to_workflow(self):
        """Returns the UI to the previously active workflow phase."""
        if self.orchestrator.project_id and self.previous_phase:
            self.orchestrator.set_phase(self.previous_phase.name)
            self.update_ui_after_state_change()

    def on_back_from_load_project(self):
        self.reset_to_idle()

    def on_debug_jump_to_phase(self, phase_name: str):
        self.orchestrator.debug_jump_to_phase(phase_name)
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
        worker.signals.finished.connect(self.genesis_page._on_task_finished)
        self.threadpool.start(worker)

    def on_retry_environment_failure(self):
        """
        Handles the "Retry" button click ONLY from an Environment Failure page.
        This method re-runs the original task, NOT the automated-fix logic.
        """
        if not self.orchestrator.task_awaiting_approval:
            logging.warning("Retry (Env) clicked, but no failure context found.")
            return

        # Set UI to busy state and transition to the Genesis processing view
        self.setEnabled(False)
        self.statusBar().showMessage("Re-running the last failed task...")
        self.orchestrator.set_phase("GENESIS")
        self.update_ui_after_state_change()

        # Switch the Genesis page to its processing view
        self.genesis_page.ui.stackedWidget.setCurrentWidget(self.genesis_page.ui.processingPage)
        self.genesis_page.ui.logOutputTextEdit.clear()

        # Start the background worker to re-run handle_proceed_action
        worker = Worker(self.orchestrator.handle_proceed_action)
        worker.signals.progress.connect(self.genesis_page.on_progress_update)
        worker.signals.result.connect(self.genesis_page._handle_development_result)
        worker.signals.error.connect(self.genesis_page._on_task_error)
        worker.signals.finished.connect(self._on_background_task_finished)
        worker.signals.finished.connect(self.genesis_page._on_task_finished)
        self.threadpool.start(worker)

    def on_decision_option2(self):
        """
        Handles the "Pause for Manual Fix" decision.
        This method now checks for an IDE path and, if present,
        launches a background worker to get file paths from the
        stack trace before launching the IDE.
        """
        try:
            ide_path = self.orchestrator.db_manager.get_config_value("IDE_EXECUTABLE_PATH")

            if ide_path and ide_path.strip() and self.orchestrator.task_awaiting_approval:
                failure_log = self.orchestrator.task_awaiting_approval.get("failure_log", "")

                if failure_log:
                    logging.info(f"IDE path is set. Starting worker to parse stack trace for: {ide_path}")
                    self.statusBar().showMessage("Parsing stack trace for IDE...")

                    # --- BEGIN NON-BLOCKING LOGIC ---
                    # Pass necessary data to the worker
                    worker = Worker(
                        self.orchestrator.get_files_from_stack_trace,
                        failure_log=failure_log
                    )

                    # Pass ide_path and project_root to the result handler via lambda
                    project_root = self.orchestrator.project_root_path
                    worker.signals.result.connect(
                        lambda file_list: self._on_ide_launch_ready(file_list, ide_path, project_root)
                    )

                    # Connect error signal for graceful failure
                    worker.signals.error.connect(self._on_ide_launch_error)

                    # Start the worker thread
                    self.threadpool.start(worker)
                    # --- END NON-BLOCKING LOGIC ---

                    # Note: We DO NOT call the pause logic here.
                    # The worker's result handler (_on_ide_launch_ready)
                    # is now responsible for calling the pause logic
                    # *after* the IDE is launched.
                    return

                else:
                    logging.warning("IDE path is set, but no failure log was found in context. Proceeding to pause.")

            else:
                logging.info("No IDE path set or no task awaiting approval. Proceeding with standard pause.")
        except Exception as e:
            # This is a safeguard for the launch *setup* logic.
            logging.error(f"Failed to initiate IDE launch: {e}", exc_info=True)
            QMessageBox.warning(self, "IDE Launch Failed", f"Could not initiate IDE launch. Proceeding to pause.\nError: {e}")

        # --- FALLBACK ---
        # If any of the IDE launch conditions fail,
        # just run the original pause logic immediately.
        self.orchestrator.handle_pm_debug_choice("MANUAL_PAUSE")
        self.update_ui_after_state_change()

    def _on_ide_launch_ready(self, file_list: list[str], ide_path: str, project_root: str):
        """
        Slot to receive file list from the background worker.
        This method runs on the main UI thread and is safe to
        launch the IDE and update the UI.
        """
        logging.info(f"Worker finished. Received {len(file_list)} files. Launching IDE.")

        try:
            command = [ide_path]

            # Add all found absolute file paths
            for f in file_list:
                safe_f = f.strip().replace("\"", "")
                abs_path = Path(project_root) / safe_f
                if abs_path.exists():
                    command.append(str(abs_path))

            # Fallback: if no files found, just open the project root
            if len(command) == 1:
                command.append(str(project_root))

            subprocess.Popen(command)
            logging.info(f"Launched IDE with command: {command}")

        except Exception as e:
            logging.error(f"Failed to launch IDE subprocess: {e}", exc_info=True)
            QMessageBox.warning(self, "IDE Launch Failed", f"Could not launch the configured IDE. Proceeding to pause.\nError: {e}")
        # --- FINAL STEP ---
        # Now that the IDE is launched (or failed to launch),
        # we proceed with the original pause logic.
        self.orchestrator.handle_pm_debug_choice("MANUAL_PAUSE")
        self.update_ui_after_state_change()

    def _on_ide_launch_error(self, error_tuple):
        """
        Slot to handle errors from the stack trace parsing worker.
        """
        exctype, value, traceback_str = error_tuple
        logging.error(f"Worker failed to parse stack trace: {value}\n{traceback_str}")
        QMessageBox.warning(self, "IDE Launch Failed", f"Could not parse stack trace for IDE. Proceeding to pause.\nError: {value}")

        # Fallback to standard pause
        self.orchestrator.handle_pm_debug_choice("MANUAL_PAUSE")
        self.update_ui_after_state_change()

    def on_decision_option3(self):
        self.orchestrator.handle_pm_debug_choice("SKIP_TASK_AND_LOG")
        self.update_ui_after_state_change()

    def on_decision_acknowledge_failures(self):
        """Handles the PM's choice to complete the sprint with acknowledged failures."""
        self.orchestrator.handle_complete_with_failures()
        self.update_ui_after_state_change()

    def on_sprint_integration_run(self, command: str):
        """Handles the user's choice to run the sprint integration test."""
        self.orchestrator.handle_sprint_integration_test_decision("RUN", command)
        self.update_ui_after_state_change()

    def on_sprint_integration_skip(self):
        """Handles the user's choice to skip the sprint integration test."""
        self.orchestrator.handle_sprint_integration_test_decision("SKIP")
        self.update_ui_after_state_change()

    def on_sprint_integration_pause(self):
        """Handles the user's choice to pause for manual review."""
        self.orchestrator.handle_sprint_integration_test_decision("PAUSE")
        # The orchestrator will save state and reset, so we trigger a UI update to reflect the idle state.
        self.update_ui_after_state_change()

    def on_sprint_test_result_ack(self):
        """Handles the user clicking 'Continue' on the test results page."""
        self.orchestrator.handle_sprint_test_result_ack()
        self.update_ui_after_state_change()

    def on_gateway_generate_backlog(self):
        """
        Handles the user's choice to generate the project backlog, now
        intelligently routing to the correct orchestrator method based on
        whether the project is Greenfield or Brownfield.
        """
        self.setEnabled(False)
        self.statusBar().showMessage("Generating project backlog from specifications...")

        # Determine which workflow to call by checking for existing code artifacts
        is_brownfield = False
        try:
            artifacts = self.orchestrator.db_manager.get_all_artifacts_for_project(self.orchestrator.project_id)
            if any(art['artifact_type'] == 'EXISTING_CODE' for art in artifacts):
                is_brownfield = True
        except Exception as e:
            logging.error(f"Failed to check project type, defaulting to Greenfield. Error: {e}")

        if is_brownfield:
            logging.info("Routing backlog generation to BROWNFIELD method: run_backlog_generation_task")
            # --- This is the Brownfield path ---
            worker = Worker(self.orchestrator.run_backlog_generation_task)
            # Connect to the robust error handler we created
            worker.signals.error.connect(self._handle_backlog_gen_error)
        else:
            logging.info("Routing backlog generation to GREENFIELD method: handle_backlog_generation")
            # --- This is the Greenfield path ---
            worker = Worker(self.orchestrator.handle_backlog_generation)
            # Connect to the robust error handler we created
            worker.signals.error.connect(self._handle_intake_direct_gen_error)

        # The finished signal is the same for both
        worker.signals.finished.connect(self._on_background_task_finished)
        self.threadpool.start(worker)

    def on_gateway_pause_project(self):
        """Handles the user's choice to pause the project at the gateway."""
        self.orchestrator.pause_project()
        self.update_ui_after_state_change()

    def on_intake_full_lifecycle_selected(self):
        """Handles the PM's choice to proceed with the full spec elaboration lifecycle."""
        status_message = "Processing specifications for full lifecycle..."
        self.setEnabled(False)
        self.show_persistent_status(status_message)

        worker = Worker(self.orchestrator.handle_intake_assessment_decision, "FULL_LIFECYCLE")
        worker.signals.error.connect(self._on_background_task_error)
        worker.signals.finished.connect(self._on_background_task_finished)
        self.threadpool.start(worker)

    def on_intake_direct_to_dev_selected(self):
        """Handles the PM's choice to proceed directly to backlog generation."""
        status_message = "Processing specifications for direct development..."
        self.show_persistent_status(status_message)

        worker = Worker(self.orchestrator.handle_intake_assessment_decision, "DIRECT_TO_DEVELOPMENT")
        worker.signals.error.connect(self._handle_intake_direct_gen_error)
        worker.signals.finished.connect(self._on_background_task_finished)
        self.threadpool.start(worker)

    def on_intake_back_selected(self):
        """Handles the user clicking 'Back' on the assessment page, returning to the brief submission page."""
        self.orchestrator.set_phase("SPEC_ELABORATION")
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

    def on_validation_proceed(self):
        """Handles the user's choice to proceed after a successful validation check."""
        self.orchestrator.handle_sprint_validation_decision("PROCEED")
        self.update_ui_after_state_change()

    def on_validation_cancel(self):
        """Handles the user's choice to cancel the sprint after validation."""
        self.orchestrator.handle_sprint_validation_decision("CANCEL")
        self.update_ui_after_state_change()

    def on_validation_rerun_stale(self, stale_item_ids: list):
        """Handles re-running analysis for stale items in a background thread."""
        self.setEnabled(False)
        self.statusBar().showMessage(f"Re-running analysis for {len(stale_item_ids)} stale item(s)...")

        worker = Worker(self.orchestrator.rerun_stale_sprint_analysis, stale_item_ids)
        worker.signals.error.connect(self._on_background_task_error)
        worker.signals.finished.connect(self._on_background_task_finished)
        self.threadpool.start(worker)

    def on_return_to_backlog(self):
        """
        Handles the signal to complete a sprint review. It now conditionally
        runs the doc update worker only if the sprint contained change requests.
        """
        try:
            # This part now returns a boolean flag
            needs_doc_update = self.orchestrator.handle_sprint_review_complete()

            if needs_doc_update:
                logging.info("Sprint contained Change Requests. Running post-sprint document update...")
                # Show the processing page and run the doc update in the background.
                status_message = "Finalizing sprint: Updating project documents..."
                self.genesis_page.update_processing_display(simple_status_message=status_message)
                self.genesis_page.ui.stackedWidget.setCurrentWidget(self.genesis_page.ui.processingPage)
                self.genesis_page.ui.logOutputTextEdit.clear()
                self.ui.mainContentArea.setCurrentWidget(self.genesis_page)

                worker = Worker(self.orchestrator.run_doc_update_and_finalize_sprint)
                worker.signals.progress.connect(self.genesis_page.on_progress_update)
                worker.signals.error.connect(self.genesis_page._on_task_error)
                worker.signals.finished.connect(self._on_background_task_finished)
                self.threadpool.start(worker)
            else:
                logging.info("Sprint contained no Change Requests. Skipping document update.")
                # No doc update needed. Clean up state and go directly to backlog.
                self.orchestrator.run_doc_update_and_finalize_sprint(skip_doc_update=True)
                self.update_ui_after_state_change() # Go directly to backlog

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to finalize sprint statuses:\n{e}")
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

    def on_run_backend_regression(self):
        """Runs the backend regression test suite."""
        self._run_test_suite("regression", "Running backend regression test suite...")

    def on_run_backend_integration(self):
        """Runs the backend integration test suite."""
        self._run_test_suite("integration", "Running backend integration test suite...")

    def on_initiate_manual_ui(self):
        """Initiates the on-demand manual UI testing workflow."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please load a project to run tests.")
            return

        # The orchestrator now performs the check and returns a status
        success = self.orchestrator.initiate_on_demand_manual_testing()

        if success:
            self.update_ui_after_state_change()
        else:
            QMessageBox.information(self, "Action Not Available",
                                    "Cannot initiate UI testing because no code has been generated for this project yet. "
                                    "Please complete at least one development sprint first.")

    def on_initiate_automated_ui(self):
        """Placeholder for initiating automated UI testing."""
        QMessageBox.information(self, "Not Implemented", "On-demand automated UI testing will be implemented in a future update.")

    def _run_test_suite(self, test_type: str, status_message: str):
        """Generic helper to run a test suite in a background thread."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to run tests.")
            return

        db = self.orchestrator.db_manager
        project_details = db.get_project_by_id(self.orchestrator.project_id)
        command_key = "integration_test_command" if test_type == "integration" else "test_execution_command"
        command = project_details[command_key]

        if not command:
            QMessageBox.warning(self, "Not Configured", f"The command for '{test_type}' tests is not configured in Project Settings.")
            return

        self.setEnabled(False)
        self.statusBar().showMessage(status_message)

        worker = Worker(self.orchestrator.run_full_test_suite, test_type=test_type)
        worker.signals.result.connect(self._handle_test_run_result)
        worker.signals.error.connect(self._handle_test_run_error)
        worker.signals.finished.connect(self._on_background_task_finished) # Use the existing robust handler
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

    def _on_calibration_progress(self, progress_data):
        """Updates the main window's status bar with progress from the worker."""
        if isinstance(progress_data, tuple) and len(progress_data) == 2:
            status, message = progress_data
            self.statusBar().showMessage(message)

    def _on_calibration_finished(self):
        """Re-enables the main window and clears the status bar."""
        self.setEnabled(True)
        self.statusBar().clearMessage()

    def _task_connect_and_calibrate(self, **kwargs):
        """Background worker task for connection test and calibration."""
        progress_callback = kwargs.get('progress_callback')
        # Step 1: Connection Test
        progress_callback(("INFO", "Attempting to connect to the new LLM provider..."))
        self.orchestrator._llm_service = None
        try:
            _ = self.orchestrator.llm_service
            progress_callback(("SUCCESS", "Connection successful. Starting auto-calibration..."))
        except Exception as e:
            return ("CONNECTION_FAILURE", str(e))

        # Step 2: Auto-Calibration
        success, message = self.orchestrator.run_auto_calibration(progress_callback=progress_callback)
        if success:
            return ("SUCCESS", message)
        else:
            return ("CALIBRATION_FAILURE", message)

    def _handle_calibration_complete(self, result_tuple):
        """Handles the final result of the calibration worker."""
        self.setEnabled(True)
        status, message = result_tuple
        if status == "SUCCESS":
            QMessageBox.information(self, "Success", f"Auto-calibration complete. Context limit has been set to {int(message):,} characters.")
        elif status == "CONNECTION_FAILURE":
            QMessageBox.critical(self, "Connection Failed", f"Failed to connect to the new LLM provider. Please check your settings.\n\nDetails: {message}")
        elif status == "CALIBRATION_FAILURE":
            QMessageBox.warning(self, "Calibration Failed", f"Connection succeeded, but auto-calibration failed:\n{message}")
        # Refresh settings data in case the user re-opens the dialog
        self._check_mandatory_settings()

    def _task_connect_and_calibrate(self, **kwargs):
        """Background worker task for connection test and calibration."""
        progress_callback = kwargs.get('progress_callback')
        # Step 1: Connection Test
        progress_callback(("INFO", "Attempting to connect to the new LLM provider..."))
        self.orchestrator._llm_service = None
        try:
            _ = self.orchestrator.llm_service
            progress_callback(("SUCCESS", "Connection successful. Starting auto-calibration..."))
        except Exception as e:
            return ("CONNECTION_FAILURE", str(e))

        # Step 2: Auto-Calibration
        success, message = self.orchestrator.run_auto_calibration(progress_callback=progress_callback)
        if success:
            return ("SUCCESS", message)
        else:
            return ("CALIBRATION_FAILURE", message)

    def _on_calibration_progress(self, progress_data):
        """Updates the main window's status bar with progress from the worker."""
        if isinstance(progress_data, tuple) and len(progress_data) == 2:
            status, message = progress_data
            self.statusBar().showMessage(message)

    def _handle_calibration_complete(self, result_tuple):
        """Handles the final result of the calibration worker."""
        self.setEnabled(True)
        status, message = result_tuple
        if status == "SUCCESS":
            QMessageBox.information(self, "Success", f"Auto-calibration complete. Context limit has been set to {int(message):,} characters.")
        elif status == "CONNECTION_FAILURE":
            QMessageBox.critical(self, "Connection Failed", f"Failed to connect to the new LLM provider. Please check your settings.\n\nDetails: {message}")
        elif status == "CALIBRATION_FAILURE":
            QMessageBox.warning(self, "Calibration Failed", f"Connection succeeded, but auto-calibration failed:\n{message}")
        # Refresh the settings dialog's data in case the user re-opens it
        self._check_mandatory_settings()

    def on_raise_cr(self):
        """
        Delegates the action to the CR Management page, but only if a project
        and ratified backlog are active. Otherwise, shows a warning.
        """
        # First, we must get the project's current state.
        is_project_active = self.orchestrator.project_id is not None
        project_details = self.orchestrator.db_manager.get_project_by_id(self.orchestrator.project_id) if is_project_active else None

        # Use the same 'is_backlog_ready' logic as the menu item.
        is_backlog_ready = is_project_active and bool(project_details and project_details['is_backlog_generated'])

        if is_backlog_ready:
            # If ready, proceed to open the dialog.
            self.cr_management_page.on_add_item_clicked()
        else:
            # If not ready, show the informative message box.
            QMessageBox.warning(self, "Action Not Available",
                                "A project must be open and have a ratified backlog before new items can be added.")

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
        # self.previous_phase = self.orchestrator.current_phase
        # MODIFIED: Store current phase in orchestrator's new persistent property
        self.orchestrator.last_operational_phase = self.orchestrator.current_phase
        self.orchestrator.set_phase("VIEWING_DOCUMENTS")
        self.update_ui_after_state_change()

    def on_view_reports(self):
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please create or load a project to view its reports.")
            return
        # self.previous_phase = self.orchestrator.current_phase
        # MODIFIED: Store current phase in orchestrator's new persistent property
        self.orchestrator.last_operational_phase = self.orchestrator.current_phase
        self.orchestrator.set_phase("VIEWING_REPORTS")
        self.update_ui_after_state_change()

    def on_view_sprint_history(self):
        """Switches to the Sprint History page."""
        if not self.orchestrator.project_id:
            QMessageBox.warning(self, "No Project", "Please load a project to view its sprint history.")
            return

        # self.previous_phase = self.orchestrator.current_phase
        # MODIFIED: Store current phase in orchestrator's new persistent property
        self.orchestrator.last_operational_phase = self.orchestrator.current_phase
        self.orchestrator.set_phase("VIEWING_SPRINT_HISTORY")
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
            created_keys = "\n".join([f"- {item['external_key']} (Klyve ID: {item['id']})" for item in synced_items])
            details += f"Successfully Created Issues:\n{created_keys}\n\n"

        if errors:
            detailed_errors = "\n".join([f"- Item ID {e['id']}: {e['reason']}" for e in errors])
            details += f"Failure Details:\n{detailed_errors}"

        if details:
            msg_box.setDetailedText(details.strip())

        QTimer.singleShot(100, lambda: msg_box.exec())

