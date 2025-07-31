import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
import logging

from master_orchestrator import MasterOrchestrator
from main_window import ASDFMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    db_dir = Path("data")
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "asdf.db"
    orchestrator = MasterOrchestrator(db_path=str(db_path))

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

    window = ASDFMainWindow(orchestrator=orchestrator)
    window.show()

    sys.exit(app.exec())