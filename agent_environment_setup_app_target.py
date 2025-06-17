# agent_environment_setup_app_target.py

import streamlit as st
import os
import subprocess
import logging
from pathlib import Path
from agents.agent_build_script_generator import BuildScriptGeneratorAgent

class EnvironmentSetupAgent_AppTarget:
    """
    Guides the PM through target application environment setup.
    This agent manages the UI and state for the ENV_SETUP_TARGET_APP phase.
    """

    def __init__(self):
        """Initializes the agent's state keys in session_state."""
        keys_to_init = {
            'setup_path_confirmed': False,
            'setup_git_initialized': False,
            'setup_tech_stack_confirmed': False,
            'project_path_input': "",
            'show_brownfield_warning': False,
            'setup_language': "",
            'setup_is_build_automated': True,
            'apex_file_name_input': ""
        }
        for key, value in keys_to_init.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _check_for_brownfield_project(self, directory_path: str) -> bool:
        """Scans a directory for signs of an existing project."""
        extensions_to_check = ('*.py', '*.kt', '*.java', '*.xml', '*.gradle', '*.yml', '*.json')
        for extension in extensions_to_check:
            if list(Path(directory_path).glob(f'**/{extension}')):
                return True
        if (Path(directory_path) / '.git').exists():
            return True
        return False

    def _run_path_setup_step(self):
        """Handles the UI for defining the project's root folder."""
        st.subheader("1. Define Target Project Root Folder")
        with st.session_state.orchestrator.db_manager as db:
            default_path = db.get_config_value("DEFAULT_PROJECT_PATH") or ""

        st.session_state.project_path_input = st.text_input(
            "Enter the full local path for the new target application's root folder:",
            value=st.session_state.project_path_input or default_path
        )

        if st.button("Confirm Project Folder"):
            path_input = st.session_state.project_path_input
            if path_input:
                try:
                    normalized_path = Path(path_input).resolve()
                    if self._check_for_brownfield_project(str(normalized_path)):
                        st.session_state.show_brownfield_warning = True
                    else:
                        normalized_path.mkdir(parents=True, exist_ok=True)
                        st.session_state.project_root_path = str(normalized_path)
                        st.session_state.setup_path_confirmed = True
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred: {e}")
            else:
                st.warning("Please enter a path.")

    def _run_git_initialization_step(self):
        """Handles the UI for initializing the Git repository."""
        st.subheader("2. Initialize Git Repository")
        project_path = st.session_state.project_root_path

        if st.button("Initialize Git Repository"):
            try:
                subprocess.run(['git', 'init'], cwd=project_path, check=True, capture_output=True, text=True)
                st.session_state.setup_git_initialized = True
                st.success("Successfully initialized Git repository.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to initialize Git repository: {e}")

    def _run_tech_stack_setup_step(self):
        """Handles UI for Technology Stack, Build Script, and Apex File Name."""
        st.subheader("3. Define Technology & Build Configuration")

        st.session_state.setup_language = st.selectbox(
            "Primary Programming Language:",
            ["", "Python", "Kotlin"],
            key='language_select_key'
        )

        if st.session_state.setup_language:
            build_choice_str = st.radio(
                "Build Script Handling:",
                ["Have ASDF generate a standard build script", "I will manage the build script manually"],
                key="build_script_radio_key"
            )
            st.session_state.setup_is_build_automated = (build_choice_str == "Have ASDF generate a standard build script")

        st.text_input(
            "Main Executable File Name (without extension):",
            placeholder="e.g., 'main' or 'app'",
            key="apex_file_name_input"
        )

        if st.session_state.setup_language and st.session_state.apex_file_name_input:
            if st.button("Confirm Technology & Build", type="primary"):
                if st.session_state.setup_is_build_automated:
                    agent = BuildScriptGeneratorAgent()
                    script_info = agent.generate_script(st.session_state.setup_language)
                    if script_info:
                        filename, content = script_info
                        try:
                            project_path = Path(st.session_state.project_root_path)
                            (project_path / filename).write_text(content, encoding='utf-8')
                            st.success(f"Generated and saved `{filename}`.")
                        except Exception as e:
                            st.error(f"Failed to save build script: {e}")

                st.session_state.setup_tech_stack_confirmed = True
                st.rerun()

    def render(self):
        """Renders the setup UI in a controlled, sequential manner."""
        if st.session_state.get('show_brownfield_warning'):
            st.error("The selected folder contains an existing project. Please choose a different folder or click OK to cancel.")
            if st.button("OK"):
                st.session_state.show_brownfield_warning = False
                st.session_state.project_path_input = ""
                st.rerun()
            return

        if not st.session_state.setup_path_confirmed:
            self._run_path_setup_step()
            return

        st.success(f"Project root folder confirmed: `{st.session_state.project_root_path}`")
        st.divider()

        if not st.session_state.setup_git_initialized:
            self._run_git_initialization_step()
            return

        st.success("Git repository initialized.")
        st.divider()

        if not st.session_state.setup_tech_stack_confirmed:
            self._run_tech_stack_setup_step()
            return

        st.success("Technology & Build configuration confirmed.")
        st.info("All setup steps are complete. Click the main button above to proceed.")
        # Signal to the main app that this agent's work is done.
        st.session_state.agent_setup_complete = True
