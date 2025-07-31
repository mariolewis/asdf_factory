# gui/settings_dialog.py

import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget,
                               QFormLayout, QLabel, QComboBox, QStackedWidget,
                               QLineEdit, QSpinBox, QDialogButtonBox, QSpacerItem,
                               QSizePolicy)

from master_orchestrator import MasterOrchestrator

class SettingsDialog(QDialog):
    """
    The dialog window for managing ASDF settings, built programmatically for robustness.
    """
    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator

        self.setWindowTitle("ASDF Settings")
        self.setMinimumSize(600, 450)
        self.setModal(True)

        # Create widgets and layouts programmatically
        self._create_widgets()
        self._create_layouts()

        self.populate_fields()
        self.connect_signals()

    def _create_widgets(self):
        """Creates all the widgets for the dialog."""
        self.main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()

        # --- LLM Providers Tab Widgets ---
        self.llm_providers_tab = QWidget()
        self.provider_combo_box = QComboBox()
        self.provider_stacked_widget = QStackedWidget()

        self.gemini_page = QWidget()
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.Password)

        self.chatgpt_page = QWidget()
        self.openai_api_key_input = QLineEdit()
        self.openai_api_key_input.setEchoMode(QLineEdit.Password)

        self.claude_page = QWidget()
        self.anthropic_api_key_input = QLineEdit()
        self.anthropic_api_key_input.setEchoMode(QLineEdit.Password)

        self.phi3local_page = QWidget()
        self.anyother_page = QWidget()
        self.custom_endpoint_url_input = QLineEdit()
        self.custom_endpoint_api_key_input = QLineEdit()
        self.custom_endpoint_api_key_input.setEchoMode(QLineEdit.Password)

        # --- Factory Behavior Tab Widgets ---
        self.factory_behavior_tab = QWidget()
        self.max_debug_spin_box = QSpinBox()
        self.context_limit_spin_box = QSpinBox()
        self.logging_combo_box = QComboBox()
        self.project_path_input = QLineEdit()
        self.archive_path_input = QLineEdit()

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

    def _create_layouts(self):
        """Creates and arranges layouts for the dialog."""
        # --- LLM Providers Tab Layout ---
        llm_tab_layout = QVBoxLayout(self.llm_providers_tab)
        provider_form_layout = QFormLayout()
        provider_form_layout.addRow("Select LLM Provider:", self.provider_combo_box)
        llm_tab_layout.addLayout(provider_form_layout)

        # Setup pages and add them to stacked widget
        gemini_layout = QFormLayout(self.gemini_page)
        gemini_layout.addRow("Gemini API Key:", self.gemini_api_key_input)
        self.provider_stacked_widget.addWidget(self.gemini_page)

        chatgpt_layout = QFormLayout(self.chatgpt_page)
        chatgpt_layout.addRow("OpenAI API Key:", self.openai_api_key_input)
        self.provider_stacked_widget.addWidget(self.chatgpt_page)

        claude_layout = QFormLayout(self.claude_page)
        claude_layout.addRow("Anthropic API Key:", self.anthropic_api_key_input)
        self.provider_stacked_widget.addWidget(self.claude_page)

        phi3_layout = QVBoxLayout(self.phi3local_page)
        phi3_layout.addWidget(QLabel("No configuration needed. Ensure your local Ollama server is running."))
        self.provider_stacked_widget.addWidget(self.phi3local_page)

        anyother_layout = QFormLayout(self.anyother_page)
        anyother_layout.addRow("Endpoint URL:", self.custom_endpoint_url_input)
        anyother_layout.addRow("Endpoint API Key:", self.custom_endpoint_api_key_input)
        self.provider_stacked_widget.addWidget(self.anyother_page)

        llm_tab_layout.addWidget(self.provider_stacked_widget)
        llm_tab_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- Factory Behavior Tab Layout ---
        factory_tab_layout = QFormLayout(self.factory_behavior_tab)
        factory_tab_layout.addRow("Max Debug Attempts:", self.max_debug_spin_box)
        factory_tab_layout.addRow("Context Window Limit:", self.context_limit_spin_box)
        factory_tab_layout.addRow("Logging Level:", self.logging_combo_box)
        factory_tab_layout.addRow("Default Project Path:", self.project_path_input)
        factory_tab_layout.addRow("Default Archive Path:", self.archive_path_input)

        self.tab_widget.addTab(self.llm_providers_tab, "LLM Providers")
        self.tab_widget.addTab(self.factory_behavior_tab, "Factory Behavior")

        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.addWidget(self.button_box)

    def populate_fields(self):
        with self.orchestrator.db_manager as db:
            self.all_config = db.get_all_config_values()

        provider_options = ["Gemini", "ChatGPT", "Claude", "Phi-3 (Local)", "Any Other"]
        self.provider_combo_box.addItems(provider_options)
        current_provider = self.all_config.get("SELECTED_LLM_PROVIDER", "Gemini")
        self.provider_combo_box.setCurrentText(current_provider)

        self.gemini_api_key_input.setText(self.all_config.get("GEMINI_API_KEY", ""))
        self.openai_api_key_input.setText(self.all_config.get("OPENAI_API_KEY", ""))
        self.anthropic_api_key_input.setText(self.all_config.get("ANTHROPIC_API_KEY", ""))
        self.custom_endpoint_url_input.setText(self.all_config.get("CUSTOM_ENDPOINT_URL", ""))
        self.custom_endpoint_api_key_input.setText(self.all_config.get("CUSTOM_ENDPOINT_API_KEY", ""))

        self.max_debug_spin_box.setRange(1, 10)
        self.max_debug_spin_box.setValue(int(self.all_config.get("MAX_DEBUG_ATTEMPTS", 2)))

        self.context_limit_spin_box.setRange(10000, 10000000)
        self.context_limit_spin_box.setSingleStep(10000)

        logging_options = ["Standard", "Detailed", "Debug"]
        self.logging_combo_box.addItems(logging_options)
        self.logging_combo_box.setCurrentText(self.all_config.get("LOGGING_LEVEL", "Standard"))

        self.project_path_input.setText(self.all_config.get("DEFAULT_PROJECT_PATH", ""))
        self.archive_path_input.setText(self.all_config.get("DEFAULT_ARCHIVE_PATH", ""))

        self.on_provider_changed()

    def connect_signals(self):
        self.provider_combo_box.currentTextChanged.connect(self.on_provider_changed)
        self.button_box.accepted.connect(self.save_settings_and_accept)
        self.button_box.rejected.connect(self.reject)

    def on_provider_changed(self):
        provider_name = self.provider_combo_box.currentText()
        page_map = {
            "Gemini": self.gemini_page, "ChatGPT": self.chatgpt_page,
            "Claude": self.claude_page, "Phi-3 (Local)": self.phi3local_page,
            "Any Other": self.anyother_page
        }
        page_to_show = page_map.get(provider_name)
        if page_to_show:
            self.provider_stacked_widget.setCurrentWidget(page_to_show)

        provider_key_map = {
            "Gemini": "GEMINI_CONTEXT_LIMIT", "ChatGPT": "OPENAI_CONTEXT_LIMIT",
            "Claude": "ANTHROPIC_CONTEXT_LIMIT", "Phi-3 (Local)": "LOCALPHI3_CONTEXT_LIMIT",
            "Any Other": "ENTERPRISE_CONTEXT_LIMIT"
        }
        provider_default_key = provider_key_map.get(provider_name)
        if provider_default_key:
            default_value = int(self.all_config.get(provider_default_key, 2000000))
            self.context_limit_spin_box.setValue(default_value)

    def save_settings_and_accept(self):
        logging.info("Saving settings from dialog...")
        try:
            with self.orchestrator.db_manager as db:
                db.set_config_value("SELECTED_LLM_PROVIDER", self.provider_combo_box.currentText())
                db.set_config_value("GEMINI_API_KEY", self.gemini_api_key_input.text())
                db.set_config_value("OPENAI_API_KEY", self.openai_api_key_input.text())
                db.set_config_value("ANTHROPIC_API_KEY", self.anthropic_api_key_input.text())
                db.set_config_value("CUSTOM_ENDPOINT_URL", self.custom_endpoint_url_input.text())
                db.set_config_value("CUSTOM_ENDPOINT_API_KEY", self.custom_endpoint_api_key_input.text())

                db.set_config_value("MAX_DEBUG_ATTEMPTS", str(self.max_debug_spin_box.value()))
                db.set_config_value("CONTEXT_WINDOW_CHAR_LIMIT", str(self.context_limit_spin_box.value()))
                db.set_config_value("LOGGING_LEVEL", self.logging_combo_box.currentText())
                db.set_config_value("DEFAULT_PROJECT_PATH", self.project_path_input.text())
                db.set_config_value("DEFAULT_ARCHIVE_PATH", self.archive_path_input.text())

            self.orchestrator._llm_service = None
            logging.info("Settings saved successfully.")
            self.accept()
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
            self.reject()