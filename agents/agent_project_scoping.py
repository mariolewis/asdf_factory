# agents/agent_project_scoping.py

"""
This module contains the ProjectScopingAgent class.

This agent is responsible for performing a high-level complexity analysis
on a given specification to prevent the factory from attempting projects
that exceed a configurable complexity threshold.
(ASDF Change Request CR-ASDF-004)
"""

import logging
import textwrap
import json
from llm_service import LLMService

class ProjectScopingAgent:
    """
    Analyzes project specifications to provide a complexity rating.
    (ASDF Change Request CR-ASDF-004)
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
        Performs a detailed complexity and risk analysis on the specification text.
        Returns a structured dictionary with the full analysis.
        """
        import re

        logging.info("ProjectScopingAgent: Analyzing specification for complexity and risk...")

        prompt = textwrap.dedent(f"""
            You are an expert project manager and senior systems architect. Your task is to perform a detailed complexity and risk analysis of the following software specification.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            2.  **Decomposed Analysis:** You must provide a two-part analysis: a `complexity_analysis` and a `risk_assessment`.
            3.  **JSON Schema:** The JSON object MUST strictly adhere to the following schema:
                {{
                  "complexity_analysis": {{
                    "feature_scope": {{"rating": "...", "justification": "..."}},
                    "data_schema": {{"rating": "...", "justification": "..."}},
                    "ui_ux": {{"rating": "...", "justification": "..."}},
                    "integrations": {{"rating": "...", "justification": "..."}}
                  }},
                  "risk_assessment": {{
                    "overall_risk_level": "...",
                    "summary": "...",
                    "token_consumption_outlook": "...",
                    "recommendations": ["..."]
                  }}
                }}
            4.  **Ratings:** All `rating` keys and the `overall_risk_level` key must use one of these values: "Low", "Medium", "High", or "Very Large". The `token_consumption_outlook` must be "Low", "Medium", or "High".
            5.  **Justification & Summary:** The `justification` and `summary` values must be concise, single-sentence or single-paragraph explanations.
            6.  **Recommendations:** The `recommendations` value must be an array of strings. If the risk is high, recommend increasing the 'Context Window Character Limit' setting.
            7.  **No Other Text:** Do not include any text or markdown formatting outside of the raw JSON object itself.

            ---
            SPECIFICATION TEXT:
            {spec_text}
            ---

            JSON OUTPUT:
        """)

        for attempt in range(3): # Try up to 3 times
            try:
                response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if not json_match:
                    raise ValueError("No JSON object found in the LLM response.")

                json_str = json_match.group(0)
                result = json.loads(json_str)
                logging.info(f"Successfully received and parsed complexity and risk analysis on attempt {attempt + 1}.")
                return result

            except json.JSONDecodeError as e:
                logging.warning(f"Attempt {attempt + 1}: Failed to parse LLM response. Error: {e}. Retrying...")
                # Add a correction instruction to the prompt for the next attempt
                prompt += f"\n\n--- PREVIOUS ATTEMPT FAILED ---\nYour last response was not valid JSON due to the following error: {e}. You MUST correct the format and return a single, valid JSON object."
                continue # Go to the next iteration of the loop

        # If all retries fail
        logging.error("ProjectScopingAgent failed to parse LLM response after multiple attempts.")
        return {
            "error": "Failed to get a valid analysis from the AI model after multiple retries.",
            "details": "The LLM provided a consistently malformed JSON response."
        }