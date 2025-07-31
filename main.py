import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtGui import QAction
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
import logging

# Import the backend and the compiled UI for the settings page
from master_orchestrator import MasterOrchestrator
from gui.ui_settings_page import Ui_SettingsPage


def on_settings_clicked():
    """
    Creates, populates, and shows the settings dialog.
    """
    logging.info("MENU CLICK: 'Settings...' menu item was clicked.")

    # Create a new, empty dialog window as a container
    dialog = QDialog(window)

    # Create an instance of our compiled UI from ui_settings_page.py
    ui_settings = Ui_SettingsPage()

    # Use setupUi to populate our empty dialog with the widgets and layouts
    ui_settings.setupUi(dialog)

    # We will add the logic to populate and save the fields in the next step.
    # For now, we just show the dialog.
    dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- Backend Initialization ---
    db_dir = Path("data")
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "asdf.db"
    orchestrator = MasterOrchestrator(db_path=str(db_path))

    # --- Centralized Logging Configuration ---
    with orchestrator.db_manager as db:
        log_level_str = db.get_config_value("LOGGING_LEVEL") or "Standard"
    log_level_map = {"Standard": logging.INFO, "Detailed": logging.DEBUG, "Debug": logging.DEBUG}
    log_level = log_level_map.get(log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s',
        force=True
    )
    logging.info(f"Logging level set to '{log_level_str}'.")

    # --- UI Loading ---
    ui_file_path = Path(__file__).parent / "gui" / "main_window.ui"
    ui_file = QFile(ui_file_path)
    if not ui_file.open(QFile.ReadOnly):
        logging.error(f"Cannot open UI file: {ui_file.errorString()}")
        sys.exit(-1)

    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()

    if not window:
        logging.error(f"Failed to load UI file: {loader.errorString()}")
        sys.exit(-1)

    window.orchestrator = orchestrator

    # --- Connect Signals ---
    window.findChild(QAction, "actionSettings").triggered.connect(on_settings_clicked)
    # Other connections can be added here as needed
    window.findChild(QAction, "actionExit").triggered.connect(window.close)

    window.show()
    sys.exit(app.exec())