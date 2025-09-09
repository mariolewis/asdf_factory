import logging
import json
import textwrap
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
        This version internally handles dependency and sequencing analysis.
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
            1.  **Internal Pre-Analysis:** Before creating the plan, you MUST analyze the 'Change Request to Implement' (which may contain multiple items). Identify any dependencies between items, potential technical conflicts (e.g., two items modifying the same function), and determine the most logical implementation sequence. The final plan you generate MUST already be in this optimal sequence.
            2.  **Adhere to Existing Tech Stack:** You MUST analyze the provided Technical Specification. The plan you create must ONLY use the programming language, frameworks, and libraries already defined in that specification. Do not introduce new languages.
            3.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]`. Each element must be a JSON object `{{}}` representing one micro-specification.
            4.  **JSON Object Schema:** Each JSON object MUST have keys: `micro_spec_id`, `task_description`, `component_name`, `component_type`, `component_file_path`, `test_file_path`. For tasks modifying EXISTING components, you MUST also include the `artifact_id`.
            5.  **Modify, Don't Recreate:** The plan should focus on modifying existing components identified in the RoWD and Source Code Context. Only plan for new components if the change request explicitly requires them.
            6.  **Use Canonical Paths:** For any task that modifies an EXISTING component, the `component_file_path` and `artifact_id` in your generated plan MUST exactly match the `file_path` and `artifact_id` for that component in the provided RoWD context.
            7.  **Non-Destructive Changes:** For `DB_MIGRATION_SCRIPT`, `BUILD_SCRIPT_MODIFICATION`, or `CONFIG_FILE_UPDATE` types, the `task_description` MUST contain only the specific change snippet (e.g., a single SQL `ALTER TABLE` statement).
            8.  **No Other Text:** Do not include any text or markdown formatting outside of the raw JSON array itself.
            9.  **Avoid Ambiguous Formatting:** The `task_description` content will be rendered as rich text. To prevent formatting errors, you MUST NOT use the pipe character ('|') or sequences of hyphens ('---') within the description text.

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

    def refine_refactoring_plan(self, current_plan_json: str, pm_feedback: str, final_spec_text: str, tech_spec_text: str, rowd_json: str) -> str:
        """
        Refines an existing refactoring plan based on PM feedback.

        Args:
            current_plan_json (str): The JSON string of the current plan.
            pm_feedback (str): The specific feedback from the PM to address.
            final_spec_text (str): The full application specification for context.
            tech_spec_text (str): The full technical specification for context.
            rowd_json (str): The full RoWD for context.

        Returns:
            A JSON string of the new, refined development plan.
        """
        logging.info("RefactoringPlannerAgent: Refining development plan based on PM feedback...")
        try:
            prompt = textwrap.dedent(f"""
                You are an expert Solutions Architect revising a development plan. Your task is to refine an existing JSON refactoring plan based on specific feedback from a Product Manager.

                **MANDATORY INSTRUCTIONS:**
                1.  **Modify, Don't Regenerate:** You MUST modify the "Current Plan Draft" to incorporate the "PM Feedback". Preserve all tasks that are not affected by the feedback.
                2.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]`, identical in schema to the original plan.
                3.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON array itself.

                **--- CONTEXT: Project Specifications ---**
                Full Application Specification: {final_spec_text}
                Full Technical Specification: {tech_spec_text}
                Record-of-Work-Done (RoWD): {rowd_json}

                **--- INPUT 1: Current Plan Draft (JSON) ---**
                ```json
                {current_plan_json}
                ```

                **--- INPUT 2: PM Feedback to Address ---**
                ```
                {pm_feedback}
                ```

                **--- Refined Refactoring Plan (JSON Array Output) ---**
            """)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()

            if cleaned_response.startswith("[") and cleaned_response.endswith("]"):
                json.loads(cleaned_response) # Final validation
                return cleaned_response
            else:
                raise ValueError("AI response was not in the expected JSON array format.")

        except Exception as e:
            error_msg = f"An unexpected error occurred during refactoring plan refinement: {e}"
            logging.error(error_msg)
            return json.dumps([{"error": error_msg}])