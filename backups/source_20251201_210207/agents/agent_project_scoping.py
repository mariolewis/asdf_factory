# agents/agent_project_scoping.py

"""
This module contains the ProjectScopingAgent class.

This agent is responsible for performing a high-level complexity analysis
on a given specification to prevent the factory from attempting projects
that exceed a configurable complexity threshold.
(Klyve Change Request CR-Klyve-004)
"""

import logging
import textwrap
import json
from llm_service import LLMService, parse_llm_json
import vault

class ProjectScopingAgent:
    """
    Analyzes project specifications to provide a complexity rating.
    (Klyve Change Request CR-Klyve-004)
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the ProjectScopingAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the ProjectScopingAgent.")
        self.llm_service = llm_service

    def analyze_complexity(self, spec_text: str) -> dict:
        """
        Performs a detailed complexity and risk analysis on the specification text,
        anchored by objective metrics to forecast "Klyve Effort".
        Returns a structured dictionary with the full analysis.
        """
        import re
        import json
        import textwrap
        import logging

        logging.info("ProjectScopingAgent: Analyzing specification for Klyve Effort...")


        # After (REPLACE the old prompt with this new one)
        prompt = vault.get_prompt("agent_project_scoping__prompt_49").format(spec_text=spec_text)

        for attempt in range(3):
            try:
                response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if not json_match:
                    raise ValueError("No JSON object found in the LLM response.")

                json_str = json_match.group(0)
                result = parse_llm_json(json_str)

                if "complexity_analysis" not in result or "risk_assessment" not in result:
                    raise ValueError("LLM response was valid JSON but missed required keys ('complexity_analysis' or 'risk_assessment').")

                logging.info(f"Successfully received and parsed Klyve Effort analysis on attempt {attempt + 1}.")
                return result

            except (json.JSONDecodeError, ValueError) as e:
                logging.warning(f"Attempt {attempt + 1}: Failed to parse or validate LLM response. Error: {e}. Retrying...")
                prompt += f"\\n\\n--- PREVIOUS ATTEMPT FAILED ---\\nYour last response was not valid or complete due to the following error: {e}. You MUST correct the format and return a single, valid JSON object with all required keys."
                continue

        logging.error("ProjectScopingAgent failed to parse LLM response after multiple attempts.")
        return {
            "error": "Failed to get a valid analysis from the AI model after multiple retries.",
            "details": "The LLM provided a consistently malformed or incomplete JSON response."
        }