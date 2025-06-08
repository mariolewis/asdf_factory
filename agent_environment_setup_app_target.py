# agent_environment_setup_app_target.py

"""
This module contains the EnvironmentSetupAgent_AppTarget class.

The agent is responsible for guiding the PM through the process of setting up
the development environment for the target application. This includes defining
the project path, ensuring necessary tools are installed, and initializing a
Git repository. (ASDF PRD v0.2, Phase 0)
"""

import streamlit as st
import os
import subprocess


class EnvironmentSetupAgent_AppTarget:
    """
    Guides the PM through target application environment setup.

    This agent uses a series of interactive steps within the Streamlit GUI
    to ensure the environment for the application to be built is ready.
    It is designed to adhere to the Single Responsibility Principle.
    (ASDF Dev Plan v0.2, F-Dev 2.1)
    """

    def __init__(self):
        """Initializes the EnvironmentSetupAgent_AppTarget."""
        pass

    def _run_git_initialization_step(self):
        """
        Handles the Git repository initialization step.
        This is a private method intended for use by run_setup_flow.
        """
        st.subheader("Initialize Git Repository")

        project_path = st.session_state.project_root_path
        git_dir = os.path.join(project_path, '.git')

        # Check if git is already initialized and update session state accordingly.
        if os.path.exists(git_dir):
            st.session_state.git_initialized = True

        if st.session_state.git_initialized:
            st.success("Git repository is initialized in the project folder.")
        else:
            st.info("The project folder is not yet a Git repository. This is a required step.")
            if st.button("Initialize Git Repository"):
                try:
                    # Using subprocess to run the 'git init' command.
                    # The 'cwd' argument sets the current working directory for the command.
                    result = subprocess.run(
                        ['git', 'init'],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    st.session_state.git_initialized = True
                    st.success("Successfully initialized an empty Git repository.")
                    st.code(result.stdout)
                    st.rerun()
                except FileNotFoundError:
                    st.error("Error: The 'git' command was not found. Is Git installed and in your system's PATH variable?")
                except subprocess.CalledProcessError as e:
                    st.error(f"Failed to initialize Git repository. Error:\n{e.stderr}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

    def run_setup_flow(self):
        """
        Executes the full environment setup flow, starting with defining the project path.
        """
        st.header("Phase 0: Target Application Environment Setup")
        st.write(
            "This phase will guide you through setting up the necessary environment "
            "for the new application you want to build."
        )

        # Using a subheader for a sub-step, per our formatting discussion.
        st.subheader("Define Target Project Root Folder")

        # Initialize required keys in session state for this flow.
        if 'project_root_path' not in st.session_state:
            st.session_state.project_root_path = None
        if 'path_confirmed' not in st.session_state:
            st.session_state.path_confirmed = False
        if 'git_initialized' not in st.session_state:
            st.session_state.git_initialized = False

        if st.session_state.path_confirmed:
            st.success(f"Project root folder confirmed: `{st.session_state.project_root_path}`")
            # --- Divider for visual separation ---
            st.divider()
            # Call the next step in the flow
            self._run_git_initialization_step()
        else:
            path_input = st.text_input(
                "Enter the full local path for the new target application's root folder:",
                placeholder="e.g., E:\\ASDF_Projects\\MyNewApp",
                help="This is the main directory where all the code for your new application will be stored."
            )

            if st.button("Confirm Project Folder"):
                if path_input:
                    try:
                        normalized_path = os.path.normpath(path_input)
                        os.makedirs(normalized_path, exist_ok=True)
                        st.session_state.project_root_path = normalized_path
                        st.session_state.path_confirmed = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred while creating the directory: {e}")
                        st.error("Please check the path for invalid characters or permission issues and try again.")
                else:
                    st.warning("Please enter a path before confirming.")