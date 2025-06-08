"""
This module contains the DocUpdateAgentRoWD class.
"""

class DocUpdateAgentRoWD:
    """
    Agent responsible for updating the Record-of-Work-Done (RoWD) database
    [cite_start]for the target application. [cite: 52, 148]
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