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
        """
        logging.info(f"Generating test environment setup tasks for OS: {target_os}")

        prompt = textwrap.dedent(f"""
            You are an expert DevOps engineer. Based on the provided technical specification for a "{target_os}" environment, provide a step-by-step plan for setting up the testing toolchain.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array of objects `[]`.
            2.  **Object Schema:** Each object MUST have two keys: "tool_name" (a string) and "instructions" (a string).
            3.  **Grouping:** Group all actions for a single tool (e.g., installing pytest and its plugins) into a single object.
            4.  **STRICT MARKDOWN FORMATTING:** The "instructions" value MUST use Markdown for all formatting. Use '##' for main headings and '###' for sub-headings. For lists, each item MUST start on a new line with an asterisk and a space (e.g., "* List item text."). Paragraphs MUST be separated by a full blank line. This is mandatory.
            5.  **No Other Text:** Do not include any text or explanations outside of the raw JSON array.

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
            # This is the corrected line, using self.llm_service and generate_text
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            return response_text
        except Exception as e:
            logging.error(f"Failed to get help for task: {e}")
            return "An error occurred while trying to get help. Please check the application logs."