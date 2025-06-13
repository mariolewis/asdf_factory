# agents/agent_planning_app_target.py

"""
This module contains the PlanningAgent_AppTarget class.
(ASDF PRD v0.4, F-Phase 2)
"""

import logging
import textwrap
import google.generativeai as genai
import json

class PlanningAgent_AppTarget:
    """
    Agent responsible for generating a detailed, sequential development plan
    based on the finalized application and technical specifications.
    """

    def __init__(self, api_key: str):
        """
        Initializes the PlanningAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for LLM interactions.
        """
        if not api_key:
            raise ValueError("API key is required for the PlanningAgent_AppTarget.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        logging.info("PlanningAgent_AppTarget initialized.")

    def generate_development_plan(self, final_spec_text: str, tech_spec_text: str) -> str:
        """
        Analyzes specifications and generates a development plan as a JSON string.

        Args:
            final_spec_text: The full text of the finalized application spec.
            tech_spec_text: The full text of the finalized technical spec.

        Returns:
            A JSON string representing the sequential development plan, or an
            error JSON object on failure.
        """
        logging.info("PlanningAgent_AppTarget: Generating development plan...")

        prompt = textwrap.dedent(f"""
            You are an expert Lead Solutions Architect. Your task is to create a detailed, sequential development plan in JSON format based on the provided Application Specification and Technical Specification.

            **MANDATORY INSTRUCTIONS:**
            1.  **Deconstruct the Project:** Break down the entire application into a logical sequence of fine-grained, independent components. The sequence should start with foundational elements (like data models or utility classes) and build up to more complex features.
            2.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]`. Each element must be a JSON object `{{}}` representing one micro-specification (a single task).
            3.  **JSON Object Schema:** Each JSON object MUST have keys: `micro_spec_id`, `task_description`, `component_name`, `component_type`, `component_file_path`, `test_file_path`.
            4.  **Micro-specifications:** The `task_description` for each task must be a clear and detailed instruction for another AI agent to build that specific component.
            5.  **Component Types:** The `component_type` key MUST be one of: `CLASS`, `FUNCTION`, `DB_MIGRATION_SCRIPT`, `BUILD_SCRIPT_MODIFICATION`, or `CONFIG_FILE_UPDATE`.
            6.  **File Paths:** Provide logical relative paths for `component_file_path` and `test_file_path` based on standard project structures for the chosen technology stack.
            7.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON array itself.

            **--- INPUT 1: Finalized Application Specification ---**
            {final_spec_text}

            **--- INPUT 2: Finalized Technical Specification ---**
            {tech_spec_text}

            **--- Detailed Development Plan (JSON Array Output) ---**
        """)

        try:
            response = self.model.generate_content(prompt)
            cleaned_response = response.text.strip()
            # Validate that the response is a JSON array
            if cleaned_response.startswith('[') and cleaned_response.endswith(']'):
                json.loads(cleaned_response) # Final validation check
                return cleaned_response
            else:
                logging.error(f"PlanningAgent received non-JSON-array response: {cleaned_response}")
                raise ValueError("The AI response was not in the expected JSON array format.")

        except Exception as e:
            logging.error(f"PlanningAgent_AppTarget API call failed: {e}")
            return f'{{"error": "An unexpected error occurred while generating the development plan: {e}"}}'