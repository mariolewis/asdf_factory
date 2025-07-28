import logging
import json
from llm_service import LLMService

"""
This module contains the FixPlannerAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FixPlannerAgent_AppTarget:
    """
    Agent responsible for creating a detailed plan to fix a bug.

    Based on a root cause hypothesis from the TriageAgent, this agent
    generates a micro-specification for change that instructs other agents
    on how to modify the code to resolve the issue.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the FixPlannerAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the FixPlannerAgent_AppTarget.")
        self.llm_service = llm_service

    def create_fix_plan(self, root_cause_hypothesis: str, relevant_code: str) -> str:
        """
        Generates a detailed, sequential JSON plan to fix a diagnosed bug.
        """
        try:
            prompt = f"""
            You are a Principal Software Architect specializing in code remediation. Your task is to take a root cause analysis of a bug and the relevant faulty code, and create a precise, sequential development plan in JSON format to fix the bug.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]`. Each element in the array must be a JSON object `{{}}` representing one micro-task.
            2.  **One File Per Task:** Each task must modify ONLY ONE file. If the fix requires changing two files, you must create two separate task objects in the JSON array.
            3.  **JSON Object Schema:** Each task object MUST have the keys: `micro_spec_id`, `task_description`, `component_name`, `component_type`, `component_file_path`, `test_file_path`.
            4.  **Be Specific:** The `task_description` must be extremely specific, stating exactly what lines to add, remove, or change in the specified `component_file_path`.
            5.  **No Other Text:** Do not include any text or markdown formatting outside of the raw JSON array itself.

            **--- INPUT 1: Root Cause Hypothesis (The problem to solve) ---**
            ```
            {root_cause_hypothesis}
            ```

            **--- INPUT 2: Current Faulty Source Code (The code to be fixed) ---**
            ```
            {relevant_code}
            ```

            **--- Detailed Fix Plan (JSON Array Output) ---**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            # Clean the response to remove potential markdown fences
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()

            # Validate that the response is a JSON array
            if cleaned_response.startswith('[') and cleaned_response.endswith(']'):
                json.loads(cleaned_response) # Final validation check
                return cleaned_response
            else:
                logging.error(f"FixPlannerAgent received non-JSON-array response: {cleaned_response}")
                raise ValueError("The AI response was not in the expected JSON array format.")

        except Exception as e:
            error_message = f"An error occurred during fix plan generation: {e}"
            logging.error(error_message)
            return json.dumps([{"error": error_message}]) # Return a valid JSON array with an error message