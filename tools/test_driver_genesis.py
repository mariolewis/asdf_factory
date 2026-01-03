import sys
import logging
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QThreadPool
from unittest.mock import MagicMock

# Import the page you want to test
from gui.genesis_page import GenesisPage

# Setup basic logging
logging.basicConfig(level=logging.INFO)

def main():
    app = QApplication(sys.argv)

    # --- 1. Create a Fake Main Window ---
    # In the real app, GenesisPage lives inside a MainWindow.
    # We must simulate this so self.window().statusBar() works.
    main_window = QMainWindow()
    main_window.setWindowTitle("Driver Test: Genesis Page Host")
    main_window.resize(1000, 700)

    # Initialize the status bar (normally done by .ui file or setupUi)
    main_window.statusBar().showMessage("Ready")

    # --- 2. Mock the Orchestrator ---
    mock_orchestrator = MagicMock()
    mock_orchestrator.active_plan = "Test Plan"
    mock_orchestrator.is_task_processing = False

    # Set to False to test "Normal" (1-button) mode
    # Set to True to test "Manual Fix" (3-button) mode
    mock_orchestrator.is_resuming_from_manual_fix = False

    mock_orchestrator.get_sprint_goal.return_value = "Test the EU AI Act Warning Dialog"

    mock_orchestrator.get_current_task_details.return_value = {
        "task": {"component_name": "Test Component A", "micro_spec_id": 123},
        "cursor": 0,
        "total": 5,
        "is_fix_mode": False,
        "confidence_score": 85
    }

    # --- 3. Instantiate the Page ---
    # We pass the mock orchestrator as before
    page = GenesisPage(orchestrator=mock_orchestrator)

    # Fix 1: Add threadpool to avoid crash on button click
    page.threadpool = QThreadPool()

    # Fix 2: Add page to the Main Window so self.window() finds the parent
    main_window.setCentralWidget(page)

    # --- 4. Prepare and Show ---
    page.prepare_for_display()
    main_window.show()

    print("Driver running.")
    print(f"Mode: {'Manual Fix (3-Buttons)' if mock_orchestrator.is_resuming_from_manual_fix else 'Normal (1-Button)'}")
    print("Click 'Proceed'. Expected behavior: Popup appears -> Click Yes -> 'Developing task...' appears in Status Bar.")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()