# agents/agent_planning_app_target.py

import logging
import textwrap
import json
import re
import time
from llm_service import LLMService, parse_llm_json
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
        Includes RETRY LOGIC to handle JSON format errors.
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

        # RETRY LOOP ADDED
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response_json_str = self.llm_service.generate_text(prompt, task_complexity="complex")
                json_match = re.search(r'\[.*\]', response_json_str, re.DOTALL)
                if not json_match:
                    raise ValueError("LLM response did not contain a valid JSON array.")

                cleaned_response = json_match.group(0)
                parsed_json = parse_llm_json(cleaned_response)
                logging.info(f"Successfully generated {len(parsed_json)} backlog items.")
                return cleaned_response

            except Exception as e:
                logging.warning(f"Attempt {attempt + 1}/{max_retries} failed to generate backlog: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1) # Brief pause before retry
                    continue
                else:
                    logging.error(f"Failed to generate backlog items after {max_retries} attempts.")
                    error_response = [{"error": "Failed to generate a valid backlog.", "details": str(e)}]
                    return json.dumps(error_response)

    def generate_reference_backlog_from_specs(self, final_spec_text, tech_spec_text, ux_spec_text=None):
        """
        Parses specs to generate a two-level (Epic -> Feature) reference model.
        Includes RETRY LOGIC.
        """
        logging.info("PlanningAgent: Generating two-level reference backlog from specs...")

        ux_spec_context = ""
        if ux_spec_text:
            ux_spec_context = f"""
            **--- UX/UI Specification (Primary Source) ---**
            {ux_spec_text}
            """

        prompt = vault.get_prompt("agent_planning_app_target__prompt_110").format(ux_spec_context=ux_spec_context, final_spec_text=final_spec_text, tech_spec_text=tech_spec_text)

        # RETRY LOOP ADDED
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
                # Robustly find and extract the JSON array
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if not json_match:
                    # Attempt robust fallback via service if regex fails here
                    parsed = parse_llm_json(response_text)
                    return json.dumps(parsed) # Return string representation if parsed successfully

                cleaned_response = json_match.group(0)
                parse_llm_json(cleaned_response) # Validation
                return cleaned_response

            except Exception as e:
                logging.warning(f"Attempt {attempt + 1}/{max_retries} failed to generate reference backlog: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Failed to generate reference backlog after {max_retries} attempts.")
                    raise e
                time.sleep(1)

    def _summarize_text(self, text: str, document_type: str) -> str:
        """Helper to summarize long texts."""
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
        Includes RETRY LOGIC.
        """
        logging.info("PlanningAgent: Generating development plan directly from full specifications...")

        if not final_spec_text or not tech_spec_text:
            return json.dumps({"error": "Cannot generate plan: One or both of the specification documents are empty."})

        prompt = vault.get_prompt("agent_planning_app_target__prompt_187").format(final_spec_text=final_spec_text, tech_spec_text=tech_spec_text)

        # RETRY LOOP ADDED
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response_json_str = self.llm_service.generate_text(prompt, task_complexity="complex")

                if not response_json_str or not response_json_str.strip():
                    raise ValueError("LLM returned an empty response.")

                # Clean and parse
                parsed = parse_llm_json(response_json_str)

                if not isinstance(parsed, dict) or "development_plan" not in parsed:
                    # Sometimes LLM returns a list instead of dict wrapper, handle gracefully if possible
                    if isinstance(parsed, list):
                        parsed = {"development_plan": parsed}
                    else:
                        raise ValueError("LLM returned invalid JSON structure for development plan.")

                logging.info("Successfully generated development plan.")
                return json.dumps(parsed) # Return clean JSON string

            except Exception as e:
                logging.warning(f"Attempt {attempt + 1}/{max_retries} failed to generate plan: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    logging.error(f"Failed to generate development plan after {max_retries} attempts: {e}")
                    error_response = {"error": "Failed to generate a valid development plan.", "details": str(e)}
                    return json.dumps(error_response)

    def refine_plan(self, current_plan_json: str, pm_feedback: str, final_spec_text: str, tech_spec_text: str) -> str:
        """
        Refines an existing development plan based on PM feedback.
        Includes RETRY LOGIC.
        """
        logging.info("PlanningAgent: Refining development plan based on PM feedback...")

        prompt = vault.get_prompt("agent_planning_app_target__prompt_237").format(final_spec_text=final_spec_text, tech_spec_text=tech_spec_text, current_plan_json=current_plan_json, pm_feedback=pm_feedback)

        # RETRY LOOP ADDED
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response_json_str = self.llm_service.generate_text(prompt, task_complexity="complex")

                # Try to extract JSON object
                parsed = parse_llm_json(response_json_str)

                logging.info("Successfully refined development plan from API.")
                return json.dumps(parsed)

            except Exception as e:
                logging.warning(f"Attempt {attempt + 1}/{max_retries} failed to refine plan: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    logging.error(f"PlanningAgent_AppTarget refinement failed after {max_retries} attempts.")
                    error_response = {"error": "Failed to refine the development plan.", "details": str(e)}
                    return json.dumps(error_response)