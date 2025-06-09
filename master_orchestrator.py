import logging
import uuid
from datetime import datetime
from enum import Enum, auto

from asdf_db_manager import ASDFDBManager

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FactoryPhase(Enum):
    """Enumeration for the main factory F-Phases."""
    IDLE = auto()
    ENV_SETUP_TARGET_APP = auto()
    SPEC_ELABORATION = auto()
    PLANNING = auto()
    GENESIS = auto()
    RAISING_CHANGE_REQUEST = auto()
    IMPLEMENTING_CHANGE_REQUEST = auto()
    EDITING_CHANGE_REQUEST = auto()
    # Add other phases as they are developed

class MasterOrchestrator:
    """
    The central state machine and workflow manager for the ASDF.
    It coordinates agents, manages project state, and handles project lifecycle.
    """

    def __init__(self, db_path: str):
        """
        Initializes the MasterOrchestrator.

        Args:
            db_path (str): The path to the ASDF's SQLite database.
        """
        self.db_manager = ASDFDBManager(db_path)
        self.project_id: str | None = None
        self.project_name: str | None = None
        self.active_cr_id_for_edit: int | None = None
        self.current_phase: FactoryPhase = FactoryPhase.IDLE

        # Ensure core tables exist on startup
        with self.db_manager as db:
            db.create_tables()

        logging.info("MasterOrchestrator initialized.")

    def get_status(self) -> dict:
        """Returns the current status of the orchestrator."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "current_phase": self.current_phase.name
        }

    def start_new_project(self, project_name: str):
        """
        Initializes a new project.

        This method follows the logic for 'Start New Project' from F-Phase 7.
        It creates a new project record in the database and sets the orchestrator's
        state to begin the development process for the new project.

        Args:
            project_name (str): The human-readable name for the new project.
        """
        if self.project_id:
            logging.warning(f"A project '{self.project_name}' is already active. Starting a new one will override it in this session.")
            # [cite_start]In a future implementation, we would call the Stop & Export logic here as per PRD[cite: 312].

        self.project_id = f"proj_{uuid.uuid4().hex[:8]}"
        self.project_name = project_name
        self.current_phase = FactoryPhase.ENV_SETUP_TARGET_APP # Set initial phase after start
        timestamp = datetime.utcnow().isoformat()

        try:
            with self.db_manager as db:
                db.create_project(self.project_id, self.project_name, timestamp)
            logging.info(f"Successfully started new project: '{self.project_name}' (ID: {self.project_id})")
            logging.info(f"Orchestrator status: {self.get_status()}")
        except Exception as e:
            logging.error(f"Failed to start new project '{self.project_name}': {e}")
            # Reset state on failure
            self.project_id = None
            self.project_name = None
            self.current_phase = FactoryPhase.IDLE
            raise

    def set_phase(self, phase_name: str):
        """
        Sets the current project phase.

        This provides a controlled way for the GUI or other components to
        signal a transition in the factory's workflow.

        Args:
            phase_name (str): The name of the phase to transition to
                              (e.g., "SPEC_ELABORATION").
        """
        if not self.project_id:
            logging.error("Cannot set phase; no active project.")
            return

        try:
            # Find the corresponding Enum member from the string name
            new_phase = FactoryPhase[phase_name]
            self.current_phase = new_phase
            logging.info(f"Project '{self.project_name}' phase changed to: {self.current_phase.name}")
            # In a future implementation, this would also save the state
            # to the OrchestrationState table in the database.
        except KeyError:
            logging.error(f"Attempted to set an invalid phase: {phase_name}")

    def handle_proceed_action(self):
        """
        Handles the logic for when the PM clicks 'Proceed' at a checkpoint.

        This is a placeholder for the core logic of F-Phase 3 where the
        orchestrator would fetch the next component from the plan and
        invoke the necessary development agents.
        """
        if self.current_phase == FactoryPhase.GENESIS:
            logging.info("PM chose to 'Proceed'. Orchestrator will now begin development of the next component.")
            # TODO: Implement logic to get the next component from the dev plan
            # and kick off the LogicAgent, CodeAgent, etc.
            pass
        else:
            logging.warning(f"Received 'Proceed' action in an unexpected phase: {self.current_phase.name}")

    def handle_raise_cr_action(self):
        """
        Handles the logic for when the PM clicks 'Raise New Change Request'.

        This transitions the factory into the state for capturing the details
        of the new change request.
        """
        if self.current_phase == FactoryPhase.GENESIS:
            logging.info("PM initiated 'Raise New Change Request'. Transitioning to CR input screen.")
            self.set_phase("RAISING_CHANGE_REQUEST")
        else:
            logging.warning(f"Received 'Raise CR' action in an unexpected phase: {self.current_phase.name}")

    def save_new_change_request(self, description: str) -> bool:
        """
        Saves a new change request to the database.

        Args:
            description (str): The description of the change from the PM.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        if not self.project_id:
            logging.error("Cannot save change request; no active project.")
            return False

        if not description or not description.strip():
            logging.warning("Cannot save empty change request description.")
            return False

        try:
            with self.db_manager as db:
                db.add_change_request(self.project_id, description)

            # After successfully saving, return to the main development checkpoint.
            self.set_phase("GENESIS")
            logging.info("Successfully saved new change request and returned to Genesis phase.")
            return True
        except Exception as e:
            logging.error(f"Failed to save new change request: {e}")
            return False

    def handle_view_cr_register_action(self):
        """
        Transitions the factory into the state for viewing and selecting a CR
        from the register.
        """
        if self.current_phase == FactoryPhase.GENESIS:
            logging.info("PM chose to 'Implement CR'. Transitioning to CR selection screen.")
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")
        else:
            logging.warning(f"Received 'Implement CR' action in an unexpected phase: {self.current_phase.name}")

    def handle_implement_cr_action(self, cr_id: int):
        """
        Handles the logic for when the PM selects a CR and confirms its implementation.

        This kicks off the detailed planning for the selected change.

        Args:
            cr_id (int): The ID of the change request to be implemented.
        """
        logging.info(f"PM has confirmed implementation for Change Request ID: {cr_id}.")
        logging.info("Transitioning to Refactoring/Planning for the selected change.")

        # TODO: Implement logic to update the CR status to 'PLANNING_IN_PROGRESS'.
        # TODO: Invoke the RefactoringPlannerAgent with the details of the selected CR.
        # TODO: After the new plan is created, hand off execution to the Genesis pipeline.

        # For now, we'll just log the action and return to the main checkpoint.
        self.set_phase("GENESIS")
        pass

    def handle_run_impact_analysis_action(self, cr_id: int):
        """
        Orchestrates the running of an impact analysis for a specific CR.

        Args:
            cr_id (int): The ID of the change request to be analyzed.
        """
        logging.info(f"PM has requested to run impact analysis for CR ID: {cr_id}.")

        # TODO: In F-Dev 5, invoke the actual ImpactAnalysisAgent here.
        # For now, we will simulate the agent's output for UI development purposes.
        simulated_rating = "Medium"
        simulated_details = "Simulated analysis: This change will likely affect the UserProfile class and the authentication module. Database schema changes may be required in the 'Users' table."

        try:
            with self.db_manager as db:
                db.update_cr_impact_analysis(cr_id, simulated_rating, simulated_details)
            logging.info(f"Successfully simulated and saved impact analysis for CR ID: {cr_id}.")
        except Exception as e:
            logging.error(f"Failed to save impact analysis results for CR ID {cr_id}: {e}")

    def handle_delete_cr_action(self, cr_id: int):
        """
        Handles the deletion of a change request from the register.

        The UI layer is responsible for confirming this action with the user
        and for ensuring it's only called on CRs with a 'RAISED' status.

        Args:
            cr_id (int): The ID of the change request to delete.
        """
        logging.info(f"PM has requested to delete Change Request ID: {cr_id}.")
        try:
            with self.db_manager as db:
                db.delete_change_request(cr_id)
            logging.info(f"Successfully deleted CR ID: {cr_id}.")
        except Exception as e:
            logging.error(f"Failed to delete CR ID {cr_id}: {e}")

    def handle_edit_cr_action(self, cr_id: int):
        """
        Transitions the factory into the state for editing a specific CR
        and stores the ID of that CR.

        Args:
            cr_id (int): The ID of the change request to be edited.
        """
        logging.info(f"PM initiated 'Edit' for CR ID: {cr_id}. Transitioning to CR editing screen.")
        self.active_cr_id_for_edit = cr_id
        self.set_phase("EDITING_CHANGE_REQUEST")

    def save_edited_change_request(self, new_description: str) -> bool:
        """
        Saves the updated description for the currently active change request
        and resets its impact analysis.

        Args:
            new_description (str): The new, edited description from the PM.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        if self.active_cr_id_for_edit is None:
            logging.error("Attempted to save an edited CR but no active_cr_id_for_edit is set.")
            return False

        if not new_description or not new_description.strip():
            logging.warning("Cannot save empty change request description.")
            return False

        try:
            cr_id_to_update = self.active_cr_id_for_edit
            with self.db_manager as db:
                db.update_change_request(cr_id_to_update, new_description)

            # After saving, reset the active edit ID and return to the register screen.
            self.active_cr_id_for_edit = None
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")
            logging.info(f"Successfully saved edits for CR ID: {cr_id_to_update}")
            return True
        except Exception as e:
            logging.error(f"Failed to save edited change request for CR ID {self.active_cr_id_for_edit}: {e}")
            return False

    def get_active_cr_details_for_edit(self) -> dict | None:
        """
        Retrieves the full details for the CR currently marked for editing.

        Returns:
            A dictionary containing the CR's details, or None if no CR
            is active for editing or if an error occurs.
        """
        if self.active_cr_id_for_edit is None:
            logging.warning("Attempted to get details for edit, but no CR is active for editing.")
            return None

        try:
            with self.db_manager as db:
                cr_row = db.get_cr_by_id(self.active_cr_id_for_edit)
                if cr_row:
                    # Convert the database row object to a standard dictionary for easier use in the UI
                    return dict(cr_row)
                return None
        except Exception as e:
            logging.error(f"Failed to retrieve details for CR ID {self.active_cr_id_for_edit}: {e}")
            return None

    def cancel_cr_edit(self):
        """
        Cancels the editing process for a change request and returns to the
        register view.
        """
        logging.info(f"CR edit cancelled for ID: {self.active_cr_id_for_edit}. Returning to register.")
        self.active_cr_id_for_edit = None
        self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

    def get_all_change_requests(self) -> list:
        """
        Retrieves all change requests for the active project from the database.

        Returns:
            list: A list of change request records, or an empty list if no project
                  is active or an error occurs.
        """
        if not self.project_id:
            logging.warning("Attempted to get change requests with no active project.")
            return []

        try:
            with self.db_manager as db:
                return db.get_all_change_requests_for_project(self.project_id)
        except Exception as e:
            logging.error(f"Failed to retrieve change requests for project {self.project_id}: {e}")
            return []

    def pause_project(self):
        """def handle_raise_cr_action(self):
        """
        Handles the logic for when the PM clicks 'Raise New Change Request'.

        This transitions the factory into the state for capturing the details
        of the new change request.
        """
        if self.current_phase == FactoryPhase.GENESIS:
            logging.info("PM initiated 'Raise New Change Request'. Transitioning to CR input screen.")
            self.set_phase("RAISING_CHANGE_REQUEST")
        else:
            logging.warning(f"Received 'Raise CR' action in an unexpected phase: {self.current_phase.name}")
        Pauses the currently active project. (Placeholder)

        As per F-Phase 7, this will save the complete current state of the
        orchestration to the database, allowing for a graceful pause.
        [cite_start]The project remains the active project. [cite: 314, 315]
        """
        if not self.project_id:
            logging.warning("No active project to pause.")
            return

        logging.info(f"Placeholder: Pausing project '{self.project_name}'.")
        # Future implementation will save the detailed state to the DB.
        self.current_phase = FactoryPhase.IDLE # Example of a state change
        pass

    def resume_project(self):
        """
        Resumes a paused project. (Placeholder)

        As per F-Phase 7, this will load the last saved state from the
        [cite_start]database and resume operations from the appropriate phase and step. [cite: 316]
        """
        if not self.project_id:
            logging.warning("No active project to resume.")
            return

        logging.info(f"Placeholder: Resuming project '{self.project_name}'.")
        # Future implementation will load state from DB and set the correct phase.
        pass

    def discontinue_project(self):
        """
        Discontinues the currently active project. (Placeholder)

        [cite_start]As per F-Phase 3 PM Checkpoints, this option halts the project. [cite: 266]
        This is a placeholder for the 'Stop & Export' or 'Delete' logic.
        """
        if not self.project_id:
            logging.warning("No active project to discontinue.")
            return

        logging.info(f"Placeholder: Discontinuing project '{self.project_name}'.")
        # Future implementation will handle archival and cleanup.
        self.project_id = None
        self.project_name = None
        self.current_phase = FactoryPhase.IDLE
        pass