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
from llm_service import LLMService, parse_llm_json
import vault

class BuildScriptGeneratorAgent:
    """
    Generates standard build scripts for selected technology stacks using an LLM.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the BuildScriptGeneratorAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the BuildScriptGeneratorAgent.")
        self.llm_service = llm_service


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

        prompt = vault.get_prompt("agent_build_script_generator__prompt_46").format(target_os=target_os, tech_stack_description=tech_stack_description)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            result = parse_llm_json(response_text)

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