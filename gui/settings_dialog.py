# gui/settings_dialog.py

import logging
import shutil
import os
from pathlib import Path
from PySide6.QtCore import Qt, QThreadPool, QTimer
from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (QTableView, QHeaderView, QAbstractItemView,
                               QPushButton)
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QTabWidget, QWidget,
                               QFormLayout, QLabel, QComboBox, QStackedWidget,
                               QLineEdit, QSpinBox, QDialogButtonBox, QSpacerItem,
                               QSizePolicy, QMessageBox, QHBoxLayout, QListWidget, QGroupBox, QListWidgetItem)
from PySide6.QtCore import QThreadPool
from .worker import Worker

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
        self.threadpool = QThreadPool()
        self.initial_provider = ""
        self.is_calibrating_on_save = False
        self.provider_changed = False
        self.active_style_path = ""

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
        self.provider_combo_box.addItems(["Gemini", "ChatGPT", "Claude", "Grok", "Deepseek", "Llama", "Phi-3 (Local)", "Any Other"])
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

        self.grok_page = QWidget()
        self.grok_api_key_input = QLineEdit()
        self.grok_api_key_input.setEchoMode(QLineEdit.Password)
        self.grok_reasoning_model_input = QLineEdit()
        self.grok_fast_model_input = QLineEdit()

        self.deepseek_page = QWidget()
        self.deepseek_api_key_input = QLineEdit()
        self.deepseek_api_key_input.setEchoMode(QLineEdit.Password)
        self.deepseek_reasoning_model_input = QLineEdit()
        self.deepseek_fast_model_input = QLineEdit()

        self.llama_page = QWidget()
        self.llama_api_key_input = QLineEdit()
        self.llama_api_key_input.setEchoMode(QLineEdit.Password)
        self.llama_reasoning_model_input = QLineEdit()
        self.llama_fast_model_input = QLineEdit()

        # --- Factory Behavior Tab Widgets ---
        self.factory_behavior_tab = QWidget()
        self.max_debug_spin_box = QSpinBox()
        self.max_debug_spin_box.setRange(1, 10)
        self.context_limit_input = QLineEdit()
        self.context_limit_input.setReadOnly(False)
        self.calibrate_button = QPushButton("Auto-Calibrate Now")
        self.logging_combo_box = QComboBox()
        self.logging_combo_box.addItems(["Standard", "Detailed", "Debug"])
        self.project_path_input = QLineEdit()
        self.archive_path_input = QLineEdit()

        # --- Templates Tab Widgets ---
        self.templates_tab = QWidget()
        self.template_instruction_label = QLabel("Here you can manage global document templates. A template defines the structure and boilerplate text for a specific document type. When a template is set, the AI will use it to format its output for all new projects.")
        self.template_type_combo = QComboBox()
        self.template_type_combo.addItems(["Application Specification", "Technical Specification", "UX/UI Specification"])
        self.template_path_input = QLineEdit()
        self.template_path_input.setReadOnly(True)
        self.template_browse_button = QPushButton("Browse...")
        self.template_add_button = QPushButton("Add/Update Template")
        self.templates_list_widget = QListWidget()
        self.template_remove_button = QPushButton("Remove Selected")

        # --- Docx Styles Tab Widgets ---
        self.docxStylesTab = QWidget()
        self.docxStyleInstructionLabel = QLabel("Manage .docx templates for visual styling. The active template will be used to format all exported documents.\n"
                                                "Templates MUST contain the following named styles: Title, Heading 1, Heading 2, Heading 3, Normal, Bullet List, List Numbered, Code Block.")
        self.docxStyleListWidget = QListWidget()
        self.addDocxStyleButton = QPushButton("Add New Style...")
        self.removeDocxStyleButton = QPushButton("Remove Selected")
        self.setActiveDocxStyleButton = QPushButton("Set as Active")
        self.activeStyleLabel = QLabel("Active Style Template:")

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)

        # --- Integrations Tab Widgets
        self.integrations_tab = QWidget()
        self.provider_list = QListWidget()
        self.provider_list.addItems(["None", "Jira"]) # Add more providers here in the future
        self.provider_list.setMaximumWidth(150)

        self.integrations_stacked_widget = QStackedWidget()

        # Page for when no provider is selected
        self.no_provider_page = QWidget()
        self.no_provider_page.setLayout(QVBoxLayout())
        self.no_provider_page.layout().addWidget(QLabel("No integration provider selected."))
        self.no_provider_page.layout().addStretch()

        # Page for Jira settings
        self.jira_page = QWidget()
        self.jira_url_input = QLineEdit()
        self.jira_username_input = QLineEdit()
        self.jira_token_input = QLineEdit()
        self.jira_token_input.setEchoMode(QLineEdit.Password)

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

        grok_layout = QFormLayout(self.grok_page)
        grok_layout.addRow("Grok API Key:", self.grok_api_key_input)
        grok_layout.addRow("Reasoning Model:", self.grok_reasoning_model_input)
        grok_layout.addRow("Fast Model:", self.grok_fast_model_input)
        self.provider_stacked_widget.addWidget(self.grok_page)

        deepseek_layout = QFormLayout(self.deepseek_page)
        deepseek_layout.addRow("Deepseek API Key:", self.deepseek_api_key_input)
        deepseek_layout.addRow("Reasoning Model:", self.deepseek_reasoning_model_input)
        deepseek_layout.addRow("Fast Model:", self.deepseek_fast_model_input)
        self.provider_stacked_widget.addWidget(self.deepseek_page)

        llama_layout = QFormLayout(self.llama_page)
        llama_layout.addRow("Llama API Key (Replicate):", self.llama_api_key_input)
        llama_layout.addRow("Reasoning Model:", self.llama_reasoning_model_input)
        llama_layout.addRow("Fast Model:", self.llama_fast_model_input)
        self.provider_stacked_widget.addWidget(self.llama_page)

        llm_tab_layout.addWidget(self.provider_stacked_widget)
        llm_tab_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        factory_tab_layout = QFormLayout(self.factory_behavior_tab)
        factory_tab_layout.addRow("Max Debug Attempts:", self.max_debug_spin_box)
        context_limit_layout = QHBoxLayout()
        context_limit_layout.addWidget(self.context_limit_input)
        context_limit_layout.addWidget(self.calibrate_button)
        factory_tab_layout.addRow("Context Window Limit:", context_limit_layout)
        self.calibrate_button.setToolTip("Queries the selected LLM to determine and set its optimal context limit with a safety margin.")
        factory_tab_layout.addRow("Logging Level:", self.logging_combo_box)
        factory_tab_layout.addRow("Default Project Path:", self.project_path_input)
        factory_tab_layout.addRow("Default Export Path:", self.archive_path_input)

        # --- Templates Tab Layout ---
        templates_tab_layout = QVBoxLayout(self.templates_tab)
        self.template_instruction_label.setWordWrap(True)
        templates_tab_layout.addWidget(self.template_instruction_label)

        # Section for adding/updating
        add_header_label = QLabel("<b>Add/Update a Template</b>")
        templates_tab_layout.addWidget(add_header_label)

        add_layout = QFormLayout()
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.template_path_input)
        path_layout.addWidget(self.template_browse_button)
        add_layout.addRow("Template Type:", self.template_type_combo)
        add_layout.addRow("Template File:", path_layout)
        templates_tab_layout.addLayout(add_layout)

        add_button_layout = QHBoxLayout()
        add_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        add_button_layout.addWidget(self.template_add_button)
        templates_tab_layout.addLayout(add_button_layout)

        # Spacer
        templates_tab_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Section for the current list
        list_header_label = QLabel("<b>Currently Saved Templates</b>")
        templates_tab_layout.addWidget(list_header_label)
        templates_tab_layout.addWidget(self.templates_list_widget)

        remove_button_layout = QHBoxLayout()
        remove_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        remove_button_layout.addWidget(self.template_remove_button)
        templates_tab_layout.addLayout(remove_button_layout)

        # --- Integrations Tab Layout
        integrations_main_layout = QHBoxLayout(self.integrations_tab)
        integrations_main_layout.addWidget(self.provider_list)

        # Add pages to the stacked widget
        self.integrations_stacked_widget.addWidget(self.no_provider_page)

        jira_layout = QFormLayout(self.jira_page)
        jira_layout.addRow("Jira URL (e.g., your-org.atlassian.net):", self.jira_url_input)
        jira_layout.addRow("Username (Email):", self.jira_username_input)
        jira_layout.addRow("API Token:", self.jira_token_input)
        self.integrations_stacked_widget.addWidget(self.jira_page)

        integrations_main_layout.addWidget(self.integrations_stacked_widget)

        # --- Docx Styles Tab Layout ---
        docx_styles_tab_layout = QVBoxLayout(self.docxStylesTab)
        self.docxStyleInstructionLabel.setWordWrap(True)
        docx_styles_tab_layout.addWidget(self.docxStyleInstructionLabel)
        docx_styles_tab_layout.addWidget(self.activeStyleLabel) # Add the active label
        docx_styles_tab_layout.addWidget(self.docxStyleListWidget)

        style_buttons_layout = QHBoxLayout()
        style_buttons_layout.addWidget(self.setActiveDocxStyleButton)
        style_buttons_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        style_buttons_layout.addWidget(self.addDocxStyleButton)
        style_buttons_layout.addWidget(self.removeDocxStyleButton)
        docx_styles_tab_layout.addLayout(style_buttons_layout)

        self.tab_widget.addTab(self.factory_behavior_tab, "Factory Behavior")
        self.tab_widget.addTab(self.llm_providers_tab, "LLM Providers")
        self.tab_widget.addTab(self.templates_tab, "Templates")
        self.tab_widget.addTab(self.docxStylesTab, "Docx Styles")
        self.tab_widget.addTab(self.integrations_tab, "Integrations")

        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.addWidget(self.button_box)

    def _populate_templates_tab(self):
        """Fetches all templates from the DB and populates the new QListWidget."""
        self.templates_list_widget.clear()
        self.template_name_map = {
            "Application Specification": "Default Application Specification",
            "Technical Specification": "Default Technical Specification",
            "UX/UI Specification": "Default UX/UI Specification"
        }
        self.reverse_template_name_map = {v: k for k, v in self.template_name_map.items()}

        try:
            templates = self.orchestrator.db_manager.get_all_templates()
            if not templates:
                self.templates_list_widget.addItem("No templates saved.")
                self.templates_list_widget.setEnabled(False)
                return

            self.templates_list_widget.setEnabled(True)
            for template in templates:
                template_name = template['template_name']
                file_path = Path(template['file_path'])
                display_name = self.reverse_template_name_map.get(template_name, template_name)

                item_text = f"{display_name}: {file_path.name}"
                item = QListWidgetItem(item_text)
                # Store the internal name and ID for the remove function
                item.setData(Qt.UserRole, {"id": template['template_id'], "name": template_name})
                self.templates_list_widget.addItem(item)

        except Exception as e:
            logging.error(f"Failed to populate templates tab: {e}")
            QMessageBox.critical(self, "Error", f"Could not load templates from database: {e}")

    def _on_template_browse_clicked(self):
        """Opens a file dialog to select a template file."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Template File", "", "Documents (*.docx *.pdf *.txt)")
        if path:
            self.template_path_input.setText(path)

    def _on_add_update_template_clicked(self):
        """Handles the logic for adding or updating a template."""
        selected_type = self.template_type_combo.currentText()
        source_path_str = self.template_path_input.text()

        if not source_path_str:
            QMessageBox.warning(self, "File Not Selected", "Please browse for a template file to add.")
            return

        internal_name = self.template_name_map.get(selected_type)
        if not internal_name:
            QMessageBox.critical(self, "Error", "An internal error occurred: could not map template type.")
            return

        try:
            # Check if a template of this type already exists
            existing_template = self.orchestrator.db_manager.get_template_by_name(internal_name)
            if existing_template:
                reply = QMessageBox.question(self, "Confirm Overwrite",
                                            f"A template for '{selected_type}' already exists. Do you want to replace it?",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                # If overwriting, first remove the old record and file
                self.orchestrator.db_manager.delete_template(existing_template['template_id'])
                if Path(existing_template['file_path']).exists():
                    os.remove(existing_template['file_path'])

            # Proceed with adding the new template
            source_path = Path(source_path_str)
            templates_dir = Path("data") / "templates"
            templates_dir.mkdir(parents=True, exist_ok=True)
            destination_path = templates_dir / source_path.name

            shutil.copy(source_path, destination_path)
            self.orchestrator.db_manager.add_template(internal_name, str(destination_path))

            self._populate_templates_tab()
            self.template_path_input.clear()
            QMessageBox.information(self, "Success", f"Template for '{selected_type}' was saved successfully.")

        except Exception as e:
            logging.error(f"Failed to add/update template: {e}")
            QMessageBox.critical(self, "Error", f"Could not save template: {e}")

    def _on_remove_template_clicked(self):
        """Handles the logic for removing a selected template."""
        selected_items = self.templates_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a template from the list to remove.")
            return

        item = selected_items[0]
        item_data = item.data(Qt.UserRole)
        template_id = item_data.get("id")
        template_name = item_data.get("name")
        display_name = self.reverse_template_name_map.get(template_name, template_name)

        reply = QMessageBox.question(self, "Confirm Deletion",
                                    f"Are you sure you want to permanently delete the template for '{display_name}'?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                template_record = self.orchestrator.db_manager.get_template_by_name(template_name)
                if template_record:
                    # Delete the physical file
                    if Path(template_record['file_path']).exists():
                        os.remove(template_record['file_path'])

                # Delete the record from the database
                self.orchestrator.db_manager.delete_template(template_id)

                # Refresh the table view
                self._populate_templates_tab()
                QMessageBox.information(self, "Success", f"Template for '{display_name}' was removed.")

            except Exception as e:
                logging.error(f"Failed to remove template: {e}")
                QMessageBox.critical(self, "Error", f"Could not remove template: {e}")

    def _populate_docx_styles_list(self):
        """Fetches all .docx templates from the styles dir and populates the list."""
        self.docxStyleListWidget.clear()
        self.active_style_path = self.all_config.get("SELECTED_DOCX_STYLE_PATH", "data/templates/styles/default_docx_template.docx")

        styles_dir = Path("data/templates/styles")
        styles_dir.mkdir(parents=True, exist_ok=True) # Ensure it exists

        found_active = False
        default_template_path = "data/templates/styles/default_docx_template.docx"

        for docx_file in styles_dir.glob("*.docx"):
            item_path_str = str(docx_file).replace('\\', '/')
            item = QListWidgetItem(docx_file.name)
            item.setData(Qt.UserRole, item_path_str)
            self.docxStyleListWidget.addItem(item)

            if item_path_str == self.active_style_path:
                item.setSelected(True)
                self.activeStyleLabel.setText(f"Active Style: <b>{docx_file.name}</b>")
                found_active = True

        if not found_active:
            # Check if the default is in the list
            default_in_list = False
            for i in range(self.docxStyleListWidget.count()):
                item = self.docxStyleListWidget.item(i)
                if item.data(Qt.UserRole) == default_template_path:
                    item.setSelected(True)
                    default_in_list = True
                    break

            if default_in_list or Path(default_template_path).exists():
                self.active_style_path = default_template_path
                self.activeStyleLabel.setText(f"Active Style: <b>default_docx_template.docx</b>")
                if not default_in_list:
                    # Add default to list if it exists but wasn't globbed (e.g., first run)
                    item = QListWidgetItem("default_docx_template.docx")
                    item.setData(Qt.UserRole, default_template_path)
                    self.docxStyleListWidget.addItem(item)
                    item.setSelected(True)
            else:
                self.activeStyleLabel.setText(f"Active Style: <b>None (Default missing!)</b>")
                self.active_style_path = "" # No valid template

    def _on_add_style_clicked(self):
        """Handles logic for adding a new .docx style template."""
        path, _ = QFileDialog.getOpenFileName(self, "Select .docx Style Template", "", "Word Documents (*.docx)")
        if not path:
            return

        source_path = Path(path)
        styles_dir = Path("data/templates/styles")
        destination_path = styles_dir / source_path.name

        try:
            shutil.copy(source_path, destination_path)
            new_path_str = str(destination_path).replace('\\', '/')

            # Add to list and set as active
            item = QListWidgetItem(destination_path.name)
            item.setData(Qt.UserRole, new_path_str)
            self.docxStyleListWidget.addItem(item)
            item.setSelected(True)
            self._on_set_active_style_clicked() # This will update the active_style_path

        except Exception as e:
            logging.error(f"Failed to copy new style template: {e}")
            QMessageBox.critical(self, "Error", f"Could not copy template: {e}")

    def _on_remove_style_clicked(self):
        """Handles logic for removing a selected style template."""
        selected_items = self.docxStyleListWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a style to remove.")
            return

        item = selected_items[0]
        item_path_str = item.data(Qt.UserRole)

        if item_path_str == "data/templates/styles/default_docx_template.docx":
            QMessageBox.warning(self, "Action Not Allowed", "The default template cannot be removed.")
            return

        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to delete '{Path(item_path_str).name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                os.remove(item_path_str)
                # Remove from list widget
                self.docxStyleListWidget.takeItem(self.docxStyleListWidget.row(item))

                if item_path_str == self.active_style_path:
                    # If we deleted the active one, revert to default
                    self._populate_docx_styles_list() # This will re-select default

            except Exception as e:
                logging.error(f"Failed to remove style template: {e}")
                QMessageBox.critical(self, "Error", f"Could not remove template: {e}")

    def _on_set_active_style_clicked(self):
        """Sets the selected style as the active one for the orchestrator."""
        selected_items = self.docxStyleListWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a style to set as active.")
            return

        item = selected_items[0]
        self.active_style_path = item.data(Qt.UserRole)
        self.activeStyleLabel.setText(f"Active Style: <b>{item.text()}</b>")
        # The path will be saved to DB when the user clicks "Save"

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
        self.grok_api_key_input.setText(get_val("GROK_API_KEY"))
        self.grok_reasoning_model_input.setText(get_val("GROK_REASONING_MODEL"))
        self.grok_fast_model_input.setText(get_val("GROK_FAST_MODEL"))
        self.deepseek_api_key_input.setText(get_val("DEEPSEEK_API_KEY"))
        self.deepseek_reasoning_model_input.setText(get_val("DEEPSEEK_REASONING_MODEL"))
        self.deepseek_fast_model_input.setText(get_val("DEEPSEEK_FAST_MODEL"))
        self.llama_api_key_input.setText(get_val("LLAMA_API_KEY"))
        self.llama_reasoning_model_input.setText(get_val("LLAMA_REASONING_MODEL"))
        self.llama_fast_model_input.setText(get_val("LLAMA_FAST_MODEL"))

        self.max_debug_spin_box.setValue(int(get_val("MAX_DEBUG_ATTEMPTS", 2)))
        self.context_limit_input.setText(get_val("CONTEXT_WINDOW_CHAR_LIMIT", "2500000"))
        self.logging_combo_box.setCurrentText(get_val("LOGGING_LEVEL", "Standard"))
        self.project_path_input.setText(get_val("DEFAULT_PROJECT_PATH"))
        self.archive_path_input.setText(get_val("DEFAULT_ARCHIVE_PATH"))

        # --- Populate Integrations
        provider = get_val("INTEGRATION_PROVIDER", "None")
        # Find the item and get its row number to set the selection
        matching_items = self.provider_list.findItems(provider, Qt.MatchExactly)
        if matching_items:
            row = self.provider_list.row(matching_items[0])
            self.provider_list.setCurrentRow(row)
        self.jira_url_input.setText(get_val("INTEGRATION_URL"))
        self.jira_username_input.setText(get_val("INTEGRATION_USERNAME"))
        self.jira_token_input.setText(get_val("INTEGRATION_API_TOKEN"))

        self.on_provider_changed()
        self.initial_provider = self.provider_combo_box.currentText()
        self._populate_templates_tab()
        self._populate_docx_styles_list()

    def connect_signals(self):
        self.provider_combo_box.currentTextChanged.connect(self.on_provider_changed)
        self.button_box.accepted.connect(self.save_settings_and_accept)
        self.button_box.rejected.connect(self.reject)
        self.provider_list.currentRowChanged.connect(self.on_integration_provider_changed)
        self.calibrate_button.clicked.connect(self.on_calibrate_clicked)

        # --- Template Signal Connections ---
        self.template_browse_button.clicked.connect(self._on_template_browse_clicked)
        self.template_add_button.clicked.connect(self._on_add_update_template_clicked)
        self.template_remove_button.clicked.connect(self._on_remove_template_clicked)

        # --- Docx Style Signal Connections ---
        self.addDocxStyleButton.clicked.connect(self._on_add_style_clicked)
        self.removeDocxStyleButton.clicked.connect(self._on_remove_style_clicked)
        self.setActiveDocxStyleButton.clicked.connect(self._on_set_active_style_clicked)

    def on_provider_changed(self):
        provider_name = self.provider_combo_box.currentText()
        page_map = {
            "Gemini": self.gemini_page, "ChatGPT": self.chatgpt_page,
            "Claude": self.claude_page, "Grok": self.grok_page,
            "Deepseek": self.deepseek_page, "Llama": self.llama_page,
            "Phi-3 (Local)": self.phi3local_page,
            "Any Other": self.anyother_page
        }
        page_to_show = page_map.get(provider_name)
        if page_to_show:
            self.provider_stacked_widget.setCurrentWidget(page_to_show)

    def on_integration_provider_changed(self, index):
        """Switches the configuration page based on the selected provider."""
        # Index 0 is "None", Index 1 is "Jira"
        self.integrations_stacked_widget.setCurrentIndex(index)

    def on_calibrate_clicked(self):
        """Initiates the background task for manual auto-calibration."""
        self.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        worker = Worker(self._task_run_calibration)
        worker.signals.result.connect(self._handle_calibration_result)
        worker.signals.error.connect(self._handle_calibration_error)
        self.threadpool.start(worker)

    def _task_run_calibration(self, **kwargs):
        """Background worker task that calls the orchestrator."""
        # First, ensure the orchestrator has the latest LLM service initialized
        self.orchestrator._llm_service = None
        return self.orchestrator.run_auto_calibration()

    def _handle_calibration_result(self, result_tuple):
        """Handles the result of the calibration worker."""
        self.setEnabled(True)
        QApplication.restoreOverrideCursor()
        success, message = result_tuple
        if success:
            self.context_limit_input.setText(message)
            if not self.is_calibrating_on_save:
                QMessageBox.information(self, "Success", f"Auto-calibration complete. Context limit has been set to {message} characters.")
        else:
            QMessageBox.critical(self, "Calibration Failed", f"Auto-calibration failed:\n{message}")

        if self.is_calibrating_on_save:
            self.is_calibrating_on_save = False # Reset flag
            if success:
                QMessageBox.information(self, "Calibration Complete",
                            "Auto-calibration is complete and all settings have been saved.")
                self.accept()

    def _handle_calibration_error(self, error_tuple):
        """Handles a system error from the calibration worker."""
        self.setEnabled(True)
        QApplication.restoreOverrideCursor()
        if self.is_calibrating_on_save:
            self.is_calibrating_on_save = False # Reset flag
        error_msg = f"An unexpected error occurred during calibration:\n{error_tuple[1]}"
        QMessageBox.critical(self, "Error", error_msg)

    def _on_calibration_finished(self):
        """Re-enables the main window and clears the status bar."""
        self.setEnabled(True)
        self.statusBar().clearMessage()

    def save_settings_and_accept(self):
        """
        Saves all settings to the database, sets a flag if the provider
        changed, and then accepts (closes) the dialog immediately.
        """
        logging.info("Attempting to save settings from dialog...")
        db_manager = self.orchestrator.db_manager
        new_provider = self.provider_combo_box.currentText()
        self.provider_changed = new_provider != self.initial_provider

        try:
            # The full settings_to_save dictionary remains the same as before
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
                "GROK_API_KEY": self.grok_api_key_input.text(),
                "GROK_REASONING_MODEL": self.grok_reasoning_model_input.text(),
                "GROK_FAST_MODEL": self.grok_fast_model_input.text(),
                "DEEPSEEK_API_KEY": self.deepseek_api_key_input.text(),
                "DEEPSEEK_REASONING_MODEL": self.deepseek_reasoning_model_input.text(),
                "DEEPSEEK_FAST_MODEL": self.deepseek_fast_model_input.text(),
                "LLAMA_API_KEY": self.llama_api_key_input.text(),
                "LLAMA_REASONING_MODEL": self.llama_reasoning_model_input.text(),
                "LLAMA_FAST_MODEL": self.llama_fast_model_input.text(),
                "CUSTOM_ENDPOINT_URL": self.custom_endpoint_url_input.text(),
                "CUSTOM_ENDPOINT_API_KEY": self.custom_endpoint_api_key_input.text(),
                "CUSTOM_REASONING_MODEL": self.custom_reasoning_model_input.text(),
                "CUSTOM_FAST_MODEL": self.custom_fast_model_input.text(),
                "MAX_DEBUG_ATTEMPTS": str(self.max_debug_spin_box.value()),
                "CONTEXT_WINDOW_CHAR_LIMIT": self.context_limit_input.text(),
                "LOGGING_LEVEL": self.logging_combo_box.currentText(),
                "DEFAULT_PROJECT_PATH": self.project_path_input.text(),
                "DEFAULT_ARCHIVE_PATH": self.archive_path_input.text(),
                "SELECTED_DOCX_STYLE_PATH": self.active_style_path,
                "INTEGRATION_PROVIDER": self.provider_list.currentItem().text(),
                "INTEGRATION_URL": self.jira_url_input.text(),
                "INTEGRATION_USERNAME": self.jira_username_input.text(),
                "INTEGRATION_API_TOKEN": self.jira_token_input.text()
            }
            for key, value in settings_to_save.items():
                db_manager.set_config_value(key, value)
            self.orchestrator._llm_service = None
            logging.info("Settings saved. LLM service will be re-initialized on next use.")
            self.accept()
        except Exception as e:
            logging.error(f"Failed to save settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")
