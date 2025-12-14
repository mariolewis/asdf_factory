# agents/agent_coding_standard_app_target.py

"""
This module contains the CodingStandardAgent_AppTarget class.
This agent implements F-Phase 2.A from the PRD.
"""

import logging
import textwrap
from llm_service import LLMService
import vault

class CodingStandardAgent_AppTarget:
    """
    Agent responsible for generating a detailed, technology-stack-specific
    coding standard for the target application.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the CodingStandardAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the CodingStandardAgent_AppTarget.")
        self.llm_service = llm_service
        logging.info("CodingStandardAgent_AppTarget initialized.")

    def generate_standard(self, tech_spec_text: str, technology_name: str, template_content: str | None = None) -> str:
        """
        Analyzes a technical specification and generates a coding standard document.

        Args:
            tech_spec_text: The full text of the finalized technical specification.
            template_content (str, optional): The content of a template to follow.

        Returns:
            A string containing the generated coding standard, formatted in Markdown.
            Returns an error message on failure.
        """
        logging.info("CodingStandardAgent: Generating coding standard...")

        template_instruction = ""
        if template_content:
            template_instruction = vault.get_prompt("agent_coding_standard_app_target__template_instruction_46").format(template_content=template_content)

        prompt = vault.get_prompt("agent_coding_standard_app_target__prompt_56").format(technology_name=technology_name, template_instruction=template_instruction, tech_spec_text=tech_spec_text)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            logging.info("Successfully generated coding standard from API.")
            return response_text
        except Exception as e:
            logging.error(f"CodingStandardAgent_AppTarget failed: {e}")
            raise e # Re-raise the exception

    def refine_standard(self, current_draft: str, pm_feedback: str) -> str:
        """
        Refines an existing coding standard draft based on PM feedback.

        Args:
            current_draft (str): The current version of the coding standard.
            pm_feedback (str): The feedback from the PM for refinement.

        Returns:
            A string containing the refined coding standard, formatted in Markdown.
        """
        logging.info("CodingStandardAgent: Refining coding standard based on PM feedback...")

        prompt = vault.get_prompt("agent_coding_standard_app_target__prompt_104").format(current_draft=current_draft, pm_feedback=pm_feedback)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            logging.info("Successfully refined coding standard from API.")
            return response_text
        except Exception as e:
            logging.error(f"CodingStandardAgent_AppTarget refinement failed: {e}")
            raise e # Re-raise the exception