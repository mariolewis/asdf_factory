# main_window.py

import logging
from pathlib import Path
from datetime import datetime
import os
import subprocess
import sys

from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QStackedWidget,
                               QInputDialog, QMessageBox, QFileSystemModel, QMenu)
from PySide6.QtGui import QAction
from PySide6.QtCore import QFile, Signal, Qt, QDir

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


class ASDFMainWindow(QMainWindow):
    """
    The main window for the ASDF desktop application.
    This is the complete, architecturally corrected version.
    """
    def __init__(self, orchestrator: MasterOrchestrator):
        super().__init__()
        self.orchestrator = orchestrator
        self.last_known_phase = None

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._create_pages()
        self._setup_file_tree()
        self._create_menus_and_toolbar()
        self._connect_signals()

        # This is the final step, ensures the UI starts in a clean, correct state
        self.update_ui()

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

    def _setup_file_tree(self):
        """Initializes the file system model and view."""
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setFilter(QDir.NoDotAndDotDot | QDir.AllEntries)
        self.ui.projectFilesTreeView.setModel(self.file_system_model)

        self.ui.projectFilesTreeView.hideColumn(1)
        self.ui.projectFilesTreeView.hideColumn(2)
        self.ui.projectFilesTreeView.hideColumn(3)
        self.ui.projectFilesTreeView.setHeaderHidden(True)
        self.ui.projectFilesTreeView.setContextMenuPolicy(Qt.CustomContextMenu)

    def _create_menus_and_toolbar(self):
        """Programmatically creates dynamic menus."""
        for phase in FactoryPhase:
            if phase.name == "IDLE": continue
            action = QAction(phase.name.replace("_", " ").title(), self)
            action.triggered.connect(lambda checked=False, p=phase.name: self.on_debug_jump_to_phase(p))
            self.ui.menuDebug.addAction(action)

        # --- Create Status Bar Widgets ---
        self.status_project_label = QLabel("Project: N/A")
        self.status_phase_label = QLabel("Phase: Idle")
        self.status_git_label = QLabel("Branch: N/A")
        self.ui.statusbar.addPermanentWidget(self.status_project_label)
        self.ui.statusbar.addPermanentWidget(self.status_phase_label)
        self.ui.statusbar.addPermanentWidget(self.status_git_label)

    def _connect_signals(self):
        """Connects all UI signals to their corresponding slots."""
        # Main Menu
        self.ui.actionNew_Project.triggered.connect(self.on_new_project)
        self.ui.actionLoad_Archived_Project.triggered.connect(self.on_load_project)
        self.ui.actionClose_Project.triggered.connect(self.on_close_project)
        self.ui.actionStop_Export_Project.triggered.connect(self.on_stop_export_project)
        self.ui.actionSettings.triggered.connect(self.show_settings_dialog)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionAbout_ASDF.triggered.connect(self.on_about)

        # Toolbar & Other Menu Actions
        self.ui.actionProceed.triggered.connect(self.on_proceed)
        self.ui.actionRun_Tests.triggered.connect(self.on_run_tests)
        self.ui.actionRaise_CR.triggered.connect(self.on_raise_cr)
        self.ui.actionReport_Bug.triggered.connect(self.on_report_bug)
        self.ui.actionView_Documents.triggered.connect(self.on_view_documents)
        self.ui.actionView_Reports.triggered.connect(self.on_view_reports)

        # Page Signals that trigger a full UI refresh
        self.load_project_page.project_loaded.connect(self.update_ui)
        self.load_project_page.back_to_main.connect(self.on_back_from_load_project)
        self.preflight_check_page.project_load_finalized.connect(self.update_ui)
        self.preflight_check_page.project_load_failed.connect(self.reset_to_idle)

        # --- THIS BLOCK WAS MISSING ---
        # Connect completion signals from pages that transition the phase
        self.env_setup_page.setup_complete.connect(self.update_ui)
        self.spec_elaboration_page.spec_elaboration_complete.connect(self.update_ui)
        self.tech_spec_page.tech_spec_complete.connect(self.update_ui)
        self.build_script_page.build_script_setup_complete.connect(self.update_ui)
        self.test_env_page.test_env_setup_complete.connect(self.update_ui)
        self.coding_standard_page.coding_standard_complete.connect(self.update_ui)
        self.planning_page.planning_complete.connect(self.update_ui)
        self.genesis_page.genesis_complete.connect(self.update_ui)

        # Connect state change signals from pages that perform background tasks
        for page in [self.spec_elaboration_page, self.tech_spec_page, self.build_script_page,
                     self.test_env_page, self.coding_standard_page, self.planning_page, self.genesis_page]:
            page.state_changed.connect(self.update_ui)
        # --- END OF MISSING BLOCK ---

        # Decision Page
        self.decision_page.option1_selected.connect(self.on_decision_option1)
        self.decision_page.option2_selected.connect(self.on_decision_option2)
        self.decision_page.option3_selected.connect(self.on_decision_option3)

        # File Tree
        self.ui.projectFilesTreeView.customContextMenuRequested.connect(self.on_file_tree_context_menu)

    def update_ui(self):
        """
        The single source of truth for synchronizing the entire UI with the
        orchestrator's current state.
        """
        current_phase = self.orchestrator.current_phase
        current_phase_name = current_phase.name

        # 1. Update Status Bar
        project_name = self.orchestrator.project_name or "N/A"
        display_phase_name = self.orchestrator.PHASE_DISPLAY_NAMES.get(current_phase, current_phase_name)
        git_branch = self.orchestrator.get_current_git_branch()
        self.status_project_label.setText(f"Project: {project_name}")
        self.status_phase_label.setText(f"Phase: {display_phase_name}")
        self.status_git_label.setText(f"Branch: {git_branch}")

        # 2. Update Menu Item States
        is_project_active = self.orchestrator.project_id is not None
        is_project_dirty = self.orchestrator.is_project_dirty
        self.ui.actionNew_Project.setEnabled(True)
        self.ui.actionLoad_Archived_Project.setEnabled(True)
        self.ui.actionClose_Project.setEnabled(is_project_active and not is_project_dirty)
        self.ui.actionStop_Export_Project.setEnabled(is_project_active) # Enabled whenever a project is active

        # 3. Update File Tree View
        project_root = ""
        if is_project_active:
            with self.orchestrator.db_manager as db:
                project_details = db.get_project_by_id(self.orchestrator.project_id)
                if project_details and project_details['project_root_folder']:
                    project_root = project_details['project_root_folder']
        self.file_system_model.setRootPath(project_root)
        self.ui.projectFilesTreeView.setRootIndex(self.file_system_model.index(project_root))

        # 4. Handle Phase Transitions (Resetting pages)
        if current_phase != self.last_known_phase:
            logging.info(f"Phase transition detected: {self.last_known_phase} -> {current_phase}")
            page_reset_map = { "ENV_SETUP_TARGET_APP": self.env_setup_page, "SPEC_ELABORATION": self.spec_elaboration_page, "TECHNICAL_SPECIFICATION": self.tech_spec_page, "BUILD_SCRIPT_SETUP": self.build_script_page, "TEST_ENVIRONMENT_SETUP": self.test_env_page, "CODING_STANDARD_GENERATION": self.coding_standard_page, "PLANNING": self.planning_page, "GENESIS": self.genesis_page, }
            if current_phase_name in page_reset_map:
                page_reset_map[current_phase_name].prepare_for_new_project()
            self.last_known_phase = current_phase

        # 5. Switch to the Correct Page
        page_display_map = { "ENV_SETUP_TARGET_APP": self.env_setup_page, "SPEC_ELABORATION": self.spec_elaboration_page, "TECHNICAL_SPECIFICATION": self.tech_spec_page, "BUILD_SCRIPT_SETUP": self.build_script_page, "TEST_ENVIRONMENT_SETUP": self.test_env_page, "CODING_STANDARD_GENERATION": self.coding_standard_page, "PLANNING": self.planning_page, "GENESIS": self.genesis_page, "VIEWING_PROJECT_HISTORY": self.load_project_page, "AWAITING_PREFLIGHT_RESOLUTION": self.preflight_check_page, }

        if current_phase_name in page_display_map:
            if current_phase_name == "VIEWING_PROJECT_HISTORY": self.load_project_page.refresh_projects_list()
            if current_phase_name == "AWAITING_PREFLIGHT_RESOLUTION": self.preflight_check_page.update_and_display()
            self.ui.mainContentArea.setCurrentWidget(page_display_map[current_phase_name])
        elif current_phase_name in ["DEBUG_PM_ESCALATION", "AWAITING_PM_TRIAGE_INPUT"]:
            # Handle decision pages
            context = self.orchestrator.task_awaiting_approval or {}
            if current_phase_name == "DEBUG_PM_ESCALATION": self.decision_page.configure(header="Debug Escalation", instruction="The factory has been unable to automatically fix a persistent bug.", details=context.get("failure_log", ""), option1_text="Retry Automated Fix", option2_text="Pause for Manual Fix", option3_text="Ignore Bug & Proceed")
            else: self.decision_page.configure(header="Interactive Triage", instruction="The automated triage system could not determine the root cause.", details=context.get("failure_log", ""), option1_text="Retry with Manual Input", option2_text="Cancel and Return")
            self.ui.mainContentArea.setCurrentWidget(self.decision_page)
        elif not is_project_active:
            self.ui.mainContentArea.setCurrentWidget(self.ui.welcomePage)
        else:
            self.ui.mainContentArea.setCurrentWidget(self.ui.phasePage)
            self.ui.phaseLabel.setText(f"UI for phase '{current_phase_name}' is not yet implemented.")

    # --- Action Handlers / Slots ---

    def on_new_project(self):
        """Handles the File -> New Project action."""
        if self.orchestrator.project_id:
            reply = QMessageBox.question(self, "Active Project", "An active project exists. Do you want to stop and export it before starting a new one?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes: self.on_stop_export_project()
            elif reply == QMessageBox.Cancel: return

        project_name, ok = QInputDialog.getText(self, "New Project", "Enter a name for your new project:")
        if ok and project_name:
            self.orchestrator.start_new_project(project_name)
            self.update_ui()

    def on_load_project(self):
        """Handles the File -> Load Archived Project action."""
        if self.orchestrator.project_id:
            reply = QMessageBox.question(self, "Active Project", "An active project exists. Do you want to stop and export it before loading another?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes: self.on_stop_export_project()
            elif reply == QMessageBox.Cancel: return

        self.orchestrator.set_phase("VIEWING_PROJECT_HISTORY")
        self.update_ui()

    def on_close_project(self):
        self.orchestrator.close_active_project()
        self.update_ui()

    def on_stop_export_project(self):
        if not self.orchestrator.project_id: return
        default_name = f"{self.orchestrator.project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        archive_name, ok = QInputDialog.getText(self, "Stop & Export Project", "Enter a name for the archive file:", text=default_name)
        if ok and archive_name:
            archive_path = self.orchestrator.stop_and_export_project("data/archives", archive_name)
            if archive_path: QMessageBox.information(self, "Success", f"Project archived to:\n{archive_path}")
            else: QMessageBox.critical(self, "Error", "Failed to export project.")
            self.update_ui()

    def reset_to_idle(self):
        self.orchestrator.reset()
        self.update_ui()

    def show_settings_dialog(self):
        dialog = SettingsDialog(self.orchestrator, self)
        dialog.populate_fields()
        dialog.exec()
        self.update_ui()

    def on_about(self):
        QMessageBox.about(self, "About ASDF", "<h3>Autonomous Software Development Factory (ASDF)</h3><p>Version 0.8 (PySide6 Migration)</p><p>This application uses AI to assist in the end-to-end creation of software.</p>")

    def on_back_from_load_project(self):
        self.orchestrator.set_phase("IDLE")
        self.update_ui()

    def on_debug_jump_to_phase(self, phase_name: str):
        self.orchestrator._debug_jump_to_phase(phase_name)
        self.update_ui()

    def on_decision_option1(self):
        if self.orchestrator.current_phase.name == "DEBUG_PM_ESCALATION": self.orchestrator.handle_pm_debug_choice("RETRY")
        elif self.orchestrator.current_phase.name == "AWAITING_PM_TRIAGE_INPUT": QMessageBox.information(self, "In Progress", "Interactive triage input is not yet implemented.")
        self.update_ui()

    def on_decision_option2(self):
        if self.orchestrator.current_phase.name == "DEBUG_PM_ESCALATION": self.orchestrator.handle_pm_debug_choice("MANUAL_PAUSE")
        elif self.orchestrator.current_phase.name == "AWAITING_PM_TRIAGE_INPUT": self.orchestrator.set_phase("GENESIS")
        self.update_ui()

    def on_decision_option3(self):
        if self.orchestrator.current_phase.name == "DEBUG_PM_ESCALATION": self.orchestrator.handle_pm_debug_choice("IGNORE")
        self.update_ui()

    def on_proceed(self): QMessageBox.information(self, "Not Implemented", "The 'Proceed' action is not yet implemented.")
    def on_run_tests(self): QMessageBox.information(self, "Not Implemented", "The 'Run Tests' action is not yet implemented.")
    def on_raise_cr(self): QMessageBox.information(self, "Not Implemented", "The 'Raise CR' action is not yet implemented.")
    def on_report_bug(self): QMessageBox.information(self, "Not Implemented", "The 'Report Bug' action is not yet implemented.")
    def on_view_documents(self): QMessageBox.information(self, "Not Implemented", "The 'View Documents' action is not yet implemented.")
    def on_view_reports(self): QMessageBox.information(self, "Not Implemented", "The 'View Reports' action is not yet implemented.")

    def on_file_tree_context_menu(self, point):
        index = self.ui.projectFilesTreeView.indexAt(point)
        if not index.isValid() or self.file_system_model.isDir(index): return

        file_path = self.file_system_model.filePath(index)
        menu = QMenu(self)
        open_action = menu.addAction("Open File")
        open_action.triggered.connect(lambda: self.on_open_file_in_tree(file_path))
        menu.exec(self.ui.projectFilesTreeView.viewport().mapToGlobal(point))

    def on_open_file_in_tree(self, file_path):
        logging.info(f"Request to open file: {file_path}")
        try:
            if sys.platform == "win32": os.startfile(file_path)
            elif sys.platform == "darwin": subprocess.run(["open", file_path], check=True)
            else: subprocess.run(["xdg-open", file_path], check=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")