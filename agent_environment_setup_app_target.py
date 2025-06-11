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
import textwrap


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

        if os.path.exists(git_dir):
            st.session_state.git_initialized = True

        if st.session_state.git_initialized:
            st.success("Git repository is initialized in the project folder.")
            st.divider()
            self._run_tech_stack_setup_step()
        else:
            st.info("The project folder is not yet a Git repository. This is a required step.")
            if st.button("Initialize Git Repository"):
                try:
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

        if 'language' not in st.session_state:
            st.session_state.language = None
        if 'frameworks' not in st.session_state:
            st.session_state.frameworks = []

        st.write("First, please specify the primary programming language for your target application.")
        language = st.selectbox(
            "Primary Language:",
            ["", "Python", "Kotlin"],
            key='language_select'
        )
        st.session_state.language = language

        if st.session_state.language == "Python":
            with st.expander("Python Environment Setup Guide", expanded=True):
                st.markdown(textwrap.dedent(f"""
                    **Best Practice:** It is highly recommended to use a virtual environment for each Python project to manage dependencies separately.

                    **Step 1: Verify Python Installation**

                    As per the ASDF PRD, we must first check if the required tool is already installed. Open your command prompt or terminal and run the following command to ensure you have Python 3.9+ installed:
                    """))
                st.code("python --version", language="bash")
                st.markdown(textwrap.dedent("""
                    If Python is not installed or the version is older than 3.9, please install or update it from the official [Python website](https://www.python.org/).

                    **Step 2: Create a Virtual Environment**
                    """))
                st.markdown(textwrap.dedent(f"""
                    Navigate to your project's root folder (`{st.session_state.project_root_path}`) in your terminal and run this command:
                    """))
                st.code("python -m venv venv", language="bash")
                st.markdown(textwrap.dedent("""
                    This will create a `venv` folder inside your project directory. This is a crucial step for isolating project dependencies.

                    **Step 3: Activate the Virtual Environment**

                    To start using the virtual environment, you need to activate it.
                    - **On Windows:**
                    """))
                st.code(".\\venv\\Scripts\\activate", language="bash")
                st.markdown(textwrap.dedent("""
                    - **On macOS/Linux:**
                    """))
                st.code("source venv/bin/activate", language="bash")
                st.markdown(textwrap.dedent("""
                    Your terminal prompt should now change to indicate that the virtual environment is active. All subsequent `pip` commands will install packages into this environment.

                    **Step 4: Create a Dependencies File**

                    With your virtual environment active, please create an empty file named `requirements.txt` in your project's root folder. This file will be used later by ASDF to manage your project's Python dependencies.
                    """))

        elif st.session_state.language == "Kotlin":
            with st.expander("Kotlin Environment Setup Guide", expanded=True):
                st.markdown(textwrap.dedent("""
                    **Prerequisites:** Kotlin development for the JVM (Java Virtual Machine) requires a JDK (Java Development Kit) and a build tool like Gradle or Maven. This guide uses Gradle.

                    **Step 1: Verify JDK Installation**

                    First, check if you have a JDK installed (version 8 or higher is recommended). Open your terminal and run:
                    """))
                st.code("java -version", language="bash")
                st.markdown(textwrap.dedent("""
                    If the JDK is not installed, we recommend installing it from a trusted provider like [Adoptium](https://adoptium.net/).

                    **Step 2: Verify Gradle Installation**

                    Next, check if Gradle is installed by running this command:
                    """))
                st.code("gradle -v", language="bash")
                st.markdown(textwrap.dedent("""
                    If it is not installed, you can find instructions on the [official Gradle website](https://gradle.org/install/).
                    """))
                st.markdown(textwrap.dedent(f"""
                    **Step 3: Create `build.gradle.kts` File**

                    In your project's root folder (`{st.session_state.project_root_path}`), create a file named `build.gradle.kts`. This file tells Gradle how to build your project. Paste the following basic configuration into it:
                    """))
                st.code(textwrap.dedent("""
                    plugins {
                        kotlin("jvm") version "1.9.23"
                        application
                    }

                    group = "com.example"
                    version = "1.0-SNAPSHOT"

                    repositories {
                        mavenCentral()
                    }

                    dependencies {
                        testImplementation(kotlin("test"))
                    }

                    application {
                        mainClass.set("com.example.MainKt")
                    }
                    """), language="kotlin")
                st.markdown(textwrap.dedent("""
                    You can adjust the `group`, `version`, and `mainClass` later as needed.

                    **Step 4: Create Directory Structure**
                    """))
                st.markdown(textwrap.dedent(f"""
                    Finally, create the standard source directory structure for a Gradle project inside your root folder (`{st.session_state.project_root_path}`):
                    `src/main/kotlin`

                    ASDF will place all new Kotlin source code files inside this `src/main/kotlin` directory.
                    """))

        # At the end of _run_tech_stack_setup_step()
        st.divider()
        if st.session_state.language:
            self._run_apex_definition_step()

    def _run_apex_definition_step(self):
        """
        Handles the definition of the project's main executable file.
        """
        st.subheader("Name the Main Executable File)")
        st.markdown("Please provide a name for the main executable file for your application, **without the file extension**.")

        st.text_input(
            "Executable File Name:",
            placeholder="e.g., 'main' for main.py, or 'app' for app.py",
            key="apex_file_name_input"
        )

    def run_setup_flow(self):
        """
        Executes the full environment setup flow, starting with defining the project path.
        """
        st.header("Phase 0: Target Application Environment Setup")
        st.write(
            "This phase will guide you through setting up the necessary environment "
            "for the new application you want to build."
        )

        st.subheader("Define Target Project Root Folder")

        if 'project_root_path' not in st.session_state:
            st.session_state.project_root_path = None
        if 'path_confirmed' not in st.session_state:
            st.session_state.path_confirmed = False
        if 'git_initialized' not in st.session_state:
            st.session_state.git_initialized = False

        if st.session_state.path_confirmed:
            st.success(f"Project root folder confirmed: `{st.session_state.project_root_path}`")
            st.divider()
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