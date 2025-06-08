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

        # Initialize required keys in session state for this step.
        # [cite_start]Adheres to Streamlit best practices for state management. [cite: 491, 492]
        if 'project_root_path' not in st.session_state:
            st.session_state.project_root_path = None
        if 'path_confirmed' not in st.session_state:
            st.session_state.path_confirmed = False

        # If path is already confirmed, show a success message and stop.
        # The flow will continue to the next step in a future implementation.
        if st.session_state.path_confirmed:
            st.success(f"Project root folder confirmed: `{st.session_state.project_root_path}`")
        else:
            path_input = st.text_input(
                "Enter the full local path for the new target application's root folder:",
                placeholder="e.g., E:\\ASDF_Projects\\MyNewApp",
                help="This is the main directory where all the code for your new application will be stored."
            )

            if st.button("Confirm Project Folder"):
                if path_input:
                    try:
                        # Sanitize and normalize the path for the OS
                        normalized_path = os.path.normpath(path_input)

                        # Create the directory. exist_ok=True prevents an error if it already exists.
                        os.makedirs(normalized_path, exist_ok=True)

                        # [cite_start]Store the confirmed path in the session state [cite: 491]
                        st.session_state.project_root_path = normalized_path
                        st.session_state.path_confirmed = True

                        # Force an immediate rerun of the script to reflect the new state
                        st.rerun()

                    except Exception as e:
                        st.error(f"An error occurred while creating the directory: {e}")
                        st.error("Please check the path for invalid characters or permission issues and try again.")
                else:
                    st.warning("Please enter a path before confirming.")