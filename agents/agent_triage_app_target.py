# agents/agent_triage_app_target.py

import logging
import re
from klyve_db_manager import KlyveDBManager
import textwrap
import json
from llm_service import LLMService

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

        prompt = textwrap.dedent(f"""
            You are a log analysis expert. Your task is to parse the following raw text, which contains a software stack trace, and extract all unique, relative file paths mentioned in it.

            **MANDATORY INSTRUCTIONS:**
            1.  **Identify File Paths:** Scan the text for any strings that represent a file path (e.g., `src/main/app.py`, `modules/utils.kt`).
            2.  **JSON Array Output:** Your response MUST be a single, valid JSON array of strings. Each string in the array must be one of the unique file paths you identified.
            3.  **Order Matters:** The file paths should be in the order they appear in the trace, from the initial call to the point of error.
            4.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON array itself. If no file paths are found, return an empty array `[]`.

            **--- Stack Trace Log ---**
            {stack_trace_log}
            **--- End of Log ---**

            **JSON Array of File Paths:**
        """)

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
            prompt = f"""
            You are a Senior Software Engineer specializing in debugging complex systems.
            Your task is to analyze the provided error logs, test reports, and source code to form a concise,
            well-reasoned hypothesis about the root cause of a failure.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Holistically:** Consider all provided inputs—the error log, the test report (if any), and the source code—to form your conclusion.
            2.  **Be Specific:** Your hypothesis must be specific. Pinpoint the likely function, class, or logical error. Avoid vague statements.
            3.  **Concise Output:** Your entire response should be a single, concise paragraph that clearly states the hypothesis. Do not include conversational text or apologies.

            **--- INPUTS ---**

            **1. Error Logs / Stack Trace:**
            ```
            {error_logs}
            ```

            **2. Failed Test Report (e.g., from UI tests):**
            ```
            {test_report if test_report else "N/A"}
            ```

            **3. Potentially Relevant Source Code:**
            ```python
            {relevant_code}
            ```

            **--- Root Cause Hypothesis ---**
            """

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

        prompt = textwrap.dedent(f"""
            You are a dependency analysis expert. Your task is to analyze a JSON representation of a project's Record-of-Work-Done (RoWD) to determine a likely execution path that leads to a failure.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Dependencies:** The RoWD contains a 'dependencies' key for each artifact, which lists the `artifact_id`s it calls. You must use this information to trace a path.
            2.  **Find the Path:** Trace a likely call stack (a sequence of files) starting from the main executable file (`apex_file_name`) and ending at the `failing_component_name`.
            3.  **JSON Array Output:** Your response MUST be a single, valid JSON array of strings. Each string in the array should be the `file_path` of an artifact in the determined execution path.
            4.  **Order Matters:** The file paths in the array must be in the logical order of execution, starting with the file path of the apex executable.
            5.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON array itself.

            **--- INPUTS ---**
            **1. Main Executable Name (Starting Point):** `{apex_file_name}`
            **2. Failing Component Name (End Point):** `{failing_component_name}`
            **3. Record-of-Work-Done (RoWD) JSON Data:**
            {rowd_json}

            **--- Likely Execution Path (JSON Array of file_path strings) ---**
        """)

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