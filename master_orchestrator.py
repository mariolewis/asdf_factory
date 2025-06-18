# A conservative character limit to prevent exceeding the LLM's context window.
# This serves as a proxy for token count.
CONTEXT_CHARACTER_LIMIT = 15000

import logging
import uuid
import json
import re
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
import git

from asdf_db_manager import ASDFDBManager
from agents.logic_agent_app_target import LogicAgent_AppTarget
from agents.code_agent_app_target import CodeAgent_AppTarget
from agents.test_agent_app_target import TestAgent_AppTarget
from agents.doc_update_agent_rowd import DocUpdateAgentRoWD
from agents.build_and_commit_agent_app_target import BuildAndCommitAgentAppTarget
from agents.agent_refactoring_planner_app_target import RefactoringPlannerAgent_AppTarget
from agents.agent_integration_planner_app_target import IntegrationPlannerAgent
from agents.agent_orchestration_code_app_target import OrchestrationCodeAgent
from agents.agent_triage_app_target import TriageAgent_AppTarget
from agents.agent_code_review import CodeReviewAgent
from agents.agent_orchestration_code_app_target import OrchestrationCodeAgent
from agents.agent_ui_test_planner_app_target import UITestPlannerAgent_AppTarget
from agents.agent_test_result_evaluation_app_target import TestResultEvaluationAgent_AppTarget
from agents.agent_fix_planner_app_target import FixPlannerAgent_AppTarget
from agents.agent_learning_capture import LearningCaptureAgent
from agents.agent_impact_analysis_app_target import ImpactAnalysisAgent_AppTarget
from agents.agent_test_environment_advisor import TestEnvironmentAdvisorAgent

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FactoryPhase(Enum):
    """Enumeration for the main factory F-Phases."""
    IDLE = auto()
    ENV_SETUP_TARGET_APP = auto()
    SPEC_ELABORATION = auto()
    TECHNICAL_SPECIFICATION = auto()
    BUILD_SCRIPT_SETUP = auto()
    TEST_ENVIRONMENT_SETUP = auto()
    CODING_STANDARD_GENERATION = auto()
    PLANNING = auto()
    GENESIS = auto()
    MANUAL_UI_TESTING = auto()
    AWAITING_PM_DECLARATIVE_CHECKPOINT = auto()
    AWAITING_PREFLIGHT_RESOLUTION = auto()
    RAISING_CHANGE_REQUEST = auto()
    AWAITING_IMPACT_ANALYSIS_CHOICE = auto()
    IMPLEMENTING_CHANGE_REQUEST = auto()
    EDITING_CHANGE_REQUEST = auto()
    REPORTING_OPERATIONAL_BUG = auto()
    AWAITING_LINKED_DELETE_CONFIRMATION = auto()
    DEBUG_PM_ESCALATION = auto()
    VIEWING_PROJECT_HISTORY = auto()
    AWAITING_CONTEXT_REESTABLISHMENT = auto()
    AWAITING_PM_TRIAGE_INPUT = auto()
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
        self.active_plan_cursor = 0
        self.task_awaiting_approval = None
        self.preflight_check_result = None
        self.debug_attempt_counter = 0

        # --- CONFIGURE LOGGING ---
        # Get the configured logging level from the database.
        with self.db_manager as db:
            # Ensure core tables exist before we try to read from them.
            db.create_tables()
            # Default to 'Standard' if no value is found in the database.
            log_level_str = db.get_config_value("LOGGING_LEVEL") or "Standard"
            # Ensure a default context window character limit is set if not present.
            if not db.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT"):
                db.set_config_value(
                    "CONTEXT_WINDOW_CHAR_LIMIT",
                    "15000",
                    "The character limit for context provided to LLM agents before it's trimmed."
                )

        # Map the string from the database to a logging level constant.
        # As per PRD 5.6.5, "Detailed" and "Debug" offer higher verbosity.
        log_level_map = {
            "Standard": logging.INFO,
            "Detailed": logging.DEBUG,
            "Debug": logging.DEBUG,
        }
        log_level = log_level_map.get(log_level_str, logging.INFO)

        # Configure the root logger for the entire application.
        # We use force=True to override any basicConfig that might have been
        # set by an imported module automatically.
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s',
            force=True
        )

        logging.info("MasterOrchestrator initialized.")
        logging.debug(f"Logging level set to '{log_level_str}' ({log_level}).")

    PHASE_DISPLAY_NAMES = {
        FactoryPhase.IDLE: "Idle",
        FactoryPhase.ENV_SETUP_TARGET_APP: "New Application Setup",
        FactoryPhase.SPEC_ELABORATION: "Application Specification",
        FactoryPhase.TECHNICAL_SPECIFICATION: "Technical Specification",
        FactoryPhase.BUILD_SCRIPT_SETUP: "Build Script Generation",
        FactoryPhase.TEST_ENVIRONMENT_SETUP: "Test Environment Setup",
        FactoryPhase.CODING_STANDARD_GENERATION: "Coding Standard Generation",
        FactoryPhase.PLANNING: "Development Planning",
        FactoryPhase.GENESIS: "Iterative Development",
        FactoryPhase.MANUAL_UI_TESTING: "Testing & Validation",
        FactoryPhase.AWAITING_PM_DECLARATIVE_CHECKPOINT: "Checkpoint: High-Risk Change Approval",
        FactoryPhase.AWAITING_PREFLIGHT_RESOLUTION: "Pre-flight Check",
        FactoryPhase.RAISING_CHANGE_REQUEST: "Raise New Change Request",
        FactoryPhase.AWAITING_IMPACT_ANALYSIS_CHOICE: "New CR - Impact Analysis Choice",
        FactoryPhase.IMPLEMENTING_CHANGE_REQUEST: "Implement Change Request",
        FactoryPhase.EDITING_CHANGE_REQUEST: "Edit Change Request",
        FactoryPhase.REPORTING_OPERATIONAL_BUG: "Report Operational Bug",
        FactoryPhase.AWAITING_LINKED_DELETE_CONFIRMATION: "Confirm Linked Deletion",
        FactoryPhase.DEBUG_PM_ESCALATION: "Debug Escalation to PM",
        FactoryPhase.VIEWING_PROJECT_HISTORY: "Select and Load Archived Project",
        FactoryPhase.AWAITING_CONTEXT_REESTABLISHMENT: "Re-establishing Project Context",
        FactoryPhase.AWAITING_PM_TRIAGE_INPUT: "Interactive Triage - Awaiting Input"
    }

    def get_status(self) -> dict:
        """Returns the current status of the orchestrator."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "current_phase": self.current_phase.name
        }

    def load_development_plan(self, plan_json_string: str):
        """
        Loads a JSON plan into the orchestrator's active state.

        Args:
            plan_json_string (str): A string containing the JSON array of the plan.
        """
        try:
            plan = json.loads(plan_json_string)
            if isinstance(plan, list):
                self.active_plan = plan
                self.active_plan_cursor = 0
                logging.info(f"Successfully loaded development plan with {len(plan)} tasks.")
            else:
                raise ValueError("Plan must be a list (JSON array).")
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to load development plan: {e}")
            self.active_plan = None

    def get_current_task_details(self) -> dict | None:
        """
        Safely retrieves the current task from the active plan.

        Returns:
            A dictionary of the current task details, or None if no active plan
            or the plan is complete.
        """
        if self.active_plan and self.active_plan_cursor < len(self.active_plan):
            return self.active_plan[self.active_plan_cursor]
        return None

    def start_new_project(self, project_name: str):
        """
        Initializes a new project.
        If a project is already active, it performs a 'safety export' to
        [cite_start]archive the current work before starting the new one. [cite: 465, 466]
        """
        if self.project_id and self.project_name:
            logging.warning(
                f"An active project '{self.project_name}' was found. "
                "Performing a safety export before starting the new project."
            )
            # Define a default location and name for the safety archive.
            safety_archive_path = Path("data/safety_archives")
            archive_name = f"{self.project_name.replace(' ', '_')}_safety_export_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Call the existing export method.
            self.stop_and_export_project(safety_archive_path, archive_name)
            logging.info(f"Safety export complete for '{self.project_name}'.")

        # Proceed with creating the new project.
        self.project_id = f"proj_{uuid.uuid4().hex[:8]}"
        self.project_name = project_name
        self.current_phase = FactoryPhase.ENV_SETUP_TARGET_APP
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            with self.db_manager as db:
                db.create_project(self.project_id, self.project_name, timestamp)
            logging.info(f"Successfully started new project: '{self.project_name}' (ID: {self.project_id})")
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
        Handles the logic for the Genesis Pipeline, now acting as a dispatcher
        based on component type, as per CR-ASDF-003.
        """
        if self.current_phase != FactoryPhase.GENESIS:
            logging.warning(f"Received 'Proceed' action in an unexpected phase: {self.current_phase.name}")
            return

        if not self.active_plan or not isinstance(self.active_plan, list) or self.active_plan_cursor >= len(self.active_plan):
            logging.warning("Proceed action called, but no valid active development plan is loaded or the plan is complete.")
            return

        task = self.active_plan[self.active_plan_cursor]
        component_type = task.get("component_type", "CLASS") # Default to CLASS for backward compatibility
        logging.info(f"PM chose 'Proceed'. Executing task for component: {task.get('component_name')} of type: {component_type}")

        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    raise Exception("CRITICAL: LLM_API_KEY is not set.")

                project_details = db.get_project_by_id(self.project_id)
                project_root_path = Path(project_details['project_root_folder'])

                # --- Path 1: Standard Source Code Generation (FUNCTION/CLASS) ---
                if component_type in ["FUNCTION", "CLASS"]:
                    self._execute_source_code_generation_task(task, project_root_path, db, api_key)

                # --- Path 2: Declarative/Config File Modification ---
                elif component_type in ["DB_MIGRATION_SCRIPT", "BUILD_SCRIPT_MODIFICATION", "CONFIG_FILE_UPDATE"]:
                    # For now, this path executes automatically. The interactive PM checkpoint
                    # will be added in the next step.
                    self._execute_declarative_modification_task(task, project_root_path, db, api_key)

                else:
                    raise ValueError(f"Unknown component_type '{component_type}' in development plan.")

                # --- Advance Plan Cursor on Success ---
                self.active_plan_cursor += 1
                if self.active_plan_cursor >= len(self.active_plan):
                    logging.info("Development plan complete. Starting Integration and UI Testing phase.")
                    # Directly call the method to run the entire integrated testing phase.
                    self._run_integration_and_ui_testing_phase()

        except Exception as e:
            logging.error(f"Genesis Pipeline failed while executing plan for {task.get('component_name')}. Error: {e}")
            self.escalate_for_manual_debug(str(e))

    def _execute_source_code_generation_task(self, task: dict, project_root_path: Path, db: ASDFDBManager, api_key: str):
        """
        Handles the 'generate -> review -> correct' workflow for standard source code.
        This version is now technology-agnostic.
        """
        component_name = task.get("component_name")
        logging.info(f"Executing language-agnostic code generation for: {component_name}")

        # 1. Retrieve all necessary context, including coding standard and target language
        project_details = db.get_project_by_id(self.project_id)
        coding_standard = project_details['coding_standard_text']
        target_language = project_details['technology_stack']

        if not target_language:
            raise Exception(f"Cannot generate code for '{component_name}': Target Language/Technology Stack is not set for this project.")
        if not coding_standard:
            logging.warning("No project-specific coding standard found. Using a default standard.")
            coding_standard = f"Follow standard conventions for {target_language}. Ensure all code is well-commented."

        all_artifacts_rows = db.get_all_artifacts_for_project(self.project_id)
        rowd_json = json.dumps([dict(row) for row in all_artifacts_rows])
        micro_spec_content = task.get("task_description")

        # 2. Instantiate all necessary agents
        logic_agent = LogicAgent_AppTarget(api_key=api_key)
        code_agent = CodeAgent_AppTarget(api_key=api_key)
        review_agent = CodeReviewAgent(api_key=api_key)
        test_agent = TestAgent_AppTarget(api_key=api_key)
        doc_agent = DocUpdateAgentRoWD(self.db_manager)

        # 3. Generate logic and initial code, now passing the target language
        logic_plan = logic_agent.generate_logic_for_component(micro_spec_content)
        source_code = code_agent.generate_code_for_component(logic_plan, coding_standard, target_language)

        # 4. Automated review and correction loop
        MAX_REVIEW_ATTEMPTS = 2
        review_status, discrepancies = "fail", ""
        for attempt in range(MAX_REVIEW_ATTEMPTS):
            review_status, discrepancies = review_agent.review_code(micro_spec_content, logic_plan, source_code, rowd_json, coding_standard)
            if review_status == "pass":
                break
            else:
                logging.warning(f"Component '{component_name}' failed code review on attempt {attempt + 1}. Feedback: {discrepancies}")
                if attempt < MAX_REVIEW_ATTEMPTS - 1:
                    source_code = code_agent.generate_code_for_component(logic_plan, coding_standard, target_language, feedback=discrepancies)

        if review_status != "pass":
            raise Exception(f"Component '{component_name}' failed code review after all attempts.")

        # 5. Generate unit tests for the approved code, also passing the target language
        unit_tests = test_agent.generate_unit_tests_for_component(source_code, micro_spec_content, coding_standard, target_language)

        # 6. Build, commit, and update RoWD (logic remains the same)
        build_agent = BuildAndCommitAgentAppTarget(str(project_root_path))
        is_build_automated = bool(project_details['is_build_automated'])
        commit_hash = None

        if is_build_automated:
            # This part now needs to be intelligent, we will address this next.
            # For now, we assume a generic test runner can be figured out by the build tool.
            build_success, build_output = build_agent.build_and_commit_component(
                task.get("component_file_path"), source_code, task.get("test_file_path"), unit_tests)
            if not build_success:
                raise Exception(f"Build failed for component {component_name}: {build_output}")
            commit_hash = build_output.split(":")[-1].strip()
        else:
            # Manual build path logic remains the same
            component_path = project_root_path / task.get("component_file_path")
            test_path = project_root_path / task.get("test_file_path")
            component_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.parent.mkdir(parents=True, exist_ok=True)
            component_path.write_text(source_code, encoding='utf-8')
            test_path.write_text(unit_tests, encoding='utf-8')
            files_to_commit = [task.get("component_file_path"), task.get("test_file_path")]
            commit_message = f"feat: Add component {component_name} (manual build)"
            commit_success, commit_result = build_agent.commit_changes(files_to_commit, commit_message)

            if not commit_success:
                raise Exception(f"Git commit failed for component {component_name}: {commit_result}")
            commit_hash = commit_result.split(":")[-1].strip()

        doc_agent.update_artifact_record({
            "artifact_id": f"art_{uuid.uuid4().hex[:8]}", "project_id": self.project_id,
            "file_path": task.get("component_file_path"), "artifact_name": component_name,
            "artifact_type": task.get("component_type"), "short_description": micro_spec_content,
            "status": "UNIT_TESTS_PASSING", "unit_test_status": "TESTS_PASSING",
            "commit_hash": commit_hash, "version": 1,
            "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
            "micro_spec_id": task.get("micro_spec_id")
        })

    def _execute_declarative_modification_task(self, task: dict, project_root_path: Path, db: ASDFDBManager, api_key: str):
        """
        Pauses the workflow to await PM confirmation for a declarative change.
        """
        component_name = task.get("component_name")
        logging.info(f"High-risk modification detected for '{component_name}'. Pausing for PM checkpoint.")

        # Store the task that needs approval and set the phase to wait for the UI
        self.task_awaiting_approval = task
        self.set_phase("AWAITING_PM_DECLARATIVE_CHECKPOINT")

    def handle_declarative_checkpoint_decision(self, decision: str):
        """
        Processes the PM's decision from the declarative checkpoint.

        Args:
            decision (str): The decision made by the PM ("EXECUTE" or "MANUAL").
        """
        if not self.task_awaiting_approval:
            logging.error("Received a checkpoint decision, but no task is awaiting approval.")
            return

        task = self.task_awaiting_approval
        component_name = task.get("component_name")
        logging.info(f"PM made decision '{decision}' for component '{component_name}'.")

        try:
            with self.db_manager as db:
                if decision == "EXECUTE_AUTOMATICALLY":
                    api_key = db.get_config_value("LLM_API_KEY")
                    project_details = db.get_project_by_id(self.project_id)
                    project_root_path = Path(project_details['project_root_folder'])
                    file_to_modify_path_str = task.get("component_file_path")
                    file_to_modify = project_root_path / file_to_modify_path_str

                    if not file_to_modify.exists():
                        raise FileNotFoundError(f"Cannot modify file '{file_to_modify_path_str}' because it does not exist.")

                    original_code = file_to_modify.read_text(encoding='utf-8')
                    change_snippet = task.get("task_description")

                    orch_agent = OrchestrationCodeAgent(api_key=api_key)
                    modified_code = orch_agent.apply_modifications(original_code, change_snippet)
                    file_to_modify.write_text(modified_code, encoding='utf-8')

                    build_agent = BuildAndCommitAgentAppTarget(str(project_root_path))
                    commit_message = f"refactor: Apply approved modification to {component_name}"
                    build_agent.commit_changes([file_to_modify_path_str], commit_message)

                    # Here you would update the RoWD record for this task to "COMPLETED"
                    logging.info(f"Automatically executed and committed modification for {component_name}.")

                elif decision == "WILL_EXECUTE_MANUALLY":
                    # Here you would update the RoWD record to a status like "AWAITING_MANUAL_EXECUTION"
                    logging.info(f"Acknowledged that PM will manually execute change for {component_name}.")

        finally:
            # Clean up and continue the plan
            self.task_awaiting_approval = None
            self.set_phase("GENESIS")
            # We call handle_proceed_action again to process the *next* item in the plan
            # But we must ensure the cursor is advanced first to avoid a loop
            self.active_plan_cursor += 1
            # This logic might need refinement to avoid immediately processing next step
            # For now, we'll just log and let the UI trigger the next "proceed"
            logging.info("Returning to Genesis phase to continue with the next task.")

    def _run_integration_and_ui_testing_phase(self):
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

                # Save the successful integration plan to the database.
                db.save_integration_plan(self.project_id, integration_plan_str)
                logging.info(f"Successfully saved integration plan for project {self.project_id}.")

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

                # 4. Final Build and Verification
                logging.info("Invoking VerificationAgent for final verification...")

                # Import the agent here to avoid circular dependency issues at the top level
                from agents.agent_verification_app_target import VerificationAgent_AppTarget
                verification_agent = VerificationAgent_AppTarget(api_key=api_key)

                # The agent now intelligently determines the test command from the tech spec
                tests_passed, test_output = verification_agent.run_verification_tests(
                    project_root=project_root_path,
                    tech_spec_text=project_details['tech_spec_text']
                )

                if not tests_passed:
                    # On failure, create a detailed log and call the debug pipeline.
                    failure_log = f"Final integration verification failed.\n{test_output}"
                    logging.error(failure_log)
                    self.escalate_for_manual_debug(failure_log)
                    return # Stop further execution in this method

                # If the build is successful, the 'test_output' now contains the commit hash.
                commit_hash = test_output.split(":")[-1].strip()

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

                # 6. Generate and Save UI Test Plan for Manual Execution
                logging.info("Automated verification passed. Generating UI test plan for PM review.")

                # The agent now needs both functional and technical specifications.
                functional_spec_text = project_details['final_spec_text']
                technical_spec_text = project_details['tech_spec_text']

                if not functional_spec_text or not technical_spec_text:
                    raise Exception("Cannot generate UI test plan: Missing Functional or Technical Specification in the database.")

                ui_test_planner = UITestPlannerAgent_AppTarget(api_key=api_key)
                ui_test_plan_content = ui_test_planner.generate_ui_test_plan(
                    functional_spec_text=functional_spec_text,
                    technical_spec_text=technical_spec_text
                )

                # Save the generated UI test plan to the database.
                db.save_ui_test_plan(self.project_id, ui_test_plan_content)
                logging.info(f"Successfully saved UI test plan for project {self.project_id}.")
                logging.info("Automated integration and UI test plan generation complete.")
                # Transition to the manual testing phase to await PM input.
                self.set_phase("MANUAL_UI_TESTING")

        except Exception as e:
            logging.error(f"Integration & Verification Phase failed. Error: {e}")
            self.escalate_for_manual_debug()

    def handle_ui_test_result_upload(self, test_result_content: str):
        """
        Orchestrates the evaluation of an uploaded UI test results file.

        If failures are found, it triggers the debug pipeline (F-Phase 5).

        Args:
            test_result_content (str): The string content of the uploaded
                                       test results file.
        """
        if not self.project_id:
            logging.error("Cannot handle test result upload; no active project.")
            return

        logging.info(f"Handling UI test result upload for project {self.project_id}.")
        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    raise Exception("Cannot evaluate test results: LLM_API_KEY is not set.")

            # 1. Evaluate the results using the dedicated agent.
            eval_agent = TestResultEvaluationAgent_AppTarget(api_key=api_key)
            failure_summary = eval_agent.evaluate_ui_test_results(test_result_content)

            # 2. Check the agent's response for failures.
            if "ALL_TESTS_PASSED" in failure_summary:
                logging.info("UI test result evaluation complete: All tests passed.")
                # In a future step, we will add a UI element to let the PM
                # confirm completion of this phase. For now, we just log it.

            else:
                # 3. If failures are found, trigger the debug pipeline as a functional bug.
                logging.warning("UI test result evaluation complete: Failures detected.")
                self.escalate_for_manual_debug(failure_summary, is_functional_bug=True)

        except Exception as e:
            logging.error(f"An unexpected error occurred during UI test result evaluation: {e}")
            # Escalate with the error message itself if the process fails.
            self.escalate_for_manual_debug(str(e))

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

    def save_new_change_request(self, description: str, request_type: str = 'CHANGE_REQUEST'):
        """
        Saves a new, standard functional enhancement CR to the database.

        Args:
            description (str): The description of the change from the PM.
            request_type (str): The type of CR being saved.
        """
        if not self.project_id:
            logging.error("Cannot save change request; no active project.")
            return

        try:
            with self.db_manager as db:
                db.add_change_request(self.project_id, description)
            self.set_phase("AWAITING_IMPACT_ANALYSIS_CHOICE")
            logging.info("Successfully saved new Functional Enhancement CR.")
        except Exception as e:
            logging.error(f"Failed to save new change request: {e}")

    def save_spec_correction_cr(self, new_spec_text: str):
        """
        Saves a 'Specification Correction' CR, runs an immediate impact analysis
        by comparing it to the old spec, and auto-generates a linked CR for the
        required code changes.
        """
        if not self.project_id:
            logging.error("Cannot save spec correction; no active project.")
            return

        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                project_details = db.get_project_by_id(self.project_id)
                original_spec_text = project_details['final_spec_text']

                # 1. Save the primary "Specification Correction" CR
                spec_cr_description = "Correction to Application Specification. See linked CR for code implementation."
                spec_cr_id = db.add_change_request(
                    project_id=self.project_id,
                    description=spec_cr_description,
                    request_type='SPEC_CORRECTION'
                )
                db.update_cr_status(spec_cr_id, "COMPLETED")

                # 2. Update the specification text in the Projects table immediately
                db.save_final_specification(self.project_id, new_spec_text)
                logging.info(f"Saved new specification text for CR-{spec_cr_id}.")

                # 3. Run impact analysis by comparing old and new specs
                all_artifacts = db.get_all_artifacts_for_project(self.project_id)
                rowd_json = json.dumps([dict(row) for row in all_artifacts])

                # Create a synthetic change request description for the agent
                cr_desc_for_agent = (
                    "Analyze the difference between the 'Original Specification' and the 'New Specification' "
                    "to identify the necessary code changes. The 'New Specification' is the source of truth."
                    f"\n\n--- Original Specification ---\n{original_spec_text}"
                    f"\n\n--- New Specification ---\n{new_spec_text}"
                )

                impact_agent = ImpactAnalysisAgent_AppTarget(api_key=api_key)
                _, summary, impacted_ids = impact_agent.analyze_impact(
                    change_request_desc=cr_desc_for_agent,
                    final_spec_text=new_spec_text, # Analyze against the new spec
                    rowd_json=rowd_json
                )

                # 4. Auto-generate the linked "Code Implementation" CR
                if summary:
                    code_cr_description = (
                        f"Auto-generated CR to implement changes for Specification Correction CR-{spec_cr_id}.\n\n"
                        f"Analysis Summary: {summary}"
                    )
                    db.add_linked_change_request(
                        project_id=self.project_id,
                        description=code_cr_description,
                        linked_cr_id=spec_cr_id
                    )
                    logging.info(f"Auto-generated linked code implementation CR for Spec CR-{spec_cr_id}.")

            # 5. Return to the CR register to show the results
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

        except Exception as e:
            logging.error(f"Failed to process specification correction CR: {e}")
            self.set_phase("RAISING_CHANGE_REQUEST") # Return to the previous screen on error

    def handle_report_bug_action(self):
        """
        Transitions the factory into the state for reporting a new bug.
        """
        if self.current_phase == FactoryPhase.GENESIS:
            logging.info("PM initiated 'Report Bug'. Transitioning to bug reporting screen.")
            self.set_phase("REPORTING_OPERATIONAL_BUG")
        else:
            logging.warning(f"Received 'Report Bug' action in an unexpected phase: {self.current_phase.name}")

    def save_bug_report(self, description: str, severity: str) -> bool:
        """
        Saves a new bug report to the database via the DAO.

        Args:
            description (str): The description of the bug from the PM.
            severity (str): The severity rating from the PM.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        if not self.project_id:
            logging.error("Cannot save bug report; no active project.")
            return False

        if not description or not description.strip():
            logging.warning("Cannot save empty bug report description.")
            return False

        try:
            with self.db_manager as db:
                db.add_bug_report(self.project_id, description, severity)

            # After successfully saving, return to the main development checkpoint.
            self.set_phase("GENESIS")
            logging.info("Successfully saved new bug report and returned to Genesis phase.")
            return True
        except Exception as e:
            logging.error(f"Failed to save new bug report: {e}")
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
        This now uses the centralized context builder to ensure context window
        limits are respected and the PM is informed of any trimming.
        """
        logging.info(f"PM has confirmed implementation for Change Request ID: {cr_id}.")

        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    raise Exception("CRITICAL: LLM_API_KEY is not set.")

                cr_details = db.get_cr_by_id(cr_id)
                project_details = db.get_project_by_id(self.project_id)
                project_root_path = Path(project_details['project_root_folder'])

                # 1. Gather impacted artifact IDs and source code files
                impacted_ids = []
                impacted_ids_json = cr_details['impacted_artifact_ids']
                if impacted_ids_json:
                    impacted_ids = json.loads(impacted_ids_json)

                source_code_files = {}
                for artifact_id in impacted_ids:
                    artifact_record = db.get_artifact_by_id(artifact_id)
                    if artifact_record and artifact_record['file_path']:
                        try:
                            source_path = project_root_path / artifact_record['file_path']
                            if source_path.exists():
                                source_code_files[artifact_record['file_path']] = source_path.read_text(encoding='utf-8')
                        except Exception:
                            pass # Ignore files that can't be read

                # 2. Build and validate the context package using the new helper method
                core_docs = {
                    "final_spec_text": project_details['final_spec_text'],
                    "tech_spec_text": project_details['tech_spec_text'],
                }
                context_package = self._build_and_validate_context_package(db, core_docs, source_code_files)

                # Handle errors from the context builder
                if context_package.get("error"):
                    raise Exception(f"Context Builder Error: {context_package['error']}")

                # 3. Inform the PM if the context was trimmed
                if context_package.get("was_trimmed"):
                    excluded_files_list = context_package.get("excluded_files", [])
                    # Store this message in session state for the UI to display
                    st.session_state.info_message = (
                        "Warning: The context for this task was too large and was automatically trimmed to prevent an error. "
                        f"The following {len(excluded_files_list)} files were excluded: {', '.join(excluded_files_list)}. "
                        "The resulting plan may be less precise."
                    )

                # 4. Prepare final context for the planning agent
                final_context_str = "\n".join(context_package["source_code"].values())
                all_artifacts = db.get_all_artifacts_for_project(self.project_id)
                rowd_json = json.dumps([dict(row) for row in all_artifacts])

                db.update_cr_status(cr_id, "PLANNING_IN_PROGRESS")

                # 5. Invoke the RefactoringPlannerAgent
                planner_agent = RefactoringPlannerAgent_AppTarget(api_key=api_key)
                new_plan_str = planner_agent.create_refactoring_plan(
                    change_request_desc=cr_details['description'],
                    full_context_str=final_context_str, # Use the potentially trimmed context
                    rowd_json=rowd_json
                )

                if "error" in new_plan_str:
                    raise Exception(f"RefactoringPlannerAgent failed: {new_plan_str}")

                # 6. Store the plan and transition to the Genesis phase
                self.active_plan = json.loads(new_plan_str)
                self.active_plan_cursor = 0
                logging.info("Successfully generated new development plan from Change Request.")
                self.set_phase("GENESIS")

        except Exception as e:
            logging.error(f"Failed to process implementation for CR-{cr_id}. Error: {e}")
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

    def handle_run_impact_analysis_action(self, cr_id: int):
        """
        Orchestrates the running of an impact analysis for a specific CR.
        """
        logging.info(f"PM has requested to run impact analysis for CR ID: {cr_id}.")
        try:
            with self.db_manager as db:
                # Get necessary context
                api_key = db.get_config_value("LLM_API_KEY")
                cr_details = db.get_cr_by_id(cr_id)
                project_details = db.get_project_by_id(self.project_id)
                all_artifacts = db.get_all_artifacts_for_project(self.project_id)

                # Prepare context for the agent
                rowd_json = json.dumps([dict(row) for row in all_artifacts], indent=4)

                # Invoke the agent
                agent = ImpactAnalysisAgent_AppTarget(api_key=api_key)
                rating, summary, impacted_ids = agent.analyze_impact(
                    change_request_desc=cr_details['description'],
                    final_spec_text=project_details['final_spec_text'],
                    rowd_json=rowd_json
                )

                if rating is None:
                    # The agent failed, log the summary which now contains the error
                    raise Exception(f"ImpactAnalysisAgent failed: {summary}")

                # Save the real results to the database
                db.update_cr_impact_analysis(cr_id, rating, summary, impacted_ids)
                logging.info(f"Successfully ran and saved impact analysis for CR ID: {cr_id}.")

        except Exception as e:
            logging.error(f"Failed to run impact analysis for CR ID {cr_id}: {e}")
            # Optionally, set an error state to be displayed in the UI

    #
# --- REPLACE THE ENTIRE METHOD WITH THIS ---
#
    def handle_delete_cr_action(self, cr_id_to_delete: int):
        """
        Handles the deletion of a CR, now with checks for linked CRs.
        If a link is found, it pauses for PM confirmation.
        """
        logging.info(f"PM initiated delete for CR ID: {cr_id_to_delete}.")
        try:
            with self.db_manager as db:
                cr_to_delete = db.get_cr_by_id(cr_id_to_delete)
                if not cr_to_delete:
                    logging.error(f"Cannot delete CR-{cr_id_to_delete}: Not found.")
                    return

                # Check for links in either direction
                linked_id = cr_to_delete['linked_cr_id']
                other_cr_linking_to_this = db.get_cr_by_linked_id(cr_id_to_delete)

                if linked_id or other_cr_linking_to_this:
                    # This is part of a linked pair. Pause for confirmation.
                    logging.warning(f"CR-{cr_id_to_delete} is part of a linked pair. Awaiting PM confirmation for deletion.")
                    self.task_awaiting_approval = {
                        "primary_cr_id": cr_id_to_delete,
                        "linked_cr_id": linked_id or other_cr_linking_to_this['cr_id']
                    }
                    self.set_phase("AWAITING_LINKED_DELETE_CONFIRMATION")
                else:
                    # This is a standalone CR, delete it directly.
                    db.delete_change_request(cr_id_to_delete)
                    logging.info(f"Successfully deleted standalone CR ID: {cr_id_to_delete}.")
                    # The UI will rerun and show the updated list.

        except Exception as e:
            logging.error(f"Failed to process delete action for CR-{cr_id_to_delete}: {e}")

    def handle_linked_delete_confirmation(self, primary_cr_id: int, linked_cr_id: int):
        """
        Deletes a pair of linked CRs after PM confirmation.
        """
        logging.info(f"PM confirmed deletion of linked pair: CR-{primary_cr_id} and CR-{linked_cr_id}.")
        try:
            with self.db_manager as db:
                # Add logic here to roll back the spec change if necessary
                spec_cr = db.get_cr_by_id(linked_cr_id)
                if spec_cr and spec_cr['request_type'] == 'SPEC_CORRECTION':
                    # This is a placeholder for a more complex rollback logic
                    logging.warning(f"Spec Correction CR-{linked_cr_id} is being deleted. A full implementation would roll back the spec text.")

                # Delete both records
                db.delete_change_request(primary_cr_id)
                db.delete_change_request(linked_cr_id)

            logging.info("Successfully deleted linked CR pair.")
        except Exception as e:
            logging.error(f"Failed to delete linked CR pair: {e}")
        finally:
            # Always return to the register view
            self.task_awaiting_approval = None
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

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

    def get_cr_and_bug_report_data(self, project_id: str, filter_type: str) -> list[dict]:
        """
        Fetches and consolidates data for the 'Change Requests & Bug Fixes' report.

        Args:
            project_id (str): The ID of the project to report on.
            filter_type (str): The filter to apply ("Pending", "Closed", or "All").

        Returns:
            A list of dictionaries, each representing a CR or a bug fix.
        """
        report_data = []

        # Define status categories
        cr_pending_statuses = ["RAISED", "IMPACT_ANALYZED", "PLANNING_IN_PROGRESS", "IMPLEMENTATION_IN_PROGRESS"]
        cr_closed_statuses = ["COMPLETED", "CANCELLED"]
        bug_pending_statuses = ["UNIT_TESTS_FAILING", "DEBUG_IN_PROGRESS", "AWAITING_PM_TRIAGE_INPUT", "DEBUG_PM_ESCALATION"]

        # Determine which statuses to query based on the filter
        cr_statuses_to_query = []
        bug_statuses_to_query = []

        if filter_type == "Pending":
            cr_statuses_to_query = cr_pending_statuses
            bug_statuses_to_query = bug_pending_statuses
        elif filter_type == "Closed":
            cr_statuses_to_query = cr_closed_statuses
            # There isn't a "closed" state for bugs in the same way, so we fetch none.
            bug_statuses_to_query = []
        elif filter_type == "All":
            cr_statuses_to_query = cr_pending_statuses + cr_closed_statuses
            bug_statuses_to_query = bug_pending_statuses

        with self.db_manager as db:
            # Fetch Change Requests
            if cr_statuses_to_query:
                change_requests = db.get_change_requests_by_statuses(project_id, cr_statuses_to_query)
                for cr in change_requests:
                    report_data.append({
                        "id": f"CR-{cr['cr_id']}",
                        "type": "CR",
                        "status": cr['status'],
                        "description": cr['description']
                    })

            # Fetch Bug Fixes
            if bug_statuses_to_query:
                bug_artifacts = db.get_artifacts_by_statuses(project_id, bug_statuses_to_query)
                for bug in bug_artifacts:
                    report_data.append({
                        "id": bug['artifact_id'],
                        "type": "Bugfix",
                        "status": bug['status'],
                        "description": f"Failure in component: {bug['artifact_name']}"
                    })

        return sorted(report_data, key=lambda x: x['id'])

    def resume_project(self):
        """
        Resumes a paused project by loading its last saved state from the database.
        """
        if not self.project_id:
            logging.warning("No active project to resume.")
            return False

        try:
            with self.db_manager as db:
                state_data = db.get_orchestration_state(self.project_id)

            if state_data:
                saved_phase_name = state_data['current_phase']
                self.set_phase(saved_phase_name)
                logging.info(f"Project '{self.project_name}' resumed successfully. Returning to phase: {saved_phase_name}.")
                # In a more advanced implementation, we would also restore the
                # 'state_details' JSON blob to recover more granular state.
                return True
            else:
                logging.warning(f"No saved state found for project '{self.project_name}'. Cannot resume.")
                return False

        except Exception as e:
            logging.error(f"An error occurred while resuming project {self.project_id}: {e}")
            return False

    def escalate_for_manual_debug(self, failure_log: str, is_functional_bug: bool = False):
        """
        Initiates the triage and planning process for a bug.
        It now acts as a router: for functional bugs, it bypasses technical
        triage. For technical errors, it proceeds with Tiers 1, 2, and 3.

        Args:
            failure_log (str): The error log or functional bug description.
            is_functional_bug (bool): Flag to indicate if the bug is functional,
                                      allowing a bypass of technical triage.
        """
        logging.info("A failure has triggered the debugging pipeline.")

        # This is the new router logic.
        if is_functional_bug:
            logging.info("Functional bug detected. Bypassing technical triage and proceeding directly to fix planning.")
            self._plan_fix_from_description(failure_log)
            return # Exit early, skipping the technical triage tiers.

        # --- The existing technical triage logic now only runs if it's not a functional bug ---
        self.debug_attempt_counter += 1
        logging.info(f"Technical debug attempt counter is now: {self.debug_attempt_counter}")

        with self.db_manager as db:
            max_attempts_str = db.get_config_value("MAX_DEBUG_ATTEMPTS") or "2"
            max_attempts = int(max_attempts_str)

        if self.debug_attempt_counter > max_attempts:
            logging.warning(f"Automated debug attempts ({self.debug_attempt_counter - 1}) have exceeded the limit of {max_attempts}. Escalating to PM.")
            self.set_phase("DEBUG_PM_ESCALATION")
            return

        try:
            with self.db_manager as db:
                project_details = db.get_project_by_id(self.project_id)
                project_root_path = Path(project_details['project_root_folder'])
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    raise Exception("Cannot proceed with debugging. LLM API Key is not set.")

                # Atomic Rollback on Failure
                logging.warning(f"Performing atomic rollback on '{project_root_path}' before attempting new fix.")
                try:
                    repo = git.Repo(project_root_path)
                    repo.git.reset('--hard', 'HEAD')
                    repo.git.clean('-fdx')
                    logging.info("Rollback successful. Repository is now in a clean state.")
                except Exception as e:
                    logging.error(f"CRITICAL: Atomic rollback failed: {e}")
                    self.set_phase("DEBUG_PM_ESCALATION")
                    return

                context_package = {}
                all_artifacts = db.get_all_artifacts_for_project(self.project_id)
                rowd_json = json.dumps([dict(row) for row in all_artifacts], indent=4)

                # Tier 1: Automated Stack Trace Analysis
                logging.info("Attempting Tier 1 analysis: Parsing stack trace.")
                if "Traceback (most recent call last):" in failure_log:
                    file_path_pattern = r'File "([^"]+)"'
                    found_paths = re.findall(file_path_pattern, failure_log)
                    unique_paths = list(dict.fromkeys(found_paths))
                    if unique_paths:
                        for file_path_str in unique_paths:
                            try:
                                full_path = Path(file_path_str).resolve()
                                if project_root_path.resolve() in full_path.parents or project_root_path.resolve() == full_path:
                                    relative_path = str(full_path.relative_to(project_root_path))
                                    context_package[relative_path] = full_path.read_text(encoding='utf-8')
                            except Exception as e:
                                logging.warning(f"Could not read source file from traceback: {file_path_str}. Error: {e}")

                if context_package:
                    logging.info("Tier 1 Success: Context gathered from stack trace. Proceeding to plan a fix.")
                    self._plan_and_execute_fix(failure_log, context_package, api_key)
                    return

                # Tier 2: Automated Apex Trace Analysis
                logging.warning("Tier 1 Failed: No usable stack trace found. Proceeding to Tier 2 analysis.")
                apex_file_name = project_details["apex_executable_name"]
                if apex_file_name:
                    failing_component_match = re.search(r"component '([^']+)'", failure_log, re.IGNORECASE)
                    if failing_component_match:
                        failing_component_name = failing_component_match.group(1)
                        agent = TriageAgent_AppTarget(api_key=api_key, db_manager=self.db_manager)
                        path_list_json = agent.perform_apex_trace_analysis(rowd_json, apex_file_name, failing_component_name)
                        try:
                            file_paths_to_load = json.loads(path_list_json)
                            if file_paths_to_load:
                                for file_path in file_paths_to_load:
                                    full_path = project_root_path / file_path
                                    if full_path.exists():
                                        context_package[file_path] = full_path.read_text(encoding='utf-8')
                        except json.JSONDecodeError:
                            logging.error(f"Tier 2: Failed to parse JSON response from TriageAgent: {path_list_json}")

                if context_package:
                    logging.info("Tier 2 Success: Context gathered from guided trace. Proceeding to plan a fix.")
                    self._plan_and_execute_fix(failure_log, context_package, api_key)
                    return

                # Tier 3: Interactive Triage
                logging.warning("Tier 2 Failed: Could not determine context automatically. Proceeding to Tier 3 for PM interaction.")
                self.set_phase("AWAITING_PM_TRIAGE_INPUT")

        except Exception as e:
            logging.error(f"A critical error occurred during the triage process: {e}")
            self.set_phase("DEBUG_PM_ESCALATION")

    def handle_pm_triage_input(self, pm_error_description: str):
        """
        Handles the text input provided by the PM during interactive triage (Tier 3).
        It uses the TriageAgent to form a hypothesis and the FixPlannerAgent to create a plan.

        Args:
            pm_error_description (str): The PM's description of the error.
        """
        logging.info("Tier 3: Received manual error description from PM. Attempting to generate fix plan.")

        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    raise Exception("Cannot proceed with triage. LLM API Key is not set.")

            # Use TriageAgent to refine the PM's description into a testable hypothesis.
            triage_agent = TriageAgent_AppTarget(api_key=api_key, db_manager=self.db_manager)
            hypothesis = triage_agent.analyze_and_hypothesize(
                error_logs=pm_error_description,
                relevant_code="No specific code context available; base analysis on user description.",
                test_report=""
            )

            if "An error occurred" in hypothesis:
                 raise Exception(f"TriageAgent failed to form a hypothesis: {hypothesis}")

            logging.info(f"TriageAgent formed hypothesis: {hypothesis}")

            # Use FixPlannerAgent to create a plan from the hypothesis.
            planner_agent = FixPlannerAgent_AppTarget(api_key=api_key)
            fix_plan_str = planner_agent.create_fix_plan(
                root_cause_hypothesis=hypothesis,
                relevant_code="No specific code context was automatically identified. Base the fix on the TriageAgent's hypothesis."
            )

            if "error" in fix_plan_str.lower():
                raise Exception(f"FixPlannerAgent failed to generate a plan: {fix_plan_str}")

            fix_plan = json.loads(fix_plan_str)
            if not fix_plan:
                 raise Exception("FixPlannerAgent returned an empty plan.")

            # Step 3: Capture this successful interaction as a learning moment.
            learning_agent = LearningCaptureAgent(self.db_manager)
            tags = self._extract_tags_from_text(hypothesis)
            learning_agent.add_learning_entry(
                context=f"During interactive triage (Tier 3) for project: {self.project_name}",
                problem=pm_error_description,
                solution=fix_plan_str,
                tags=tags
            )

            # Load the new fix plan and transition to Genesis to execute it.
            self.active_plan = fix_plan
            self.active_plan_cursor = 0
            self.set_phase("GENESIS")
            logging.info("Successfully generated a fix plan from PM description. Transitioning to GENESIS phase.")

        except Exception as e:
            logging.error(f"Tier 3 interactive triage failed. Error: {e}")
            self.set_phase("DEBUG_PM_ESCALATION")

    def handle_pm_debug_choice(self, choice: str):
        """
        Handles the decision made by the PM during a debug escalation.

        Args:
            choice (str): The PM's selected option ('RETRY', 'MANUAL_PAUSE', or 'IGNORE').
        """
        logging.info(f"PM selected debug escalation option: {choice}")

        if choice == "RETRY":
            # Reset the counter and re-trigger the entire triage process.
            self.debug_attempt_counter = 0
            # A failure log needs to be passed; we retrieve the last known one
            # from the task awaiting approval, if it exists.
            failure_log_from_state = self.task_awaiting_approval.get('failure_log', "PM-initiated retry after escalation.")
            self.escalate_for_manual_debug(failure_log_from_state)

        elif choice == "MANUAL_PAUSE":
            # Use the existing pause_project method.
            self.pause_project()
            logging.info("Project paused for manual PM investigation.")

        elif choice == "IGNORE":
            # Acknowledge the bug and move on to the next task in the plan.
            # A more advanced implementation would update the artifact's status.
            logging.warning("Acknowledging and ignoring bug. Proceeding with the next task.")
            self.set_phase("GENESIS")

        # Clean up the task that was awaiting approval.
        self.task_awaiting_approval = None

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


    def stop_and_export_project(self, archive_dir: str | Path, archive_name: str) -> str | None:
        """
        Exports all project data to files, adds a record to history,
        and clears the active project from the database.

        Args:
            archive_dir (str | Path): The base directory for the archive.
            archive_name (str): The name for the archive files (without extension).

        Returns:
            str | None: The full path to the created RoWD archive file on success,
                        or None on failure.
        """
        if not self.project_id:
            logging.warning("No active project to stop and export.")
            return None

        archive_dir = Path(archive_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Define the primary archive file path (for the RoWD)
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
                    timestamp=datetime.now(timezone.utc).isoformat()
                )

                self._clear_active_project_data(db)

            self.project_id = None
            self.project_name = None
            self.current_phase = FactoryPhase.IDLE
            logging.info(f"Successfully exported project '{self.project_name}' to {archive_dir}")
            return str(rowd_file)

        except Exception as e:
            logging.error(f"Failed to stop and export project: {e}")
            return None

    def _perform_preflight_checks(self, project_root_str: str) -> dict:
        """
        Performs a sequence of pre-flight checks on an existing project environment.

        Args:
            project_root_str: The path to the project's root folder.

        Returns:
            A dictionary containing the status and a message.
        """
        project_root = Path(project_root_str)

        # 1. Path Validation
        if not project_root.exists():
            return {"status": "PATH_NOT_FOUND", "message": f"The project folder could not be found. Please confirm the new location: {project_root_str}"}

        # 2. VCS Validation
        if not (project_root / '.git').is_dir():
            return {"status": "GIT_MISSING", "message": "The project folder was found, but the Git repository is missing. Please re-initialize the repository."}

        try:
            repo = git.Repo(project_root)
        except git.InvalidGitRepositoryError:
            return {"status": "GIT_MISSING", "message": "The project folder contains an invalid Git repository."}

        # 3. State Drift Validation
        if repo.is_dirty(untracked_files=True):
            return {"status": "STATE_DRIFT", "message": "Uncommitted local changes have been detected. To prevent conflicts, please resolve the state of the repository."}

        # 4. Core Artifact Validation (Placeholder for more complex logic)
        # This check is basic for now. A future version would iterate through the RoWD
        # and ensure key files exist. We'll simulate one check.
        if "build.gradle.kts" in [p.name for p in project_root.iterdir()]:
             logging.info("Pre-flight check: Found build.gradle.kts, core artifact check passed (simulated).")

        # All checks passed
        return {"status": "ALL_PASS", "message": "Project environment successfully verified."}

    def handle_discard_changes(self, project_id: str):
        """
        Handles the 'Discard all local changes' expert option for a project
        with state drift. Resets the git repository and re-runs checks.
        """
        logging.warning(f"Executing 'git reset --hard' for project {project_id}")
        try:
            with self.db_manager as db:
                # We need the project path from the history table to perform the reset
                history_record = db.get_project_history_by_id(project_id) # Assuming project_id is the history_id here
                if not history_record:
                     history_records = db.get_project_history()
                     history_record = next((p for p in history_records if p['project_id'] == project_id), None)

                if not history_record:
                    raise Exception(f"Could not find history record for project ID {project_id} to get path.")

                project_root = Path(history_record['project_root_folder'])
                repo = git.Repo(project_root)

                # Reset the repository to the last commit
                repo.git.reset('--hard', 'HEAD')
                logging.info(f"Successfully reset repository at {project_root}")

                # Re-run pre-flight checks to confirm the environment is now clean
                check_result = self._perform_preflight_checks(str(project_root))
                self.preflight_check_result = check_result
                # The UI will re-render based on this updated result

        except Exception as e:
            logging.error(f"Failed to discard changes for project {project_id}: {e}")
            self.preflight_check_result = {"status": "ERROR", "message": str(e)}

    def delete_archived_project(self, history_id: int) -> tuple[bool, str]:
        """
        Permanently deletes an archived project's history record and its
        associated archive files from the filesystem.

        Args:
            history_id (int): The history_id of the project to delete.

        Returns:
            A tuple containing a success/failure boolean and a status message.
        """
        logging.info(f"Attempting to delete archived project with history_id: {history_id}.")
        try:
            with self.db_manager as db:
                # 1. Fetch the record to get the archive file path
                history_record = db.get_project_history_by_id(history_id)
                if not history_record:
                    error_msg = f"No project history found for ID {history_id}."
                    logging.error(error_msg)
                    return False, error_msg

                archive_path_str = history_record['archive_file_path']

                # 2. Delete the associated archive files
                rowd_file = Path(archive_path_str)
                cr_file = rowd_file.with_name(rowd_file.name.replace("_rowd.json", "_cr.json"))

                if rowd_file.exists():
                    rowd_file.unlink()
                    logging.info(f"Deleted archive file: {rowd_file}")
                else:
                    logging.warning(f"Could not find archive file to delete at: {rowd_file}")

                if cr_file.exists():
                    cr_file.unlink()
                    logging.info(f"Deleted CR archive file: {cr_file}")

                # 3. Delete the record from the database
                db.delete_project_from_history(history_id)

                success_msg = f"Successfully deleted archived project (History ID: {history_id})."
                logging.info(success_msg)
                return True, success_msg

        except Exception as e:
            error_msg = f"An unexpected error occurred while deleting project history {history_id}: {e}"
            logging.error(error_msg)
            return False, error_msg

    def load_archived_project(self, history_id: int):
        """
        Loads an archived project's data, performs pre-flight checks,
        and sets the appropriate phase for UI resolution.
        """
        try:
            with self.db_manager as db:
                if self.project_id:
                    default_archive_path = Path("data/safety_archives")
                    archive_name = f"{self.project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    self.stop_and_export_project(default_archive_path, archive_name)

                history_record = db.get_project_history_by_id(history_id)
                if not history_record:
                    error_msg = f"Error: No project history found for ID {history_id}"
                    self.preflight_check_result = {"status": "ERROR", "message": error_msg}
                    self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")
                    return

                rowd_file_path = Path(history_record['archive_file_path'])
                cr_file_path = rowd_file_path.with_name(rowd_file_path.name.replace("_rowd.json", "_cr.json"))

                if not rowd_file_path.exists():
                    error_msg = f"Archive file not found at path: {rowd_file_path}"
                    self.preflight_check_result = {"status": "ERROR", "message": error_msg}
                    self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")
                    return

                # Perform the checks BEFORE loading data
                project_root_str = history_record['project_root_folder']
                check_result = self._perform_preflight_checks(project_root_str)
                self.preflight_check_result = check_result

                # If checks fail fatally, we don't bother loading the data yet.
                # The user must resolve the issue first.
                if check_result['status'] in ["PATH_NOT_FOUND", "GIT_MISSING", "STATE_DRIFT"]:
                    self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")
                    logging.info(f"Pre-flight checks failed ({check_result['status']}). Pausing for user resolution.")
                    return

                # --- If checks pass, proceed to load data ---
                self._clear_active_project_data(db)

                with open(rowd_file_path, 'r', encoding='utf-8') as f:
                    artifacts_to_load = json.load(f)
                if artifacts_to_load:
                    db.bulk_insert_artifacts(artifacts_to_load)

                if cr_file_path.exists():
                    with open(cr_file_path, 'r', encoding='utf-8') as f:
                        crs_to_load = json.load(f)
                    if crs_to_load:
                        db.bulk_insert_change_requests(crs_to_load)

                self.project_id = history_record['project_id']
                self.project_name = history_record['project_name']

                # Set the phase for UI resolution
                self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")
                logging.info(f"Successfully loaded archived project '{self.project_name}'. Awaiting pre-flight resolution.")

        except Exception as e:
            error_msg = f"A critical error occurred while loading the project: {e}"
            logging.error(error_msg)
            self.preflight_check_result = {"status": "ERROR", "message": error_msg}
            self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")


    def get_project_history(self):
        """Retrieves all records from the ProjectHistory table."""
        try:
            with self.db_manager as db:
                return db.get_project_history()
        except Exception as e:
            logging.error(f"Failed to retrieve project history: {e}")
            return []

    def _plan_and_execute_fix(self, failure_log: str, context_package: dict, api_key: str):
        """
        A helper method that invokes the FixPlannerAgent with gathered context
        and prepares the resulting plan for execution by the Genesis pipeline.

        Args:
            failure_log (str): The error log or failure description.
            context_package (dict): A dictionary containing the source code of relevant files.
            api_key (str): The LLM API key.
        """
        logging.info("Invoking FixPlannerAgent with rich context to generate a fix plan...")

        # For now, we will pass the first available source code as the context.
        # This will be enhanced when we implement the full trace analysis.
        relevant_code = next(iter(context_package.values()), "No code context available.")

        planner_agent = FixPlannerAgent_AppTarget(api_key=api_key)
        fix_plan_str = planner_agent.create_fix_plan(
            root_cause_hypothesis=failure_log,
            relevant_code=relevant_code
        )

        # Check for errors from the agent call
        if "error" in fix_plan_str:
            raise Exception(f"FixPlannerAgent failed to generate a plan: {fix_plan_str}")

        fix_plan = json.loads(fix_plan_str)
        if not fix_plan:
             raise Exception("FixPlannerAgent returned an empty plan.")

        self.active_plan = fix_plan
        self.active_plan_cursor = 0
        self.set_phase("GENESIS")
        logging.info("Successfully generated a fix plan. Transitioning to GENESIS phase to apply the fix.")

    def _build_and_validate_context_package(self, db: ASDFDBManager, core_documents: dict, source_code_files: dict) -> dict:
        """
        Gathers context, checks size, trims if necessary by prioritizing core
        documents and smaller source files, and reports on any excluded files.

        Args:
            db (ASDFDBManager): The active database manager instance.
            core_documents (dict): A dict of essential documents (e.g., specs).
            source_code_files (dict): A dict of file_path: content for source code.

        Returns:
            A dictionary containing the final context, status flags, and a list of any excluded files.
        """
        final_context = {}
        excluded_files = []
        context_was_trimmed = False

        limit_str = db.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "15000"
        char_limit = int(limit_str)

        # 1. Add core documents and calculate their size.
        core_doc_chars = 0
        for name, content in core_documents.items():
            final_context[name] = content
            core_doc_chars += len(content)

        # 2. Check if essential docs alone are too large.
        if core_doc_chars > char_limit:
            logging.error(f"Context Builder: Core documents ({core_doc_chars} chars) alone exceed the context limit of {char_limit}. Cannot proceed.")
            return {"source_code": {}, "was_trimmed": True, "error": "Core documents are too large for the context window.", "excluded_files": list(source_code_files.keys())}

        # 3. Calculate remaining budget and add source files until it's full.
        remaining_chars = char_limit - core_doc_chars
        sorted_source_files = sorted(source_code_files.items(), key=lambda item: len(item[1]))

        for file_path, content in sorted_source_files:
            if len(content) <= remaining_chars:
                final_context[file_path] = content
                remaining_chars -= len(content)
            else:
                # Flag that we couldn't include all files and track which one was excluded.
                context_was_trimmed = True
                excluded_files.append(file_path)

        if context_was_trimmed:
            logging.warning(f"Context Builder: Context trimmed. Excluded {len(excluded_files)} file(s): {', '.join(excluded_files)}")

        return {
            "source_code": final_context,
            "was_trimmed": context_was_trimmed,
            "error": None,
            "excluded_files": excluded_files
        }

    def _plan_fix_from_description(self, description: str):
        """
        Takes a natural language description of a bug, forms a hypothesis,
        and generates a fix plan. This is the core of functional bug handling.

        Args:
            description (str): The text description of the bug.
        """
        logging.info(f"Attempting to plan fix from description: '{description[:100]}...'")
        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    raise Exception("Cannot proceed with triage. LLM API Key is not set.")

            # Step 1: Use TriageAgent to refine the description into a testable hypothesis.
            triage_agent = TriageAgent_AppTarget(api_key=api_key, db_manager=self.db_manager)
            hypothesis = triage_agent.analyze_and_hypothesize(
                error_logs=description,
                relevant_code="No specific code context available; base analysis on user description.",
                test_report=""
            )
            if "An error occurred" in hypothesis:
                raise Exception(f"TriageAgent failed to form a hypothesis: {hypothesis}")
            logging.info(f"TriageAgent formed hypothesis: {hypothesis}")

            # Step 2: Use FixPlannerAgent to create a plan from the hypothesis.
            planner_agent = FixPlannerAgent_AppTarget(api_key=api_key)
            fix_plan_str = planner_agent.create_fix_plan(
                root_cause_hypothesis=hypothesis,
                relevant_code="No specific code context was automatically identified. Base the fix on the TriageAgent's hypothesis."
            )
            if "error" in fix_plan_str.lower():
                raise Exception(f"FixPlannerAgent failed to generate a plan: {fix_plan_str}")
            fix_plan = json.loads(fix_plan_str)
            if not fix_plan:
                raise Exception("FixPlannerAgent returned an empty plan.")

            # Step 3: Load the new fix plan and transition to Genesis to execute it.
            self.active_plan = fix_plan
            self.active_plan_cursor = 0
            self.set_phase("GENESIS")
            logging.info("Successfully generated a fix plan from description. Transitioning to GENESIS.")

        except Exception as e:
            logging.error(f"Failed to plan fix from description. Error: {e}")
            self.set_phase("DEBUG_PM_ESCALATION")

    def handle_pm_triage_input(self, pm_error_description: str):
        """
        Handles the text input provided by the PM during interactive triage (Tier 3)
        by calling the reusable fix-planning helper method.

        Args:
            pm_error_description (str): The PM's description of the error.
        """
        logging.info("Tier 3: Received manual error description from PM. Routing to fix-planning.")
        self._plan_fix_from_description(pm_error_description)

    def _extract_tags_from_text(self, text: str) -> list[str]:
        """A simple helper to extract potential search tags from text."""
        # Find capitalized words or words in quotes that might be features or nouns
        keywords = re.findall(r'\"([^"]+)\"|\b[A-Z][a-zA-Z]{3,}\b', text)
        # Flatten list if there are tuples from regex, lowercase, and get unique tags
        flat_list = []
        for item in keywords:
            if isinstance(item, tuple):
                flat_list.extend(filter(None, item))
            else:
                flat_list.append(item)
        tags = set(kw.lower() for kw in flat_list if len(kw) > 3)
        return list(tags)[:5] # Limit to 5 tags to keep it focused

    def capture_spec_clarification_learning(self, problem_context: str, solution_text: str, spec_text: str):
        """
        Captures a learning moment from a successful specification clarification.

        Args:
            problem_context (str): The issues/questions the AI raised.
            solution_text (str): The clarification provided by the PM.
            spec_text (str): The full specification text for context and tags.
        """
        try:
            agent = LearningCaptureAgent(self.db_manager)
            tags = self._extract_tags_from_text(spec_text)

            agent.add_learning_entry(
                context=f"During specification elaboration for project: {self.project_name}",
                problem=problem_context,
                solution=solution_text,
                tags=tags
            )
            logging.info("Successfully captured specification clarification as a learning entry.")
        except Exception as e:
            # We don't want to halt the main flow if learning capture fails.
            logging.warning(f"Could not capture learning entry for spec clarification: {e}")

    def start_test_environment_setup(self):
        """
        Calls the advisor agent to get a list of test environment setup tasks.

        Returns:
            A list of setup task dictionaries, or None on failure.
        """
        logging.info("Initiating test environment setup guidance.")
        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                project_details = db.get_project_by_id(self.project_id)
                tech_spec_text = project_details['tech_spec_text']

                if not api_key or not tech_spec_text:
                    raise Exception("Cannot get setup tasks: Missing API Key or Technical Specification.")

            # TODO: In a future iteration, capture the target OS during tech spec phase
            # and pass it here for more accurate guidance.
            target_os = "Linux" # Using a generic default for now.

            agent = TestEnvironmentAdvisorAgent(api_key=api_key)
            tasks = agent.get_setup_tasks(tech_spec_text, target_os)
            return tasks

        except Exception as e:
            logging.error(f"Failed to start test environment setup: {e}")
            return None

    def get_help_for_setup_task(self, task_instructions: str):
        """
        Calls the advisor agent to get detailed help for a specific setup task.

        Returns:
            A string containing helpful information.
        """
        logging.info("Getting help for a test environment setup task.")
        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                if not api_key:
                    raise Exception("Cannot get help: Missing API Key.")

            # TODO: Pass the correct target_os.
            target_os = "Linux" # Using a generic default for now.

            agent = TestEnvironmentAdvisorAgent(api_key=api_key)
            help_text = agent.get_help_for_task(task_instructions, target_os)
            return help_text

        except Exception as e:
            logging.error(f"Failed to get help for setup task: {e}")
            return "An error occurred while fetching help. Please check the logs."

    def finalize_test_environment_setup(self, test_command: str):
        """
        Saves the confirmed test command and transitions to the next phase.

        Returns:
            True on success, False on failure.
        """
        logging.info(f"Finalizing test environment setup. Confirmed command: '{test_command}'")
        try:
            with self.db_manager as db:
                db.update_project_test_command(self.project_id, test_command)

            self.set_phase("CODING_STANDARD_GENERATION")
            logging.info("Test environment setup complete. Transitioning to Coding Standard Generation.")
            return True
        except Exception as e:
            logging.error(f"Failed to finalize test environment setup: {e}")
            return False