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
            # --- Divider for visual separation ---
            st.divider()
            # Call the next step in the flow
            self._run_tech_stack_setup_step()
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

    def _run_tech_stack_setup_step(self):
        """
        Handles the technology stack identification and setup guidance.
        """
        st.subheader("Technology Stack Setup")

        # Initialize session state for this step
        if 'language' not in st.session_state:
            st.session_state.language = None
        if 'frameworks' not in st.session_state:
            st.session_state.frameworks = []

        # Part 1: Select Programming Language
        st.write("First, please specify the primary programming language for your target application.")
        language = st.selectbox(
            "Primary Language:",
            ["", "Python", "Kotlin"], # Add other languages here in the future
            key='language_select'
        )

        st.session_state.language = language

        # Display guidance based on selected language
        if st.session_state.language == "Python":
            with st.expander("Python Environment Setup Guide", expanded=True):
            st.markdown(f"""
                **Best Practice:** It is highly recommended to use a virtual environment for each Python project to manage dependencies separately.

                **Step 1: Verify Python Installation**

                [cite_start]As per the ASDF PRD, we must first check if the required tool is already installed[cite: 72]. Open your command prompt or terminal and run the following command to ensure you have Python 3.9+ installed:
                """)
            st.code("python --version", language="bash")
            st.markdown("""
                If Python is not installed or the version is older than 3.9, please install or update it from the official [Python website](https://www.python.org/).

                **Step 2: Create a Virtual Environment**

                Navigate to your project's root folder (`{st.session_state.project_root_path}`) in your terminal and run this command:
                """)
            st.code("python -m venv venv", language="bash")
            st.markdown("This will create a `venv` folder inside your project directory. This is a crucial step for isolating project dependencies.")

            st.markdown("""
                **Step 3: Activate the Virtual Environment**

                To start using the virtual environment, you need to activate it.
                - **On Windows:**
                """)
            st.code(".\\venv\\Scripts\\activate", language="bash")
            st.markdown("- **On macOS/Linux:**")
            st.code("source venv/bin/activate", language="bash")
            st.markdown("Your terminal prompt should now change to indicate that the virtual environment is active. All subsequent `pip` commands will install packages into this environment.")

            st.markdown("""
                **Step 4: Create a Dependencies File**

                With your virtual environment active, please create an empty file named `requirements.txt` in your project's root folder. This file will be used later by ASDF to manage your project's Python dependencies.
                """)
        elif st.session_state.language == "Kotlin":
            st.info("Guidance for setting up a Kotlin project with Gradle or Maven will be provided here.", icon="💡")

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