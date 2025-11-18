# main.py

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
import logging

from klyve_db_manager import KlyveDBManager
from master_orchestrator import MasterOrchestrator
from main_window import KlyveMainWindow

def initialize_database(db_manager: KlyveDBManager):
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
        "GROK_API_KEY": ("", "API Key for Grok."),
        "GROK_REASONING_MODEL": ("llama3-70b-8192", "Default reasoning model for Grok."),
        "GROK_FAST_MODEL": ("llama3-8b-8192", "Default fast model for Grok."),
        "DEEPSEEK_API_KEY": ("", "API Key for Deepseek."),
        "DEEPSEEK_REASONING_MODEL": ("deepseek-chat", "Default reasoning model for Deepseek."),
        "DEEPSEEK_FAST_MODEL": ("deepseek-coder", "Default fast model for Deepseek."),
        "LLAMA_API_KEY": ("", "API Key for Llama (via Replicate)."),
        "LLAMA_REASONING_MODEL": ("meta/meta-llama-3-70b-instruct", "Default reasoning model for Llama."),
        "LLAMA_FAST_MODEL": ("meta/meta-llama-3-8b-instruct", "Default fast model for Llama."),
        "MAX_DEBUG_ATTEMPTS": ("2", "Max automated fix attempts before escalating to the PM."),
        "CONTEXT_WINDOW_CHAR_LIMIT": ("2500000", "Max characters for complex analysis context."),
        "LOGGING_LEVEL": ("Standard", "Verbosity of Klyve's internal logs."),
        "DEFAULT_PROJECT_PATH": ("", "Default parent directory for new target projects."),
        "DEFAULT_ARCHIVE_PATH": ("", "Default folder for saving project exports."),
        "SELECTED_DOCX_STYLE_PATH": ("data/templates/styles/default_docx_template.docx", "Path to the .docx file used for styling exported documents."),
        "GEMINI_CONTEXT_LIMIT": ("2500000", "Default context limit for Gemini."),
        "OPENAI_CONTEXT_LIMIT": ("380000", "Default context limit for OpenAI."),
        "ANTHROPIC_CONTEXT_LIMIT": ("600000", "Default context limit for Anthropic."),
        "LOCALPHI3_CONTEXT_LIMIT": ("380000", "Default context limit for local Phi-3."),
        "ENTERPRISE_CONTEXT_LIMIT": ("128000", "Default context limit for enterprise models."),
        "GROK_CONTEXT_LIMIT": ("256000", "Default context limit for Grok models."),
        "DEEPSEEK_CONTEXT_LIMIT": ("16384", "Default context limit for Deepseek models."),
        "LLAMA_CONTEXT_LIMIT": ("8000", "Default context limit for Llama models."),
        "INTEGRATION_PROVIDER": ("None", "The selected external project management tool provider."),
        "INTEGRATION_URL": ("", "The base URL for the external tool's API."),
        "INTEGRATION_USERNAME": ("", "The username or email for the integration account."),
        "INTEGRATION_API_TOKEN": ("", "The API token for the integration account."),
        "IDE_EXECUTABLE_PATH": ("", "The absolute path to the developer's IDE executable (e.g., code.cmd, pycharm64.exe)."),
    }

    all_config = db_manager.get_all_config_values()
    for key, (value, desc) in defaults.items():
        if key not in all_config:
            db_manager.set_config_value(key, value, desc)
            logging.info(f"Initialized missing config key '{key}' with default value.")

if __name__ == "__main__":
    # Import traceback for logging fatal errors
    import traceback

    try:
        QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)
        app = QApplication(sys.argv)

        # --- 1. Setup Application Assets (Icon & Splash) ---
        # (Uncomment and ensure these files exist before enabling)
        # icon_path = Path(__file__).parent / "gui" / "icons" / "asdf_logo.ico"
        # if icon_path.exists():
        #     app.setWindowIcon(QIcon(str(icon_path)))

        # --- 2. Setup Database ---
        db_dir = Path("data")
        db_dir.mkdir(exist_ok=True)
        db_path = db_dir / "klyve.db"

        # Initialize DB Manager
        # (Note: Add your Dev Mode/Security logic here later when ready)
        db_manager = KlyveDBManager(db_path=str(db_path))
        initialize_database(db_manager)

        # --- 3. Setup Logging ---
        log_level_str = db_manager.get_config_value("LOGGING_LEVEL") or "Standard"
        log_level_map = {"Standard": logging.INFO, "Detailed": logging.DEBUG, "Debug": logging.DEBUG}
        log_level = log_level_map.get(log_level_str, logging.INFO)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s',
            force=True
        )
        logging.info(f"Klyve started. Logging level: '{log_level_str}'")

        # --- 4. Initialize Core Components ---
        orchestrator = MasterOrchestrator(db_manager=db_manager)
        window = KlyveMainWindow(orchestrator=orchestrator)

        # --- 5. Robust Stylesheet Loading ---
        try:
            style_file = Path(__file__).parent / "gui" / "style.qss"
            if style_file.exists():
                with open(style_file, "r") as f:
                    app.setStyleSheet(f.read())
                    logging.info("Successfully loaded global stylesheet.")
            else:
                logging.warning(f"Stylesheet not found at: {style_file}")
        except Exception as e:
            logging.error(f"Failed to load stylesheet: {e}")
            # We continue without style rather than crashing

        # --- 6. Launch ---
        window.showMaximized()
        sys.exit(app.exec())

    except Exception as e:
        # --- FATAL ERROR HANDLER ---
        # If anything above fails, log it and show a popup to the user.
        error_msg = f"A critical error occurred causing Klyve to shut down.\n\nError: {e}"
        logging.critical("CRITICAL STARTUP FAILURE", exc_info=True)

        # We need a temporary app instance to show the message box if the main one failed
        if not QApplication.instance():
            temp_app = QApplication(sys.argv)

        QMessageBox.critical(None, "Critical Startup Error", error_msg)
        sys.exit(1)