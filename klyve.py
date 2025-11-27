# main.py

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen, QDialog
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QTimer
import logging
from datetime import datetime, timezone

# Import the new config module
import config
from klyve_db_manager import KlyveDBManager
from master_orchestrator import MasterOrchestrator
from main_window import KlyveMainWindow
from gui.legal_dialog import LegalDialog

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

def _setup_logging(db_manager):
    """
    Configures logging based on the operating mode.
    User Mode: No logging (NullHandler).
    Dev Mode: Console logging ONLY (No file).
    """
    # 1. Reset any existing logging configuration
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    # 2. Configure based on mode
    if config.is_dev_mode():
        # Dev Mode: Console Output Only
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        log_level_str = db_manager.get_config_value("LOGGING_LEVEL") or "Standard"
        log_level_map = {"Standard": logging.INFO, "Detailed": logging.DEBUG, "Debug": logging.DEBUG}
        log_level = log_level_map.get(log_level_str, logging.INFO)

        logging.basicConfig(level=log_level, handlers=[console_handler], force=True)
        print(f"--- KLYVE DEV MODE ACTIVE (Console Logging Enabled: {log_level_str}) ---")
    else:
        # User Mode: Strict Silence
        # We use NullHandler to prevent "No handlers could be found" warnings from libraries
        logging.basicConfig(level=logging.CRITICAL, handlers=[logging.NullHandler()], force=True)
        logging.disable(logging.CRITICAL)

def _initialize_klyve(app, splash):
    try:
        # --- 0. Prevent Premature Exit ---
        app.setQuitOnLastWindowClosed(False)

        # --- 1. Setup Database Paths ---
        db_dir = Path("data")
        db_dir.mkdir(exist_ok=True)
        db_path = db_dir / "klyve.db"

        # Initialize DB Manager (needed to read config for logging)
        db_manager = KlyveDBManager(db_path=str(db_path))

        # --- 2. Setup Logging ---
        _setup_logging(db_manager)

        # --- 3. Initialize Database Content ---
        initialize_database(db_manager)

        # --- 4. Robust Stylesheet Loading ---
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

        # --- 5. Legal Guardrail (EULA Check) ---
        if not db_manager.get_config_value("EULA_ACCEPTED_TIMESTAMP"):
            logging.info("EULA not yet accepted. Showing Legal Dialog.")
            if splash and splash.isVisible():
                splash.hide()

            legal_dialog = LegalDialog()
            result = legal_dialog.exec()

            if result != QDialog.Accepted:
                logging.info("User declined EULA or closed dialog. Exiting application.")
                sys.exit(0)

            acceptance_time = datetime.now(timezone.utc).isoformat()
            db_manager.set_config_value("EULA_ACCEPTED_TIMESTAMP", acceptance_time, "Timestamp of EULA acceptance.")

            if splash:
                splash.show()

        # --- 6. Initialize Core Components ---
        orchestrator = MasterOrchestrator(db_manager=db_manager)
        # FIX: Attach window to 'app' to prevent Garbage Collection from deleting it
        # when this function ends.
        app._main_window = KlyveMainWindow(orchestrator=orchestrator)
        window = app._main_window

        # --- 7. Launch ---
        window.showMaximized()
        app.setQuitOnLastWindowClosed(True)

        if splash and splash.isVisible():
            QTimer.singleShot(0, lambda: splash.finish(window))

    except Exception as e:
        # CRITICAL SAFETY NET
        error_msg = f"Initialization Failure:\n{str(e)}"

        # Only dump stack trace to console if in Dev Mode
        if config.is_dev_mode():
            logging.disable(logging.NOTSET)
            logging.error(error_msg, exc_info=True)

        if splash and splash.isVisible():
            splash.hide()
        QMessageBox.critical(None, "Critical Startup Error", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    import traceback

    try:
        QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)
        app = QApplication(sys.argv)

        # --- 1. Setup Application Assets ---
        assets_dir = Path(__file__).parent / "gui"
        icon_path = assets_dir / "icons" / "klyve_logo.ico"
        splash_path = assets_dir / "images" / "splash_screen.png"

        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))

        splash = None
        if splash_path.exists():
            try:
                splash_pix = QPixmap(str(splash_path))
                splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
                splash.show()
                app.processEvents()
            except Exception as e:
                print(f"Failed to load splash screen: {e}")

        # Start initialization after a brief delay to allow splash to render
        QTimer.singleShot(3000, lambda: _initialize_klyve(app, splash))

        sys.exit(app.exec())

    except Exception as e:
        # Only print to console if in Dev Mode
        if config.is_dev_mode():
            print(f"CRITICAL STARTUP FAILURE: {e}")
            traceback.print_exc()

        if not QApplication.instance():
            temp_app = QApplication(sys.argv)

        QMessageBox.critical(None, "Critical Startup Error", f"A critical error occurred:\n{e}")
        sys.exit(1)