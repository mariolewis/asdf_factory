# agents/agent_test_environment_advisor.py

import logging
import json
import textwrap
from typing import Optional, List, Dict
from llm_service import LLMService
import vault

class TestEnvironmentAdvisorAgent:
    """
    An intelligent agent that provides step-by-step guidance for setting up
    the test environment based on a project's technical specification and OS.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the TestEnvironmentAdvisorAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the TestEnvironmentAdvisorAgent.")
        self.llm_service = llm_service

    def get_setup_tasks(self, tech_spec_text: str, target_os: str) -> Optional[List[Dict]]:
        """
        Generates a structured, step-by-step list of test environment setup tasks.
        """
        logging.info(f"Generating test environment setup tasks for OS: {target_os}")

        prompt = vault.get_prompt("agent_test_environment_advisor__prompt_32").format(target_os=target_os, tech_spec_text=tech_spec_text)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            tasks = json.loads(cleaned_response)
            if isinstance(tasks, list):
                return tasks
            return None
        except Exception as e:
            logging.error(f"Failed to generate or parse setup tasks: {e}")
            return None

    def get_help_for_task(self, task_instructions: str, target_os: str) -> str:
        """
        Provides more detailed help or troubleshooting for a specific setup task.

        Args:
            task_instructions (str): The specific instructions the user is having trouble with.
            target_os (str): The target operating system.

        Returns:
            A helpful, detailed explanation as a string.
        """
        logging.info("Getting help for a specific setup task...")

        prompt = vault.get_prompt("agent_test_environment_advisor__prompt_73").format(target_os=target_os, task_instructions=task_instructions)

        try:
            # This is the corrected line, using self.llm_service and generate_text
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            return response_text
        except Exception as e:
            logging.error(f"Failed to get help for task: {e}")
            return "An error occurred while trying to get help. Please check the application logs."