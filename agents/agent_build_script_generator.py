# agents/agent_build_script_generator.py

"""
This module contains the BuildScriptGeneratorAgent class.
This agent is now intelligent and can generate a build script for any
technology stack by querying the LLM.
"""

import logging
import json
import textwrap
from typing import Tuple, Optional
import google.generativeai as genai

class BuildScriptGeneratorAgent:
    """
    Generates standard build scripts for selected technology stacks using an LLM.
    """

    def __init__(self, api_key: str):
        """
        Initializes the BuildScriptGeneratorAgent.

        Args:
            api_key (str): The Gemini API key for LLM interactions.
        """
        if not api_key:
            raise ValueError("API key is required for the BuildScriptGeneratorAgent.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20') # Flash is suitable for this constrained task

    #
# --- REPLACE THE ENTIRE METHOD WITH THIS ---
#
    def generate_script(self, tech_stack_description: str, target_os: str) -> Optional[Tuple[str, str]]:
        """
        Generates a filename and content for a build script via LLM,
        tailored for a specific OS.

        Args:
            tech_stack_description (str): A description of the technology stack.
            target_os (str): The target OS (e.g., "Windows", "Linux", "macOS").

        Returns:
            A tuple containing (filename, file_content), or None on failure.
        """
        logging.info(f"Generating build script for tech stack on OS: {target_os}")

        prompt = textwrap.dedent(f"""
            You are an expert build engineer. Your task is to generate a standard, starter build script based on the provided technology stack description, specifically for a "{target_os}" environment.

            You MUST return your response as a single, valid JSON object with two keys:
            - "filename": The conventional name for the build script (e.g., "pom.xml", "build.gradle.kts", "requirements.txt").
            - "content": A string containing the complete text of a high-quality starter build script. Ensure any shell commands or paths are correct for the specified "{target_os}" environment.

            Do not include any other text or explanations outside of the raw JSON object.

            **Technology Stack Description:**
            ---
            {tech_stack_description}
            ---

            **JSON Output:**
        """)

        try:
            response = self.model.generate_content(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(cleaned_response)

            filename = result.get("filename")
            content = result.get("content")

            if filename and content:
                return filename, content
            else:
                logging.error("LLM output was missing 'filename' or 'content' keys.")
                return None
        except Exception as e:
            logging.error(f"An unexpected error occurred during build script generation: {e}")
            return None