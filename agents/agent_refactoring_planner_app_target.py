import google.generativeai as genai
import logging
import json

"""
This module contains the RefactoringPlannerAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RefactoringPlannerAgent_AppTarget:
    """
    Agent responsible for creating a detailed development plan to implement
    a change request. It acts as the core of the Refactoring Pipeline.
    """

    def __init__(self, api_key: str):
        """
        Initializes the RefactoringPlannerAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        genai.configure(api_key=self.api_key)

    def create_refactoring_plan(self, change_request_desc: str, final_spec_text: str, rowd_json: str) -> str:
        """
        Generates a detailed, sequential plan of micro-specifications to implement a change.

        Args:
            change_request_desc (str): The description of the change request to be implemented.
            final_spec_text (str): The full text of the finalized application specification.
            rowd_json (str): A JSON string representing the list of artifacts in the
                             Record-of-Work-Done (RoWD).

        Returns:
            str: A JSON string representing a list of micro-specification dictionaries.
                 Returns an error message string if an API call fails.
        """
        try:
            model = genai.GenerativeModel('gemini-pro')

            prompt = f"""
            You are an expert Solutions Architect. Your task is to create a detailed, sequential development plan in JSON format to implement a given change request. This plan will be composed of "micro-specifications" that will be executed by other AI agents.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]`. Each element in the array must be a JSON object `{}` representing one micro-specification.
            2.  **JSON Object Schema:** Each JSON object (micro-specification) MUST have the following keys:
                - `micro_spec_id`: A unique string identifier for the task (e.g., "ms_chg_001").
                - `task_description`: A detailed, natural language description of the task for the AI agents to follow.
                - `component_name`: The name of the primary artifact being created or modified (e.g., "is_valid_email", "UserProfile").
                - `component_type`: The type of artifact (e.g., "FUNCTION", "CLASS", "FILE").
                - `component_file_path`: The relative path to the component's source file (e.g., "src/utils/validators.py").
                - `test_file_path`: The relative path to the component's unit test file (e.g., "tests/test_validators.py").
            3.  **Analyze and Deconstruct:** Analyze the change request and deconstruct the work into the smallest logical, sequential steps. Each step becomes one JSON object in the array.
            4.  **Do Not Include Other Text:** Do not include any text, explanations, or markdown formatting like ```json outside of the raw JSON array itself.

            **--- INPUTS ---**
            **1. Change Request to Implement:** `{change_request_desc}`
            **2. Finalized Application Specification:** `{final_spec_text}`
            **3. Record-of-Work-Done (RoWD) - Existing Artifacts (JSON):** `{rowd_json}`

            **--- Detailed Refactoring Plan (JSON Array Output) ---**
            """

            response = model.generate_content(prompt)
            # Basic validation to ensure we're getting a JSON array
            cleaned_response = response.text.strip()
            if cleaned_response.startswith("[") and cleaned_response.endswith("]"):
                # The response is already the JSON string we need.
                return cleaned_response
            else:
                raise ValueError("AI response was not in the expected JSON array format.")

        except Exception as e:
            error_message = f"An unexpected error occurred while creating the refactoring plan: {e}"
            logging.error(error_message)
            # Return the error message so the orchestrator can handle it.
            return f'{{"error": "{error_message}"}}'