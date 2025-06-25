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

    def create_refactoring_plan(self, change_request_desc: str, final_spec_text: str, rowd_json: str, source_code_context: dict | None = None) -> str:
        """
        Generates a detailed, sequential plan of micro-specifications to implement a change,
        optionally using the full source code of impacted components for higher accuracy.
        """
        try:
            model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')

            # --- Prepare the source code context for the prompt ---
            source_code_context_str = "# No specific source code provided for review.\n"
            if source_code_context:
                source_code_context_str = "--- Full Source Code of Impacted Artifacts (for detailed review) ---\n"
                for file_path, code in source_code_context.items():
                    source_code_context_str += f"### File: {file_path}\n```\n{code}\n```\n\n"

            prompt = f"""
            You are an expert Solutions Architect. Your task is to create a detailed, sequential development plan in JSON format to implement a given change request. The plan can include creating/modifying source code, as well as modifying declarative configuration files.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]`. Each element must be a JSON object `{{}}` representing one micro-specification.
            2.  **JSON Object Schema:** Each JSON object MUST have keys: `micro_spec_id`, `task_description`, `component_name`, `component_type`, `component_file_path`, `test_file_path`.
            3.  **Component Types:** The `component_type` key MUST be one of the following strings:
                - `FUNCTION`
                - `CLASS`
                - `DB_MIGRATION_SCRIPT` (for database schema changes)
                - `BUILD_SCRIPT_MODIFICATION` (for changes to pom.xml, build.gradle, etc.)
                - `CONFIG_FILE_UPDATE` (for changes to .properties, .yml files, etc.)
            4.  **Non-Destructive Changes:** For `DB_MIGRATION_SCRIPT`, `BUILD_SCRIPT_MODIFICATION`, or `CONFIG_FILE_UPDATE` types, the `task_description` MUST contain the specific, non-destructive change snippet (e.g., a single SQL `ALTER TABLE` statement, an XML dependency snippet to add, a single new key-value pair). DO NOT output the entire file content for these types. The goal is to modify, not replace.
            5.  **Analysis:** Base your plan on the Change Request, the overall Application Specification, the RoWD metadata, and critically, the **full source code** of the impacted artifacts if it is provided. This source code is the ground truth.
            6.  **No Other Text:** Do not include any text or markdown formatting outside of the raw JSON array itself.

            **--- INPUTS ---**
            **1. Change Request to Implement:** {change_request_desc}
            **2. Finalized Application Specification:** {final_spec_text}
            **3. Record-of-Work-Done (RoWD) - Existing Artifacts (JSON):** {rowd_json}
            **4. Source Code Context:**
            {source_code_context_str}

            **--- Detailed Refactoring Plan (JSON Array Output) ---**
            """

            response = self.model.generate_content(prompt)
            cleaned_response = response.text.strip()
            if cleaned_response.startswith("[") and cleaned_response.endswith("]"):
                json.loads(cleaned_response)
                return cleaned_response
            else:
                raise ValueError("AI response was not in the expected JSON array format.")

        except Exception as e:
            error_msg = f"An unexpected error occurred during refactoring planning: {e}"
            logging.error(error_msg)
            return f'{{"error": "{error_msg}"}}'