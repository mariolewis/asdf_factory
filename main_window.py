# main_window.py

import logging
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QStackedWidget, QInputDialog, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader

from master_orchestrator import MasterOrchestrator
from gui.settings_dialog import SettingsDialog
from gui.env_setup_page import EnvSetupPage


class ASDFMainWindow(QMainWindow):
    """
    The main window for the ASDF desktop application.
    Manages all the different pages (views) of the application.
    """
    def __init__(self, orchestrator: MasterOrchestrator):
        super().__init__()
        self.orchestrator = orchestrator

        # Load the main window UI from its compiled file
        self.load_main_ui()

        # Find key container widgets from the loaded UI
        self.main_content_area = self.findChild(QStackedWidget, "mainContentArea")
        self.welcome_page = self.findChild(QWidget, "welcomePage")

        # Create instances of other pages/dialogs
        self.settings_page = SettingsDialog(self.orchestrator, self) # This is now a dialog

        # Create an instance of the environment setup page
        self.env_setup_page = EnvSetupPage(self.orchestrator, self)
        self.ui.mainContentArea.addWidget(self.env_setup_page)

        self.connect_signals()
        self.update_ui_from_state()

    def load_main_ui(self):
        ui_file_path = Path(__file__).parent / "gui" / "main_window.ui"
        ui_file = QFile(ui_file_path)
        if not ui_file.open(QFile.ReadOnly):
            raise RuntimeError(f"Cannot open main UI file: {ui_file_path}")
        loader = QUiLoader()
        # This is a critical step: QUiLoader.load returns the window.
        # But we are in the window's own class. Instead, we must load it
        # and set its contents as our own. A common pattern is to load a QWidget
        # as the central widget. Our .ui file's root is a QMainWindow, which is the issue.
        #
        # CORRECTED FINAL APPROACH: We compile the UI and use setupUi.
        # This requires a compiled main_window UI file.
        from gui.ui_main_window import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


    def connect_signals(self):
        """Connects UI element signals to Python methods."""
        # The compiled UI makes widgets direct attributes of self.ui
        self.ui.actionSettings.triggered.connect(self.show_settings_dialog)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionNew_Project.triggered.connect(self.on_new_project)
        self.env_setup_page.setup_complete.connect(self.update_ui_from_state)

    def on_new_project(self):
        """Handles the File -> New Project action with a check for duplicate names."""
        project_name, ok = QInputDialog.getText(self, "New Project", "Enter a name for your new project:")
        if ok and project_name:
            # Check if a project with this name already exists in the archives
            name_exists_in_history = False
            with self.orchestrator.db_manager as db:
                if db.get_project_history_by_name(project_name):
                    name_exists_in_history = True

            # Also check against the currently active project name
            is_active_project_name = (self.orchestrator.project_id is not None and self.orchestrator.project_name == project_name)

            if name_exists_in_history or is_active_project_name:
                reply = QMessageBox.warning(
                    self,
                    "Duplicate Project Name",
                    f"A project named '{project_name}' already exists.\n\n"
                    "Are you sure you want to create a new project with the same name?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return  # Abort the action

            # If no duplicate or user confirmed, proceed
            logging.info(f"Starting new project with name: {project_name}")
            self.orchestrator.start_new_project(project_name)
            self.update_ui_from_state()

    def show_settings_dialog(self):
        """Creates and shows the settings dialog."""
        logging.info("Navigating to Settings page.")
        # Re-populate fields each time it's opened to ensure they are current
        self.settings_page.populate_fields()
        self.settings_page.exec() # Show as a modal dialog
        # After dialog closes, update main UI in case settings changed
        self.update_ui_from_state()

    def update_ui_from_state(self):
        """Updates the entire UI based on the orchestrator's current state."""
        current_phase_name = self.orchestrator.current_phase.name
        logging.info(f"Updating UI for phase: {current_phase_name}")

        if not self.orchestrator.project_id:
            self.ui.mainContentArea.setCurrentWidget(self.ui.welcomePage)
            return

        # --- Phase-based Page Switching ---
        if current_phase_name == "ENV_SETUP_TARGET_APP":
            self.ui.mainContentArea.setCurrentWidget(self.env_setup_page)
        else:
            # Fallback to a placeholder page for now
            self.ui.mainContentArea.setCurrentWidget(self.ui.phasePage)
            self.ui.phaseLabel.setText(f"UI for phase '{current_phase_name}' is not yet implemented.")