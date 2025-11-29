# agents/agent_planning_app_target.py

import logging
import textwrap
import json
import re
from llm_service import LLMService
from klyve_db_manager import KlyveDBManager
import vault

class PlanningAgent_AppTarget:
    """
    Agent responsible for generating a detailed, sequential development plan
    based on the finalized application and technical specifications.
    """

    def __init__(self, llm_service: LLMService, db_manager: KlyveDBManager):
        if not llm_service:
            raise ValueError("llm_service is required for the PlanningAgent_AppTarget.")
        if not db_manager:
            raise ValueError("db_manager is required for the PlanningAgent_AppTarget.")
        self.llm_service = llm_service
        self.db_manager = db_manager
        logging.info("PlanningAgent_AppTarget initialized.")

    def generate_backlog_items(self, final_spec_text: str, tech_spec_text: str, ux_spec_text: str | None = None, db_schema_spec_text: str | None = None) -> str:
        """
        Analyzes specifications to deconstruct them into a structured list of
        backlog items, prioritizing UX specs when available.
        """
        logging.info("PlanningAgent: Generating initial backlog items from specifications...")

        ux_spec_context = ""
        if ux_spec_text:
            ux_spec_context = f"""
        **--- INPUT 1: UX/UI Specification (Primary Source for Features) ---**
        {ux_spec_text}
        --- End of UX/UI Specification ---
        """

        db_spec_context = ""
        if db_schema_spec_text:
            db_spec_context = f"""
        **--- INPUT 4: Database Schema Specification (for Context) ---**
        {db_schema_spec_text}
        --- End of Database Schema Specification ---
        """

        prompt = vault.get_prompt("agent_planning_app_target__prompt_48").format(ux_spec_context=ux_spec_context, final_spec_text=final_spec_text, tech_spec_text=tech_spec_text, db_spec_context=db_spec_context)

        try:
            response_json_str = self.llm_service.generate_text(prompt, task_complexity="complex")
            json_match = re.search(r'\[.*\]', response_json_str, re.DOTALL)
            if not json_match:
                raise ValueError("LLM response did not contain a valid JSON array.")

            cleaned_response = json_match.group(0)
            parsed_json = json.loads(cleaned_response)
            logging.info(f"Successfully generated {len(parsed_json)} backlog items.")
            return cleaned_response
        except Exception as e:
            logging.error(f"Failed to generate backlog items: {e}")
            error_response = [{"error": "Failed to generate a valid backlog.", "details": str(e)}]
            return json.dumps(error_response)

    def generate_reference_backlog_from_specs(self, final_spec_text, tech_spec_text, ux_spec_text=None):
        """
        Parses specs to generate a two-level (Epic -> Feature) reference model
        of an existing codebase for the backlog.
        """
        logging.info("PlanningAgent: Generating two-level reference backlog from specs...")

        ux_spec_context = ""
        if ux_spec_text:
            ux_spec_context = f"""
            **--- UX/UI Specification (Primary Source) ---**
            {ux_spec_text}
            """

        prompt = vault.get_prompt("agent_planning_app_target__prompt_110").format(ux_spec_context=ux_spec_context, final_spec_text=final_spec_text, tech_spec_text=tech_spec_text)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            # Robustly find and extract the JSON array from the LLM's response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("LLM response did not contain a valid JSON array.")

            cleaned_response = json_match.group(0)
            # Final validation check
            json.loads(cleaned_response)
            return cleaned_response
        except Exception as e:
            logging.error(f"Failed to generate reference backlog: {e}", exc_info=True)
            # Re-raise the exception to be caught by the worker's error handler
            raise e

    def _summarize_text(self, text: str, document_type: str) -> str:
        """Helper to summarize long texts to fit context windows."""
        # This method is retained for future use as required by the PRD, but is not used by the direct prompt.
        logging.info(f"Summarizing {document_type}...")
        prompt = vault.get_prompt("agent_planning_app_target__prompt_167").format(document_type=document_type, text=text)
        try:
            summary = self.llm_service.generate_text(prompt, task_complexity="simple")
            return summary
        except Exception as e:
            logging.error(f"Failed to summarize {document_type}: {e}")
            return text

    def generate_development_plan(self, final_spec_text: str, tech_spec_text: str) -> str:
        """
        Analyzes specifications and generates a development plan as a JSON string.
        This version uses the original, verified, working prompt.
        """
        logging.info("PlanningAgent: Generating development plan directly from full specifications...")

        try:
            if not final_spec_text or not tech_spec_text:
                raise ValueError("Cannot generate plan: One or both of the specification documents are empty.")

            # This is the original, known-good prompt from the working file.
            prompt = vault.get_prompt("agent_planning_app_target__prompt_187").format(final_spec_text=final_spec_text, tech_spec_text=tech_spec_text)

            response_json_str = self.llm_service.generate_text(prompt, task_complexity="complex")

            if not response_json_str or not response_json_str.strip():
                raise ValueError("LLM returned an empty response. This may be due to a transient error.")

            # A more robust cleaning and validation step
            cleaned_response = response_json_str.strip().removeprefix("```json").removesuffix("```").strip()
            parsed = json.loads(cleaned_response)

            if not isinstance(parsed, dict) or "development_plan" not in parsed:
                raise ValueError("LLM returned invalid JSON structure for development plan.")

            logging.info("Successfully generated development plan.")
            return cleaned_response

        except Exception as e:
            logging.error(f"Failed to generate development plan: {e}")
            error_response = {"error": "Failed to generate a valid development plan.", "details": str(e)}
            return json.dumps(error_response)

    def refine_plan(self, current_plan_json: str, pm_feedback: str, final_spec_text: str, tech_spec_text: str) -> str:
        """
        Refines an existing development plan based on PM feedback.
        """
        import re

        logging.info("PlanningAgent: Refining development plan based on PM feedback...")

        prompt = vault.get_prompt("agent_planning_app_target__prompt_237").format(final_spec_text=final_spec_text, tech_spec_text=tech_spec_text, current_plan_json=current_plan_json, pm_feedback=pm_feedback)

        try:
            response_json_str = self.llm_service.generate_text(prompt, task_complexity="complex")

            # --- CORRECTED CLEANING AND VALIDATION LOGIC ---
            # More robustly find and extract the JSON block using regex
            json_match = re.search(r"\{.*\}", response_json_str, re.DOTALL)

            if not json_match:
                logging.error(f"PlanningAgent could not find a JSON object in the LLM response during refinement. Response: '{response_json_str}'")
                raise ValueError("The AI model returned a response without a valid JSON object. Please try refining with different wording.")

            cleaned_response = json_match.group(0)
            # --- END OF CORRECTION ---

            # Final validation check
            json.loads(cleaned_response)
            logging.info("Successfully refined development plan from API.")
            return cleaned_response
        except Exception as e:
            logging.error(f"PlanningAgent_AppTarget refinement failed: {e}")
            error_response = {"error": "Failed to refine the development plan.", "details": str(e)}
            return json.dumps(error_response)