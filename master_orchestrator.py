import logging
import uuid
import json
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path

from asdf_db_manager import ASDFDBManager
from logic_agent_app_target import LogicAgent_AppTarget
from code_agent_app_target import CodeAgent_AppTarget
from test_agent_app_target import TestAgent_AppTarget
from doc_update_agent_rowd import DocUpdateAgentRoWD
from build_and_commit_agent_app_target import BuildAndCommitAgentAppTarget
from agent_refactoring_planner_app_target import RefactoringPlannerAgent_AppTarget

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FactoryPhase(Enum):
    """Enumeration for the main factory F-Phases."""
    IDLE = auto()
    ENV_SETUP_TARGET_APP = auto()
    SPEC_ELABORATION = auto()
    INTEGRATION_AND_VERIFICATION = auto()
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
        self.active_plan = None
        self.active_plan_cursor = 0 # Add this line

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
        """
        if self.project_id:
            logging.warning(f"A project '{self.project_name}' is already active. Starting a new one will override it in this session.")

        self.project_id = f"proj_{uuid.uuid4().hex[:8]}"
        self.project_name = project_name
        self.current_phase = FactoryPhase.ENV_SETUP_TARGET_APP
        # CORRECTED: Using timezone-aware UTC time
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            with self.db_manager as db:
                db.create_project(self.project_id, self.project_name, timestamp)
            logging.info(f"Successfully started new project: '{self.project_name}' (ID: {self.project_id})")
        except Exception as e:
            logging.error(f"Failed to start new project '{self.project_name}': {e}")
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
        This method executes the core Genesis Pipeline for the current task
        in the active development plan.
        """
        if self.current_phase != FactoryPhase.GENESIS:
            logging.warning(f"Received 'Proceed' action in an unexpected phase: {self.current_phase.name}")
            return

        if not self.active_plan or not isinstance(self.active_plan, list):
            logging.warning("Proceed action called, but no active development plan is loaded. Nothing to execute.")
            # In a real scenario, this might guide the PM to the planning phase.
            return

        # Check if the plan is already completed
        if self.active_plan_cursor >= len(self.active_plan):
            logging.info("Proceed action called, but the active plan is already complete.")
            return

        # Get the current task from the plan using the cursor
        task = self.active_plan[self.active_plan_cursor]
        logging.info(f"PM chose to 'Proceed'. Executing task {self.active_plan_cursor + 1}/{len(self.active_plan)}: {task.get('micro_spec_id')}")

        project_root_path = None
        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    raise Exception("CRITICAL: LLM_API_KEY is not set.")

                project_details = db.get_project_by_id(self.project_id)
                project_root_path = Path(project_details['project_root_folder'])

                # --- Extract task details from the structured plan ---
                micro_spec_id = task.get("micro_spec_id")
                micro_spec_content = task.get("task_description")
                component_name = task.get("component_name")
                component_type = task.get("component_type")
                component_file_path = task.get("component_file_path")
                test_file_path = task.get("test_file_path")
                coding_standard = "Follow PEP 8 standards. Include a clear docstring explaining the function's purpose, arguments, and return value."

                # 1. Instantiate Agents
                logic_agent = LogicAgent_AppTarget(api_key=api_key)
                code_agent = CodeAgent_AppTarget(api_key=api_key)
                test_agent = TestAgent_AppTarget(api_key=api_key)
                build_agent = BuildAndCommitAgentAppTarget(str(project_root_path))
                doc_agent = DocUpdateAgentRoWD(db_manager=db)

                # 2. Generate Logic, Code, and Tests
                logic_plan = logic_agent.generate_logic_for_component(micro_spec_content)
                source_code = code_agent.generate_code_for_component(logic_plan, coding_standard)
                unit_tests = test_agent.generate_unit_tests_for_component(source_code, micro_spec_content)

                # 3. Build, Test, and Commit
                build_success, build_output = build_agent.build_and_commit_component(
                    component_path=component_file_path,
                    component_code=source_code,
                    test_path=test_file_path,
                    test_code=unit_tests
                )

                if not build_success:
                    raise Exception(f"Build failed for component {component_name}: {build_output}")

                # 4. Update Record-of-Work-Done (RoWD)
                commit_hash = build_output.split(":")[-1].strip()
                artifact_data = {
                    "artifact_id": f"art_{uuid.uuid4().hex[:8]}",
                    "project_id": self.project_id,
                    "file_path": component_file_path,
                    "artifact_name": component_name,
                    "artifact_type": component_type,
                    "short_description": micro_spec_content,
                    "status": "UNIT_TESTS_PASSING",
                    "unit_test_status": "TESTS_PASSING",
                    "commit_hash": commit_hash,
                    "version": 1,
                    "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
                    "micro_spec_id": micro_spec_id
                }
                doc_agent.update_artifact_record(artifact_data)
                logging.info(f"Successfully executed and logged task for component: {component_name}")

                # 5. Advance the plan cursor
                self.active_plan_cursor += 1

                # 6. Check for plan completion
                if self.active_plan_cursor >= len(self.active_plan):
                    logging.info("All components in the plan have been generated. Transitioning to Integration & Verification phase.")
                    self.active_plan = None
                    self.active_plan_cursor = 0
                    self.set_phase("INTEGRATION_AND_VERIFICATION")

        except Exception as e:
            logging.error(f"Genesis Pipeline failed while executing plan. Error: {e}")
            self.escalate_for_manual_debug()

    def _run_integration_and_verification_phase(self):
        """
        Executes the full F-Phase 3.5 workflow.
        """
        logging.info("Starting Phase 3.5: Automated Integration & Verification.")
        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                project_details = db.get_project_by_id(self.project_id)
                project_root_path = Path(project_details['project_root_folder'])

                # 1. Get context: new artifacts and existing main files
                # For this example, we assume 'app.py' or a main script is the integration point.
                # A more advanced version would identify these files dynamically.
                integration_target_file = "src/main.py" # Example target

                # Create the file if it doesn't exist
                if not (project_root_path / integration_target_file).exists():
                    (project_root_path / integration_target_file).parent.mkdir(parents=True, exist_ok=True)
                    (project_root_path / integration_target_file).write_text("# Main application entry point\n", encoding='utf-8')

                existing_files = {
                    integration_target_file: (project_root_path / integration_target_file).read_text(encoding='utf-8')
                }

                # Fetch artifacts with status 'UNIT_TESTS_PASSING' that need integration
                new_artifacts = db.get_artifacts_by_statuses(self.project_id, ["UNIT_TESTS_PASSING"])
                if not new_artifacts:
                    logging.warning("Integration phase started, but no new artifacts found to integrate. Skipping.")
                    self.set_phase("PLANNING") # Or another appropriate phase
                    return

                new_artifacts_json = json.dumps([dict(row) for row in new_artifacts], indent=4)

                # 2. Invoke IntegrationPlannerAgent
                logging.info("Invoking IntegrationPlannerAgent...")
                planner_agent = IntegrationPlannerAgent(api_key=api_key)
                integration_plan_str = planner_agent.create_integration_plan(new_artifacts_json, existing_files)
                integration_plan = json.loads(integration_plan_str)

                if "error" in integration_plan:
                    raise Exception(f"IntegrationPlannerAgent failed: {integration_plan['error']}")

                # 3. Invoke OrchestrationCodeAgent for each file to be modified
                logging.info("Invoking OrchestrationCodeAgent to apply integration plan...")
                code_agent = OrchestrationCodeAgent(api_key=api_key)
                all_modified_files = []
                for file_path, modifications in integration_plan.items():
                    all_modified_files.append(file_path)
                    original_code = existing_files[file_path]
                    modifications_json = json.dumps(modifications)
                    modified_code = code_agent.apply_modifications(original_code, modifications_json)
                    (project_root_path / file_path).write_text(modified_code, encoding='utf-8')
                    logging.info(f"Successfully applied integration modifications to {file_path}.")

                # 4. Final Build, Verification, and Commit
                logging.info("Invoking BuildAndCommitAgent for final verification and commit...")
                build_agent = BuildAndCommitAgentAppTarget(str(project_root_path))
                tests_passed, test_output = build_agent.build_component("pytest")

                if not tests_passed:
                    raise Exception(f"Final integration verification failed.\n{test_output}")

                # Find the CR that triggered this work and create a commit message
                active_cr = db.get_cr_by_status(self.project_id, "PLANNING_IN_PROGRESS")
                commit_message = f"feat: Integrate components for CR-{active_cr['cr_id']}" if active_cr else "feat: Integrate newly developed components"

                # Add all new and modified files to the commit
                files_to_commit = all_modified_files + [art['file_path'] for art in new_artifacts]
                commit_success, commit_result = build_agent.commit_changes(files_to_commit, commit_message)

                if not commit_success:
                    raise Exception(f"Final Git commit failed: {commit_result}")

                # 5. Update artifact and CR statuses
                commit_hash = commit_result.split(":")[-1].strip()
                for art in new_artifacts:
                    db.update_artifact_status(art['artifact_id'], "INTEGRATION_TESTED", commit_hash)

                if active_cr:
                    db.update_cr_status(active_cr['cr_id'], "COMPLETED")

                logging.info("Phase 3.5: Integration & Verification completed successfully.")
                self.set_phase("PLANNING") # Return to planning/checkpoint for next steps

        except Exception as e:
            logging.error(f"Integration & Verification Phase failed. Error: {e}")
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
        Handles the logic for when the PM confirms a CR for implementation.
        This orchestrates the RefactoringPlannerAgent to create a detailed
        plan for the Genesis Pipeline to execute.
        """
        logging.info(f"PM has confirmed implementation for Change Request ID: {cr_id}.")

        try:
            with self.db_manager as db:
                # 1. Get necessary context from the database
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    raise Exception("CRITICAL: LLM_API_KEY is not set.")

                cr_details = db.get_cr_by_id(cr_id)
                if not cr_details:
                    raise Exception(f"Could not find details for CR ID {cr_id}")

                project_details = db.get_project_by_id(self.project_id)
                final_spec_text = project_details['final_spec_text']

                all_artifacts = db.get_all_artifacts_for_project(self.project_id)
                rowd_json = json.dumps([dict(row) for row in all_artifacts], indent=4)

                # 2. Update CR status to show planning is in progress
                db.update_cr_status(cr_id, "PLANNING_IN_PROGRESS")
                logging.info(f"Updated status for CR-{cr_id} to PLANNING_IN_PROGRESS.")

                # 3. Instantiate and invoke the RefactoringPlannerAgent
                planner_agent = RefactoringPlannerAgent_AppTarget(api_key=api_key)
                logging.info(f"Invoking RefactoringPlannerAgent for CR-{cr_id}...")
                new_plan = planner_agent.create_refactoring_plan(
                    change_request_desc=cr_details['description'],
                    final_spec_text=final_spec_text,
                    rowd_json=rowd_json
                )

                if "An error occurred" in new_plan:
                    raise Exception(f"RefactoringPlannerAgent failed: {new_plan}")

                # 4. Store the newly generated plan in the orchestrator's state
                # NOTE: In a future iteration, this plan would be saved to a dedicated
                # 'DevelopmentPlans' table in the database.
                self.active_plan = json.loads(new_plan)
                self.active_plan_cursor = 0
                logging.info("Successfully generated new development plan from Change Request.")
                logging.debug(f"New Plan:\n{self.active_plan}")

                # 5. Transition to the Genesis phase to begin execution of the new plan
                self.set_phase("GENESIS")
                logging.info("Transitioning to GENESIS phase to execute the new plan.")

        except Exception as e:
            logging.error(f"Failed to process implementation for CR-{cr_id}. Error: {e}")
            # Optionally, reset the phase or escalate
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST") # Return to previous screen on error

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
        Pauses the currently active project by saving its state to the DB.
        The project remains the active project.
        """
        if not self.project_id:
            logging.warning("No active project to pause.")
            return

        try:
            with self.db_manager as db:
                db.save_orchestration_state(
                    project_id=self.project_id,
                    current_phase=self.current_phase.name,
                    current_step="paused_at_checkpoint",
                    state_details='{"details": "State saved on pause"}',
                    # CORRECTED: Using timezone-aware UTC time
                    timestamp=datetime.now(timezone.utc).isoformat()
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

        rowd_file = archive_dir / f"{archive_name}_rowd.json"
        cr_file = archive_dir / f"{archive_name}_cr.json"

        try:
            with self.db_manager as db:
                artifacts = db.get_all_artifacts_for_project(self.project_id)
                change_requests = db.get_all_change_requests_for_project(self.project_id)
                project_details = db.get_project_by_id(self.project_id)

                artifacts_list = [dict(row) for row in artifacts]
                with open(rowd_file, 'w', encoding='utf-8') as f:
                    json.dump(artifacts_list, f, indent=4)

                cr_list = [dict(row) for row in change_requests]
                with open(cr_file, 'w', encoding='utf-8') as f:
                    json.dump(cr_list, f, indent=4)

                db.add_project_to_history(
                    project_id=self.project_id,
                    project_name=self.project_name,
                    root_folder=project_details['project_root_folder'] if project_details else "N/A",
                    archive_file_path=str(rowd_file),
                    # CORRECTED: Using timezone-aware UTC time
                    timestamp=datetime.now(timezone.utc).isoformat()
                )

                self._clear_active_project_data(db)

            self.project_id = None
            self.project_name = None
            self.current_phase = FactoryPhase.IDLE
            logging.info(f"Successfully exported project '{self.project_name}' to {archive_dir}")
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