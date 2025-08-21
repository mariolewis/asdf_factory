# gui/settings_dialog.py

import logging
import shutil
import os
from pathlib import Path
from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (QTableView, QHeaderView, QAbstractItemView,
                               QPushButton, QStandardItemEditorFactory)
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget,
                               QFormLayout, QLabel, QComboBox, QStackedWidget,
                               QLineEdit, QSpinBox, QDialogButtonBox, QSpacerItem,
                               QSizePolicy, QMessageBox)

from master_orchestrator import MasterOrchestrator

class AddTemplateDialog(QDialog):
    """A simple dialog to get the name and path for a new template."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Template")
        self.setMinimumWidth(400)
        self.file_path = ""

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        browse_button = QPushButton("Browse...")

        form_layout.addRow("Template Name:", self.name_input)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        form_layout.addRow("Template File:", path_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)

        browse_button.clicked.connect(self._browse_for_file)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _browse_for_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Template File", "", "Documents (*.md *.txt *.docx)")
        if path:
            self.file_path = path
            self.path_input.setText(path)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "path": self.file_path
        }
class SettingsDialog(QDialog):
    """
    The dialog window for managing ASDF settings.
    """
    def __init__(self, orchestrator: MasterOrchestrator, parent=None):
        super().__init__(parent)
        self.orchestrator = orchestrator
        self.all_config = {}

        self.setWindowTitle("ASDF Settings")
        self.setMinimumSize(600, 500)
        self.setModal(True)

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

        self.gemini_page = QWidget()
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.Password)
        self.gemini_reasoning_model_input = QLineEdit()
        self.gemini_fast_model_input = QLineEdit()

        self.chatgpt_page = QWidget()
        self.openai_api_key_input = QLineEdit()
        self.openai_api_key_input.setEchoMode(QLineEdit.Password)
        self.openai_reasoning_model_input = QLineEdit()
        self.openai_fast_model_input = QLineEdit()

        self.claude_page = QWidget()
        self.anthropic_api_key_input = QLineEdit()
        self.anthropic_api_key_input.setEchoMode(QLineEdit.Password)
        self.anthropic_reasoning_model_input = QLineEdit()
        self.anthropic_fast_model_input = QLineEdit()

        self.phi3local_page = QWidget()

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

        # --- Templates Tab Widgets ---
        self.templates_tab = QWidget()
        self.templates_table_view = QTableView()
        self.templates_model = QStandardItemModel(self)
        self.add_template_button = QPushButton("Add New Template...")
        self.remove_template_button = QPushButton("Remove Selected")
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
        factory_tab_layout.addRow("Default Export Path:", self.archive_path_input)

        templates_tab_layout = QVBoxLayout(self.templates_tab)
        templates_tab_layout.addWidget(QLabel("Manage default templates for document generation."))

        self.templates_table_view.setModel(self.templates_model)
        self.templates_table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.templates_table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.templates_table_view.setAlternatingRowColors(True)
        templates_tab_layout.addWidget(self.templates_table_view)

        template_button_layout = QHBoxLayout()
        template_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        template_button_layout.addWidget(self.add_template_button)
        template_button_layout.addWidget(self.remove_template_button)
        templates_tab_layout.addLayout(template_button_layout)

        self.tab_widget.addTab(self.templates_tab, "Templates")
        self.tab_widget.addTab(self.llm_providers_tab, "LLM Providers")
        self.tab_widget.addTab(self.factory_behavior_tab, "Factory Behavior")

        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.addWidget(self.button_box)

    def _populate_templates_tab(self):
        """Fetches all templates from the DB and populates the templates table."""
        self.templates_model.clear()
        self.templates_model.setHorizontalHeaderLabels(['ID', 'Template Name', 'File Path'])

        try:
            templates = self.orchestrator.db_manager.get_all_templates()
            for template in templates:
                id_item = QStandardItem(str(template['template_id']))
                name_item = QStandardItem(template['template_name'])
                path_item = QStandardItem(template['file_path'])
                self.templates_model.appendRow([id_item, name_item, path_item])

            self.templates_table_view.setModel(self.templates_model)
            self.templates_table_view.setColumnHidden(0, True) # Hide the ID
            self.templates_table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.templates_table_view.resizeColumnToContents(2)
        except Exception as e:
            logging.error(f"Failed to populate templates tab: {e}")
            QMessageBox.critical(self, "Error", f"Could not load templates from database: {e}")

    def _on_add_template_clicked(self):
        """Handles the logic for adding a new template."""
        dialog = AddTemplateDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            name = data.get("name")
            source_path_str = data.get("path")

            if not name or not source_path_str:
                QMessageBox.warning(self, "Input Missing", "Both a template name and a file path are required.")
                return

            try:
                source_path = Path(source_path_str)
                templates_dir = Path("data") / "templates"
                destination_path = templates_dir / source_path.name

                # Copy the file to the local templates directory
                shutil.copy(source_path, destination_path)

                # Save the record to the database
                self.orchestrator.db_manager.add_template(name, str(destination_path))

                # Refresh the table view
                self._populate_templates_tab()
                QMessageBox.information(self, "Success", f"Template '{name}' was added successfully.")

            except Exception as e:
                logging.error(f"Failed to add new template: {e}")
                QMessageBox.critical(self, "Error", f"Could not add template: {e}")

    def _on_remove_template_clicked(self):
        """Handles the logic for removing a selected template."""
        selection_model = self.templates_table_view.selectionModel()
        if not selection_model.hasSelection():
            QMessageBox.warning(self, "No Selection", "Please select a template from the list to remove.")
            return

        selected_row = selection_model.selectedRows()[0].row()
        template_id_item = self.templates_model.item(selected_row, 0)
        template_name_item = self.templates_model.item(selected_row, 1)
        file_path_item = self.templates_model.item(selected_row, 2)

        template_id = int(template_id_item.text())
        template_name = template_name_item.text()
        file_path = file_path_item.text()

        reply = QMessageBox.question(self, "Confirm Deletion",
                                    f"Are you sure you want to permanently delete the template '{template_name}'?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Delete the record from the database
                self.orchestrator.db_manager.delete_template(template_id)

                # Delete the physical file
                if Path(file_path).exists():
                    os.remove(file_path)

                # Refresh the table view
                self._populate_templates_tab()
                QMessageBox.information(self, "Success", f"Template '{template_name}' was removed.")

            except Exception as e:
                logging.error(f"Failed to remove template: {e}")
                QMessageBox.critical(self, "Error", f"Could not remove template: {e}")

    def populate_fields(self):
        """Loads all current settings from the database and populates the UI fields."""
        self.all_config = self.orchestrator.db_manager.get_all_config_values()

        # Helper to safely get values
        def get_val(key, default=""):
            return self.all_config.get(key, default)

        self.provider_combo_box.setCurrentText(get_val("SELECTED_LLM_PROVIDER", "Gemini"))
        self.gemini_api_key_input.setText(get_val("GEMINI_API_KEY"))
        self.gemini_reasoning_model_input.setText(get_val("GEMINI_REASONING_MODEL"))
        self.gemini_fast_model_input.setText(get_val("GEMINI_FAST_MODEL"))
        self.openai_api_key_input.setText(get_val("OPENAI_API_KEY"))
        self.openai_reasoning_model_input.setText(get_val("OPENAI_REASONING_MODEL"))
        self.openai_fast_model_input.setText(get_val("OPENAI_FAST_MODEL"))
        self.anthropic_api_key_input.setText(get_val("ANTHROPIC_API_KEY"))
        self.anthropic_reasoning_model_input.setText(get_val("ANTHROPIC_REASONING_MODEL"))
        self.anthropic_fast_model_input.setText(get_val("ANTHROPIC_FAST_MODEL"))
        self.custom_endpoint_url_input.setText(get_val("CUSTOM_ENDPOINT_URL"))
        self.custom_endpoint_api_key_input.setText(get_val("CUSTOM_ENDPOINT_API_KEY"))
        self.custom_reasoning_model_input.setText(get_val("CUSTOM_REASONING_MODEL"))
        self.custom_fast_model_input.setText(get_val("CUSTOM_FAST_MODEL"))

        self.max_debug_spin_box.setValue(int(get_val("MAX_DEBUG_ATTEMPTS", 2)))
        self.context_limit_spin_box.setValue(int(get_val("CONTEXT_WINDOW_CHAR_LIMIT", 2500000)))
        self.logging_combo_box.setCurrentText(get_val("LOGGING_LEVEL", "Standard"))
        self.project_path_input.setText(get_val("DEFAULT_PROJECT_PATH"))
        self.archive_path_input.setText(get_val("DEFAULT_ARCHIVE_PATH"))

        self.on_provider_changed()
        self._populate_templates_tab()

    def connect_signals(self):
        self.provider_combo_box.currentTextChanged.connect(self.on_provider_changed)
        self.button_box.accepted.connect(self.save_settings_and_accept)
        self.button_box.rejected.connect(self.reject)
        self.add_template_button.clicked.connect(self._on_add_template_clicked)
        self.remove_template_button.clicked.connect(self._on_remove_template_clicked)

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
        """Saves all settings from all tabs to the database."""
        logging.info("Saving settings from dialog...")
        try:
            # (The logic to gather settings remains the same)
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

            db_manager = self.orchestrator.db_manager
            for key, value in settings_to_save.items():
                db_manager.set_config_value(key, value)

            # This is the corrected line:
            self.orchestrator._llm_service = None # Clear the cached service

            logging.info("Settings saved. LLM service will be re-initialized on next use.")
            self.accept()

        except Exception as e:
            logging.error(f"Failed to save settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")
            self.reject()