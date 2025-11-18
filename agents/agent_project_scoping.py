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
from llm_service import LLMService

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
        prompt = textwrap.dedent(f"""
            You are the Klyve's internal Resource Forecaster. Your task is to perform a holistic analysis on the provided specification to produce a realistic and consistent Delivery Assessment.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            2.  **Analyze Holistically:** You MUST read the entire specification text to inform all of your ratings.
            3.  **Qualitative Rubric:** You MUST use the following qualitative guidelines to determine your ratings for the `complexity_analysis`:
                - **`feature_scope`**: Your rating MUST be one of "Low", "Medium", "High", or "Very Large". A simple utility is "Low". A standard multi-feature app is "Medium". A large system with distinct modules is "High". An enterprise-scale system (e.g., ERP) is "Very Large".
                - **`data_schema`**: Your rating MUST be one of "Low", "Medium", "High", or "Very Large". A few simple tables is "Low". A standard relational schema is "Medium". A schema with complex joins or non-relational data is "High". A distributed, high-throughput, or extremely complex domain model is "Very Large".
                - **`ui_ux`**: Your rating MUST be one of "Low", "Medium", "High", or "Very Large". A simple CLI/form-based UI is "Low". A standard multi-screen CRUD application is "Medium". A highly interactive dashboard with real-time data is "High". A system with specialized graphical editors or novel interaction paradigms is "Very Large".
                - **`integrations`**: Your rating MUST be one of "Low", "Medium", "High", or "Very Large". No external calls is "Low". A few standard REST APIs is "Medium". Multiple disparate systems or legacy platforms is "High". Integration with hardware, proprietary protocols, or a large microservice mesh is "Very Large".
            4. **Risk Assessment Logic:** After the complexity analysis, you MUST determine the `overall_risk_level` using this two-step logic:
                a. **Baseline Risk from Size:** Determine a baseline risk (Low, Medium, High, Critical) based on the sheer length and density of the specification text.
                b. **Adjust Risk for Complexity:** You MUST increase the final `overall_risk_level` above the baseline if your `complexity_analysis` reveals significant inherent difficulty (e.g., two or more "High" ratings).
            5. **JSON Schema & Summary:** Adhere to the required JSON schema and write a non-technical summary for the PM.
            6.  **JSON Schema:** The JSON object MUST strictly adhere to the following schema:
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