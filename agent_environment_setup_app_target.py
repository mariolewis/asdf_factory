# agent_environment_setup_app_target.py

import streamlit as st
import os
import subprocess
import logging
from pathlib import Path

class EnvironmentSetupAgent_AppTarget:
    """
    Guides the PM through the simplified target application environment setup.
    This agent now only handles project path definition and Git initialization.
    """

    def __init__(self):
        """Initializes the agent's state keys in session_state."""
        keys_to_init = {
            'setup_path_confirmed': False,
            'project_path_input': "",
            'show_brownfield_warning': False,
            'agent_setup_complete': False
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

        if st.button("Initialize Git Repository & Complete Setup"):
            try:
                subprocess.run(['git', 'init'], cwd=project_path, check=True, capture_output=True, text=True)
                st.success("Successfully initialized Git repository.")
                # Signal that all steps for this agent are now complete.
                st.session_state.agent_setup_complete = True
                st.rerun()
            except Exception as e:
                st.error(f"Failed to initialize Git repository: {e}")

    def render(self):
        """Renders the setup UI in a controlled, sequential manner."""
        if st.session_state.get('show_brownfield_warning'):
            st.error("The selected folder contains an existing project. Please choose a different folder or click OK to cancel.")
            if st.button("OK"):
                st.session_state.show_brownfield_warning = False
                st.session_state.project_path_input = ""
                st.rerun()
            return

        # --- Step 1: Path Setup ---
        if not st.session_state.setup_path_confirmed:
            self._run_path_setup_step()
            return

        st.success(f"Project root folder confirmed: `{st.session_state.project_root_path}`")
        st.divider()

        # --- Step 2: Git Setup ---
        if not st.session_state.get('agent_setup_complete'):
            self._run_git_initialization_step()
            return

        st.success("Git repository initialized.")
        st.info("All initial setup steps are complete. Click the main button above to proceed.")