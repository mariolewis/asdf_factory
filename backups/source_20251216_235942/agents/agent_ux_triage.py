# agents/agent_ux_triage.py

"""
This module contains the UX_Triage_Agent class.
"""

import logging
import textwrap
import json
from llm_service import LLMService, parse_llm_json
import vault

class UX_Triage_Agent:
    """
    Agent responsible for the initial analysis of a project brief to infer
    if a GUI is required and to recommend the necessity of a dedicated
    UX/UI Design phase.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the UX_Triage_Agent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the UX_Triage_Agent.")
        self.llm_service = llm_service
        logging.info("UX_Triage_Agent initialized.")

    def analyze_brief(self, project_brief: str) -> dict:
        """
        Analyzes a project brief and returns a structured assessment.
        """
        logging.info("UX_Triage_Agent: Analyzing project brief...")

        prompt = vault.get_prompt("agent_ux_triage__prompt_37").format(project_brief=project_brief)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            cleaned_response_text = response_text.strip().replace("```json", "").replace("```", "")
            result = parse_llm_json(cleaned_response_text)
            logging.info("Successfully received initial UX triage analysis.")
            return result
        except Exception as e:
            logging.error(f"UX_Triage_Agent failed to get or parse LLM response: {e}")
            return {{
                "error": "Failed to get a valid analysis from the AI model.",
                "details": str(e)
            }}