import logging
import uuid
from datetime import datetime
from enum import Enum, auto

from asdf_db_manager import ASDFDBManager
from logic_agent_app_target import LogicAgent_AppTarget
from code_agent_app_target import CodeAgent_AppTarget
from test_agent_app_target import TestAgent_AppTarget
from doc_update_agent_rowd import DocUpdateAgentRoWD
# NOTE: We will use BuildAndCommitAgent_AppTarget in the next step.

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
    DEBUG_PM_ESCALATION = auto()
    VIEWING_PROJECT_HISTORY = auto()
    AWAITING_CONTEXT_REESTABLISHMENT = auto()
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
        This method executes the core Genesis Pipeline for one component.
        """
        if self.current_phase != FactoryPhase.GENESIS:
            logging.warning(f"Received 'Proceed' action in an unexpected phase: {self.current_phase.name}")
            return

        logging.info("PM chose to 'Proceed'. Orchestrator will now begin development of the next component.")

        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    logging.error("CRITICAL: Cannot proceed with code generation. LLM_API_KEY is not set.")
                    # In a real UI, we would display a blocking error message here.
                    return

                # --- In a real run, this data would be fetched from the Development Plan ---
                # For this implementation, we use placeholder data as the Planning phase is not yet complete.
                micro_spec_id = f"ms_{uuid.uuid4().hex[:6]}"
                micro_spec_content = "Create a Python utility function named 'is_valid_email' that takes one string argument (email_address) and returns True if the string is a valid email format, otherwise False. It should handle basic format checking (e.g., presence of '@' and '.')."
                component_name = "is_valid_email"
                component_type = "FUNCTION"
                file_path = "src/utils/validators.py"
                coding_standard = "Follow PEP 8 standards. Include a clear docstring explaining the function's purpose, arguments, and return value."
                # -------------------------------------------------------------------------

                logging.info(f"Executing Genesis Pipeline for component: {component_name}")

                # 1. Instantiate Agents
                logic_agent = LogicAgent_AppTarget(api_key=api_key)
                code_agent = CodeAgent_AppTarget(api_key=api_key)
                test_agent = TestAgent_AppTarget(api_key=api_key)
                doc_agent = DocUpdateAgentRoWD(db_manager=self.db_manager)

                # 2. Generate Logic
                logging.info("Invoking LogicAgent...")
                logic_plan = logic_agent.generate_logic_for_component(micro_spec_content)
                if "An error occurred" in logic_plan:
                    raise Exception(f"LogicAgent failed: {logic_plan}")

                # 3. Generate Code
                logging.info("Invoking CodeAgent...")
                source_code = code_agent.generate_code_for_component(logic_plan, coding_standard)
                if "An error occurred" in source_code:
                    raise Exception(f"CodeAgent failed: {source_code}")

                # 4. Generate Unit Tests
                logging.info("Invoking TestAgent...")
                unit_tests = test_agent.generate_unit_tests_for_component(source_code, micro_spec_content)
                if "An error occurred" in unit_tests:
                    raise Exception(f"TestAgent failed: {unit_tests}")

                # NOTE: In a full implementation, the 'BuildAndCommitAgent' would be called here
                # to write the source_code and unit_tests to their respective files, run the tests,
                # and commit to Git upon success. For now, we proceed assuming success.

                # 5. Update Record-of-Work-Done (RoWD)
                logging.info("Invoking DocUpdateAgentRoWD to update the database...")
                artifact_id = f"art_{uuid.uuid4().hex[:8]}"
                artifact_data = {
                    "artifact_id": artifact_id,
                    "project_id": self.project_id,
                    "file_path": file_path,
                    "artifact_name": component_name,
                    "artifact_type": component_type,
                    "short_description": micro_spec_content,
                    "status": "CODING_COMPLETED", # This would be UNIT_TESTS_PASSING after the build agent runs
                    "version": 1,
                    "last_modified_timestamp": datetime.utcnow().isoformat(),
                    "micro_spec_id": micro_spec_id,
                    "unit_test_status": "PENDING_EXECUTION"
                }
                doc_agent.update_artifact_record(artifact_data)

                logging.info(f"Genesis Pipeline completed successfully for component: {component_name}")
                # The orchestrator remains in the GENESIS phase for the next checkpoint.

        except Exception as e:
            logging.error(f"Genesis Pipeline failed. Error: {e}")
            # Here, we would transition to the DEBUG_PM_ESCALATION phase
            self.escalate_for_manual_debug()

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

    def escalate_for_manual_debug(self):
        """
        Transitions the factory into the state where the PM must intervene
        after automated debugging has failed.
        """
        logging.warning("Automated debugging failed after max attempts. Escalating to PM.")
        self.set_phase("DEBUG_PM_ESCALATION")

    def handle_pm_debug_choice(self, choice: str, details: dict = None):
        """
        Handles the decision made by the PM during a debug escalation.

        Args:
            choice (str): The option selected by the PM (e.g., 'RETRY', 'MANUAL', 'IGNORE').
            details (dict, optional): Any additional details provided by the PM. Defaults to None.
        """
        logging.info(f"PM selected debug option: {choice}")
        # In a real implementation, this would trigger different agent workflows.
        # For now, we will just log the choice and return to the main GENESIS phase
        # to not get stuck in the escalation screen during development.
        # TODO: Implement the distinct logic for each PM choice.

        self.set_phase("GENESIS")

    def pause_project(self):
        """
        [cite_start]Pauses the currently active project by saving its state to the DB. [cite: 282]
        [cite_start]The project remains the active project. [cite: 283]
        """
        if not self.project_id:
            logging.warning("No active project to pause.")
            return

        try:
            with self.db_manager as db:
                # In a real implementation, state_details would be a rich JSON object
                db.save_orchestration_state(
                    project_id=self.project_id,
                    current_phase=self.current_phase.name,
                    current_step="paused_at_checkpoint", # Example step
                    state_details='{"details": "State saved on pause"}',
                    timestamp=datetime.utcnow().isoformat()
                )
            logging.info(f"Project '{self.project_name}' paused and state saved.")
        except Exception as e:
            logging.error(f"Failed to save state while pausing project {self.project_id}: {e}")


    def _clear_active_project_data(self, db):
        """Helper method to clear all data for the current project."""
        if not self.project_id:
            return
        db.delete_all_artifacts_for_project(self.project_id)
        db.delete_all_change_requests_for_project(self.project_id)
        db.delete_orchestration_state_for_project(self.project_id)
        logging.info(f"Cleared all active data for project ID: {self.project_id}")


    def stop_and_export_project(self, archive_dir: str | Path, archive_name: str) -> bool:
        """
        Exports all project data to files, adds a record to history,
        and clears the active project from the database.
        """
        if not self.project_id:
            logging.warning("No active project to stop and export.")
            return False

        archive_dir = Path(archive_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Define file paths
        rowd_file = archive_dir / f"{archive_name}_rowd.json"
        cr_file = archive_dir / f"{archive_name}_cr.json"

        try:
            with self.db_manager as db:
                # 1. Fetch all data for the active project
                artifacts = db.get_all_artifacts_for_project(self.project_id)
                change_requests = db.get_all_change_requests_for_project(self.project_id)
                project_details = db.get_project_by_id(self.project_id)

                # [cite_start]2. Export RoWD (Artifacts) to JSON file [cite: 288]
                artifacts_list = [dict(row) for row in artifacts]
                with open(rowd_file, 'w', encoding='utf-8') as f:
                    json.dump(artifacts_list, f, indent=4)

                # [cite_start]3. Export Change Requests to a separate JSON file [cite: 290]
                cr_list = [dict(row) for row in change_requests]
                with open(cr_file, 'w', encoding='utf-8') as f:
                    json.dump(cr_list, f, indent=4)

                # [cite_start]4. Create a record in the ProjectHistory table [cite: 291]
                db.add_project_to_history(
                    project_id=self.project_id,
                    project_name=self.project_name,
                    # Storing the *archive file path* is crucial. We'll store the RoWD file path.
                    root_folder=project_details['project_root_folder'] if project_details else "N/A",
                    archive_file_path=str(rowd_file),
                    timestamp=datetime.utcnow().isoformat()
                )

                # [cite_start]5. Clear the active tables for the project [cite: 292]
                self._clear_active_project_data(db)

            # 6. Reset orchestrator state
            logging.info(f"Successfully exported project '{self.project_name}' to {archive_dir}")
            self.project_id = None
            self.project_name = None
            self.current_phase = FactoryPhase.IDLE
            return True

        except Exception as e:
            logging.error(f"Failed to stop and export project: {e}")
            return False


    def load_archived_project(self, history_id: int):
        """
        Loads an archived project's data into the active tables.
        """
        try:
            with self.db_manager as db:
                # [cite_start]Safety export any currently active project first [cite: 294]
                if self.project_id:
                    # In a real GUI flow, we'd get a path from the user. For now, we create a default.
                    default_archive_path = Path("data/safety_archives")
                    archive_name = f"{self.project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    self.stop_and_export_project(default_archive_path, archive_name)

                # Get the selected project's history record
                history_record = db.get_project_history_by_id(history_id) # Assumes this method exists
                if not history_record:
                    logging.error(f"No project history found for ID {history_id}")
                    return f"Error: No project history found for ID {history_id}"

                rowd_file_path = Path(history_record['archive_file_path'])
                # Infer CR file path from RoWD file path
                cr_file_path = rowd_file_path.with_name(rowd_file_path.name.replace("_rowd.json", "_cr.json"))

                # [cite_start]Check if archive files exist before proceeding [cite: 298]
                if not rowd_file_path.exists():
                    error_msg = f"Archive file not found at path: {rowd_file_path}"
                    logging.error(error_msg)
                    return error_msg # This message will be shown in the GUI

                # Clear any lingering data before import
                self._clear_active_project_data(db)

                # [cite_start]Import RoWD data [cite: 303]
                with open(rowd_file_path, 'r', encoding='utf-8') as f:
                    artifacts_to_load = json.load(f)
                if artifacts_to_load:
                    db.bulk_insert_artifacts(artifacts_to_load)

                # Import Change Request data
                if cr_file_path.exists():
                    with open(cr_file_path, 'r', encoding='utf-8') as f:
                        crs_to_load = json.load(f)
                    if crs_to_load:
                        db.bulk_insert_change_requests(crs_to_load)

                # Set the orchestrator's state to the loaded project
                self.project_id = history_record['project_id']
                self.project_name = history_record['project_name']
                # [cite_start]Set phase to begin context re-establishment [cite: 304, 305]
                self.set_phase("AWAITING_CONTEXT_REESTABLISHMENT")
                logging.info(f"Successfully loaded archived project '{self.project_name}'. Awaiting context re-establishment.")
                return None # Indicates success

        except Exception as e:
            error_msg = f"A critical error occurred while loading the project: {e}"
            logging.error(error_msg)
            return error_msg


    def get_project_history(self):
        """Retrieves all records from the ProjectHistory table."""
        try:
            with self.db_manager as db:
                return db.get_project_history()
        except Exception as e:
            logging.error(f"Failed to retrieve project history: {e}")
            return []