# main.py

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
import logging

from asdf_db_manager import ASDFDBManager
from master_orchestrator import MasterOrchestrator
from main_window import ASDFMainWindow

def initialize_database(db_manager: ASDFDBManager):
    """
    Ensures the database is created and populated with all necessary defaults.
    """
    logging.info("Initializing and verifying database...")
    db_manager.create_tables()

    defaults = {
        "SELECTED_LLM_PROVIDER": ("Gemini", "The currently active LLM provider."),
        "GEMINI_API_KEY": ("", "API Key for Google Gemini."),
        "GEMINI_REASONING_MODEL": ("gemini-2.5-pro", "The sophisticated model for complex tasks."),
        "GEMINI_FAST_MODEL": ("gemini-2.5-flash-preview-05-20", "The faster model for simpler tasks."),
        "OPENAI_API_KEY": ("", "API Key for OpenAI/ChatGPT."),
        "OPENAI_REASONING_MODEL": ("gpt-4-turbo", "Default reasoning model for OpenAI."),
        "OPENAI_FAST_MODEL": ("gpt-3.5-turbo", "Default fast model for OpenAI."),
        "ANTHROPIC_API_KEY": ("", "API Key for Anthropic Claude."),
        "ANTHROPIC_REASONING_MODEL": ("claude-3-opus-20240229", "Default reasoning model for Anthropic."),
        "ANTHROPIC_FAST_MODEL": ("claude-3-haiku-20240307", "Default fast model for Anthropic."),
        "CUSTOM_ENDPOINT_URL": ("", "Endpoint URL for custom/enterprise LLMs."),
        "CUSTOM_ENDPOINT_API_KEY": ("", "API Key for custom/enterprise LLMs."),
        "CUSTOM_REASONING_MODEL": ("", "Reasoning model name for custom endpoint."),
        "CUSTOM_FAST_MODEL": ("", "Fast model name for custom endpoint."),
        "MAX_DEBUG_ATTEMPTS": ("2", "Max automated fix attempts before escalating to the PM."),
        "CONTEXT_WINDOW_CHAR_LIMIT": ("2500000", "Max characters for complex analysis context."),
        "LOGGING_LEVEL": ("Standard", "Verbosity of ASDF's internal logs."),
        "DEFAULT_PROJECT_PATH": ("", "Default parent directory for new target projects."),
        "DEFAULT_ARCHIVE_PATH": ("", "Default folder for saving project exports."),
        "GEMINI_CONTEXT_LIMIT": ("2500000", "Default context limit for Gemini."),
        "OPENAI_CONTEXT_LIMIT": ("380000", "Default context limit for OpenAI."),
        "ANTHROPIC_CONTEXT_LIMIT": ("600000", "Default context limit for Anthropic."),
        "LOCALPHI3_CONTEXT_LIMIT": ("380000", "Default context limit for local Phi-3."),
        "ENTERPRISE_CONTEXT_LIMIT": ("128000", "Default context limit for enterprise models."),
        "INTEGRATION_PROVIDER": ("None", "The selected external project management tool provider."),
        "INTEGRATION_URL": ("", "The base URL for the external tool's API."),
        "INTEGRATION_USERNAME": ("", "The username or email for the integration account."),
        "INTEGRATION_API_TOKEN": ("", "The API token for the integration account.")
    }

    all_config = db_manager.get_all_config_values()
    for key, (value, desc) in defaults.items():
        if key not in all_config:
            db_manager.set_config_value(key, value, desc)
            logging.info(f"Initialized missing config key '{key}' with default value.")

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)
    app = QApplication(sys.argv)
    db_dir = Path("data")
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / "asdf.db"

    db_manager = ASDFDBManager(db_path=str(db_path))
    initialize_database(db_manager)

    log_level_str = db_manager.get_config_value("LOGGING_LEVEL") or "Standard"
    log_level_map = {"Standard": logging.INFO, "Detailed": logging.DEBUG, "Debug": logging.DEBUG}
    log_level = log_level_map.get(log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s',
        force=True
    )
    logging.info(f"Logging level set to '{log_level_str}'.")

    orchestrator = MasterOrchestrator(db_manager=db_manager)
    window = ASDFMainWindow(orchestrator=orchestrator)

    # --- Robust Stylesheet Loading ---
    try:
        style_file = Path(__file__).parent / "gui" / "style.qss"
        if not style_file.exists():
            raise FileNotFoundError(f"Stylesheet not found at: {style_file}")

        with open(style_file, "r") as f:
            app.setStyleSheet(f.read())
            logging.info("Successfully loaded global stylesheet.")

    except Exception as e:
        error_msg = f"Fatal Error: Could not load the stylesheet 'gui/style.qss'.\nThe application cannot continue.\n\nDetails: {e}"
        logging.critical(error_msg)
        QMessageBox.critical(None, "Stylesheet Load Error", error_msg)
        sys.exit(1) # Exit if the stylesheet fails to load

    window.showMaximized()
    sys.exit(app.exec())