# agents/agent_dev_environment_advisor.py

import logging
import json
import textwrap
from typing import Optional, List, Dict
from llm_service import LLMService

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

        prompt = textwrap.dedent(f"""
            You are an expert DevOps engineer. Your task is to parse ONLY the "Development Environment Setup Guide" section from the provided Technical Specification and create a step-by-step plan for a "{target_os}" environment.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array of objects `[]`.
            2.  **Object Schema:** Each object MUST have two keys: "tool_name" (a string, e.g., "Python 3.9", "Node.js") and "instructions" (a string detailing the setup steps for that tool).
            3.  **Focus:** You MUST ignore all other sections of the document (like testing, architecture, etc.) and focus exclusively on the development environment setup. If no such section exists, return an empty array.
            4.  **Use Markdown:** The "instructions" value MUST be formatted using simple Markdown for clarity (e.g., bulleted lists with `*`, bolding with `**`, and code snippets with backticks).
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
            logging.error(f"Failed to generate or parse dev environment setup tasks: {e}")
            return None