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

    def analyze_complexity(self, spec_text: str, effort_metrics: dict, context_char_limit: int) -> dict:
        """
        Performs a detailed complexity and risk analysis on the specification text,
        anchored by objective metrics to forecast "ASDF Effort".
        Returns a structured dictionary with the full analysis.
        """
        import re
        import json
        import textwrap
        import logging

        logging.info("ProjectScopingAgent: Analyzing specification for ASDF Effort...")

        # Format the objective metrics for the prompt
        metrics_str = (
            f"- Context Pressure Score (Character Count): {effort_metrics.get('context_pressure_score', 0):,}\\n"
            f"- Component Density Score (Keyword Count): {effort_metrics.get('component_density_score', 0)}\\n"
            f"- UI-to-Backend Keyword Ratio: {effort_metrics.get('ui_score', 0)} to {effort_metrics.get('backend_score', 0)}"
        )

        prompt = textwrap.dedent(f"""
            You are the ASDF's internal Resource Forecaster. Your task is to perform a two-part analysis on the provided specification to produce a realistic and consistent Delivery Assessment.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            2.  **Two-Step Analysis:** You will perform two distinct evaluations in order:
                a.  **Part 1: Complexity Analysis:** First, analyze the inherent complexity of the project. You MUST follow the Calibration Rubric below, using the objective scores provided to determine your ratings for Feature Scope and UI/UX.
                b.  **Part 2: Risk Assessment:** After completing the complexity analysis, separately assess the overall delivery risk based on BOTH the project's size (Context Pressure) AND its inherent complexity.
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
            4.  **No Other Text:** Do not include any text or markdown formatting outside of the raw JSON object.

            **--- Objective Metrics (Non-LLM Analysis) ---**
            {metrics_str}
            System's Context Character Limit: {context_char_limit:,}

            **--- Calibration Rubric (For Part 1: Complexity Analysis) ---**
            - **Rule for Feature Scope:** Your rating for "feature_scope" MUST be based directly on the "Component Density Score".
            - Score < 15 = "Low"
            - Score 15-50 = "Medium"
            - Score > 50 = "High"
            - **Rule for UI/UX:** Your rating for "ui_ux" MUST be primarily based on the "UI-to-Backend Keyword Ratio".
            - If the ratio has a UI score of 0, the rating must be "Low".
            - If the UI score is greater than the Backend score, the rating must be at least "Medium".
            - If the UI score is more than double the Backend score OR the specification explicitly calls for a "highly interactive" or "custom" interface, the rating must be "High".
            - **Rule for Data Schema & Integrations:** Your ratings for these must be based on your analysis of the specification text.

            **--- Risk Assessment Logic (For Part 2: Risk Assessment) ---**
            - **Step A: Determine Baseline Risk from Size.** Calculate a baseline risk level (Low, Medium, High, Critical) by comparing the "Context Pressure Score" to the "System's Context Character Limit".
            - Score > 85% of limit = "Critical"
            - Score > 60% of limit = "High"
            - Score > 30% of limit = "Medium"
            - Otherwise = "Low"
            - **Step B: Adjust Risk based on Complexity.** You MUST increase the final "overall_risk_level" above the baseline if the Complexity Analysis shows significant inherent difficulty (e.g., two or more "High" ratings).
            - **Step C: Write the Summary for a Non-Technical PM.** Your summary MUST be written for a Product Manager who does not know what "Context Pressure" or "LLM context windows" are.
            - **DO NOT** use technical jargon.
            - **DO** use an analogy (e.g., project blueprint vs. system's workbench size) to explain the risk.
            - **DO** focus on the practical implications.
            - **DO NOT** reference specific requirement numbers or details not present in the original brief.

            ---
            SPECIFICATION TEXT:
            {spec_text}
            ---

            JSON OUTPUT:
        """)

        for attempt in range(3):
            try:
                response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if not json_match:
                    raise ValueError("No JSON object found in the LLM response.")

                json_str = json_match.group(0)
                result = json.loads(json_str)

                if "complexity_analysis" not in result or "risk_assessment" not in result:
                    raise ValueError("LLM response was valid JSON but missed required keys ('complexity_analysis' or 'risk_assessment').")

                logging.info(f"Successfully received and parsed ASDF Effort analysis on attempt {attempt + 1}.")
                return result

            except (json.JSONDecodeError, ValueError) as e:
                logging.warning(f"Attempt {attempt + 1}: Failed to parse or validate LLM response. Error: {e}. Retrying...")
                prompt += f"\\n\\n--- PREVIOUS ATTEMPT FAILED ---\\nYour last response was not valid or complete due to the following error: {e}. You MUST correct the format and return a single, valid JSON object with all required keys."
                continue

        logging.error("ProjectScopingAgent failed to parse LLM response after multiple attempts.")
        return {{
            "error": "Failed to get a valid analysis from the AI model after multiple retries.",
            "details": "The LLM provided a consistently malformed or incomplete JSON response."
        }}