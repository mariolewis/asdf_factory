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
        Performs a high-level complexity analysis on the specification text.
        (ASDF Change Request CR-ASDF-004, Stage 2: Complexity Analysis Filter)

        Args:
            spec_text: The full text of the specification.

        Returns:
            A dictionary containing the complexity rating and justification.
            Example: {"rating": "High", "justification": "The project involves... a lot of things"}
        """
        logging.info("ProjectScopingAgent: Analyzing specification complexity...")

        prompt = textwrap.dedent(f"""
            As an expert project manager and systems architect, analyze the following software specification.
            Your task is to provide a high-level complexity rating. The rating should be one of: "Low", "Medium", "High", or "Very Large".

            Consider factors such as:
            - The number of distinct features or modules.
            - The requirement for database schemas and the number of tables.
            - The presence of complex business logic, algorithms, or external integrations.
            - The scope of the user interface.

            Provide your output in a JSON format with two keys: "rating" and "justification".
            The "justification" should be a concise, one-sentence explanation for your rating.

            ---
            SPECIFICATION TEXT:
            {spec_text}
            ---

            JSON OUTPUT:
        """)

        try:
            response = self.model.generate_content(prompt)
            # Clean the response to ensure it's valid JSON
            cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(cleaned_response_text)
            logging.info(f"Successfully received complexity analysis: {result}")
            return result
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logging.error(f"ProjectScopingAgent failed to parse LLM response: {e}\\nResponse was: {response.text}")
            return {"rating": "Error", "justification": "Failed to get a valid analysis from the AI model."}
        except Exception as e:
            logging.error(f"ProjectScopingAgent API call failed: {e}")
            return {"rating": "Error", "justification": f"An unexpected error occurred: {e}"}