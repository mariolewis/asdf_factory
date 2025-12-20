# main.py

import sys
import os
import platform
import ctypes
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen, QDialog, QWidget, QStyle
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
from gui.utils import center_window

# =========================================================================
# GLOBAL FIX: Monkey Patch QMessageBox for Linux Centering
# =========================================================================
# CHANGE: We check if we are on Linux. If NOT, we skip this entire block.
if sys.platform == "linux":
    def _create_screen_anchor():
        """
        Creates an invisible, full-screen widget to act as a parent.
        This tricks Wayland into centering child dialogs (Splash/EULA)
        perfectly on the screen.
        """
        anchor = QWidget()
        anchor.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        anchor.setAttribute(Qt.WA_TranslucentBackground)

        # Force it to cover the primary screen
        screen = QApplication.primaryScreen()
        if screen:
            anchor.setGeometry(screen.geometry())

        anchor.showFullScreen()
        return anchor

    def _resolve_parent(parent):
        # 1. Use provided parent
        if parent and isinstance(parent, QWidget):
            return parent
        # 2. Use Main Window attached to App (Best for Runtime)
        app = QApplication.instance()
        if app and hasattr(app, '_main_window') and app._main_window:
            return app._main_window
        # 3. Fallback
        return QApplication.activeWindow()

    def _center_msg_box(msg, parent):
        msg.adjustSize()
        def do_center():
            target = _resolve_parent(parent)
            if target:
                child_geo = msg.frameGeometry()
                child_geo.moveCenter(target.frameGeometry().center())
                msg.move(child_geo.topLeft())
            else:
                screen = msg.screen() or QApplication.primaryScreen()
                if screen:
                    child_geo = msg.frameGeometry()
                    child_geo.moveCenter(screen.availableGeometry().center())
                    msg.move(child_geo.topLeft())
        QTimer.singleShot(0, do_center)

    def _patched_message_box(icon, parent, title, text, buttons=QMessageBox.Ok, default=QMessageBox.NoButton):
        real_parent = _resolve_parent(parent)
        msg = QMessageBox(real_parent) # Parented to Main Window
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(buttons)
        msg.setDefaultButton(default)
        _center_msg_box(msg, real_parent)
        return msg.exec()

    # Wrappers
    def _patched_information(parent, title, text, buttons=QMessageBox.Ok, default=QMessageBox.NoButton):
        return _patched_message_box(QMessageBox.Information, parent, title, text, buttons, default)
    def _patched_warning(parent, title, text, buttons=QMessageBox.Ok, default=QMessageBox.NoButton):
        return _patched_message_box(QMessageBox.Warning, parent, title, text, buttons, default)
    def _patched_critical(parent, title, text, buttons=QMessageBox.Ok, default=QMessageBox.NoButton):
        return _patched_message_box(QMessageBox.Critical, parent, title, text, buttons, default)
    def _patched_question(parent, title, text, buttons=QMessageBox.Yes | QMessageBox.No, default=QMessageBox.NoButton):
        return _patched_message_box(QMessageBox.Question, parent, title, text, buttons, default)
    def _patched_about(parent, title, text):
        real_parent = _resolve_parent(parent)
        msg = QMessageBox(real_parent)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setIcon(QMessageBox.Information)
        _center_msg_box(msg, real_parent)
        msg.exec()

    # Apply Patch ONLY ON LINUX
    QMessageBox.information = _patched_information
    QMessageBox.warning = _patched_warning
    QMessageBox.critical = _patched_critical
    QMessageBox.question = _patched_question
    QMessageBox.about = _patched_about

# CHANGE: For Windows, we define this helper as None so the code below doesn't break
else:
    def _create_screen_anchor():
        return None

# =========================================================================

def initialize_database(db_manager: KlyveDBManager):
    """
    Ensures the database is created and populated with all necessary defaults.
    """
    logging.info("Initializing and verifying database...")
    db_manager.create_tables()

    defaults = {
        # Neutralized Defaults
        "SELECTED_LLM_PROVIDER": ("ChatGPT", "The currently active LLM provider."), # First alphabetically
        "CONTEXT_WINDOW_CHAR_LIMIT": ("100000", "Max characters for complex analysis context."), # Safe neutral baseline

        # Blanked Models
        "GEMINI_API_KEY": ("", "API Key for Google Gemini."),
        "GEMINI_REASONING_MODEL": ("", "The sophisticated model for complex tasks."),
        "GEMINI_FAST_MODEL": ("", "The faster model for simpler tasks."),
        "OPENAI_API_KEY": ("", "API Key for OpenAI/ChatGPT."),
        "OPENAI_REASONING_MODEL": ("", "Default reasoning model for OpenAI."),
        "OPENAI_FAST_MODEL": ("", "Default fast model for OpenAI."),
        "ANTHROPIC_API_KEY": ("", "API Key for Anthropic Claude."),
        "ANTHROPIC_REASONING_MODEL": ("", "Default reasoning model for Anthropic."),
        "ANTHROPIC_FAST_MODEL": ("", "Default fast model for Anthropic."),
        "CUSTOM_ENDPOINT_URL": ("", "Endpoint URL for custom/enterprise LLMs."),
        "CUSTOM_ENDPOINT_API_KEY": ("", "API Key for custom/enterprise LLMs."),
        "CUSTOM_REASONING_MODEL": ("", "Reasoning model name for custom endpoint."),
        "CUSTOM_FAST_MODEL": ("", "Fast model name for custom endpoint."),
        "GROK_API_KEY": ("", "API Key for Grok."),
        "GROK_REASONING_MODEL": ("", "Default reasoning model for Grok."),
        "GROK_FAST_MODEL": ("", "Default fast model for Grok."),
        "DEEPSEEK_API_KEY": ("", "API Key for Deepseek."),
        "DEEPSEEK_REASONING_MODEL": ("", "Default reasoning model for Deepseek."),
        "DEEPSEEK_FAST_MODEL": ("", "Default fast model for Deepseek."),
        "LLAMA_API_KEY": ("", "API Key for Llama (via Replicate)."),
        "LLAMA_REASONING_MODEL": ("", "Default reasoning model for Llama."),
        "LLAMA_FAST_MODEL": ("", "Default fast model for Llama."),

        # Operational Settings
        "MAX_DEBUG_ATTEMPTS": ("2", "Max automated fix attempts before escalating to the PM."),
        "LOGGING_LEVEL": ("Standard", "Verbosity of Klyve's internal logs."),
        "DEFAULT_PROJECT_PATH": ("", "Default parent directory for new target projects."),
        "DEFAULT_ARCHIVE_PATH": ("", "Default folder for saving project exports."),
        "SELECTED_DOCX_STYLE_PATH": ("data/templates/styles/default_docx_template.docx", "Path to the .docx file used for styling exported documents."),

        # Context Limits (Retained as reference, but main limit is lower)
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


def global_exception_handler(exctype, value, tb):
    """
    Sanitizes error tracebacks to hide internal file paths before logging.
    """
    # Format the traceback
    raw_tb = "".join(traceback.format_exception(exctype, value, tb))

    # Sanitize Paths (Hide user/project structure)
    # We replace the project root with <FROZEN_ROOT>
    try:
        if getattr(sys, 'frozen', False):
            base_dir = str(Path(sys.executable).parent)
        else:
            base_dir = str(Path(__file__).parent)

        # Simple string replacement for the base dir
        sanitized_tb = raw_tb.replace(base_dir, "<CORE>")

        # Regex for other absolute paths (Drive letters)
        sanitized_tb = re.sub(r'[a-zA-Z]:\\[\\\w\s\.\-]*\\klyve', '<CORE>', sanitized_tb)

    except Exception:
        sanitized_tb = raw_tb # Fallback

    # Log it
    logging.critical("Uncaught Exception:", exc_info=(exctype, value, tb))

    # In Dev Mode, print to stderr. In Prod, suppress console output of raw paths.
    if config.is_dev_mode():
        sys.__excepthook__(exctype, value, tb)
    else:
        # Show a sanitized GUI dialog if possible
        error_msg = f"An internal error occurred.\nType: {exctype.__name__}\nDetails: {str(value)}\n\nSee logs for details."
        try:
            if QApplication.instance():
                QMessageBox.critical(None, "Critical Error", error_msg)
        except:
            pass
        sys.exit(1)


def _initialize_klyve(app, splash, splash_anchor):
    try:
        app.setQuitOnLastWindowClosed(False)

        # --- Setup Database & Config ---
        user_data_dir = Path.home() / ".klyve" / "data"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        db_path = user_data_dir / "klyve.db"
        db_manager = KlyveDBManager(db_path=str(db_path))

        initialize_database(db_manager)
        _setup_logging(db_manager)

        try:
            style_file = Path(config.get_resource_path("gui/style.qss"))
            if style_file.exists():
                with open(style_file, "r") as f:
                    app.setStyleSheet(f.read())
        except Exception as e:
            logging.error(f"Failed to load stylesheet: {e}")

        # --- 5. Legal Guardrail (EULA Check) ---
        if not db_manager.get_config_value("EULA_ACCEPTED_TIMESTAMP"):
            logging.info("EULA not yet accepted.")
            if splash and splash.isVisible():
                splash.hide()

            # CHANGE: On Windows, _create_screen_anchor returns None, so we handle it gracefully
            if sys.platform == "linux":
                eula_anchor = _create_screen_anchor()
                legal_dialog = LegalDialog(parent=eula_anchor)
            else:
                eula_anchor = None
                legal_dialog = LegalDialog() # No parent needed on Windows, it will center itself

            result = legal_dialog.exec()

            if eula_anchor:
                eula_anchor.close()
                eula_anchor.deleteLater()

            if result != QDialog.Accepted:
                sys.exit(0)

            acceptance_time = datetime.now(timezone.utc).isoformat()
            db_manager.set_config_value("EULA_ACCEPTED_TIMESTAMP", acceptance_time, "Timestamp of EULA acceptance.")

            if splash:
                splash.show()

        # --- 6. Initialize Core Components ---
        orchestrator = MasterOrchestrator(db_manager=db_manager)

        # Attach to app so _resolve_parent finds it
        app._main_window = KlyveMainWindow(orchestrator=orchestrator)
        window = app._main_window

        # --- 7. Launch ---
        window.showMaximized()
        app.setQuitOnLastWindowClosed(True)

        if splash and splash.isVisible():
            QTimer.singleShot(0, lambda: splash.finish(window))

        # FIX: Close the Splash Anchor now that main window is up
        if splash_anchor:
            QTimer.singleShot(100, splash_anchor.close)

    except Exception as e:
        error_msg = f"Initialization Failure:\n{str(e)}"
        if config.is_dev_mode():
            logging.error(error_msg, exc_info=True)
        if splash: splash.hide()
        QMessageBox.critical(None, "Critical Startup Error", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    import traceback

    # CHANGE: Add Windows High DPI Fix
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    try:
        QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, False)
        app = QApplication(sys.argv)
        sys.excepthook = global_exception_handler

        icon_path = Path(config.get_resource_path("gui/icons/klyve_logo.ico"))
        splash_path = Path(config.get_resource_path("gui/images/splash_screen.png"))

        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))

        splash = None
        splash_anchor = None

        if splash_path.exists():
            try:
                splash_pix = QPixmap(str(splash_path))

                # High-DPI Scaling
                dpr = app.devicePixelRatio()
                target_physical_width = int(480 * dpr)
                splash_pix = splash_pix.scaledToWidth(target_physical_width, Qt.TransformationMode.SmoothTransformation)
                splash_pix.setDevicePixelRatio(dpr)

                # --- OS-SPECIFIC POSITIONING FIX ---
                if sys.platform == "linux":
                    # Linux/Wayland: Use Invisible Anchor Trick
                    splash_anchor = _create_screen_anchor()

                    # 1. Create Standard Splash (No parent in constructor)
                    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)

                    # 2. Manual Reparenting (Safe method)
                    splash.setParent(splash_anchor)

                    # 3. Manual Centering relative to Anchor
                    splash_geo = splash.geometry()
                    splash_geo.moveCenter(splash_anchor.rect().center())
                    splash.move(splash_geo.topLeft())
                else:
                    # Windows: Standard Centering (Robust & Simple)
                    splash_anchor = None # Not needed on Windows
                    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
                    center_window(splash)
                # -----------------------------------

                splash.show()
                app.processEvents()
            except Exception as e:
                print(f"Failed to load splash screen: {e}")

        # Pass splash_anchor to init for cleanup
        QTimer.singleShot(3000, lambda: _initialize_klyve(app, splash, splash_anchor))

        sys.exit(app.exec())

    except Exception as e:
        if config.is_dev_mode():
            print(f"CRITICAL STARTUP FAILURE: {e}")
            traceback.print_exc()

        if not QApplication.instance():
            temp_app = QApplication(sys.argv)
        sys.excepthook = global_exception_handler

        QMessageBox.critical(None, "Critical Startup Error", f"A critical error occurred:\n{e}")
        sys.exit(1)