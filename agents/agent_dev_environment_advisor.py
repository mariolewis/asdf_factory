# agents/agent_dev_environment_advisor.py

import logging
import json
import textwrap
from typing import Optional, List, Dict
from llm_service import LLMService, parse_llm_json
import vault

class DevEnvironmentAdvisorAgent:
    """
    An intelligent agent that extracts a step-by-step guide for setting up
    the development environment from a project's technical specification.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the DevEnvironmentAdvisorAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the DevEnvironmentAdvisorAgent.")
        self.llm_service = llm_service

    def get_setup_tasks(self, tech_spec_text: str, target_os: str) -> Optional[List[Dict]]:
        """
        Parses the 'Development Environment Setup Guide' section of a technical
        spec and returns a structured list of tasks.
        """
        logging.info(f"Generating development environment setup tasks for OS: {target_os}")

        prompt = vault.get_prompt("agent_dev_environment_advisor__prompt_33").format(target_os=target_os, tech_spec_text=tech_spec_text)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            tasks = parse_llm_json(cleaned_response)
            if isinstance(tasks, list):
                return tasks
            return None
        except Exception as e:
            logging.error(f"Failed to generate or parse dev environment setup tasks: {e}")
            return None