# gui/settings_dialog.py

import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget,
                               QFormLayout, QLabel, QComboBox, QStackedWidget,
                               QLineEdit, QSpinBox, QDialogButtonBox, QSpacerItem,
                               QSizePolicy)

from master_orchestrator import MasterOrchestrator

class SettingsDialog(QDialog):
    """
    The dialog window for managing ASDF settings.
    This is a complete, verified replacement.
    """
    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.all_config = {}

        self.setWindowTitle("ASDF Settings")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        # This new structure ensures widgets are created and populated correctly.
        self._create_widgets()
        self._create_layouts()
        self.connect_signals()

    def _create_widgets(self):
        """Creates all the widgets for the dialog."""
        self.main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()

        # --- LLM Providers Tab Widgets ---
        self.llm_providers_tab = QWidget()
        self.provider_combo_box = QComboBox()
        self.provider_combo_box.addItems(["Gemini", "ChatGPT", "Claude", "Phi-3 (Local)", "Any Other"])
        self.provider_stacked_widget = QStackedWidget()

        # Gemini Page
        self.gemini_page = QWidget()
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.Password)
        self.gemini_reasoning_model_input = QLineEdit()
        self.gemini_fast_model_input = QLineEdit()

        # ChatGPT Page
        self.chatgpt_page = QWidget()
        self.openai_api_key_input = QLineEdit()
        self.openai_api_key_input.setEchoMode(QLineEdit.Password)
        self.openai_reasoning_model_input = QLineEdit()
        self.openai_fast_model_input = QLineEdit()

        # Claude Page
        self.claude_page = QWidget()
        self.anthropic_api_key_input = QLineEdit()
        self.anthropic_api_key_input.setEchoMode(QLineEdit.Password)
        self.anthropic_reasoning_model_input = QLineEdit()
        self.anthropic_fast_model_input = QLineEdit()

        # Phi-3 Local Page
        self.phi3local_page = QWidget()

        # Any Other/Custom Page
        self.anyother_page = QWidget()
        self.custom_endpoint_url_input = QLineEdit()
        self.custom_endpoint_api_key_input = QLineEdit()
        self.custom_endpoint_api_key_input.setEchoMode(QLineEdit.Password)
        self.custom_reasoning_model_input = QLineEdit()
        self.custom_fast_model_input = QLineEdit()

        # --- Factory Behavior Tab Widgets ---
        self.factory_behavior_tab = QWidget()
        self.max_debug_spin_box = QSpinBox()
        self.max_debug_spin_box.setRange(1, 10)
        self.context_limit_spin_box = QSpinBox()
        self.context_limit_spin_box.setRange(10000, 10000000)
        self.context_limit_spin_box.setSingleStep(10000)
        self.logging_combo_box = QComboBox()
        self.logging_combo_box.addItems(["Standard", "Detailed", "Debug"])
        self.project_path_input = QLineEdit()
        self.archive_path_input = QLineEdit()

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

    def _create_layouts(self):
        """Creates and arranges layouts for the dialog."""
        llm_tab_layout = QVBoxLayout(self.llm_providers_tab)
        provider_form_layout = QFormLayout()
        provider_form_layout.addRow("Select LLM Provider:", self.provider_combo_box)
        llm_tab_layout.addLayout(provider_form_layout)

        gemini_layout = QFormLayout(self.gemini_page)
        gemini_layout.addRow("Gemini API Key:", self.gemini_api_key_input)
        gemini_layout.addRow("Reasoning Model:", self.gemini_reasoning_model_input)
        gemini_layout.addRow("Fast Model:", self.gemini_fast_model_input)
        self.provider_stacked_widget.addWidget(self.gemini_page)

        chatgpt_layout = QFormLayout(self.chatgpt_page)
        chatgpt_layout.addRow("OpenAI API Key:", self.openai_api_key_input)
        chatgpt_layout.addRow("Reasoning Model:", self.openai_reasoning_model_input)
        chatgpt_layout.addRow("Fast Model:", self.openai_fast_model_input)
        self.provider_stacked_widget.addWidget(self.chatgpt_page)

        claude_layout = QFormLayout(self.claude_page)
        claude_layout.addRow("Anthropic API Key:", self.anthropic_api_key_input)
        claude_layout.addRow("Reasoning Model:", self.anthropic_reasoning_model_input)
        claude_layout.addRow("Fast Model:", self.anthropic_fast_model_input)
        self.provider_stacked_widget.addWidget(self.claude_page)

        phi3_layout = QVBoxLayout(self.phi3local_page)
        phi3_layout.addWidget(QLabel("No configuration needed. Ensure your local Ollama server is running."))
        self.provider_stacked_widget.addWidget(self.phi3local_page)

        anyother_layout = QFormLayout(self.anyother_page)
        anyother_layout.addRow("Endpoint URL:", self.custom_endpoint_url_input)
        anyother_layout.addRow("Endpoint API Key:", self.custom_endpoint_api_key_input)
        anyother_layout.addRow("Reasoning Model:", self.custom_reasoning_model_input)
        anyother_layout.addRow("Fast Model:", self.custom_fast_model_input)
        self.provider_stacked_widget.addWidget(self.anyother_page)

        llm_tab_layout.addWidget(self.provider_stacked_widget)
        llm_tab_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

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
        """Loads all current settings from the database and populates the UI fields."""
        with self.orchestrator.db_manager as db:
            self.all_config = db.get_all_config_values()

        self.provider_combo_box.setCurrentText(self.all_config.get("SELECTED_LLM_PROVIDER"))
        self.gemini_api_key_input.setText(self.all_config.get("GEMINI_API_KEY"))
        self.gemini_reasoning_model_input.setText(self.all_config.get("GEMINI_REASONING_MODEL"))
        self.gemini_fast_model_input.setText(self.all_config.get("GEMINI_FAST_MODEL"))
        self.openai_api_key_input.setText(self.all_config.get("OPENAI_API_KEY"))
        self.openai_reasoning_model_input.setText(self.all_config.get("OPENAI_REASONING_MODEL"))
        self.openai_fast_model_input.setText(self.all_config.get("OPENAI_FAST_MODEL"))
        self.anthropic_api_key_input.setText(self.all_config.get("ANTHROPIC_API_KEY"))
        self.anthropic_reasoning_model_input.setText(self.all_config.get("ANTHROPIC_REASONING_MODEL"))
        self.anthropic_fast_model_input.setText(self.all_config.get("ANTHROPIC_FAST_MODEL"))
        self.custom_endpoint_url_input.setText(self.all_config.get("CUSTOM_ENDPOINT_URL"))
        self.custom_endpoint_api_key_input.setText(self.all_config.get("CUSTOM_ENDPOINT_API_KEY"))
        self.custom_reasoning_model_input.setText(self.all_config.get("CUSTOM_REASONING_MODEL"))
        self.custom_fast_model_input.setText(self.all_config.get("CUSTOM_FAST_MODEL"))

        self.max_debug_spin_box.setValue(int(self.all_config.get("MAX_DEBUG_ATTEMPTS")))
        self.context_limit_spin_box.setValue(int(self.all_config.get("CONTEXT_WINDOW_CHAR_LIMIT")))
        self.logging_combo_box.setCurrentText(self.all_config.get("LOGGING_LEVEL"))
        self.project_path_input.setText(self.all_config.get("DEFAULT_PROJECT_PATH"))
        self.archive_path_input.setText(self.all_config.get("DEFAULT_ARCHIVE_PATH"))

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

    def save_settings_and_accept(self):
        logging.info("Saving settings from dialog...")
        try:
            settings_to_save = {
                "SELECTED_LLM_PROVIDER": self.provider_combo_box.currentText(),
                "GEMINI_API_KEY": self.gemini_api_key_input.text(),
                "GEMINI_REASONING_MODEL": self.gemini_reasoning_model_input.text(),
                "GEMINI_FAST_MODEL": self.gemini_fast_model_input.text(),
                "OPENAI_API_KEY": self.openai_api_key_input.text(),
                "OPENAI_REASONING_MODEL": self.openai_reasoning_model_input.text(),
                "OPENAI_FAST_MODEL": self.openai_fast_model_input.text(),
                "ANTHROPIC_API_KEY": self.anthropic_api_key_input.text(),
                "ANTHROPIC_REASONING_MODEL": self.anthropic_reasoning_model_input.text(),
                "ANTHROPIC_FAST_MODEL": self.anthropic_fast_model_input.text(),
                "CUSTOM_ENDPOINT_URL": self.custom_endpoint_url_input.text(),
                "CUSTOM_ENDPOINT_API_KEY": self.custom_endpoint_api_key_input.text(),
                "CUSTOM_REASONING_MODEL": self.custom_reasoning_model_input.text(),
                "CUSTOM_FAST_MODEL": self.custom_fast_model_input.text(),
                "MAX_DEBUG_ATTEMPTS": str(self.max_debug_spin_box.value()),
                "CONTEXT_WINDOW_CHAR_LIMIT": str(self.context_limit_spin_box.value()),
                "LOGGING_LEVEL": self.logging_combo_box.currentText(),
                "DEFAULT_PROJECT_PATH": self.project_path_input.text(),
                "DEFAULT_ARCHIVE_PATH": self.archive_path_input.text()
            }

            provider = settings_to_save["SELECTED_LLM_PROVIDER"]
            if provider in ["Gemini", "ChatGPT", "Claude", "Any Other"]:
                prefix_map = {"Gemini": "GEMINI", "ChatGPT": "OPENAI", "Claude": "ANTHROPIC", "Any Other": "CUSTOM"}
                prefix = prefix_map.get(provider)
                reasoning_key = f"{prefix}_REASONING_MODEL"
                fast_key = f"{prefix}_FAST_MODEL"
                if not settings_to_save[reasoning_key] and settings_to_save[fast_key]:
                    settings_to_save[reasoning_key] = settings_to_save[fast_key]
                elif not settings_to_save[fast_key] and settings_to_save[reasoning_key]:
                    settings_to_save[fast_key] = settings_to_save[reasoning_key]

            with self.orchestrator.db_manager as db:
                for key, value in settings_to_save.items():
                    db.set_config_value(key, value)

            self.orchestrator.llm_service = self.orchestrator._create_llm_service()
            logging.info("Settings saved and LLM service re-initialized.")
            self.accept()

        except Exception as e:
            logging.error(f"Failed to save settings: {e}", exc_info=True)
            self.reject()