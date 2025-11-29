# agents/agent_triage_app_target.py

import logging
import re
from klyve_db_manager import KlyveDBManager
import textwrap
import json
from llm_service import LLMService
import vault

class TriageAgent_AppTarget:
    """
    Agent responsible for analyzing failures and hypothesizing the root cause.
    """

    def __init__(self, llm_service: LLMService, db_manager: KlyveDBManager):
        """
        Initializes the TriageAgent_AppTarget.
        """
        if not llm_service:
            raise ValueError("llm_service cannot be empty.")
        if not db_manager:
            raise ValueError("Database manager cannot be None.")

        self.llm_service = llm_service
        self.db_manager = db_manager

    def parse_stack_trace(self, stack_trace_log: str) -> list[str]:
        """
        Uses an LLM to parse a raw stack trace and extract a list of file paths.
        """
        logging.info("TriageAgent: Performing Tier 1 Analysis - Parsing stack trace.")

        prompt = vault.get_prompt("agent_triage_app_target__prompt_33").format(stack_trace_log=stack_trace_log)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            file_paths = json.loads(cleaned_response)
            if isinstance(file_paths, list):
                logging.info(f"Stack trace analysis identified {len(file_paths)} relevant files.")
                return file_paths
            return []
        except Exception as e:
            logging.error(f"Stack trace parsing via LLM failed: {e}")
            raise e # Re-raise the exception

    def analyze_and_hypothesize(self, error_logs: str, relevant_code: str, test_report: str = "") -> str:
        """
        Analyzes failure data and returns a root cause hypothesis.
        """
        try:
            prompt = vault.get_prompt("agent_triage_app_target__prompt_66").format(error_logs=error_logs, test_report_if_test_report_else_N_A=test_report if test_report else 'N/A', relevant_code=relevant_code)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()

        except Exception as e:
            error_message = f"An error occurred during triage hypothesis: {e}"
            logging.error(error_message)
            raise e # Re-raise the exception

    def perform_apex_trace_analysis(self, rowd_json: str, apex_file_name: str, failing_component_name: str) -> str:
        """
        Performs a guided dependency trace using the RoWD to find a likely
        execution path from the main executable to a failing component.
        """
        logging.info(f"TriageAgent: Performing Tier 2 Apex Trace Analysis from '{apex_file_name}' to '{failing_component_name}'.")

        prompt = vault.get_prompt("agent_triage_app_target__prompt_111").format(apex_file_name=apex_file_name, failing_component_name=failing_component_name, rowd_json=rowd_json)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip()
            if cleaned_response.startswith('[') and cleaned_response.endswith(']'):
                return cleaned_response
            else:
                logging.error(f"Apex Trace Analysis returned invalid format: {cleaned_response}")
                return "[]"
        except Exception as e:
            logging.error(f"Apex Trace Analysis API call failed: {e}")
            raise e # Re-raise the exception