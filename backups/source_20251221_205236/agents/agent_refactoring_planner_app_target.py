import logging
import json
import textwrap
from llm_service import LLMService, parse_llm_json
import vault

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

    def create_refactoring_plan(self, change_request_desc: str, final_spec_text: str, tech_spec_text: str, rowd_json: str, source_code_context: dict, ux_spec_text: str = None, db_schema_spec_text: str = None, **kwargs) -> str:
        """
        Generates a detailed, sequential plan of micro-specifications to implement a change,
        now using optional UX and DB specs for higher accuracy.
        """
        try:
            source_code_context_str = "# No specific source code provided for review.\n"
            if source_code_context:
                source_code_context_str = "--- Full Source Code of Impacted Artifacts (for detailed review) ---\n"
                for file_path, code in source_code_context.items():
                    source_code_context_str += f"### File: {file_path}\n```\n{code}\n```\n\n"

            ux_spec_context = ""
            if ux_spec_text:
                ux_spec_context = f"""
            **--- INPUT 5: UX/UI Specification (Primary source for UI tasks) ---**
            {ux_spec_text}
            """

            db_spec_context = ""
            if db_schema_spec_text:
                db_spec_context = f"""
            **--- INPUT 6: Database Schema Specification (Primary source for data tasks) ---**
            {db_schema_spec_text}
            """

            detected_technologies_json = kwargs.get("detected_technologies_json", "[]")

            prompt = vault.get_prompt("agent_refactoring_planner_app_target__prompt_58").format(tech_spec_text=tech_spec_text, change_request_desc=change_request_desc, rowd_json=rowd_json, source_code_context_str=source_code_context_str, detected_technologies_json=detected_technologies_json, ux_spec_context=ux_spec_context, db_spec_context=db_spec_context)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()
            if cleaned_response.startswith("[") and cleaned_response.endswith("]"):
                parsed_plan = parse_llm_json(cleaned_response)
                # Apply Safety Net
                parsed_plan = self._ensure_test_paths(parsed_plan)
                return json.dumps(parsed_plan)
            else:
                raise ValueError("AI response was not in the expected JSON array format.")

        except Exception as e:
            error_msg = f"An unexpected error occurred during refactoring planning: {e}"
            logging.error(error_msg, exc_info=True)
            raise e # Re-raise the exception

    def refine_refactoring_plan(self, current_plan_json: str, pm_feedback: str, change_request_desc: str, tech_spec_text: str, rowd_json: str) -> str:
        """
        Refines an existing refactoring plan based on PM feedback, ensuring traceability is maintained.
        """
        logging.info("RefactoringPlannerAgent: Refining development plan based on PM feedback...")
        try:
            prompt = vault.get_prompt("agent_refactoring_planner_app_target__prompt_114").format(tech_spec_text=tech_spec_text, rowd_json=rowd_json, change_request_desc=change_request_desc, current_plan_json=current_plan_json, pm_feedback=pm_feedback)
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()
            if cleaned_response.startswith("[") and cleaned_response.endswith("]"):
                parsed_plan = parse_llm_json(cleaned_response)
                # Apply Safety Net
                parsed_plan = self._ensure_test_paths(parsed_plan)
                return json.dumps(parsed_plan)
            else:
                raise ValueError("AI response was not in the expected JSON array format.")
        except Exception as e:
            error_msg = f"An unexpected error occurred during refactoring plan refinement: {e}"
            logging.error(error_msg)
            raise e # Re-raise the exception

    def _ensure_test_paths(self, plan: list) -> list:
        """
        Helper to enforce that all code generation tasks have a test_file_path.
        If missing, it derives a default path to prevent downstream crashes.
        """
        from pathlib import Path
        for task in plan:
            if task.get("type") == "source_code_generation":
                # Check if path is missing or empty
                if not task.get("test_file_path"):
                    comp_path = task.get("component_file_path")
                    if comp_path:
                        p = Path(comp_path)
                        safe_name = p.stem
                        suffix = p.suffix
                        # Default naming convention
                        if suffix == '.cs':
                            derived = f"tests/{safe_name}Tests.cs"
                        else:
                            derived = f"tests/test_{safe_name}{suffix}"

                        task["test_file_path"] = derived
                        logging.warning(f"RefactoringPlanner: Auto-corrected missing test_file_path: {derived}")
        return plan