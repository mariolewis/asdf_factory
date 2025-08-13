import logging
import json
from llm_service import LLMService

"""
This module contains the RefactoringPlannerAgent_AppTarget class.
"""

# Configure basic logging
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RefactoringPlannerAgent_AppTarget:
    """
    Agent responsible for creating a detailed development plan to implement
    a change request. It acts as the core of the Refactoring Pipeline.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the RefactoringPlannerAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the RefactoringPlannerAgent_AppTarget.")
        self.llm_service = llm_service

    def create_refactoring_plan(self, change_request_desc: str, final_spec_text: str, tech_spec_text: str, rowd_json: str, source_code_context: dict | None = None) -> str:
        """
        Generates a detailed, sequential plan of micro-specifications to implement a change,
        optionally using the full source code of impacted components for higher accuracy.
        """
        try:
            source_code_context_str = "# No specific source code provided for review.\n"
            if source_code_context:
                source_code_context_str = "--- Full Source Code of Impacted Artifacts (for detailed review) ---\n"
                for file_path, code in source_code_context.items():
                    source_code_context_str += f"### File: {file_path}\n```\n{code}\n```\n\n"

            prompt = f"""
            You are an expert Solutions Architect. Your task is to create a detailed, sequential development plan in JSON format to implement a given change request by modifying an existing codebase.

            **MANDATORY INSTRUCTIONS:**
            1.  **Adhere to Existing Tech Stack:** You MUST analyze the provided Technical Specification. The plan you create must ONLY use the programming language, frameworks, and libraries already defined in that specification. Do not introduce new languages.
            2.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]`. Each element must be a JSON object `{{}}` representing one micro-specification.
            3.  **JSON Object Schema:** Each JSON object MUST have keys: `micro_spec_id`, `task_description`, `component_name`, `component_type`, `component_file_path`, `test_file_path`.
            4.  **Modify, Don't Recreate:** The plan should focus on modifying existing components identified in the RoWD and Source Code Context. Only plan for new components if the change request explicitly requires them.
            5.  **Non-Destructive Changes:** For `DB_MIGRATION_SCRIPT`, `BUILD_SCRIPT_MODIFICATION`, or `CONFIG_FILE_UPDATE` types, the `task_description` MUST contain only the specific change snippet (e.g., a single SQL `ALTER TABLE` statement).
            6.  **No Other Text:** Do not include any text or markdown formatting outside of the raw JSON array itself.

            **--- INPUTS ---**
            **1. Technical Specification (Defines the programming language and stack):**
            {tech_spec_text}

            **2. Change Request to Implement:**
            {change_request_desc}

            **3. Finalized Application Specification:**
            {final_spec_text}

            **4. Record-of-Work-Done (RoWD) - Existing Artifacts (JSON):**
            {rowd_json}

            **5. Source Code Context:**
            {source_code_context_str}

            **--- Detailed Refactoring Plan (JSON Array Output) ---**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()

            if cleaned_response.startswith("[") and cleaned_response.endswith("]"):
                response_data = json.loads(cleaned_response)
                # Check for an error structure within a valid JSON response
                if isinstance(response_data, list) and len(response_data) > 0 and response_data[0].get("error"):
                    raise ValueError(response_data[0]["error"])
                return cleaned_response
            else:
                raise ValueError("AI response was not in the expected JSON array format.")

        except Exception as e:
            error_msg = f"An unexpected error occurred during refactoring planning: {e}"
            logging.error(error_msg)
            return json.dumps([{"error": error_msg}])