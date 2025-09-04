# agents/agent_sprint_pre_execution_check.py

import logging
import textwrap
import json
from llm_service import LLMService

class SprintPreExecutionCheckAgent:
    """
    An agent that analyzes a proposed set of sprint items against the
    current project state to identify potential risks before planning.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the SprintPreExecutionCheckAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the SprintPreExecutionCheckAgent.")
        self.llm_service = llm_service
        logging.info("SprintPreExecutionCheckAgent initialized.")

    def run_check(self, selected_items_json: str, rowd_json: str, full_backlog_json: str) -> str:
        """
        Runs a pre-execution check on selected sprint items.

        Args:
            selected_items_json (str): A JSON string of the backlog items selected for the sprint.
            rowd_json (str): A JSON string of the entire Record-of-Work-Done.
            full_backlog_json (str): A JSON string of the entire project backlog.

        Returns:
            A JSON string containing the analysis results.
        """
        logging.info("Running sprint pre-execution check...")

        prompt = textwrap.dedent(f"""
            You are an expert Agile project manager and software architect. Your task is to analyze a set of proposed backlog items for a new sprint and identify potential risks by comparing them against the entire project backlog and the current state of the codebase (RoWD).

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            2.  **JSON Schema:** The JSON object MUST have a single key "pre_execution_report" which contains an object with three keys: "missing_dependencies", "technical_conflicts", and "sequencing_advice". Each of these keys must hold an array of strings.
            3.  **Analysis:**
                -   **Missing Dependencies:** Analyze the 'selected_sprint_items'. If an item logically depends on another item from the 'full_project_backlog' that is NOT included in the sprint, list it as a warning. For example, if "Implement User Profile Page" is in the sprint but "Implement User Authentication" is not.
                -   **Technical Conflicts:** Analyze the 'technical_preview_text' of the selected items. If two or more items propose conflicting changes to the same file or component (e.g., one wants to rename a function that another wants to modify), flag this as a conflict.
                -   **Architectural Sequencing Advice:** Review the selected items and suggest a more efficient or logical implementation order if one exists. For example, "Recommend implementing the database model changes before the API endpoint."
            4.  **No Issues:** If you find no issues in a category, return an empty array `[]` for that key. If there are no issues at all, return an object with three empty arrays.
            5.  **No Other Text:** Do not include any text or markdown formatting outside of the raw JSON object itself.

            **--- INPUT 1: Full Project Backlog (for dependency checking) ---**
            ```json
            {full_backlog_json}
            ```

            **--- INPUT 2: Selected Sprint Items (to be analyzed) ---**
            ```json
            {selected_items_json}
            ```

            **--- INPUT 3: Current Codebase State (RoWD) ---**
            ```json
            {rowd_json}
            ```

            **--- Pre-Execution Check Report (JSON Output) ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            # Clean the response to remove potential markdown fences
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()
            # Final validation check
            json.loads(cleaned_response)
            return cleaned_response
        except Exception as e:
            logging.error(f"SprintPreExecutionCheckAgent failed: {e}")
            error_json = {
                "pre_execution_report": {
                    "missing_dependencies": [],
                    "technical_conflicts": [f"An error occurred during analysis: {e}"],
                    "sequencing_advice": []
                }
            }
            return json.dumps(error_json, indent=2)