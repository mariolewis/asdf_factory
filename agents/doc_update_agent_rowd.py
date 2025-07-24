"""
This module contains the DocUpdateAgentRoWD class.
"""
import logging
import json

class DocUpdateAgentRoWD:
    """
    Agent responsible for updating the Record-of-Work-Done (RoWD) database
    for the target application.
    """

    def __init__(self, db_manager):
        """
        Initializes the DocUpdateAgentRoWD.

        Args:
            db_manager: An instance of the database manager (DAO) to interact
                        with the ASDF database.
        """
        if not db_manager:
            raise ValueError("Database manager cannot be None.")
        self.db_manager = db_manager

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

    def update_specification_text(self, original_spec: str, implementation_plan: str, api_key: str) -> str:
        """
        Updates a specification document based on a completed implementation plan.

        Args:
            original_spec (str): The original text of the specification document.
            implementation_plan (str): The JSON string of the development plan that was executed.
            api_key (str): The LLM API key.

        Returns:
            str: The new, updated specification text. Returns original spec on failure.
        """
        logging.info("Invoking LLM to update specification document post-implementation.")
        try:
            # This agent now needs to make an API call, so it needs the key and a model.
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

            prompt = f"""
            You are an expert technical writer responsible for keeping documentation in sync with source code.
            An existing specification document needs to be updated to reflect a series of code changes that were just implemented.

            **Your Task:**
            Review the original specification and the development plan that was just executed. Return a new, complete version of the specification that incorporates the changes and new features described in the plan.

            **MANDATORY INSTRUCTIONS:**
            1.  **Incorporate Changes:** Integrate the changes from the development plan into the original document. Do not omit any sections from the original specification that were not affected.
            2.  **Increment Version:** Find a version number in the document's title or header (e.g., "v1.1", "Version 1.2.3"). You MUST increment the last digit of the version number (e.g., "v1.1" becomes "v1.2"; "Version 2.0" becomes "Version 2.1"). If no version number exists, add one (e.g., "v1.1").
            3.  **Clean Output:** Your output MUST be only the raw text of the new, updated specification document.

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

            response = model.generate_content(prompt)
            if not response.text:
                raise ValueError("LLM returned an empty response for spec update.")

            return response.text

        except Exception as e:
            logging.error(f"Failed to update specification document via LLM: {e}")
            # On failure, return the original spec to prevent data loss.
            return original_spec