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
            You are an expert Solutions Architect. Your task is to create a detailed, sequential development plan in JSON format to implement a given change request.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Dependencies:** Before creating the plan, you MUST analyze the 'Change Request to Implement'. Determine the most logical implementation sequence. The final plan you generate MUST be in this optimal sequence.
            2.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]`.
            3.  **JSON Object Schema:** Each JSON object MUST have the keys: `micro_spec_id`, `task_description`, `component_name`, `component_type`, `component_file_path`, and `parent_cr_ids`. For tasks modifying EXISTING components, you MUST also include the `artifact_id`.
                - `parent_cr_ids`: This MUST be an array of integers, containing the ID(s) from the `ITEM_ID` field of the original backlog item(s) this task helps to implement.
            4.  **Test Generation (Default to Include):** You MUST include the `test_file_path` key for any task that involves creating or modifying application logic. You should ONLY OMIT the `test_file_path` key for tasks that are not logically testable.
            5.  **Use Canonical Paths:** For any task modifying an EXISTING component, the `component_file_path` and `artifact_id` MUST exactly match the `file_path` and `artifact_id` from the provided RoWD context.
            6.  **No Other Text:** Do not include any text or markdown formatting outside of the raw JSON array itself.

            **--- INPUTS ---**
            **1. Technical Specification:**
            {tech_spec_text}

            **2. Change Request to Implement (This contains one or more items, each with an ITEM_ID):**
            {change_request_desc}

            **3. Record-of-Work-Done (RoWD) - Existing Artifacts (JSON):**
            {rowd_json}

            **4. Source Code Context:**
            {source_code_context_str}

            **--- Detailed Refactoring Plan (JSON Array Output) ---**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()

            if cleaned_response.startswith("[") and cleaned_response.endswith("]"):
                response_data = json.loads(cleaned_response)
                if isinstance(response_data, list) and len(response_data) > 0 and response_data[0].get("error"):
                    raise ValueError(response_data[0]["error"])
                return cleaned_response
            else:
                raise ValueError("AI response was not in the expected JSON array format.")

        except Exception as e:
            error_msg = f"An unexpected error occurred during refactoring planning: {e}"
            logging.error(error_msg)
            return json.dumps([{"error": error_msg}])

    def refine_refactoring_plan(self, current_plan_json: str, pm_feedback: str, change_request_desc: str, tech_spec_text: str, rowd_json: str) -> str:
        """
        Refines an existing refactoring plan based on PM feedback, ensuring traceability is maintained.
        """
        logging.info("RefactoringPlannerAgent: Refining development plan based on PM feedback...")
        try:
            prompt = textwrap.dedent(f"""
                You are an expert Solutions Architect revising a development plan.
                Your task is to generate a new, refined JSON development plan by incorporating a Product Manager's feedback into a previous version.

                **MANDATORY INSTRUCTIONS:**
                1.  **Prioritize PM Feedback:** The PM's feedback is the primary directive.
                You MUST restructure, add, remove, or consolidate tasks as requested.
                2.  **Maintain Traceability:** Every task object in your final JSON array response MUST contain the `parent_cr_ids` key.
                The value should be an array of integers derived from the `ITEM_ID` fields in the 'Change Request' input, reflecting which original item(s) the task implements.
                This is a critical requirement.
                3.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]`, adhering to the original schema.
                4.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON array itself.

                **--- CONTEXT: Project Specifications ---**
                Full Technical Specification: {tech_spec_text}
                Record-of-Work-Done (RoWD): {rowd_json}

                **--- INPUT 1: Original Change Request (for parent_cr_ids context) ---**
                ```
                {change_request_desc}
                ```

                **--- INPUT 2: Current Plan Draft (JSON) ---**
                ```json
                {current_plan_json}
                ```

                **--- INPUT 3: PM Feedback to Address (Primary Directive) ---**
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