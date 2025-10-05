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

    def analyze_complexity(self, spec_text: str, effort_metrics: dict) -> dict:
        """
        Performs a detailed complexity and risk analysis on the specification text,
        anchored by objective metrics to forecast "ASDF Effort".
        Returns a structured dictionary with the full analysis.
        """
        import re

        logging.info("ProjectScopingAgent: Analyzing specification for ASDF Effort...")

        # Format the objective metrics for the prompt
        metrics_str = (
            f"- Context Pressure Score (Character Count): {effort_metrics.get('context_pressure_score', 0):,}\\n"
            f"- Component Density Score (Keyword Count): {effort_metrics.get('component_density_score', 0)}\\n"
            f"- UI-to-Backend Keyword Ratio: {effort_metrics.get('ui_score', 0)} to {effort_metrics.get('backend_score', 0)}"
        )

        prompt = textwrap.dedent(f"""
            You are the ASDF's internal Resource Forecaster. Your task is to analyze the provided specification and objective metrics to assess the operational effort required by the ASDF to build this project. Your ratings MUST be based on the rubric below.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            2.  **Analyze and Compare:** First, analyze the specification. Then, compare its complexity to the **Objective Metrics** and the **Calibration Rubric** to determine your ratings.
            3.  **JSON Schema:** The JSON object MUST strictly adhere to the following schema, including all specified keys:
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

            **--- Calibration Rubric ---**
            - **Feature Scope:**
              - "Low": A simple project, likely completable in one sprint (Component Density < 15).
              - "Medium": A standard project requiring a few sprints or a moderate number of components (Component Density 15-50).
              - "High": A major project spanning numerous sprints with high component complexity (Component Density > 50).
            - **Data Schema:**
              - "Low": Stateless or involves only a few simple, disconnected data entities.
              - "Medium": Requires a relational state with several interconnected tables or data models.
              - "High": Involves complex data transformations, non-relational data, or high-volume processing.
            - **UI/UX:**
              - "Low": A non-GUI application (CLI, service) or a UI with 1-3 basic screens.
              - "Medium": A standard GUI application with multiple screens and standard user interactions.
              - "High": A highly interactive GUI with custom components, real-time updates, or complex state management.
            - **Integrations:**
              - "Low": The project is self-contained.
              - "Medium": Requires integrating with 1-2 external APIs or services.
              - "High": Primarily an integration hub connecting multiple complex systems.
            - **Overall Risk Level:** Base this on the highest rating from the categories above, giving extra weight to a high Context Pressure Score. A Context Pressure Score over 1,000,000 characters should significantly increase the risk level.

            ---
            SPECIFICATION TEXT:
            {spec_text}
            ---

            JSON OUTPUT:
        """)

        # The retry loop from the original implementation is preserved
        for attempt in range(3):
            try:
                response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if not json_match:
                    raise ValueError("No JSON object found in the LLM response.")

                json_str = json_match.group(0)
                result = json.loads(json_str)

                # --- THIS IS THE FIX ---
                # Validate that the parsed JSON has the required structure before returning.
                if "complexity_analysis" not in result or "risk_assessment" not in result:
                    raise ValueError("LLM response was valid JSON but missed required keys ('complexity_analysis' or 'risk_assessment').")
                # --- END OF FIX ---

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