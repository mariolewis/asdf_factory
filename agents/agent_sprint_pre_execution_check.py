# agents/agent_sprint_pre_execution_check.py

import logging
import textwrap
import json
from llm_service import LLMService
import vault

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

        prompt = vault.get_prompt("agent_sprint_pre_execution_check__prompt_40").format(full_backlog_json=full_backlog_json, selected_items_json=selected_items_json, rowd_json=rowd_json)

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