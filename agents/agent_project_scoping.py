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
import google.generativeai as genai

class ProjectScopingAgent:
    """
    Analyzes project specifications to provide a complexity rating.
    (ASDF Change Request CR-ASDF-004)
    """

    def __init__(self, api_key: str):
        """
        Initializes the ProjectScopingAgent.

        Args:
            api_key (str): The Gemini API key for LLM interactions.
        """
        if not api_key:
            raise ValueError("API key is required for the ProjectScopingAgent.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

    def analyze_complexity(self, spec_text: str) -> dict:
        """
        Performs a detailed complexity and risk analysis on the specification text.
        Returns a structured dictionary with the full analysis.
        (ASDF Change Request CR-ASDF-004, Stage 2: Complexity Analysis Filter)

        Args:
            spec_text: The full text of the specification.

        Returns:
            A dictionary containing the full analysis, or an error dictionary on failure.
        """
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

        try:
            # Using a more capable model for this complex analytical task
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(prompt)
            # Clean the response to ensure it's valid JSON
            cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(cleaned_response_text)
            logging.info(f"Successfully received complexity and risk analysis.")
            return result
        except (json.JSONDecodeError, AttributeError, ValueError, KeyError) as e:
            logging.error(f"ProjectScopingAgent failed to parse LLM response: {e}\\nResponse was: {response.text}")
            return {{
                "error": "Failed to get a valid analysis from the AI model.",
                "details": response.text
            }}
        except Exception as e:
            logging.error(f"ProjectScopingAgent API call failed: {e}")
            return {{
                "error": "An unexpected error occurred during analysis.",
                "details": str(e)
            }}