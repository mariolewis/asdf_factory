# agents/agent_triage_app_target.py

import google.generativeai as genai
import logging
import re
from asdf_db_manager import ASDFDBManager

"""
This module contains the TriageAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TriageAgent_AppTarget:
    """
    Agent responsible for analyzing failures and hypothesizing the root cause.

    This agent first queries the internal knowledge base for known solutions.
    If no relevant solution is found, it uses the Gemini API to analyze
    error logs, test reports, and relevant code to determine the likely
    source of the problem.
    """

    def __init__(self, api_key: str, db_manager: ASDFDBManager):
        """
        Initializes the TriageAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
            db_manager (ASDFDBManager): An instance of the database manager for KB access.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")
        if not db_manager:
            raise ValueError("Database manager cannot be None.")

        self.api_key = api_key
        self.db_manager = db_manager
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def _extract_tags_from_error(self, error_logs: str) -> list[str]:
        """A simple helper to extract potential search tags from error logs."""
        # Find potential keywords like exceptions (e.g., NullPointerException, ValueError)
        keywords = re.findall(r'([A-Z]\w*Exception|\b[A-Z]\w*Error\b)', error_logs)
        # Find file names (e.g., some_file.py)
        files = re.findall(r'(\w+\.py|\w+\.kt)', error_logs)
        # Combine, lowercase, and get unique tags
        tags = set(kw.lower() for kw in keywords + files)
        return list(tags)

    def analyze_and_hypothesize(self, error_logs: str, relevant_code: str, test_report: str = "") -> str:
        """
        Analyzes failure data and returns a root cause hypothesis.

        It first checks the Knowledge Base. If no solution is found, it calls the LLM.

        Args:
            error_logs (str): The raw error logs from the failed build or test execution.
            relevant_code (str): The source code of the component(s) suspected
                                 to be involved in the failure.
            test_report (str, optional): The summary of failed tests. Defaults to "".

        Returns:
            str: A concise, structured hypothesis about the root cause of the failure.
        """
        # --- Step 1: Query the Knowledge Base ---
        logging.info("TriageAgent: Querying Knowledge Base for known solutions.")
        tags = self._extract_tags_from_error(error_logs)
        if tags:
            try:
                with self.db_manager as db:
                    kb_results = db.query_kb_by_tags(tags)
                if kb_results:
                    # For now, return the solution from the first match.
                    # A more advanced implementation could rank results.
                    solution = kb_results[0]['solution']
                    logging.info(f"TriageAgent: Found relevant solution in Knowledge Base (ID: {kb_results[0]['entry_id']}).")
                    return f"[From Knowledge Base] Hypothesis: The issue matches a previously solved problem. Recommended solution: {solution}"
            except Exception as e:
                logging.warning(f"TriageAgent: Failed to query Knowledge Base. Proceeding with LLM analysis. Error: {e}")
        else:
            logging.info("TriageAgent: No specific tags extracted from error log for KB query.")

        # --- Step 2: If no KB result, proceed with LLM analysis ---
        logging.info("TriageAgent: No solution found in Knowledge Base. Proceeding with LLM analysis.")
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

            response = self.model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            error_message = f"An error occurred while communicating with the Gemini API: {e}"
            logging.error(error_message)
            return error_message