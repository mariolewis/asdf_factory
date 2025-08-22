"""
This module contains the DocUpdateAgentRoWD class.
"""
import logging
import json
from llm_service import LLMService

class DocUpdateAgentRoWD:
    """
    Agent responsible for updating the Record-of-Work-Done (RoWD) database
    for the target application.
    """

    def __init__(self, db_manager, llm_service: LLMService):
        """
        Initializes the DocUpdateAgentRoWD.

        Args:
            db_manager: An instance of the database manager (DAO).
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not db_manager:
            raise ValueError("Database manager cannot be None.")
        if not llm_service:
            raise ValueError("LLMService is required for the DocUpdateAgentRoWD.")
        self.db_manager = db_manager
        self.llm_service = llm_service

    def update_artifact_record(self, artifact_data: dict) -> bool:
        """
        Creates or updates a record for a single software artifact in the RoWD.

        This method bundles the responsibility of communicating with the database
        to record the state of a developed component. It calls the appropriate
        method on the database manager to perform the write operation.

        Args:
            artifact_data (dict): A dictionary containing all the details
                                  of the artifact, corresponding to the
                                  columns in the 'Artifacts' table.

        Returns:
            bool: True if the record was saved successfully, False otherwise.
        """
        try:
            # The agent's role is to call the DAO layer.
            # This follows the separation of concerns principle.
            self.db_manager.add_or_update_artifact(artifact_data)
            return True

        except Exception as e:
            # The programming standard requires graceful error handling.
            logging.error(f"Error updating RoWD for artifact: {artifact_data.get('artifact_id')}. Error: {e}")
            return False

    def update_specification_text(self, original_spec: str, implementation_plan: str, current_date: str) -> str:
        """
        Updates a specification document based on a completed implementation plan.

        Args:
            original_spec (str): The original text of the specification document.
            implementation_plan (str): The JSON string of the development plan that was executed.
            current_date (str): The current system date to be inserted into the document.

        Returns:
            str: The new, updated specification text. Returns original spec on failure.
        """
        logging.info("Invoking LLM to update specification document post-implementation.")
        try:
            prompt = f"""
            You are an expert technical writer responsible for keeping documentation in sync with source code.
            An existing specification document needs to be updated to reflect a series of code changes that were just implemented.

            **Your Task:**
            Review the original specification and the development plan. Return a new, complete version of the specification that incorporates the changes and new features described in the plan, along with an updated date and version.

            **MANDATORY INSTRUCTIONS:**
            1.  **Incorporate Changes:** Integrate the changes from the development plan into the original document. Do not omit any sections from the original specification that were not affected.
            2.  **Increment Version:** Find a version number in the document's header (e.g., "v1.1", "Version 1.2.3"). You MUST increment the last digit of the version number (e.g., "v1.1" becomes "v1.2"; "Version 2.0" becomes "Version 2.1").
            3.  **Update Date:** You MUST find the 'Date:' line in the document's header and replace its value with the provided current date: {current_date}.
            4.  **Clean Output:** Your output MUST be only the raw text of the new, updated specification document.

            **--- INPUT 1: Original Specification Document ---**
            ```
            {original_spec}
            ```

            **--- INPUT 2: The Executed Development Plan (JSON) ---**
            ```json
            {implementation_plan}
            ```

            **--- OUTPUT: New, Updated Specification Document ---**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            if not response_text or response_text.startswith("Error:"):
                raise ValueError(f"LLM returned an error or empty response for spec update: {response_text}")

            return response_text

        except Exception as e:
            logging.error(f"Failed to update specification document via LLM: {e}")
            # On failure, return the original spec to prevent data loss.
            return original_spec