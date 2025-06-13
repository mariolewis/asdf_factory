# agents/agent_build_script_generator.py

"""
This module contains the BuildScriptGeneratorAgent class.

This agent is responsible for generating standard, starter build scripts
for different technology stacks, as per CR-ASDF-005.
"""

import textwrap
from typing import Tuple, Optional

class BuildScriptGeneratorAgent:
    """
    Generates standard build scripts for selected technology stacks.
    (ASDF Change Request CR-ASDF-005)
    """

    def __init__(self):
        """Initializes the BuildScriptGeneratorAgent."""
        pass

    def generate_script(self, tech_stack: str) -> Optional[Tuple[str, str]]:
        """
        Generates a filename and content for a standard build script.

        Args:
            tech_stack: The technology stack selected (e.g., "Python", "Kotlin").

        Returns:
            A tuple containing (filename, file_content), or None if the
            tech_stack is not supported.
        """
        if tech_stack == "Python":
            filename = "requirements.txt"
            content = textwrap.dedent("""
                # This file is managed by the ASDF.
                # Add your project's Python dependencies here, one per line.
                # Example:
                # requests==2.31.0
                # pandas
            """).strip()
            return filename, content

        elif tech_stack == "Kotlin":
            filename = "build.gradle.kts"
            content = textwrap.dedent("""
                /*
                 * This file is managed by the ASDF.
                 * This is a standard starter build script for a Kotlin project using Gradle.
                 */
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
            """).strip()
            return filename, content

        # Return None if the tech stack has no predefined build script
        return None