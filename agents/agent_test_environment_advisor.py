# agents/agent_test_environment_advisor.py

import logging
import json
import textwrap
from typing import Optional, List, Dict
from llm_service import LLMService

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

        Args:
            tech_spec_text (str): The project's full technical specification.
            target_os (str): The target operating system (e.g., "Windows", "Linux", "macOS").

        Returns:
            A list of dictionaries, where each dictionary is a setup task, or None on failure.
        """
        logging.info(f"Generating test environment setup tasks for OS: {target_os}")

        prompt = textwrap.dedent(f"""
            You are an expert DevOps and QA engineer. Based on the provided technical specification for a "{target_os}" environment, provide a step-by-step plan for setting up the complete testing toolchain.

            Your response MUST be a single, valid JSON array of objects. Each object in the array represents a single, logical tool or framework to install and MUST have two keys:
            - "tool_name": A string with the human-readable name of the tool (e.g., "pytest and pytest-mock", "JUnit 5").
            - "instructions": A string containing the clear, step-by-step installation and setup instructions for that specific tool, tailored for the "{target_os}" environment.

            **ADDITIONAL MANDATORY INSTRUCTIONS:**
            1.  **Grouping:** You MUST group all actions for a single tool (e.g., "install pytest," "install pytest-cov") into a single JSON object. Do not create separate top-level steps for sub-components of the same tool.
            2.  **Formatting:** You MUST NOT use Markdown headings (e.g., '#', '##') inside the "instructions" string. Use bolding with asterisks or simple numbered lists for clarity.

            Do not include any other text or explanations outside of the raw JSON array itself.

            **--- Technical Specification ---**
            {tech_spec_text}
            **--- End of Specification ---**

            **JSON Array Output:**
        """)

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

        prompt = textwrap.dedent(f"""
            You are a helpful and clear technical support assistant. A user is having trouble with the following software installation instruction on a "{target_os}" operating system.

            Please provide more detailed clarification, suggest alternative installation methods, or list common troubleshooting steps (like checking the system's PATH, permissions, or firewall settings) to help them resolve the issue. Format your response clearly using Markdown.

            **--- User's problematic instruction ---**
            {task_instructions}
            **--- End of instruction ---**

            **Helpful Response:**
        """)

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Failed to get help for task: {e}")
            return "An error occurred while trying to get help. Please check the application logs."