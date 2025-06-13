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
import glob
from pathlib import Path
from agents.agent_build_script_generator import BuildScriptGeneratorAgent


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

    def _check_for_brownfield_project(self, directory_path: str) -> bool:
        """
        Scans a directory to see if it contains signs of an existing project.
        (ASDF Change Request CR-ASDF-007)

        Args:
            directory_path: The path to the directory to check.

        Returns:
            True if signs of an existing project are found, False otherwise.
        """
        # [cite_start]Check for common source code or build files. [cite: 70]
        extensions_to_check = ('*.py', '*.kt', '*.java', '*.xml', '*.gradle', '*.yml', '*.json')
        for extension in extensions_to_check:
            if list(Path(directory_path).glob(f'**/{extension}')):
                logging.warning(f"Brownfield check: Found existing files with extension {extension}.")
                return True

        # [cite_start]Check for a .git directory. [cite: 70]
        if (Path(directory_path) / '.git').exists():
            logging.warning("Brownfield check: Found existing .git directory.")
            return True

        # [cite_start]Condition: Directory is not empty but lacks ASDF metadata. [cite: 71]
        # For now, the presence of any of the above files is our trigger.
        # A future implementation could check for a specific ASDF metadata file.

        return False

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
        Handles technology stack identification and build script generation.
        """
        st.subheader("Technology Stack & Build Script")

        # Initialize session state keys for this step
        if 'language' not in st.session_state:
            st.session_state.language = None
        if 'build_script_choice_made' not in st.session_state:
            st.session_state.build_script_choice_made = False

        # Step 1: Select the language
        st.write("First, please specify the primary programming language for your target application.")
        language = st.selectbox(
            "Primary Language:",
            ["", "Python", "Kotlin"],
            key='language_select',
            disabled=st.session_state.build_script_choice_made # Disable after choice is made
        )
        st.session_state.language = language

        if st.session_state.language and not st.session_state.build_script_choice_made:
            st.divider()
            st.write("**Build Script Generation (CR-ASDF-005)**")

            # Step 2: Present the choice for build script generation
            build_choice = st.radio(
                "How should the build script be handled?",
                options=[
                    "Have ASDF generate a standard build script",
                    "I will manage the build script manually"
                ],
                key="build_script_radio"
            )

            if st.button("Confirm Build Script Choice"):
                if build_choice == "Have ASDF generate a standard build script":
                    agent = BuildScriptGeneratorAgent()
                    script_info = agent.generate_script(st.session_state.language)
                    if script_info:
                        filename, content = script_info
                        try:
                            # Save the generated script to the project root
                            project_path = Path(st.session_state.project_root_path)
                            script_path = project_path / filename
                            script_path.write_text(content, encoding='utf-8')

                            # As per CR-ASDF-005, the script should be registered in the RoWD.
                            # This will be handled by a later process, for now we confirm generation.
                            st.success(f"Generated and saved `{filename}` to the project root.")
                            st.session_state.build_script_choice_made = True
                            st.rerun()

                        except Exception as e:
                            st.error(f"Failed to save build script: {e}")
                    else:
                        st.warning(f"No standard build script available for '{st.session_state.language}'. Please manage it manually.")

                else: # Manual management
                    st.info("You have opted to manage the build script manually. The factory will not create one.")
                    st.session_state.build_script_choice_made = True
                    st.rerun()

        # Step 3: Show the relevant setup guide and next step only after choice is made
        if st.session_state.build_script_choice_made:
            if st.session_state.language == "Python":
                with st.expander("Python Environment Setup Guide", expanded=True):
                    # Python setup guide content remains the same
                    st.markdown(textwrap.dedent(f"""...""")) # Truncated for brevity

            elif st.session_state.language == "Kotlin":
                 with st.expander("Kotlin Environment Setup Guide", expanded=True):
                    # Kotlin setup guide content remains the same
                    st.markdown(textwrap.dedent(f"""...""")) # Truncated for brevity

            st.divider()
            self._run_apex_definition_step()

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
        Executes the full environment setup flow, including the brownfield check.
        """
        st.header("Phase 0: Target Application Environment Setup")

        # (CR-ASDF-007) UI for the safety lockout warning
        if st.session_state.get('show_brownfield_warning'):
            st.error("Unrecognized Project Detected")
            st.warning(
                "The selected folder contains existing source code or a git repository "
                "that was not created by this application. The factory cannot manage or "
                "modify unrecognized projects to avoid data loss."
            )
            if st.button("OK"):
                # Reset state to allow the user to choose a different path
                st.session_state.show_brownfield_warning = False
                st.session_state.path_confirmed = False
                st.session_state.project_root_path = None
                st.rerun()
            return # Halt further rendering

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
                placeholder="e.g., E:\\ASDF_Projects\\MyNewApp"
            )

            if st.button("Confirm Project Folder"):
                if path_input:
                    try:
                        normalized_path = Path(path_input).resolve()
                        normalized_path.mkdir(parents=True, exist_ok=True)

                        # (CR-ASDF-007) Perform the brownfield check here
                        if self._check_for_brownfield_project(str(normalized_path)):
                            st.session_state.show_brownfield_warning = True
                            st.rerun()
                        else:
                            st.session_state.project_root_path = str(normalized_path)
                            st.session_state.path_confirmed = True
                            st.rerun()

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                else:
                    st.warning("Please enter a path before confirming.")