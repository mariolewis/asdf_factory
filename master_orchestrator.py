
import logging
import uuid
import json
import re
from datetime import datetime, timezone
from enum import Enum, auto
from llm_service import LLMService
from pathlib import Path
import textwrap
import git

from agents.agent_project_bootstrap import ProjectBootstrapAgent
from agents.agent_integration_pmt import IntegrationAgentPMT
from agents.agent_spec_clarification import SpecClarificationAgent
from agents.agent_ux_triage import UX_Triage_Agent
from agents.agent_ux_spec import UX_Spec_Agent
from agents.agent_report_generator import ReportGeneratorAgent
from agents.agent_ux_spec import UX_Spec_Agent
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
from agents.agent_ui_test_planner_app_target import UITestPlannerAgent_AppTarget
from agents.agent_test_result_evaluation_app_target import TestResultEvaluationAgent_AppTarget
from agents.agent_fix_planner_app_target import FixPlannerAgent_AppTarget
from agents.agent_learning_capture import LearningCaptureAgent
from agents.agent_impact_analysis_app_target import ImpactAnalysisAgent_AppTarget
from agents.agent_test_environment_advisor import TestEnvironmentAdvisorAgent
from agents.agent_verification_app_target import VerificationAgent_AppTarget
from agents.agent_rollback_app_target import RollbackAgent
from agents.agent_project_scoping import ProjectScopingAgent
from agents.build_and_commit_agent_app_target import BuildAndCommitAgentAppTarget
from agents.agent_plan_auditor import PlanAuditorAgent
from agents.agent_code_summarization import CodeSummarizationAgent

class EnvironmentFailureException(Exception):
    """Custom exception for unrecoverable environment errors."""
    pass

class FactoryPhase(Enum):
    """Enumeration for the main factory F-Phases."""
    IDLE = auto()
    BACKLOG_VIEW = auto()
    SPRINT_PLANNING = auto()
    SPRINT_IN_PROGRESS = auto()
    SPRINT_REVIEW = auto()
    BACKLOG_RATIFICATION = auto()
    VIEWING_ACTIVE_PROJECTS = auto()
    UX_UI_DESIGN = auto()
    AWAITING_UX_UI_PHASE_DECISION = auto()
    AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION = auto()
    ENV_SETUP_TARGET_APP = auto()
    SPEC_ELABORATION = auto()
    TECHNICAL_SPECIFICATION = auto()
    BUILD_SCRIPT_SETUP = auto()
    TEST_ENVIRONMENT_SETUP = auto()
    CODING_STANDARD_GENERATION = auto()
    PLANNING = auto()
    GENESIS = auto()
    AWAITING_INTEGRATION_CONFIRMATION = auto()
    INTEGRATION_AND_VERIFICATION = auto()
    AWAITING_INTEGRATION_RESOLUTION = auto()
    MANUAL_UI_TESTING = auto()
    AWAITING_PM_DECLARATIVE_CHECKPOINT = auto()
    AWAITING_PREFLIGHT_RESOLUTION = auto()
    AWAITING_IMPACT_ANALYSIS_CHOICE = auto()
    IMPLEMENTING_CHANGE_REQUEST = auto()
    AWAITING_LINKED_DELETE_CONFIRMATION = auto()
    DEBUG_PM_ESCALATION = auto()
    VIEWING_DOCUMENTS = auto()
    VIEWING_REPORTS = auto()
    VIEWING_PROJECT_HISTORY = auto()
    AWAITING_CONTEXT_REESTABLISHMENT = auto()
    AWAITING_PM_TRIAGE_INPUT = auto()
    AWAITING_REASSESSMENT_CONFIRMATION = auto()
    PROJECT_COMPLETED = auto()


class MasterOrchestrator:
    """
    The central state machine and workflow manager for the ASDF.
    It coordinates agents, manages project state, and handles project lifecycle.
    """

    def __init__(self, db_manager: ASDFDBManager):
        self.db_manager = db_manager
        self.resumable_state = self.db_manager.get_any_paused_state()

        # Default initial state
        self.project_id: str | None = None
        self.project_name: str | None = None
        self.current_phase: FactoryPhase = FactoryPhase.IDLE

        if self.resumable_state:
            project_id_from_state = self.resumable_state['project_id']
            project_details = self.db_manager.get_project_by_id(project_id_from_state)

            # Only resume if the corresponding project record also exists
            if project_details:
                self.project_id = project_id_from_state
                self.project_name = project_details['project_name']
                self.current_phase = FactoryPhase[self.resumable_state['current_phase']]
                logging.info(f"Orchestrator initialized into a resumable state for project: {self.project_name}")
            else:
                # If project record is gone, the state is orphaned and should be deleted.
                logging.warning(f"Found orphaned resumable state for non-existent project ID {project_id_from_state}. Deleting it.")
                self.db_manager.delete_orchestration_state_for_project(project_id_from_state)
                self.resumable_state = None # Clear the invalid state

        self.active_plan = None
        self.active_plan_cursor = 0
        self.task_awaiting_approval = None
        self.preflight_check_result = None
        self.debug_attempt_counter = 0
        self.active_ux_spec = {}
        self.is_project_dirty = False
        self.is_executing_cr_plan = False
        self.is_in_fix_mode = False
        self.fix_plan = None
        self.fix_plan_cursor = 0
        self.sprint_completed_with_failures = False
        self._llm_service = None
        self.current_task_confidence = 0
        self.active_spec_draft = None
        self.active_sprint_id = None
        logging.info("MasterOrchestrator instance created.")

    def reset(self):
        """
        Resets the orchestrator's state to its default, idle condition.
        """
        logging.info("Resetting MasterOrchestrator to idle state.")
        self.project_id = None
        self.project_root_path = None
        self.project_name = None
        self.current_phase = FactoryPhase.IDLE
        self.active_plan = None
        self.active_plan_cursor = 0
        self.task_awaiting_approval = None
        self.preflight_check_result = None
        self.debug_attempt_counter = 0
        self.active_ux_spec = {}
        self.is_project_dirty = False
        self.is_executing_cr_plan = False
        self.is_in_fix_mode = False
        self.fix_plan = None
        self.fix_plan_cursor = 0
        self.current_task_confidence = 0
        self.active_spec_draft = None
        self.active_sprint_id = None

    def close_active_project(self):
        """
        Closes the currently active project, cleans up in-progress statuses,
        clears all its data, and returns to an idle state.
        """
        logging.info(f"Closing active project: {self.project_name}")
        if self.project_id:
            try:
                # Find any items that were left in progress and revert them
                in_progress_items = self.db_manager.get_change_requests_by_statuses(
                    self.project_id, ["IMPLEMENTATION_IN_PROGRESS"]
                )
                if in_progress_items:
                    item_ids = [item['cr_id'] for item in in_progress_items]
                    # Revert them to TO_DO so they can be planned in a future sprint
                    self.db_manager.batch_update_cr_status(item_ids, "TO_DO")
                    logging.info(f"Reverted {len(item_ids)} in-progress items back to 'TO_DO' status.")
            except Exception as e:
                logging.error(f"Failed to clean up in-progress statuses during project close: {e}")

            self._clear_active_project_data(self.db_manager, self.project_id)

        self.reset()

    def close_and_save_project(self):
        """
        Public method to handle the UI's 'Close Project' action, which
        is now a non-destructive pause/save operation.
        """
        logging.info("PM initiated Close Project. This will be a non-destructive save.")
        self.pause_project()

    @property
    def llm_service(self) -> LLMService:
        """
        Provides on-demand creation of the LLM service.
        """
        if self._llm_service is None:
            logging.info("First use of LLM service detected, initializing now...")
            self._llm_service = self._create_llm_service()
            if not self._llm_service:
                raise RuntimeError("Failed to initialize LLM service. Please check your settings.")
        return self._llm_service

    PHASE_DISPLAY_NAMES = {
        FactoryPhase.IDLE: "Idle",
        FactoryPhase.BACKLOG_VIEW: "Backlog Overview",
        FactoryPhase.SPRINT_PLANNING: "Sprint Planning",
        FactoryPhase.SPRINT_IN_PROGRESS: "Sprint in Progress",
        FactoryPhase.SPRINT_REVIEW: "Sprint Review",
        FactoryPhase.BACKLOG_RATIFICATION: "Backlog Ratification",
        FactoryPhase.VIEWING_ACTIVE_PROJECTS: "Open Project",
        FactoryPhase.UX_UI_DESIGN: "User Experience & Interface Design",
        FactoryPhase.AWAITING_UX_UI_PHASE_DECISION: "Awaiting UX/UI Phase Decision",
        FactoryPhase.AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION: "UX/UI Phase Recommendation",
        FactoryPhase.ENV_SETUP_TARGET_APP: "New Application Setup",
        FactoryPhase.SPEC_ELABORATION: "Application Specification",
        FactoryPhase.TECHNICAL_SPECIFICATION: "Technical Specification",
        FactoryPhase.BUILD_SCRIPT_SETUP: "Build Script Generation",
        FactoryPhase.TEST_ENVIRONMENT_SETUP: "Test Environment Setup",
        FactoryPhase.CODING_STANDARD_GENERATION: "Coding Standard Generation",
        FactoryPhase.PLANNING: "Development Planning",
        FactoryPhase.GENESIS: "Iterative Development",
        FactoryPhase.AWAITING_INTEGRATION_CONFIRMATION: "Awaiting Integration Confirmation",
        FactoryPhase.INTEGRATION_AND_VERIFICATION: "Integration & Verification",
        FactoryPhase.AWAITING_INTEGRATION_RESOLUTION: "Awaiting Integration Resolution",
        FactoryPhase.MANUAL_UI_TESTING: "Testing & Validation",
        FactoryPhase.AWAITING_PM_DECLARATIVE_CHECKPOINT: "Checkpoint: High-Risk Change Approval",
        FactoryPhase.AWAITING_PREFLIGHT_RESOLUTION: "Pre-flight Check",
        FactoryPhase.AWAITING_IMPACT_ANALYSIS_CHOICE: "New CR - Impact Analysis Choice",
        FactoryPhase.IMPLEMENTING_CHANGE_REQUEST: "Implement Change Request",
        FactoryPhase.AWAITING_LINKED_DELETE_CONFIRMATION: "Confirm Linked Deletion",
        FactoryPhase.DEBUG_PM_ESCALATION: "Debug Escalation to PM",
        FactoryPhase.VIEWING_DOCUMENTS: "Viewing Project Documents",
        FactoryPhase.VIEWING_REPORTS: "Viewing Project Reports",
        FactoryPhase.VIEWING_PROJECT_HISTORY: "Select and Load Archived Project",
        FactoryPhase.AWAITING_CONTEXT_REESTABLISHMENT: "Re-establishing Project Context",
        FactoryPhase.AWAITING_PM_TRIAGE_INPUT: "Interactive Triage - Awaiting Input",
        FactoryPhase.AWAITING_REASSESSMENT_CONFIRMATION: "LLM Re-assessment Confirmation",
        FactoryPhase.PROJECT_COMPLETED: "Project Completed"
    }

    def get_status(self) -> dict:
        """Returns the current status of the orchestrator."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "current_phase": self.current_phase.name
        }

    @property
    def is_genesis_complete(self) -> bool:
        """
        A helper property that returns True if the main development plan is finished.
        """
        if self.current_phase == FactoryPhase.GENESIS and (not self.active_plan or self.active_plan_cursor >= len(self.active_plan)):
            return True

        # List of ALL phases that can occur after the initial development plan is complete.
        post_genesis_phases = [
            FactoryPhase.AWAITING_INTEGRATION_CONFIRMATION,
            FactoryPhase.INTEGRATION_AND_VERIFICATION,
            FactoryPhase.AWAITING_INTEGRATION_RESOLUTION,
            FactoryPhase.MANUAL_UI_TESTING,
            FactoryPhase.DEBUG_PM_ESCALATION,
            FactoryPhase.AWAITING_PM_TRIAGE_INPUT,
            FactoryPhase.IMPLEMENTING_CHANGE_REQUEST,
            FactoryPhase.IDLE
        ]
        if self.current_phase in post_genesis_phases:
            return True

        return False

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
        Safely retrieves the current task, calculates its confidence score,
        and provides all details for the UI.
        """
        plan = self.fix_plan if self.is_in_fix_mode else self.active_plan
        cursor = self.fix_plan_cursor if self.is_in_fix_mode else self.active_plan_cursor

        if not plan or cursor >= len(plan):
            if not self.is_in_fix_mode and self.active_plan:
                return {
                    "task": {"component_name": "All development tasks complete."},
                    "cursor": cursor, "total": len(self.active_plan),
                    "is_fix_mode": False, "confidence_score": 0
                }
            return None

        # --- AI Confidence Calculation Logic ---
        # This version is more robust and calculates the score for the current task.
        confidence_score = 0
        current_task = plan[cursor]
        artifact_id = current_task.get("artifact_id")

        if artifact_id:
            # This is an existing component. Confidence depends on context quality.
            db = self.db_manager
            artifact_record = db.get_artifact_by_id(artifact_id)

            # Check if we have a context package and a valid record for this artifact
            if artifact_record and hasattr(self, 'context_package_summary'):
                task_file_path = artifact_record['file_path']

                if task_file_path in self.context_package_summary.get('files_in_context', []):
                    if task_file_path in self.context_package_summary.get('summarized_files', []):
                        confidence_score = 50 # Medium: Relevant file was summarized
                    else:
                        confidence_score = 90 # High: Relevant file was included in full
                else:
                    confidence_score = 10 # Low: Relevant file was not in context at all
            else:
                confidence_score = 20 # Low: We know it's an existing file but have no context for it
        else:
            # This is a new component. Confidence is always high.
            confidence_score = 100

        self.current_task_confidence = confidence_score
        # --- End of Calculation ---

        return {
            "task": current_task,
            "cursor": cursor,
            "total": len(plan),
            "is_fix_mode": self.is_in_fix_mode,
            "confidence_score": self.current_task_confidence
        }

    def get_sprint_goal(self) -> str:
        if not self.is_executing_cr_plan or not self.project_id:
            return "N/A"
        try:
            sprint_id = self.get_active_sprint_id()
            if not sprint_id: return "Initializing sprint..."

            sprint_items = self.db_manager.get_items_for_sprint(sprint_id)

            if not sprint_items: return "Finalizing sprint..."

            return ", ".join([f"'{item['title']}'" for item in sprint_items])
        except Exception as e:
            logging.error(f"Failed to retrieve sprint goal: {e}")
            return "Error retrieving goal..."

    def get_current_mode(self) -> str:
        """
        Returns the current operational mode of the Genesis pipeline.
        """
        return "FIXING" if self.is_in_fix_mode else "DEVELOPING"

    def get_active_sprint_id(self) -> str | None:
        """
        Gets the active sprint ID, ensuring it's still valid in the database.
        """
        if not self.active_sprint_id:
            return None
        # This check could be enhanced to validate the sprint is still 'IN_PROGRESS'
        # but for now, we trust the orchestrator's state.
        return self.active_sprint_id

    def set_active_spec_draft(self, draft_text: str):
        """Allows UI pages to update the orchestrator with their current in-progress draft."""
        self.active_spec_draft = draft_text

    def manually_update_bug_status(self, cr_id: int, new_status: str):
        """
        Handles the UI request to manually change the status of a bug report.
        """
        if not self.project_id:
            logging.error("Cannot update status; no active project.")
            return

        cr_details = self.db_manager.get_cr_by_id(cr_id)
        if cr_details and cr_details['request_type'] == 'BUG_REPORT':
            self.db_manager.update_cr_status(cr_id, new_status)
            self.is_project_dirty = True
        else:
            logging.warning(f"Attempted to manually change status for a non-bug item (CR-{cr_id}). Action denied.")

    def get_sprint_summary_data(self) -> dict:
        """
        Gathers and structures the data for the sprint review summary using the active sprint ID.
        """
        summary_data = {"completed_items": [], "sprint_goal": "N/A"}
        if not self.project_id:
            return summary_data
        try:
            sprint_id = self.active_sprint_id # Use the instance variable
            if not sprint_id:
                return {"error": "Could not identify active sprint."}

            # This is the ONLY data source we should use.
            sprint_items = self.db_manager.get_items_for_sprint(sprint_id)

            # The complex logic for hierarchical IDs is correct, but it must operate on sprint_items.
            full_backlog_with_ids = self._get_backlog_with_hierarchical_numbers()
            flat_backlog_map = {}
            def flatten_hierarchy(items):
                for item in items:
                    flat_backlog_map[item['cr_id']] = item
                    if "features" in item: flatten_hierarchy(item["features"])
                    if "user_stories" in item: flatten_hierarchy(item["user_stories"])
            flatten_hierarchy(full_backlog_with_ids)

            for item in sprint_items: # CORRECTED: Iterate over the correct list
                enriched_item = flat_backlog_map.get(item['cr_id'], dict(item))
                summary_data["completed_items"].append({
                    "hierarchical_id": enriched_item.get('hierarchical_id', f"CR-{item['cr_id']}"),
                    "title": item['title'],
                    "status": "Completed"
                })

            summary_data["sprint_goal"] = ", ".join([f"'{item['title']}'" for item in sprint_items]) # CORRECTED
            return summary_data
        except Exception as e:
            logging.error(f"Failed to get sprint summary data: {e}")
            return {"error": str(e)}

    def get_uncompleted_tasks_for_manual_fix(self) -> list | None:
        """
        Retrieves a list of all tasks from the current development plan that
        do not yet have a corresponding completed artifact in the RoWD.

        Returns:
            A list of task dictionaries, or None if an error occurs.
        """
        if not self.project_id or not self.active_plan:
            logging.error("Cannot get uncompleted tasks: No active project or plan.")
            return None
        try:
            db = self.db_manager
            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            completed_spec_ids = {art['micro_spec_id'] for art in all_artifacts if art['micro_spec_id']}

            uncompleted_tasks = [
                task for task in self.active_plan
                if task.get('micro_spec_id') not in completed_spec_ids
            ]
            return uncompleted_tasks
        except Exception as e:
            logging.error(f"Failed to retrieve uncompleted tasks: {e}", exc_info=True)
            return None

    def _recalculate_plan_cursor_from_db(self):
        """
        Scans the database for completed artifacts and sets the active plan
        cursor to the correct resume point.
        """
        if not self.project_id or not self.active_plan:
            self.active_plan_cursor = 0
            return

        all_artifacts = self.db_manager.get_all_artifacts_for_project(self.project_id)
        completed_spec_ids = {art['micro_spec_id'] for art in all_artifacts if art['micro_spec_id']}

        last_completed_index = -1
        for i, task in enumerate(self.active_plan):
            if task.get('micro_spec_id') in completed_spec_ids:
                last_completed_index = i

        self.active_plan_cursor = last_completed_index + 1
        logging.info(f"Recalculated and set plan cursor to resume at step {self.active_plan_cursor + 1}.")

    def start_new_project(self, project_name: str) -> str:
        """
        Prepares a new project in the database and calculates a suggested root path,
        but does NOT create directories on the filesystem.
        Returns the suggested project root path.
        """
        if self.project_id and self.is_project_dirty:
            logging.warning(f"An active, modified project '{self.project_name}' was found. Performing a safety export.")
            archive_path_from_db = self.db_manager.get_config_value("DEFAULT_ARCHIVE_PATH")
            if not archive_path_from_db or not archive_path_from_db.strip():
                logging.error("Safety export failed: Default Project Archive Path is not set in Settings.")
            else:
                archive_path = Path(archive_path_from_db)
                archive_name = f"{self.project_name.replace(' ', '_')}_auto_export_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.stop_and_export_project(archive_path, archive_name)

        # Calculate the suggested path
        base_path_str = self.db_manager.get_config_value("DEFAULT_PROJECT_PATH")
        if not base_path_str or not base_path_str.strip():
            base_path = Path().resolve() / "projects"
        else:
            base_path = Path(base_path_str)

        sanitized_name = project_name.lower().replace(' ', '_')
        suggested_root = base_path / sanitized_name

        # Create the project in the database
        self.project_id = f"proj_{uuid.uuid4().hex[:8]}"
        self.project_name = project_name
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            # Create the project record in the DB, but DO NOT save the root folder yet.
            self.db_manager.create_project(self.project_id, self.project_name, timestamp)

            # Store the SUGGESTED path in memory for the UI to use.
            self.project_root_path = str(suggested_root)

            logging.info(f"Initialized new project '{self.project_name}' in database. Awaiting path confirmation from UI.")
            self.is_project_dirty = True
            self.set_phase("ENV_SETUP_TARGET_APP")
            return str(suggested_root)

        except Exception as e:
            logging.error(f"Failed to start new project '{self.project_name}': {e}")
            self.reset()
            raise

    def save_uploaded_brief_files(self, uploaded_files: list) -> list[str]:
        """Copies uploaded brief files to the project's docs/uploads directory and commits them."""
        if not self.project_id: return []
        project_details = self.db_manager.get_project_by_id(self.project_id)
        if not project_details: return []

        project_root = Path(project_details['project_root_folder'])
        uploads_dir = project_root / "docs" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for uploaded_file_path in uploaded_files:
            try:
                source_path = Path(uploaded_file_path)
                destination_path = uploads_dir / source_path.name
                import shutil
                shutil.copy(source_path, destination_path)
                saved_paths.append(str(destination_path))

                # Commit the new brief document
                commit_message = f"docs: Add initial brief document '{source_path.name}'"
                self._commit_document(destination_path, commit_message)
            except Exception as e:
                logging.error(f"Failed to copy or commit uploaded file {uploaded_file_path}: {e}")

        return saved_paths

    def save_text_brief_as_file(self, brief_content: str) -> str | None:
        """Saves a text-based project brief to a markdown file in the uploads directory and commits it."""
        if not self.project_id: return None

        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details: return None

            project_root = Path(project_details['project_root_folder'])
            # Corrected Path: Point to the uploads sub-directory
            uploads_dir = project_root / "docs" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)

            brief_file_path = uploads_dir / "project_brief.md"
            brief_file_path.write_text(brief_content, encoding="utf-8")

            # Commit the new brief document
            commit_message = "docs: Add initial text-based project brief"
            self._commit_document(brief_file_path, commit_message)

            return str(brief_file_path)
        except Exception as e:
            logging.error(f"Failed to save text brief as file: {e}")
            return None

    def handle_ux_ui_brief_submission(self, brief_input):
        """
        Handles the initial project brief submission, saves the brief as a physical
        file, stores its path, calls the triage agent, and prepares for the PM's decision.
        """
        if not self.project_id:
            logging.error("Cannot handle brief submission; no active project.")
            return

        try:
            brief_content = ""
            if isinstance(brief_input, str):
                brief_content = brief_input
            else: # Fallback for other potential input types
                brief_content = str(brief_input)

            # --- Use the corrected helper to save the file ---
            brief_file_path_str = self.save_text_brief_as_file(brief_content)
            if not brief_file_path_str:
                raise IOError("Failed to save the project brief to a file.")

            project_root = Path(self.db_manager.get_project_by_id(self.project_id)['project_root_folder'])
            relative_path = Path(brief_file_path_str).relative_to(project_root)

            # --- Save the relative path to the database ---
            self.db_manager.update_project_field(self.project_id, "project_brief_path", str(relative_path))

            # --- Proceed with AI Analysis ---
            if not self.llm_service:
                raise Exception("Cannot analyze brief: LLM Service is not configured.")

            self.active_ux_spec = {'project_brief': brief_content}
            triage_agent = UX_Triage_Agent(llm_service=self.llm_service)
            analysis_result = triage_agent.analyze_brief(brief_content)

            if "error" in analysis_result:
                self.task_awaiting_approval = {"analysis_error": analysis_result.get('details')}
            else:
                self.active_ux_spec['inferred_personas'] = analysis_result.get("inferred_personas", [])
                self.task_awaiting_approval = {"analysis": analysis_result}

            self.set_phase("AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION")

        except Exception as e:
            logging.error(f"Failed to handle UX/UI brief submission: {e}", exc_info=True)
            self.task_awaiting_approval = {"analysis_error": str(e)}
            self.set_phase("AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION")

    def handle_ux_ui_phase_decision(self, decision: str):
        """
        Handles the PM's decision to either start the UX/UI phase or skip it,
        ensuring the project brief is correctly handed off.
        """
        # Persist the is_gui flag regardless of the decision, as it's now known.
        analysis_result = self.task_awaiting_approval.get("analysis", {})
        is_gui = analysis_result.get("requires_gui", False)
        self.db_manager.update_project_field(self.project_id, "is_gui_project", 1 if is_gui else 0)

        if decision == "START_UX_UI_PHASE":
            logging.info("PM chose to start the dedicated UX/UI Design phase.")
            self.task_awaiting_approval = None # Clear the approval task
            self.set_phase("UX_UI_DESIGN")
        elif decision == "SKIP_TO_SPEC":
            logging.info("PM chose to skip the UX/UI Design phase. Proceeding to Application Specification.")
            # Retrieve the brief we stored earlier and hand it off to the next phase.
            brief_content = self.active_ux_spec.get('project_brief', '')
            self.task_awaiting_approval = {"pending_brief": brief_content}
            self.set_phase("SPEC_ELABORATION")
        else:
            logging.warning(f"Received an unknown decision for UX/UI phase: {decision}")

    def generate_initial_ux_spec_draft(self):
        """
        Calls the UX_Spec_Agent to generate the first consolidated draft of the
        UX/UI Specification, using a template if available.

        Returns:
            A string containing the generated Markdown draft, or an error message.
        """
        if not self.project_id:
            return "Error: No active project."

        try:
            # --- Template Loading Logic ---
            template_content = None
            try:
                template_record = self.db_manager.get_template_by_name("Default UX/UI Specification")
                if template_record:
                    template_path = Path(template_record['file_path'])
                    if template_path.exists():
                        template_content = template_path.read_text(encoding='utf-8')
                        logging.info("Found and loaded 'Default UX/UI Specification' template.")
            except Exception as e:
                logging.warning(f"Could not load default UX/UI spec template: {e}")
            # --- End Template Loading ---

            # Retrieve the brief and personas stored during the triage phase
            project_brief = self.active_ux_spec.get('project_brief', '')
            personas = self.active_ux_spec.get('inferred_personas', [])

            if not project_brief:
                raise ValueError("Project brief not found in the active UX spec context.")

            agent = UX_Spec_Agent(llm_service=self.llm_service)
            draft = agent.generate_enriched_ux_draft(project_brief, personas, template_content=template_content)

            # Add the standard document header to the draft
            full_draft_with_header = self.prepend_standard_header(
                document_content=draft,
                document_type="UX/UI Specification"
            )
            return full_draft_with_header

        except Exception as e:
            logging.error(f"Failed to generate initial UX spec draft: {e}", exc_info=True)
            return f"### Error\nAn unexpected error occurred while generating the draft: {e}"

    def refine_ux_spec_draft(self, current_draft: str, pm_feedback: str) -> str:
        """
        Calls the UX_Spec_Agent to refine the UX/UI spec draft based on PM feedback
        and updates the document's date, using a template if available.
        """
        if not self.project_id:
            return "Error: No active project."

        try:
            # --- Template Loading Logic ---
            template_content = None
            try:
                template_record = self.db_manager.get_template_by_name("Default UX/UI Specification")
                if template_record:
                    template_path = Path(template_record['file_path'])
                    if template_path.exists():
                        template_content = template_path.read_text(encoding='utf-8')
                        logging.info("Found and loaded 'Default UX/UI Specification' template for refinement.")
            except Exception as e:
                logging.warning(f"Could not load default UX/UI spec template for refinement: {e}")
            # --- End Template Loading ---

            agent = UX_Spec_Agent(llm_service=self.llm_service)
            refined_content = agent.refine_ux_spec(current_draft, pm_feedback, template_content=template_content)

            # Reliably update the date in the header
            current_date = datetime.now().strftime('%x')
            date_updated_draft = re.sub(
                r"(Date: ).*",
                r"\g<1>" + current_date,
                refined_content
            )
            return date_updated_draft

        except Exception as e:
            logging.error(f"Failed to refine UX spec draft: {e}", exc_info=True)
            return f"### Error\nAn unexpected error occurred while refining the draft: {e}"

    def handle_ux_ui_phase_decision(self, decision: str):
        """
        Handles the PM's decision to either start the UX/UI phase or skip it,
        ensuring the project brief is correctly handed off.
        """
        # Persist the is_gui flag regardless of the decision, as it's now known.
        analysis_result = self.task_awaiting_approval.get("analysis", {})
        is_gui = analysis_result.get("requires_gui", False)
        self.db_manager.update_project_field(self.project_id, "is_gui_project", 1 if is_gui else 0)

        if decision == "START_UX_UI_PHASE":
            logging.info("PM chose to start the dedicated UX/UI Design phase.")
            self.task_awaiting_approval = None # Clear the approval task
            self.set_phase("UX_UI_DESIGN")
        elif decision == "SKIP_TO_SPEC":
            logging.info("PM chose to skip the UX/UI Design phase. Proceeding to Application Specification.")
            # Retrieve the brief we stored earlier and hand it off to the next phase.
            brief_content = self.active_ux_spec.get('project_brief', '')
            self.task_awaiting_approval = {"pending_brief": brief_content}
            self.set_phase("SPEC_ELABORATION")
        else:
            logging.warning(f"Received an unknown decision for UX/UI phase: {decision}")

    def handle_ux_persona_confirmation(self, persona_list: list[str]):
        """
        Saves the confirmed personas and triggers user journey generation.
        """
        if not self.project_id:
            logging.error("Cannot handle persona confirmation; no active project.")
            return

        try:
            # Save the confirmed personas to our in-progress spec
            self.active_ux_spec['confirmed_personas'] = persona_list

            if not self.llm_service:
                raise Exception("Cannot generate user journeys: LLM Service is not configured.")

            # Get the project brief we saved earlier
            project_brief = self.active_ux_spec.get('project_brief', '')
            if not project_brief:
                raise ValueError("Project brief not found in active UX spec.")

            # Call the agent to generate user journeys
            ux_spec_agent = UX_Spec_Agent(llm_service=self.llm_service)
            user_journeys = ux_spec_agent.generate_user_journeys(project_brief, persona_list)

            # Save the generated journeys for the next UI step
            self.active_ux_spec['generated_user_journeys'] = user_journeys

        except Exception as e:
            logging.error(f"Failed to handle UX persona confirmation: {e}")
            # Store the error to display it in the UI
            self.active_ux_spec['error'] = str(e)

    def handle_ux_journey_confirmation(self, journey_list: str):
        """
        Saves the confirmed user journeys and triggers screen identification.
        """
        if not self.project_id:
            logging.error("Cannot handle journey confirmation; no active project.")
            return

        try:
            # Save the confirmed journeys to our in-progress spec
            self.active_ux_spec['confirmed_user_journeys'] = journey_list

            if not self.llm_service:
                raise Exception("Cannot identify screens: LLM Service is not configured.")

            # Call the agent to identify screens from the journeys
            ux_spec_agent = UX_Spec_Agent(llm_service=self.llm_service)
            identified_screens = ux_spec_agent.identify_screens_from_journeys(journey_list)

            # Save the identified screens for the next UI step
            self.active_ux_spec['identified_screens'] = identified_screens

            # Clear any previous error messages
            if 'error' in self.active_ux_spec:
                del self.active_ux_spec['error']

        except Exception as e:
            logging.error(f"Failed to handle UX journey confirmation: {e}")
            self.active_ux_spec['error'] = str(e)

    def handle_ux_screen_confirmation(self, screen_list_str: str):
        """
        Saves the confirmed list of screens and initializes the state for the
        detailed screen-by-screen design loop.
        """
        if not self.project_id:
            logging.error("Cannot handle screen confirmation; no active project.")
            return

        try:
            # Save the confirmed screen list to our in-progress spec
            self.active_ux_spec['confirmed_screens_text'] = screen_list_str

            # Initialize the state for the iterative design loop
            self.active_ux_spec['screen_design_cursor'] = 0
            self.active_ux_spec['screen_blueprints'] = {} # To store the JSON for each screen

            logging.info("Initialized state for detailed screen design loop.")

            # Clear any previous error messages
            if 'error' in self.active_ux_spec:
                del self.active_ux_spec['error']

        except Exception as e:
            logging.error(f"Failed to handle UX screen confirmation: {e}")
            self.active_ux_spec['error'] = str(e)

    def handle_screen_design_submission(self, screen_name: str, pm_description: str):
        """
        Handles the PM's description for a single screen, generates the JSON
        blueprint, and stores it.
        """
        if not self.project_id:
            logging.error("Cannot handle screen design submission; no active project.")
            return

        try:
            if not self.llm_service:
                raise Exception("Cannot generate screen blueprint: LLM Service is not configured.")

            ux_spec_agent = UX_Spec_Agent(llm_service=self.llm_service)
            blueprint_json_str = ux_spec_agent.generate_screen_blueprint(screen_name, pm_description)

            # Store the generated blueprint string, keyed by the screen name.
            self.active_ux_spec['screen_blueprints'][screen_name] = blueprint_json_str

            logging.info(f"Successfully generated and stored blueprint for screen: {screen_name}")

            # Clear any previous error messages
            if 'error' in self.active_ux_spec:
                del self.active_ux_spec['error']

        except Exception as e:
            logging.error(f"Failed to handle screen design submission for '{screen_name}': {e}")
            self.active_ux_spec['error'] = str(e)

    def handle_ux_next_screen(self):
        """Advances the screen design cursor to the next screen."""
        if 'screen_design_cursor' in self.active_ux_spec:
            self.active_ux_spec['screen_design_cursor'] += 1
            logging.info(f"Advanced to screen design index: {self.active_ux_spec['screen_design_cursor']}")

    def handle_ux_previous_screen(self):
        """Moves the screen design cursor to the previous screen."""
        if 'screen_design_cursor' in self.active_ux_spec and self.active_ux_spec['screen_design_cursor'] > 0:
            self.active_ux_spec['screen_design_cursor'] -= 1
            logging.info(f"Moved back to screen design index: {self.active_ux_spec['screen_design_cursor']}")

    def handle_style_guide_submission(self, pm_description: str):
        """
        Handles the PM's description for the style guide and generates it.
        """
        if not self.project_id:
            logging.error("Cannot handle style guide submission; no active project.")
            return

        try:
            if not self.llm_service:
                raise Exception("Cannot generate style guide: LLM Service is not configured.")

            ux_spec_agent = UX_Spec_Agent(llm_service=self.llm_service)
            style_guide_md = ux_spec_agent.generate_style_guide(pm_description)

            # Store the generated markdown
            self.active_ux_spec['style_guide'] = style_guide_md

            logging.info("Successfully generated and stored the Theming && Style Guide.")

            # Clear any previous error messages
            if 'error' in self.active_ux_spec:
                del self.active_ux_spec['error']

        except Exception as e:
            logging.error(f"Failed to handle style guide submission: {e}")
            self.active_ux_spec['error'] = str(e)

    def handle_ux_spec_completion(self, final_spec_markdown: str) -> bool:
        """
        Finalizes the UX/UI Specification, saves it, generates the JSON blueprint,
        and then triggers the Application Specification draft generation and assessment.
        """
        if not self.project_id:
            logging.error("Cannot complete UX Spec: No active project.")
            return False

        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not (project_details and project_details['project_root_folder']):
                 raise FileNotFoundError("Project root folder not found for saving UX spec.")

            # --- Finalize and Save the UX Spec Artifact ---
            project_root = Path(project_details['project_root_folder'])
            docs_dir = project_root / "docs"

            ux_spec_file_path_md = docs_dir / "ux_ui_specification.md"
            ux_spec_file_path_md.write_text(final_spec_markdown, encoding="utf-8")
            self._commit_document(ux_spec_file_path_md, "docs: Finalize UX/UI Specification (Markdown)")

            agent = UX_Spec_Agent(llm_service=self.llm_service)
            json_blueprint = agent.parse_final_spec_and_generate_blueprint(final_spec_markdown)
            if '"error":' in json_blueprint:
                raise Exception(f"Failed to generate JSON blueprint from final spec: {json_blueprint}")

            blueprint_file_path_json = docs_dir / "ux_ui_blueprint.json"
            blueprint_file_path_json.write_text(json_blueprint, encoding="utf-8")
            self._commit_document(blueprint_file_path_json, "docs: Add UX/UI JSON Blueprint")

            composite_spec_for_db = (
                f"{final_spec_markdown}\n\n"
                f"{'='*80}\n"
                f"MACHINE-READABLE JSON BLUEPRINT\n"
                f"{'='*80}\n\n"
                f"```json\n{json_blueprint}\n```"
            )
            db.update_project_field(self.project_id, "ux_spec_text", composite_spec_for_db)
            self.active_ux_spec = {} # Clear the temporary UX spec data

            # --- FIX: Trigger the next phase correctly ---
            # Instead of setting the phase directly, we now correctly prepare the
            # orchestrator to generate the next draft, which will automatically
            # trigger the complexity review page in the next step.
            self.task_awaiting_approval = {"pending_brief": final_spec_markdown}
            self.set_phase("SPEC_ELABORATION")
            # --- END FIX ---
            return True

        except Exception as e:
            logging.error(f"Failed to complete UX/UI Specification: {e}", exc_info=True)
            self.task_awaiting_approval = {"error": str(e)}
            return False

    def generate_application_spec_draft(self, initial_spec_text: str) -> tuple[dict, str]:
        """
        Takes an initial specification (like a completed UX spec), generates the
        full Application Spec draft, and performs a complexity analysis on it.
        """
        if not self.project_id:
            raise Exception("Cannot generate application spec; no active project.")

        # The agent generates the raw content of the specification
        spec_agent = SpecClarificationAgent(self.llm_service, self.db_manager)
        app_spec_draft_content = spec_agent.expand_brief_description(initial_spec_text)

        # The scoping agent analyzes the raw content
        scoping_agent = ProjectScopingAgent(self.llm_service)
        analysis_result = scoping_agent.analyze_complexity(app_spec_draft_content)
        if "error" in analysis_result:
            raise Exception(f"Failed to analyze project complexity: {analysis_result.get('details')}")

        # Save the assessment to the database
        analysis_json_str = json.dumps(analysis_result)
        self.finalize_and_save_complexity_assessment(analysis_json_str)

        # Add the standard header to the raw draft before returning it to the UI
        full_app_spec_draft = self.prepend_standard_header(
            document_content=app_spec_draft_content,
            document_type="Application Specification"
        )

        return analysis_result, full_app_spec_draft

    def finalize_and_save_app_spec(self, spec_draft: str):
        """
        Saves the final application spec, a .md file, and a formatted .docx file,
        then transitions to the TECHNICAL_SPECIFICATION phase.
        """
        if not self.project_id:
            logging.error("Cannot save application spec; no active project.")
            return

        try:
            final_doc_with_header = self.prepend_standard_header(
                document_content=spec_draft,
                document_type="Application Specification"
            )
            self.db_manager.update_project_field(self.project_id, "final_spec_text", final_doc_with_header)

            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "docs"

                # Save the Markdown file for system use
                spec_file_path_md = docs_dir / "application_spec.md"
                spec_file_path_md.write_text(final_doc_with_header, encoding="utf-8")
                self._commit_document(spec_file_path_md, "docs: Finalize Application Specification (Markdown)")

                # Generate and save the formatted .docx file for human use
                spec_file_path_docx = docs_dir / "application_spec.docx"
                from agents.agent_report_generator import ReportGeneratorAgent
                report_generator = ReportGeneratorAgent()
                docx_bytes = report_generator.generate_text_document_docx(
                    title=f"Application Specification - {self.project_name}",
                    content=spec_draft
                )
                with open(spec_file_path_docx, 'wb') as f:
                    f.write(docx_bytes.getbuffer())
                self._commit_document(spec_file_path_docx, "docs: Add formatted Application Specification (docx)")

            # --- THIS IS THE CHANGE ---
            # The workflow now proceeds to the technical specification phase.
            self.set_phase("TECHNICAL_SPECIFICATION")
            # --- END OF CHANGE ---

        except Exception as e:
            logging.error(f"Failed to finalize and save application spec: {e}")
            self.task_awaiting_approval = {"error": str(e)}

    def handle_backlog_ratification(self, final_backlog_hierarchy: list):
        """
        Takes the final, nested list of backlog items from the ratification screen,
        and saves them recursively to the database to create the hierarchy.
        """
        if not self.project_id:
            logging.error("Cannot ratify backlog; no active project.")
            return

        try:
            logging.info(f"Saving {len(final_backlog_hierarchy)} ratified top-level backlog items to the database.")
            # Start the recursive save process with no parent
            for item_data in final_backlog_hierarchy:
                self._save_backlog_item_recursive(item_data, parent_id=None)

            self.task_awaiting_approval = None
            self.set_phase("BACKLOG_VIEW")
            logging.info("Backlog ratification complete. Transitioning to BACKLOG_VIEW.")

        except Exception as e:
            logging.error(f"An error occurred during backlog ratification: {e}", exc_info=True)
            self.task_awaiting_approval = {"error": str(e)}
            self.set_phase("BACKLOG_RATIFICATION")

    def _save_backlog_item_recursive(self, item_data: dict, parent_id: int | None):
        """Recursively saves a backlog item and its children to the database."""
        features = item_data.pop("features", [])
        user_stories = item_data.pop("user_stories", [])

        request_type = item_data.get('type', 'BACKLOG_ITEM')

        # FIX: Determine status based on item type
        status = "TO_DO"  # Default for Backlog Items
        if request_type in ["EPIC", "FEATURE"]:
            status = ""  # Epics and Features have a neutral, blank status

        new_item_id = self.db_manager.add_change_request(
            project_id=self.project_id,
            title=item_data.get('title', 'Untitled Item'),
            description=item_data.get('description', ''),
            request_type=request_type,
            status=status,
            priority=item_data.get('priority'),
            complexity=item_data.get('complexity'),
            parent_cr_id=parent_id
        )

        if features:
            for feature_data in features:
                self._save_backlog_item_recursive(feature_data, parent_id=new_item_id)
        if user_stories:
            for story_data in user_stories:
                self._save_backlog_item_recursive(story_data, parent_id=new_item_id)

    def get_project_integration_settings(self) -> dict:
        """
        Retrieves and parses the integration_settings JSON for the active project.
        """
        if not self.project_id:
            return {}

        project_details = self.db_manager.get_project_by_id(self.project_id)
        if not project_details or not project_details['integration_settings']:
            return {}

        settings_json = project_details['integration_settings']
        if settings_json:
            try:
                return json.loads(settings_json)
            except json.JSONDecodeError:
                logging.warning(f"Could not parse integration_settings JSON for project {self.project_id}")
                return {}
        return {}

    def save_project_integration_settings(self, settings_dict: dict):
        """
        Converts the settings dictionary to JSON and saves it to the active project.
        """
        if not self.project_id:
            logging.error("Cannot save project settings; no active project.")
            return

        try:
            settings_json = json.dumps(settings_dict)
            self.db_manager.update_project_field(
                project_id=self.project_id,
                field_name="integration_settings",
                value=settings_json
            )
            logging.info(f"Successfully saved integration settings for project {self.project_id}")
        except Exception as e:
            logging.error(f"Failed to save project integration settings: {e}")
            raise

    def handle_import_from_tool(self, import_data: dict) -> list:
        """
        Handles fetching and filtering issues from an external tool.
        This method is designed to be run in a background thread.
        """
        if not self.project_id:
            raise Exception("No active project for import.")

        # 1. Fetch integration settings from DB
        db = self.db_manager
        provider = db.get_config_value("INTEGRATION_PROVIDER")
        url = db.get_config_value("INTEGRATION_URL")
        username = db.get_config_value("INTEGRATION_USERNAME")
        token = db.get_config_value("INTEGRATION_API_TOKEN")

        if not all([provider, url, username, token]) or provider == "None":
            raise ValueError("Integration is not configured. Please check your Settings.")

        # 2. Instantiate agent and build query
        agent = IntegrationAgentPMT(provider, url, username, token)
        import_mode = import_data.get("mode")
        import_value = import_data.get("value")

        query = ""
        if import_mode == "id":
            # Standard JQL format for a single issue key
            query = f'issueKey = "{import_value.upper()}"'
        else: # mode is "query"
            query = import_value

        # 3. Call agent and filter out duplicates
        logging.info(f"Searching for external issues with query: {query}")
        found_issues = agent.search_issues(query)

        new_issues_to_import = []
        for issue in found_issues:
            external_id = issue.get('id')
            if external_id:
                existing = db.get_cr_by_external_id(self.project_id, external_id)
                if not existing:
                    new_issues_to_import.append(issue)
                else:
                    # --- ADD THIS DEBUG LINE ---
                    print(f"DEBUG: Found existing record in DB: {dict(existing)}")
                    logging.warning(f"Skipping import of '{external_id}'; it already exists in the backlog.")

        return new_issues_to_import

    def add_imported_backlog_items(self, items_to_add: list):
        """Takes a list of new items from the import process and saves them to the backlog, preserving hierarchy and mapping issue types."""
        if not self.project_id:
            logging.error("Cannot add imported items; no active project.")
            return

        logging.info(f"Adding {len(items_to_add)} new imported items to the backlog.")
        db = self.db_manager
        project_settings = self.get_project_integration_settings()
        epic_type_id = project_settings.get("epic_type_id")
        story_type_id = project_settings.get("story_type_id")
        bug_type_id = project_settings.get("bug_type_id")
        change_request_type_id = project_settings.get("change_request_type_id")

        for item in items_to_add:
            parent_cr_id = None
            parent_info = item.get('parent')
            item_issuetype = item.get('issuetype', {})
            item_issuetype_id = item_issuetype.get('id') if item_issuetype else None

            # Determine parent link
            if parent_info and parent_info.get('key'):
                parent_external_id = parent_info.get('key')
                local_parent = db.get_cr_by_external_id(self.project_id, parent_external_id)
                if local_parent:
                    parent_cr_id = local_parent['cr_id']
                else:
                    logging.warning(f"Could not find local parent for imported issue '{item.get('id')}'. Parent with external key '{parent_external_id}' has not been imported yet. Item will be added at the top level.")

            # Determine request_type and status based on Jira's Issue Type ID
            request_type = "BACKLOG_ITEM" # Default
            status = "TO_DO" # Default

            if item_issuetype_id == epic_type_id:
                request_type = "EPIC"
                status = "TO_DO" # Epics can have a simple status
            elif item_issuetype_id == story_type_id:
                request_type = "FEATURE"
                status = "TO_DO" # Features can also have a simple status
            elif item_issuetype_id == bug_type_id:
                request_type = "BUG_REPORT"
                status = "BUG_RAISED"
            elif item_issuetype_id == change_request_type_id:
                request_type = "BACKLOG_ITEM"
                status = "CHANGE_REQUEST"

            # Add the new item to the database with the determined attributes
            db.add_change_request(
                project_id=self.project_id,
                title=item.get('title', 'Untitled Imported Item'),
                description=item.get('description', 'No description provided.'),
                external_id=item.get('id'),
                parent_cr_id=parent_cr_id,
                request_type=request_type,
                status=status
            )

    def handle_sync_to_tool(self, cr_ids: list) -> dict:
        """
        Handles syncing a list of ASDF backlog items to the external tool,
        including their hierarchical parent information and correct issue types.
        """
        if not self.project_id:
            raise Exception("No active project for sync.")

        db = self.db_manager

        # 1. Fetch all required settings
        global_provider = db.get_config_value("INTEGRATION_PROVIDER")
        url = db.get_config_value("INTEGRATION_URL")
        username = db.get_config_value("INTEGRATION_USERNAME")
        token = db.get_config_value("INTEGRATION_API_TOKEN")

        project_settings = self.get_project_integration_settings()
        project_provider = project_settings.get("provider")
        project_key = project_settings.get("project_key")

        # Fetch all five distinct type IDs
        epic_type_id = project_settings.get("epic_type_id")
        story_type_id = project_settings.get("story_type_id")
        task_type_id = project_settings.get("task_type_id")
        bug_type_id = project_settings.get("bug_type_id")
        change_request_type_id = project_settings.get("change_request_type_id")


        # 2. Validate core settings
        if not all([global_provider, url, username, token]) or global_provider == "None":
            raise ValueError("Global integration credentials are not configured in File -> Settings.")
        if not all([project_provider, project_key]):
            raise ValueError("Project-specific integration settings (Provider and Key) must be configured in Project -> Project Settings.")


        agent = IntegrationAgentPMT(project_provider, url, username, token)
        synced_items = []
        failed_items = []
        logging.info(f"Attempting to sync {len(cr_ids)} items to {project_provider}...")

        # 3. Loop through each item to sync
        for cr_id in cr_ids:
            item_details = db.get_cr_by_id(cr_id)
            if not item_details:
                failed_items.append({"id": cr_id, "reason": "Item not found in database."})
                continue

            # 4. Intelligently select the correct Issue Type ID
            item_type = item_details['request_type']
            issue_type_id_to_use = None
            if item_type == 'EPIC':
                issue_type_id_to_use = epic_type_id
            elif item_type == 'FEATURE':
                issue_type_id_to_use = story_type_id
            elif item_type == 'BUG_REPORT':
                issue_type_id_to_use = bug_type_id
            elif item_type == 'BACKLOG_ITEM':
                # Use the specific Change Request ID if provided, otherwise fall back to the generic Task ID
                issue_type_id_to_use = change_request_type_id or task_type_id


            if not issue_type_id_to_use:
                failed_items.append({"id": cr_id, "reason": f"No Jira Issue Type ID configured in Project Settings for ASDF type '{item_type}'."})
                continue

            # 5. Find parent information
            parent_epic = None
            if item_details['parent_cr_id']:
                parent_details = db.get_cr_by_id(item_details['parent_cr_id'])
                # Features can be parents, but their parent epic is what matters to Jira
                if parent_details and parent_details['request_type'] == 'FEATURE':
                    if parent_details['parent_cr_id']:
                        epic_details = db.get_cr_by_id(parent_details['parent_cr_id'])
                        if epic_details and epic_details['request_type'] == 'EPIC':
                            parent_epic = epic_details
                elif parent_details and parent_details['request_type'] == 'EPIC':
                    parent_epic = parent_details

            # 6. Call the agent with the complete data package
            try:
                result = agent.create_issue(
                    title=item_details['title'],
                    description=item_details['description'],
                    project_key=project_key,
                    issue_type_id=issue_type_id_to_use,
                    parent_epic=parent_epic
                )
                db.update_cr_external_link(cr_id, result['key'], result['url'])
                synced_items.append({"id": cr_id, "external_key": result['key']})
            except Exception as e:
                logging.error(f"Failed to sync CR-{cr_id}: {e}")
                failed_items.append({"id": cr_id, "reason": str(e)})

        return {"succeeded": len(synced_items), "failed": len(failed_items), "errors": failed_items, "synced_items": synced_items}

    def finalize_and_save_complexity_assessment(self, assessment_json_str: str):
        """
        Saves the complexity assessment to the DB and generates and saves both a raw
        .json file and a formatted .docx report to the filesystem.
        """
        if not self.project_id:
            logging.error("Cannot save complexity assessment; no active project.")
            return

        try:
            # Save the raw data to the database as before
            self.db_manager.update_project_field(self.project_id, "complexity_assessment_text", assessment_json_str)
            logging.info(f"Successfully saved Complexity && Risk Assessment to database for project {self.project_id}")

            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "docs"
                docs_dir.mkdir(exist_ok=True)

                # Save the raw JSON file for system use
                # assessment_file_path_json = docs_dir / "complexity_and_risk_assessment.json"
                # assessment_file_path_json.write_text(assessment_json_str, encoding="utf-8")
                # self._commit_document(assessment_file_path_json, "docs: Add Complexity and Risk Assessment (JSON)")

                # Generate and save the formatted .docx report
                assessment_file_path_docx = docs_dir / "complexity_and_risk_assessment.docx"
                report_generator = ReportGeneratorAgent()
                assessment_data = json.loads(assessment_json_str)
                docx_bytes = report_generator.generate_assessment_docx(assessment_data, self.project_name)

                with open(assessment_file_path_docx, 'wb') as f:
                    f.write(docx_bytes.getbuffer())

                self._commit_document(assessment_file_path_docx, "docs: Add formatted Complexity and Risk Assessment (docx)")

        except Exception as e:
            logging.error(f"Failed to finalize and save complexity assessment: {e}")

    def finalize_and_save_tech_spec(self, tech_spec_draft: str, target_os: str):
        """
        Saves the final technical spec to the database, a .md file, and a formatted
        .docx file, extracts key info, and transitions to the next phase.
        """
        if not self.project_id:
            logging.error("Cannot save technical spec; no active project.")
            return

        try:
            final_doc_with_header = self.prepend_standard_header(
                document_content=tech_spec_draft,
                document_type="Technical Specification"
            )

            db = self.db_manager
            db.update_project_field(self.project_id, "target_os", target_os)
            db.update_project_field(self.project_id, "tech_spec_text", final_doc_with_header)

            project_details = db.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "docs"

                # Save the Markdown file for system use
                spec_file_path_md = docs_dir / "technical_spec.md"
                spec_file_path_md.write_text(final_doc_with_header, encoding="utf-8")
                self._commit_document(spec_file_path_md, "docs: Finalize Technical Specification (Markdown)")

                # Generate and save the formatted .docx file for human use
                spec_file_path_docx = docs_dir / "technical_spec.docx"
                report_generator = ReportGeneratorAgent()
                docx_bytes = report_generator.generate_text_document_docx(
                    title=f"Technical Specification - {self.project_name}",
                    content=tech_spec_draft
                )
                with open(spec_file_path_docx, 'wb') as f:
                    f.write(docx_bytes.getbuffer())
                self._commit_document(spec_file_path_docx, "docs: Add formatted Technical Specification (docx)")


            self._extract_and_save_primary_technology(final_doc_with_header)
            self.set_phase("BUILD_SCRIPT_SETUP")

        except Exception as e:
            logging.error(f"Failed to finalize and save technical spec: {e}")

    def finalize_and_save_coding_standard(self, standard_draft: str):
        """
        Saves the final coding standard, then calls the PlanningAgent to generate
        the initial backlog, and transitions to the BACKLOG_RATIFICATION phase.
        """
        if not self.project_id:
            logging.error("Cannot save coding standard; no active project.")
            return

        try:
            final_doc_with_header = self.prepend_standard_header(
                document_content=standard_draft,
                document_type="Coding Standard"
            )

            db = self.db_manager
            db.update_project_field(self.project_id, "coding_standard_text", final_doc_with_header)

            project_details = db.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "docs"

                # Save the Markdown file for system use
                standard_file_path_md = docs_dir / "coding_standard.md"
                standard_file_path_md.write_text(final_doc_with_header, encoding="utf-8")
                self._commit_document(standard_file_path_md, "docs: Finalize Coding Standard (Markdown)")

                # Generate and save the formatted .docx file for human use
                standard_file_path_docx = docs_dir / "coding_standard.docx"
                report_generator = ReportGeneratorAgent()
                docx_bytes = report_generator.generate_text_document_docx(
                    title=f"Coding Standard - {self.project_name}",
                    content=standard_draft
                )
                with open(standard_file_path_docx, 'wb') as f:
                    f.write(docx_bytes.getbuffer())
                self._commit_document(standard_file_path_docx, "docs: Add formatted Coding Standard (docx)")

            # --- NEW LOGIC ---
            # Generate the initial backlog now that all technical specs are complete.
            logging.info("Coding standard saved. Now generating initial backlog for ratification.")
            from agents.agent_planning_app_target import PlanningAgent_AppTarget
            planning_agent = PlanningAgent_AppTarget(self.llm_service, self.db_manager)

            # Pass both the app spec and the new tech spec to the agent.
            # First, strip the irrelevant setup guide from the tech spec.
            cleaned_tech_spec = self._strip_environment_setup_from_spec(project_details['tech_spec_text'])
            backlog_items_json = planning_agent.generate_backlog_items(
                final_spec_text=project_details['final_spec_text'],
                tech_spec_text=cleaned_tech_spec
            )

            # Store the generated items for the ratification screen to use
            self.task_awaiting_approval = {"generated_backlog_items": backlog_items_json}

            self.set_phase("BACKLOG_RATIFICATION")
            # --- END NEW LOGIC ---

        except Exception as e:
            logging.error(f"Failed to finalize and save coding standard: {e}")

    def finalize_and_save_dev_plan(self, plan_json_string: str) -> tuple[bool, str]:
        """
        Saves the final dev plan to the database, a .json file, and a formatted
        .docx file, loads it into the active state, and transitions to Genesis.
        """
        if not self.project_id:
            return False, "No active project."

        try:
            # Save the raw JSON plan (with header) to the database for runtime use
            final_doc_with_header = self.prepend_standard_header(
                document_content=plan_json_string,
                document_type="Sequential Development Plan"
            )
            self.db_manager.update_project_field(self.project_id, "development_plan_text", final_doc_with_header)

            # Generate and save both raw and formatted files to the filesystem
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "docs"
                docs_dir.mkdir(exist_ok=True)

                # Save the raw JSON file for system use
                plan_file_path_json = docs_dir / "development_plan.json"
                plan_file_path_json.write_text(plan_json_string, encoding="utf-8")
                self._commit_document(plan_file_path_json, "docs: Finalize Development Plan (JSON)")

                # Generate and save the formatted .docx report
                plan_file_path_docx = docs_dir / "development_plan.docx"
                report_generator = ReportGeneratorAgent()
                plan_data = json.loads(plan_json_string)
                docx_bytes = report_generator.generate_dev_plan_docx(plan_data, self.project_name)

                with open(plan_file_path_docx, 'wb') as f:
                    f.write(docx_bytes.getbuffer())

                self._commit_document(plan_file_path_docx, "docs: Add formatted Development Plan (docx)")

            # Load the plan into the active state for execution
            full_plan_data = json.loads(plan_json_string)
            dev_plan_list = full_plan_data.get("development_plan")
            if dev_plan_list is None:
                raise ValueError("The plan JSON is missing the 'development_plan' key.")

            self.active_plan = dev_plan_list
            self.active_plan_cursor = 0
            logging.info(f"Successfully loaded development plan with {len(dev_plan_list)} tasks. Starting at task 1.")

            self.set_phase("GENESIS")
            return True, "Plan approved! Starting development..."

        except Exception as e:
            logging.error(f"Failed to finalize and save development plan: {e}")
            return False, f"Failed to process the development plan: {e}"

    def set_phase(self, phase_name: str):
        """
        Sets the current project phase and automatically saves the new state.
        """
        try:
            new_phase = FactoryPhase[phase_name]

            non_dirtying_phases = [
                FactoryPhase.IDLE,
                FactoryPhase.VIEWING_PROJECT_HISTORY,
                FactoryPhase.AWAITING_PREFLIGHT_RESOLUTION
            ]
            if self.project_id and new_phase not in non_dirtying_phases:
                self.is_project_dirty = True
                logging.info(f"Project marked as dirty due to phase transition to {new_phase.name}")

            self.current_phase = new_phase
            logging.info(f"Transitioning to phase: {self.current_phase.name}")

            if self.project_id and new_phase != FactoryPhase.VIEWING_PROJECT_HISTORY:
                self._save_current_state()

        except KeyError:
            logging.error(f"Attempted to set an invalid phase: {phase_name}")

    def update_current_step_and_save_state(self, current_step: str, state_details: dict):
        """
        Updates the granular step within a phase and immediately saves the full
        application state to the database.
        """
        logging.info(f"Updating current step to: {current_step}")
        self.current_step = current_step
        self.task_awaiting_approval = state_details
        self.is_project_dirty = True
        self._save_current_state()

    def handle_proceed_action(self, progress_callback=None):
        """
        Handles the logic for the Genesis Pipeline, now with a separate 'fix mode'
        track and correct debug counter reset logic.
        """
        # --- FIX MODE LOGIC ---
        if self.is_in_fix_mode:
            logging.info("--- In Fix Mode: Executing from fix plan. ---")
            if not self.fix_plan or self.fix_plan_cursor >= len(self.fix_plan):
                logging.info("Fix plan is now complete. Exiting fix mode and re-attempting original task.")
                self.is_in_fix_mode = False
                self.fix_plan = None
                self.fix_plan_cursor = 0
                # Re-enter the loop to re-attempt the original task that prompted the fix.
                return self.handle_proceed_action(progress_callback=progress_callback)
            else:
                task = self.fix_plan[self.fix_plan_cursor]
                component_name = task.get('component_name', 'Unnamed Fix Task')
                logging.info(f"Executing FIX task {self.fix_plan_cursor + 1}/{len(self.fix_plan)} for component: {component_name}")
                if progress_callback:
                    progress_callback(("INFO", f"Executing FIX task {self.fix_plan_cursor + 1}/{len(self.fix_plan)} for: {component_name}"))

                try:
                    db = self.db_manager
                    project_details = db.get_project_by_id(self.project_id)
                    project_root_path = Path(project_details['project_root_folder'])

                    self._execute_source_code_generation_task(task, project_root_path, db, progress_callback)
                    self.fix_plan_cursor += 1
                    return "Fix step complete."
                except EnvironmentFailureException:
                    logging.warning("Halting fix plan due to an unrecoverable environment failure.")
                    return "Environment failure during fix. Escalated to PM."
                except Exception as e:
                    # This block is updated
                    if progress_callback:
                        progress_callback(("ERROR", f"Fix task failed for {component_name}. Initiating debug protocol..."))
                    logging.error(f"A task within the fix plan failed for {component_name}. Error: {e}")
                    self.escalate_for_manual_debug(str(e))
                    return f"Error during fix execution: {e}"
        # --- END OF FIX MODE LOGIC ---

        # --- REGULAR PLAN LOGIC ---
        if self.current_phase != FactoryPhase.GENESIS:
            logging.warning(f"Received 'Proceed' action in an unexpected phase: {self.current_phase.name}")
            return "No action taken."

        if not self.active_plan or self.active_plan_cursor >= len(self.active_plan):
            self._run_final_sprint_verification(progress_callback)
            return "Sprint development tasks complete. Running final verification..."

        task = self.active_plan[self.active_plan_cursor]
        component_name = task.get('component_name')
        logging.info(f"Executing task {self.active_plan_cursor + 1} for component: {component_name}")
        if progress_callback:
            progress_callback(("INFO", f"Executing task {self.active_plan_cursor + 1}/{len(self.active_plan)} for component: {component_name}"))

        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            project_root_path = Path(project_details['project_root_folder'])
            component_type = task.get("component_type", "CLASS")

            if component_type in ["DB_MIGRATION_SCRIPT", "BUILD_SCRIPT_MODIFICATION", "CONFIG_FILE_UPDATE"]:
                self._execute_declarative_modification_task(task, project_root_path, db, progress_callback)
                return "Paused for high-risk change approval."

            if task.get("artifact_id"):
                artifact_record = db.get_artifact_by_id(task["artifact_id"])
                if artifact_record and artifact_record['file_path']:
                    canonical_path = artifact_record['file_path']
                    plan_path = task.get("component_file_path")
                    if plan_path != canonical_path:
                        logging.warning(f"Path mismatch for artifact {task['artifact_id']}. Overriding plan path '{plan_path}' with canonical RoWD path '{canonical_path}'.")
                        task["component_file_path"] = canonical_path

            self._execute_source_code_generation_task(task, project_root_path, db, progress_callback)
            self.active_plan_cursor += 1
            self.debug_attempt_counter = 0

            return "Step complete."

        except Exception as e:
            # This block is updated
            if progress_callback:
                progress_callback(("ERROR", f"Task failed for {component_name}. Initiating debug protocol..."))
            logging.error(f"Genesis Pipeline failed for {component_name}. Error: {e}", exc_info=True)
            self.escalate_for_manual_debug(str(e))
            return f"Error during fix execution: {e}"

    def run_integration_and_verification_phase(self, force_proceed=False, progress_callback=None):
        """
        Runs the full integration and verification process, now with a flag
        to bypass the initial known-issues check after PM confirmation.
        """
        logging.info("Starting integration and verification phase...")
        try:
            db = self.db_manager

            if not force_proceed:
                non_passing_statuses = ["KNOWN_ISSUE", "UNIT_TESTS_FAILING", "DEBUG_PM_ESCALATION"]
                known_issues = db.get_artifacts_by_statuses(self.project_id, non_passing_statuses)

                if known_issues:
                    if progress_callback:
                        # This line is corrected to send a tuple
                        progress_callback(("WARNING", "Integration paused: Found components with known issues."))
                    self.task_awaiting_approval = {"known_issues": [dict(row) for row in known_issues]}
                    self.set_phase("AWAITING_INTEGRATION_CONFIRMATION")
                    return

            if progress_callback:
                # This line is corrected to send a tuple
                progress_callback(("INFO", "Running integration and UI testing phase logic..."))
            self._run_integration_and_ui_testing_phase(progress_callback=progress_callback)

        except Exception as e:
            logging.error(f"Integration and verification phase failed: {e}", exc_info=True)
            self.escalate_for_manual_debug(str(e))

    def handle_integration_confirmation(self, decision: str):
        """
        Handles the PM's decision on whether to proceed with integration.
        """
        if decision == "PROCEED":
            logging.warning("PM chose to proceed with integration despite known issues.")
            self.task_awaiting_approval = {"force_integration": True}
            # --- THIS IS THE FIX ---
            # Transition back to Genesis. The main window will see this and re-trigger
            # the integration phase, but this time with the 'force' flag set.
            self.set_phase("GENESIS")
            # --- END OF FIX ---
        else:
            self.set_phase("GENESIS")

    def _execute_source_code_generation_task(self, task: dict, project_root_path: Path, db: ASDFDBManager, progress_callback=None):
        """
        Handles the 'generate -> review -> correct -> verify -> commit -> update docs' workflow.
        """
        component_name = task.get("component_name")
        if progress_callback: progress_callback(("INFO", f"Executing source code generation for: {component_name}"))

        if not self.llm_service:
            raise Exception("Cannot generate code: LLM Service is not configured.")

        project_details = db.get_project_by_id(self.project_id)
        coding_standard = project_details['coding_standard_text']
        target_language = project_details['technology_stack']
        test_command = project_details['test_execution_command']
        version_control_enabled = project_details['version_control_enabled'] == 1 if project_details else True

        all_artifacts_rows = db.get_all_artifacts_for_project(self.project_id)
        rowd_json = json.dumps([dict(row) for row in all_artifacts_rows])
        micro_spec_content = task.get("task_description")

        if progress_callback: progress_callback(("INFO", f"Generating logic plan for {component_name}..."))
        logic_agent = LogicAgent_AppTarget(llm_service=self.llm_service)
        code_agent = CodeAgent_AppTarget(llm_service=self.llm_service)
        review_agent = CodeReviewAgent(llm_service=self.llm_service)
        test_agent = TestAgent_AppTarget(llm_service=self.llm_service)
        logic_plan = logic_agent.generate_logic_for_component(micro_spec_content)
        if progress_callback: progress_callback(("SUCCESS", "... Logic plan generated."))

        if progress_callback: progress_callback(("INFO", f"Generating source code for {component_name}..."))
        style_guide_to_use = project_details['ux_spec_text'] or project_details['final_spec_text']
        source_code = code_agent.generate_code_for_component(logic_plan, coding_standard, target_language, style_guide=style_guide_to_use)
        if progress_callback: progress_callback(("SUCCESS", "... Source code generated."))

        # This block validates the AI's output
        if not source_code or not source_code.strip():
            raise Exception("Code generation failed: The AI returned empty source code for the component.")

        MAX_REVIEW_ATTEMPTS = 2
        for attempt in range(MAX_REVIEW_ATTEMPTS):
            if progress_callback: progress_callback(("INFO", f"Reviewing code for {component_name} (Attempt {attempt + 1})..."))
            review_status, review_output = review_agent.review_code(micro_spec_content, logic_plan, source_code, rowd_json, coding_standard)
            if review_status == "pass":
                break
            elif review_status == "pass_with_fixes":
                source_code = review_output
                break
            elif review_status == "fail":
                if attempt < MAX_REVIEW_ATTEMPTS - 1:
                    if progress_callback: progress_callback(("INFO", f"Re-writing code for {component_name} based on feedback..."))
                    source_code = code_agent.generate_code_for_component(logic_plan, coding_standard, target_language, feedback=review_output)
                else:
                    raise Exception(f"Component '{component_name}' failed code review after all attempts.")
        if progress_callback: progress_callback(("SUCCESS", "... Code review process complete."))

        unit_tests = None
        test_path = task.get("test_file_path")

        # Only generate tests if the plan includes a path for the test file
        if test_path:
            if progress_callback: progress_callback(("INFO", f"Generating unit tests for {component_name}..."))
            unit_tests = test_agent.generate_unit_tests_for_component(source_code, micro_spec_content, coding_standard, target_language)
            if progress_callback: progress_callback(("SUCCESS", "... Unit tests generated."))

        if progress_callback: progress_callback(("INFO", f"Writing files, testing, and committing {component_name}..."))
        build_agent = BuildAndCommitAgentAppTarget(str(project_root_path), version_control_enabled=version_control_enabled)
        status, result_message = build_agent.build_and_commit_component(
            task.get("component_file_path"), source_code,
            test_path, unit_tests,
            test_command, self.llm_service,
            version_control_enabled
        )

        if status == 'ENVIRONMENT_FAILURE':
            logging.error(f"Environment failure for {component_name}: {result_message}")
            self.task_awaiting_approval = {"failure_log": result_message, "is_env_failure": True}
            self.set_phase("DEBUG_PM_ESCALATION")
            raise EnvironmentFailureException(result_message)
        elif status != 'SUCCESS':
            raise Exception(f"BuildAndCommitAgent failed for {component_name}: {result_message}")

        commit_hash = result_message.split(":")[-1].strip() if "New commit hash:" in result_message else "N/A"
        if progress_callback: progress_callback(("SUCCESS", "... Component successfully tested and committed."))

        if progress_callback: progress_callback(("INFO", f"Summarizing new code for {component_name}..."))
        summarization_agent = CodeSummarizationAgent(llm_service=self.llm_service)
        summary = summarization_agent.summarize_code(source_code)
        if progress_callback: progress_callback(("SUCCESS", "... Code summarized."))

        if progress_callback: progress_callback(("INFO", f"Updating project records for {component_name}..."))
        doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)
        doc_agent.update_artifact_record({
            "artifact_id": f"art_{uuid.uuid4().hex[:8]}", "project_id": self.project_id,
            "file_path": task.get("component_file_path"), "artifact_name": component_name,
            "artifact_type": task.get("component_type"), "short_description": micro_spec_content,
            "status": "UNIT_TESTS_PASSING", "unit_test_status": "TESTS_PASSING",
            "commit_hash": commit_hash, "version": 1,
            "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
            "micro_spec_id": task.get("micro_spec_id"),
            "code_summary": summary
        })
        if progress_callback: progress_callback(("SUCCESS", "... Project records updated."))

    def _execute_declarative_modification_task(self, task: dict, project_root_path: Path, db: ASDFDBManager, progress_callback=None):
        """
        Pauses the workflow to await PM confirmation for a declarative change.
        """
        component_name = task.get("component_name")
        logging.info(f"High-risk modification detected for '{component_name}'. Pausing for PM checkpoint.")
        if progress_callback:
            progress_callback(f"High-risk modification detected for '{component_name}'. Pausing for PM checkpoint.")

        self.task_awaiting_approval = task
        self.set_phase("AWAITING_PM_DECLARATIVE_CHECKPOINT")

    def handle_declarative_checkpoint_decision(self, decision: str):
        """
        Processes the PM's decision from the declarative checkpoint.
        """
        if not self.task_awaiting_approval:
            logging.error("Received a checkpoint decision, but no task is awaiting approval.")
            self.set_phase("GENESIS")
            return

        task = self.task_awaiting_approval
        component_name = task.get("component_name")
        logging.info(f"PM made decision '{decision}' for component '{component_name}'.")

        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise FileNotFoundError("Project root folder not found for declarative checkpoint.")

            project_root_path = str(project_details['project_root_folder'])

            if decision == "EXECUTE_AUTOMATICALLY":
                if not self.llm_service:
                    raise Exception("Cannot execute declarative change: LLM Service is not configured.")

                file_to_modify_path_str = task.get("component_file_path")
                change_snippet = task.get("task_description")

                if not file_to_modify_path_str or file_to_modify_path_str == "N/A":
                    raise ValueError(f"Invalid file path for declarative task '{component_name}'.")

                file_to_modify = Path(project_root_path) / file_to_modify_path_str
                original_code = ""
                if file_to_modify.exists():
                    original_code = file_to_modify.read_text(encoding='utf-8')
                else:
                    file_to_modify.parent.mkdir(parents=True, exist_ok=True)
                    logging.warning(f"File '{file_to_modify_path_str}' did not exist. It will be created.")

                modifications_json = json.dumps({
                    "instruction": "Apply the following snippet to the original code. If the snippet represents a dependency or a new entry, append it logically. If it represents an update to an existing value, replace the old value.",
                    "snippet": change_snippet
                })

                orch_agent = OrchestrationCodeAgent(llm_service=self.llm_service)
                modified_code = orch_agent.apply_modifications(original_code, modifications_json)
                file_to_modify.write_text(modified_code, encoding='utf-8')

                build_agent = BuildAndCommitAgentAppTarget(project_root_path)
                commit_message = f"refactor: Apply approved modification to {component_name}"
                build_agent.commit_changes([file_to_modify_path_str], commit_message)
                logging.info(f"Automatically executed and committed modification for {component_name}.")

            elif decision == "WILL_EXECUTE_MANUALLY":
                logging.info(f"Acknowledged that PM will manually execute change for {component_name}.")

        except Exception as e:
            logging.error(f"Failed to handle declarative checkpoint decision for {component_name}. Error: {e}")
            self.escalate_for_manual_debug(str(e))
            return

        self.task_awaiting_approval = None
        self.active_plan_cursor += 1
        self.set_phase("GENESIS")
        logging.info("Declarative task handled. Returning to Genesis phase.")

    def _run_post_implementation_doc_update(self):
        """
        After a CR/bug fix, this method updates all relevant project documents
        in the database AND writes the changes back to the filesystem.
        """
        logging.info("Change implementation complete. Running post-implementation documentation update...")
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details:
                logging.error("Could not run doc update; project details not found.")
                return

            if not self.llm_service:
                logging.error("Could not run doc update; LLM Service is not configured.")
                return

            project_root = Path(project_details['project_root_folder'])
            docs_dir = project_root / "docs"

            implementation_plan_for_update = json.dumps(self.active_plan, indent=4)
            doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)

            # --- THIS IS THE NEW, REFACTORED LOGIC ---
            def update_and_save_document(doc_key: str, doc_name: str, file_name: str):
                original_doc = project_details[doc_key]
                if original_doc:
                    logging.info(f"Checking for {doc_name} updates...")

                    # Get the current date to pass to the agent
                    current_date = datetime.now().strftime('%x')

                    updated_content = doc_agent.update_specification_text(
                        original_spec=original_doc,
                        implementation_plan=implementation_plan_for_update,
                        current_date=current_date  # Pass the date to the agent
                    )

                    # The content of the document itself contains the header with the version
                    db.update_project_field(self.project_id, doc_key, updated_content)

                    # Also write the updated content back to the file system
                    doc_path = docs_dir / file_name
                    doc_path.write_text(updated_content, encoding="utf-8")
                    self._commit_document(doc_path, f"docs: Update {doc_name} after CR implementation")
                    logging.info(f"Successfully updated, saved, and committed the {doc_name}.")

            update_and_save_document('final_spec_text', 'Application Specification', 'application_spec.md')
            update_and_save_document('tech_spec_text', 'Technical Specification', 'technical_spec.md')
            update_and_save_document('ux_spec_text', 'UX/UI Specification', 'ux_ui_specification.md')
            update_and_save_document('ui_test_plan_text', 'UI Test Plan', 'ui_test_plan.md')
            # --- END OF NEW LOGIC ---

        except Exception as e:
            logging.error(f"Failed during post-implementation doc update: {e}")

    def _get_integration_context_files(self, new_artifacts: list[dict]) -> list[str]:
        """
        Uses the LLM service to determine which existing files are the most
        likely integration points.
        """
        logging.info("AI is analyzing the project to identify relevant integration files...")
        all_artifacts_rows = self.db_manager.get_all_artifacts_for_project(self.project_id)
        if not all_artifacts_rows:
            return []

        if not self.llm_service:
            logging.error("Cannot identify integration files: LLM Service is not configured.")
            return []

        rowd_json = json.dumps([dict(row) for row in all_artifacts_rows], indent=2)
        new_artifacts_json = json.dumps(new_artifacts, indent=2)

        prompt = textwrap.dedent(f"""
            You are an expert software architect. Your task is to identify which existing files in a project need to be modified to integrate a set of new components.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Context:** Review the full Record-of-Work-Done (RoWD) which describes all existing components, and the JSON for the new components to be integrated.
            2.  **Identify Integration Points:** Determine which existing files are the most logical places to "wire in" the new components. These are typically higher-level files like a main application, a service registry, a router, or a central module.
            3.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array of strings. Each string in the array must be the exact `file_path` of an existing file that needs to be modified.
            4.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON array itself.

            **--- INPUT 1: All Existing Components (RoWD) ---**
            ```json
            {rowd_json}
            ```

            **--- INPUT 2: New Components to Integrate ---**
            ```json
            {new_artifacts_json}
            ```

            **--- REQUIRED OUTPUT: JSON Array of File Paths ---**
        """)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            integration_files = json.loads(cleaned_response)
            if isinstance(integration_files, list):
                logging.info(f"AI identified the following integration files: {integration_files}")
                return integration_files
            return []
        except Exception as e:
            logging.error(f"Failed to identify integration context files via AI: {e}")
            return []

    def _get_json_from_document(self, doc_text: str) -> dict:
        """Extracts the JSON content from a document that may have a standard text header."""
        if not doc_text:
            return {}
        # The header is separated by a consistent line of 50 hyphens
        header_delimiter = f"\n{'-' * 50}\n\n"
        if header_delimiter in doc_text:
            parts = doc_text.split(header_delimiter, 1)
            if len(parts) > 1:
                return json.loads(parts[1])
        # If no header, assume the whole content is JSON
        return json.loads(doc_text)

    def _get_content_from_document(self, doc_text: str) -> str:
        """Strips the standard text header from a document to get the raw content."""
        if not doc_text:
            return ""
        header_delimiter = f"\n{'-' * 50}\n\n"
        if header_delimiter in doc_text:
            parts = doc_text.split(header_delimiter, 1)
            if len(parts) > 1:
                return parts[1]
        return doc_text # Return original text if delimiter not found

    def _strip_environment_setup_from_spec(self, tech_spec_text: str) -> str:
        """Removes the Development Environment Setup Guide from the spec text."""
        heading = "Development Environment Setup Guide"
        parts = tech_spec_text.split(heading, 1)
        return parts[0].strip()

    def _run_integration_and_ui_testing_phase(self, progress_callback=None):
        """
        Executes the full Integration and UI Testing workflow, including planning,
        execution, and final test plan generation in both .md and .docx formats.
        """
        logging.info("Starting Phase: Automated Integration && Verification.")
        if progress_callback:
            progress_callback("Starting Phase: Automated Integration && Verification.")

        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise FileNotFoundError("Project root folder not found for integration phase.")

            project_root_path = Path(project_details['project_root_folder'])
            docs_dir = project_root_path / "docs"

            if progress_callback: progress_callback("Analyzing project for integration points...")

            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            new_artifacts_for_integration = [dict(row) for row in all_artifacts]

            integration_files_to_load = self._get_integration_context_files(new_artifacts_for_integration)
            existing_code_context = {}
            for file_path in integration_files_to_load:
                full_path = project_root_path / file_path
                if full_path.exists():
                    existing_code_context[file_path] = full_path.read_text(encoding='utf-8')

            if progress_callback: progress_callback("Generating Integration Plan...")
            integration_planner = IntegrationPlannerAgent(llm_service=self.llm_service)
            integration_plan_json = integration_planner.create_integration_plan(
                json.dumps(new_artifacts_for_integration), existing_code_context
            )

            if progress_callback: progress_callback("Executing Integration Plan...")
            orchestration_agent = OrchestrationCodeAgent(llm_service=self.llm_service)
            integration_plan = json.loads(integration_plan_json)

            for file_path_str, modifications in integration_plan.items():
                if progress_callback: progress_callback(f"  - Applying changes to {file_path_str}...")
                target_file_path = project_root_path / file_path_str
                original_code = target_file_path.read_text(encoding='utf-8') if target_file_path.exists() else ""

                modified_code = orchestration_agent.apply_modifications(original_code, json.dumps(modifications))
                target_file_path.write_text(modified_code, encoding='utf-8')
                logging.info(f"Applied integration modifications to {file_path_str}")

            final_integration_plan = self.prepend_standard_header(
                document_content=integration_plan_json,
                document_type="Integration Plan"
            )
            db.update_project_field(self.project_id, "integration_plan_text", final_integration_plan)

            integration_plan_file_path = docs_dir / "integration_plan.json"
            integration_plan_file_path.write_text(integration_plan_json, encoding="utf-8")
            self._commit_document(integration_plan_file_path, "docs: Add Integration Plan")

            if progress_callback: progress_callback("Generating UI Test Plan...")
            functional_spec_text = project_details['final_spec_text']
            technical_spec_text = project_details['tech_spec_text']
            ui_test_planner = UITestPlannerAgent_AppTarget(llm_service=self.llm_service)
            ui_test_plan_content = ui_test_planner.generate_ui_test_plan(functional_spec_text, technical_spec_text)

            final_ui_test_plan = self.prepend_standard_header(
                document_content=ui_test_plan_content,
                document_type="UI Test Plan"
            )
            db.update_project_field(self.project_id, "ui_test_plan_text", final_ui_test_plan)

            # Save the Markdown file for system use
            test_plan_file_path_md = docs_dir / "ui_test_plan.md"
            test_plan_file_path_md.write_text(final_ui_test_plan, encoding="utf-8")
            self._commit_document(test_plan_file_path_md, "docs: Add UI Test Plan (Markdown)")

            # Generate and save the formatted .docx file for human use
            test_plan_file_path_docx = docs_dir / "ui_test_plan.docx"
            report_generator = ReportGeneratorAgent()
            docx_bytes = report_generator.generate_text_document_docx(
                title=f"Manual UI Test Plan - {self.project_name}",
                content=ui_test_plan_content
            )
            with open(test_plan_file_path_docx, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            self._commit_document(test_plan_file_path_docx, "docs: Add formatted UI Test Plan (docx)")

            if progress_callback: progress_callback("Integration phase complete. Proceeding to manual testing.")

            self.set_phase("MANUAL_UI_TESTING")

        except Exception as e:
            logging.error(f"Failed during integration and testing phase: {e}", exc_info=True)
            self.escalate_for_manual_debug(str(e))

    def handle_ui_test_result_upload(self, test_result_content: str):
        """
        Orchestrates the evaluation of an uploaded UI test results file.
        """
        if not self.project_id:
            logging.error("Cannot handle test result upload; no active project.")
            return

        logging.info(f"Handling UI test result upload for project {self.project_id}.")
        try:
            if not self.llm_service:
                raise Exception("Cannot evaluate test results: LLM Service is not configured.")

            # The project state is about to be changed, so we mark it as dirty.
            self.is_project_dirty = True

            eval_agent = TestResultEvaluationAgent_AppTarget(llm_service=self.llm_service)
            failure_summary = eval_agent.evaluate_ui_test_results(test_result_content)

            if "ALL_TESTS_PASSED" in failure_summary:
                logging.info("UI test result evaluation complete: All tests passed.")
                # If everything passes, we can consider the project complete and idle.
                self.set_phase("PROJECT_COMPLETED")
            else:
                logging.warning("UI test result evaluation complete: Failures detected.")
                self.escalate_for_manual_debug(failure_summary, is_functional_bug=True)

        except Exception as e:
            logging.error(f"An unexpected error occurred during UI test result evaluation: {e}")
            self.escalate_for_manual_debug(str(e))

    def handle_view_cr_register_action(self):
        """
        Transitions the factory into the state for viewing the Project Backlog.
        """
        logging.info("PM chose to 'View Project Backlog'. Transitioning to the backlog screen.")
        self.set_phase("BACKLOG_VIEW")

    def handle_implement_cr_action(self, cr_id: int, **kwargs):
        """
        Handles the logic for when the PM confirms a CR for implementation.
        """
        logging.info(f"PM has confirmed implementation for Change Request ID: {cr_id}.")

        try:
            db = self.db_manager
            cr_details = db.get_cr_by_id(cr_id)
            if not cr_details:
                raise Exception(f"CR-{cr_id} not found in the database.")

            db.update_cr_status(cr_id, "PLANNING_IN_PROGRESS")

            # (The logic for stale analysis and context building remains the same)
            analysis_timestamp_str = cr_details['last_modified_timestamp']
            last_commit_timestamp = self.get_latest_commit_timestamp()
            if analysis_timestamp_str and last_commit_timestamp:
                analysis_time = datetime.fromisoformat(analysis_timestamp_str)
                if last_commit_timestamp > analysis_time:
                    self.task_awaiting_approval = {"cr_id_for_reanalysis": cr_id}
                    self.set_phase("AWAITING_IMPACT_ANALYSIS_CHOICE")
                    return

            project_details = db.get_project_by_id(self.project_id)
            project_root_path = Path(project_details['project_root_folder'])
            impacted_ids = json.loads(cr_details['impacted_artifact_ids'] or '[]')
            source_code_files = {}
            for artifact_id in impacted_ids:
                artifact_record = db.get_artifact_by_id(artifact_id)
                if artifact_record and artifact_record['file_path']:
                    source_path = project_root_path / artifact_record['file_path']
                    if source_path.exists(): source_code_files[artifact_record['file_path']] = source_path.read_text(encoding='utf-8')

            core_docs = {"final_spec_text": project_details['final_spec_text']}
            context_package = self._build_and_validate_context_package(core_docs, source_code_files)
            if context_package.get("error"): raise Exception(f"Context Builder Error: {context_package['error']}")

            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            rowd_json = json.dumps([dict(row) for row in all_artifacts])

            planner_agent = RefactoringPlannerAgent_AppTarget(llm_service=self.llm_service)
            new_plan_str = planner_agent.create_refactoring_plan(
                cr_details['description'], project_details['final_spec_text'],
                project_details['tech_spec_text'], rowd_json, context_package["source_code"]
            )

            response_data = json.loads(new_plan_str)
            if "error" in response_data:
                raise Exception(f"RefactoringPlannerAgent failed: {response_data['error']}")

            self.active_plan = response_data
            self.active_plan_cursor = 0
            self.is_executing_cr_plan = True

            # --- THIS IS THE FIX ---
            # After the plan is successfully generated, update the status to reflect this.
            db.update_cr_status(cr_id, "IMPLEMENTATION_IN_PROGRESS")
            # --- END OF FIX ---

            logging.info("Successfully generated new development plan from Change Request.")
            self.set_phase("GENESIS")

        except Exception as e:
            logging.error(f"Failed to process implementation for CR-{cr_id}. Error: {e}")
            db.update_cr_status(cr_id, "RAISED") # Revert status on failure
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

        except Exception as e:
            logging.error(f"Failed to process implementation for CR-{cr_id}. Error: {e}")
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

    def handle_stale_analysis_choice(self, choice: str, cr_id: int):
        """
        Handles the PM's choice on how to proceed with a stale impact analysis.
        """
        self.task_awaiting_approval = None

        if choice == "RE-RUN":
            logging.info(f"PM chose to re-run stale impact analysis for CR-{cr_id}.")
            self.handle_run_impact_analysis_action(cr_id)
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

        elif choice == "PROCEED":
            logging.warning(f"PM chose to proceed with a stale impact analysis for CR-{cr_id}.")
            self.handle_implement_cr_action(cr_id)

    def handle_delete_cr_action(self, cr_id_to_delete: int):
        """
        Handles the deletion of a CR, now with checks for linked CRs.
        If a link is found, it pauses for PM confirmation.
        """
        logging.info(f"PM initiated delete for CR ID: {cr_id_to_delete}.")
        try:
            db = self.db_manager
            cr_to_delete = db.get_cr_by_id(cr_id_to_delete)
            if not cr_to_delete:
                logging.error(f"Cannot delete CR-{cr_id_to_delete}: Not found.")
                return

            linked_id = cr_to_delete['linked_cr_id']
            other_cr_linking_to_this = db.get_cr_by_linked_id(cr_id_to_delete)

            if linked_id or other_cr_linking_to_this:
                logging.warning(f"CR-{cr_id_to_delete} is part of a linked pair. Awaiting PM confirmation for deletion.")
                self.task_awaiting_approval = {
                    "primary_cr_id": cr_id_to_delete,
                    "linked_cr_id": linked_id or other_cr_linking_to_this['cr_id']
                }
                self.set_phase("AWAITING_LINKED_DELETE_CONFIRMATION")
            else:
                db.delete_change_request(cr_id_to_delete)
                logging.info(f"Successfully deleted standalone CR ID: {cr_id_to_delete}.")

        except Exception as e:
            logging.error(f"Failed to process delete action for CR-{cr_id_to_delete}: {e}")

    def handle_linked_delete_confirmation(self, primary_cr_id: int, linked_cr_id: int):
        """
        Deletes a pair of linked CRs after PM confirmation.
        """
        logging.info(f"PM confirmed deletion of linked pair: CR-{primary_cr_id} and CR-{linked_cr_id}.")
        try:
            db = self.db_manager
            spec_cr = db.get_cr_by_id(linked_cr_id)
            if spec_cr and spec_cr['request_type'] == 'SPEC_CORRECTION':
                logging.warning(f"Spec Correction CR-{linked_cr_id} is being deleted. A full implementation would roll back the spec text.")

            db.delete_change_request(primary_cr_id)
            db.delete_change_request(linked_cr_id)

            logging.info("Successfully deleted linked CR pair.")
        except Exception as e:
            logging.error(f"Failed to delete linked CR pair: {e}")
        finally:
            self.task_awaiting_approval = None
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

    def save_edited_change_request(self, cr_id: int, new_data: dict) -> bool:
        """
        Saves the updated data for a specific change request. This is now called
        by the pop-up editor on the backlog page.
        """
        try:
            # The db_manager.update_change_request method is designed to take the dictionary
            self.db_manager.update_change_request(cr_id, new_data)
            logging.info(f"Successfully saved edits for item ID: {cr_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to save edited backlog item for ID {cr_id}: {e}")
            return False

    def add_new_backlog_item(self, data: dict) -> tuple[bool, int | None]:
        """
        Adds a new backlog item of any type, linking it to a parent.
        The parent_id is now read directly from the data dictionary.
        """
        try:
            parent_cr_id = data.get("parent_id")

            item_type_from_dialog = data.get("request_type")
            title = data.get("title")
            description = data.get("description")

            if not title and description:
                title = description.split('\n')[0]
                title = (title[:75] + '...') if len(title) > 75 else title

            if not title or not description:
                logging.warning("Cannot save item with empty title or description.")
                return False, None

            final_request_type = item_type_from_dialog
            status = ""

            if item_type_from_dialog == "BUG_REPORT":
                status = "BUG_RAISED"
            elif item_type_from_dialog == "CHANGE_REQUEST_ITEM":
                final_request_type = "BACKLOG_ITEM"
                status = "CHANGE_REQUEST"
            elif item_type_from_dialog == "BACKLOG_ITEM":
                status = "TO_DO"

            new_id = self.db_manager.add_change_request(
                project_id=self.project_id,
                title=title,
                description=description,
                request_type=final_request_type,
                status=status,
                priority=data.get("priority") or data.get("severity"),
                complexity=data.get("complexity"),
                parent_cr_id=parent_cr_id
            )

            logging.info(f"Successfully added new backlog item '{title}' (Type: {final_request_type}, Status: {status}, ID: {new_id}).")
            return True, new_id
        except Exception as e:
            logging.error(f"Failed to add new backlog item: {e}", exc_info=True)
            return False, None

    def delete_backlog_item(self, cr_id: int) -> bool:
        """
        Initiates the recursive deletion of a backlog item and all its descendants.
        """
        logging.info(f"Initiating deletion for CR ID: {cr_id} and its children.")
        try:
            self._recursive_delete_cr(cr_id)
            return True
        except Exception as e:
            logging.error(f"An error occurred during recursive deletion for root CR ID {cr_id}: {e}")
            return False

    def _recursive_delete_cr(self, cr_id: int):
        """Helper method to recursively delete a CR and its children."""
        children = self.db_manager.get_children_of_cr(cr_id)
        for child in children:
            self._recursive_delete_cr(child['cr_id'])

        # After all children are deleted, delete the parent
        self.db_manager.delete_change_request(cr_id)
        logging.debug(f"Deleted CR ID: {cr_id}")

    def get_active_cr_details_for_edit(self) -> dict | None:
        """
        Retrieves the full details for the CR currently marked for editing.
        """
        if self.active_cr_id_for_edit is None:
            logging.warning("Attempted to get details for edit, but no CR is active for editing.")
            return None

        try:
            cr_row = self.db_manager.get_cr_by_id(self.active_cr_id_for_edit)
            return dict(cr_row) if cr_row else None
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
        """
        if not self.project_id:
            logging.warning("Attempted to get change requests with no active project.")
            return []

        try:
            return self.db_manager.get_all_change_requests_for_project(self.project_id)
        except Exception as e:
            logging.error(f"Failed to retrieve change requests for project {self.project_id}: {e}")
            return []

    def get_cr_details_by_id(self, cr_id: int) -> dict | None:
        """
        Retrieves the full details for a single CR from the database.
        """
        if not self.project_id:
            logging.warning("Attempted to get CR details with no active project.")
            return None
        try:
            cr_row = self.db_manager.get_cr_by_id(cr_id)
            return dict(cr_row) if cr_row else None
        except Exception as e:
            logging.error(f"Failed to retrieve details for CR ID {cr_id}: {e}")
            return None

    def get_cr_and_bug_report_data(self, project_id: str, filter_type: str) -> list[dict]:
        """
        Fetches and consolidates data for the 'Change Requests & Bug Fixes' report.
        """
        report_data = []
        db = self.db_manager

        cr_pending_statuses = ["RAISED", "IMPACT_ANALYZED", "PLANNING_IN_PROGRESS", "IMPLEMENTATION_IN_PROGRESS"]
        cr_closed_statuses = ["COMPLETED", "CANCELLED"]
        bug_pending_statuses = ["UNIT_TESTS_FAILING", "DEBUG_IN_PROGRESS", "AWAITING_PM_TRIAGE_INPUT", "DEBUG_PM_ESCALATION", "KNOWN_ISSUE"]

        cr_statuses_to_query = []
        bug_statuses_to_query = []

        if filter_type == "Pending":
            cr_statuses_to_query = cr_pending_statuses
            bug_statuses_to_query = bug_pending_statuses
        elif filter_type == "Closed":
            cr_statuses_to_query = cr_closed_statuses
        elif filter_type == "All":
            cr_statuses_to_query = cr_pending_statuses + cr_closed_statuses
            bug_statuses_to_query = bug_pending_statuses

        if cr_statuses_to_query:
            change_requests = db.get_change_requests_by_statuses(project_id, cr_statuses_to_query)
            for cr in change_requests:
                report_data.append({
                    "id": f"CR-{cr['cr_id']}",
                    "type": "CR",
                    "status": cr['status'],
                    "description": cr['description']
                })

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

    def export_backlog_to_xlsx(self):
        """
        Fetches the full backlog hierarchy and calls the ReportGeneratorAgent
        to create an XLSX file in memory.

        Returns:
            A BytesIO object containing the XLSX file data, or None on failure.
        """
        logging.info("Orchestrating backlog export to XLSX format.")
        try:
            backlog_data = self.get_full_backlog_hierarchy()
            if not backlog_data:
                logging.warning("No backlog data found to export.")
                return None

            report_agent = ReportGeneratorAgent()
            return report_agent.generate_backlog_xlsx(backlog_data)
        except Exception as e:
            logging.error(f"Failed to orchestrate backlog export: {e}", exc_info=True)
            return None

    def export_sprint_plan_to_docx(self, sprint_items: list, plan_json_str: str):
        """
        Calls the ReportGeneratorAgent to create a DOCX file for the sprint plan.

        Args:
            sprint_items (list): The list of backlog items in the sprint scope.
            plan_json_str (str): The JSON string of the implementation plan.

        Returns:
            A BytesIO object containing the DOCX file data, or None on failure.
        """
        logging.info("Orchestrating sprint plan export to DOCX format.")
        try:
            plan_data = json.loads(plan_json_str)
            report_agent = ReportGeneratorAgent()
            return report_agent.generate_sprint_plan_docx(self.project_name, sprint_items, plan_data)
        except Exception as e:
            logging.error(f"Failed to orchestrate sprint plan export: {e}", exc_info=True)
            return None

    def export_pre_execution_report_to_docx(self, report_context: dict):
        """
        Calls the ReportGeneratorAgent to create a DOCX for the pre-execution report.

        Args:
            report_context (dict): The data stored in task_awaiting_approval,
                                containing selected items and the report.

        Returns:
            A BytesIO object containing the DOCX file data, or None on failure.
        """
        logging.info("Orchestrating pre-execution report export to DOCX format.")
        try:
            selected_items = report_context.get("selected_sprint_items", [])
            report_data = report_context.get("pre_execution_report", {})

            report_agent = ReportGeneratorAgent()
            return report_agent.generate_pre_execution_report_docx(
                self.project_name, selected_items, report_data
            )
        except Exception as e:
            logging.error(f"Failed to orchestrate pre-execution report export: {e}", exc_info=True)
            return None

    def handle_save_cr_order(self, order_mapping: list):
        """Handles the request to save the new display order for backlog items."""
        if not order_mapping:
            return
        try:
            self.db_manager.batch_update_cr_order(order_mapping)
            self.is_project_dirty = True
        except Exception as e:
            logging.error(f"Failed to save new CR order: {e}")
            # Optionally, signal back to the UI that there was an error

    def resume_project(self):
        """
        Resumes a paused project by loading its last saved detailed state and
        then clearing the saved state from the database.
        """
        if not self.resumable_state:
            logging.warning("Resume called but no resumable state was found. Defaulting to Backlog View.")
            self.set_phase(FactoryPhase.BACKLOG_VIEW.name)
            return

        try:
            # Set the current phase from the saved state FIRST.
            self.current_phase = FactoryPhase[self.resumable_state['current_phase']]

            state_details_json = self.resumable_state['state_details']
            if state_details_json:
                details = json.loads(state_details_json)
                self.active_plan = details.get("active_plan")
                self.active_plan_cursor = details.get("active_plan_cursor", 0)
                self.debug_attempt_counter = details.get("debug_attempt_counter", 0)
                self.task_awaiting_approval = details.get("task_awaiting_approval")
                self.active_spec_draft = details.get("active_spec_draft")

            logging.info(f"Project '{self.project_name}' resumed successfully to phase {self.current_phase.name}.")

            # Now that the state is loaded into the orchestrator, clear the DB record.
            self.db_manager.delete_orchestration_state_for_project(self.project_id)
            self.resumable_state = None # Clear the in-memory flag

        except Exception as e:
            logging.error(f"An error occurred while resuming project {self.project_id}: {e}")
            self.set_phase(FactoryPhase.BACKLOG_VIEW.name) # Fallback to backlog on error

    def resume_from_idle(self, project_id: str):
        """Resumes an active project that is not currently loaded."""
        if self.project_id:
            logging.warning("Resuming from idle, but a project is already active. This should not happen.")
            self.reset() # Reset to be safe

        project_details = self.db_manager.get_project_by_id(project_id)
        if not project_details:
            logging.error(f"Cannot resume project {project_id}: Not found in database.")
            return

        self.project_id = project_id
        self.project_name = project_details['project_name']
        self.project_root_path = project_details['project_root_folder']

        # Check for a paused session state for this project specifically
        self.resumable_state = self.db_manager.get_any_paused_state()
        if not (self.resumable_state and self.resumable_state['project_id'] == project_id):
            self.resumable_state = None # Clear state if it belongs to another project

        # Now call the main resume logic
        self.resume_project()

    def escalate_for_manual_debug(self, failure_log: str, is_functional_bug: bool = False):
        """
        Handles the escalation process for a task failure. It increments a
        counter, and if the maximum attempts are exceeded, it sets the phase
        to escalate to the PM.
        """
        logging.info("A failure has triggered the escalation pipeline.")

        # If this is a functional bug from UI testing, it's a direct escalation.
        if is_functional_bug:
            self.task_awaiting_approval = {"failure_log": failure_log}
            self.set_phase("DEBUG_PM_ESCALATION")
            return

        db = self.db_manager
        max_attempts = int(db.get_config_value("MAX_DEBUG_ATTEMPTS") or "2")

        self.debug_attempt_counter += 1
        logging.info(f"--- Automated Debug Attempt {self.debug_attempt_counter} of {max_attempts} ---")

        if self.debug_attempt_counter > max_attempts:
            logging.warning(f"All {max_attempts} automated debug attempts have failed. Escalating to PM.")

            original_failing_task = self.get_current_task_details()
            self.task_awaiting_approval = {
                "failure_log": failure_log,
                "original_failing_task": original_failing_task
            }
            self.debug_attempt_counter = 0 # Reset for the next issue
            self.set_phase("DEBUG_PM_ESCALATION")
        else:
            # If attempts are not exhausted, log it and remain in the GENESIS phase
            # to allow the user to trigger a retry, which will now house the fix-planning logic.
            logging.warning(f"Debug attempt {self.debug_attempt_counter} failed. Awaiting PM decision on escalation screen.")
            original_failing_task = self.get_current_task_details()
            self.task_awaiting_approval = {
                "failure_log": failure_log,
                "original_failing_task": original_failing_task
            }
            self.set_phase("DEBUG_PM_ESCALATION")

    def handle_pm_triage_input(self, pm_error_description: str):
        """
        Handles the text input provided by the PM during interactive triage (Tier 3).
        This version is refactored to use the central llm_service.
        """
        logging.info("Tier 3: Received manual error description from PM. Attempting to generate fix plan.")

        try:
            if not self.llm_service:
                raise Exception("Cannot proceed with triage: LLM Service is not configured.")

            # Use TriageAgent to refine the PM's description into a testable hypothesis.
            triage_agent = TriageAgent_AppTarget(llm_service=self.llm_service, db_manager=self.db_manager)
            hypothesis = triage_agent.analyze_and_hypothesize(
                error_logs=pm_error_description,
                relevant_code="No specific code context available; base analysis on user description.",
                test_report=""
            )

            if "An error occurred" in hypothesis:
                 raise Exception(f"TriageAgent failed to form a hypothesis: {hypothesis}")

            logging.info(f"TriageAgent formed hypothesis: {hypothesis}")

            # Use FixPlannerAgent to create a plan from the hypothesis.
            planner_agent = FixPlannerAgent_AppTarget(llm_service=self.llm_service)
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
        """
        logging.info(f"PM selected debug escalation option: {choice}")

        if choice == "RETRY":
            logging.info("PM chose to retry. The main window will now initiate the fix process.")
            pass

        elif choice == "MANUAL_PAUSE":
            self._pause_sprint_for_manual_fix()
            # The UI update will be handled by the main window after this method returns
            # and the orchestrator is reset.

        elif choice == "SKIP_TASK_AND_LOG":
            self._log_failure_as_bug_report_and_proceed()

    def _pause_sprint_for_manual_fix(self):
        """
        Saves the current sprint state and returns the UI to the idle screen,
        allowing the user to perform manual fixes before reloading the project.
        """
        logging.info("Pausing sprint for manual PM investigation.")
        from PySide6.QtWidgets import QMessageBox
        try:
            sprint_id = self.get_active_sprint_id()
            if sprint_id:
                # Mark the sprint as paused in the database
                self.db_manager.update_sprint_status_only(sprint_id, "PAUSED")

            # Save the entire orchestrator state (plan, cursor, etc.)
            self._save_current_state()
            QMessageBox.information(
                None,
                "Sprint Paused",
                "The sprint has been paused and its state has been saved. The project will now be closed.\n\n"
                "After making your manual fixes, please reload the project from the 'Load Exported Project' screen to continue."
            )
        except Exception as e:
            logging.error(f"Failed to properly pause sprint: {e}", exc_info=True)
            QMessageBox.critical(None, "Error", f"Failed to save sprint state for pausing: {e}")
        finally:
            # Return the application to the idle state
            self.reset()

    def handle_retry_fix_action(self, failure_log: str, progress_callback=None):
        """
        Handles the PM's choice to retry an automated fix. This is designed
        to be run in a background thread. It generates a plan and then immediately
        executes it as a single, continuous operation.
        """
        try:
            if progress_callback:
                progress_callback(("INFO", "PM chose to retry. Attempting to generate a new automated fix plan..."))

            from agents.agent_triage_app_target import TriageAgent_AppTarget
            triage_agent = TriageAgent_AppTarget(llm_service=self.llm_service, db_manager=self.db_manager)
            hypothesis = triage_agent.analyze_and_hypothesize(failure_log, "")

            if not (hypothesis and not hypothesis.startswith("Error:")):
                raise Exception("The Triage Agent could not form a hypothesis to create a fix plan.")

            if progress_callback: progress_callback(("INFO", f"Triage hypothesis: {hypothesis}"))

            if not self._plan_and_execute_fix(hypothesis, {}):
                raise Exception("The AI was unable to generate a valid new fix plan after a manual retry.")

            if progress_callback: progress_callback(("SUCCESS", "Successfully generated a new fix plan. Now executing..."))

            # Now, execute the newly created fix plan in a loop
            while self.is_in_fix_mode and self.fix_plan and self.fix_plan_cursor < len(self.fix_plan):
                # This block is derived from the main handle_proceed_action logic
                task = self.fix_plan[self.fix_plan_cursor]
                component_name = task.get('component_name', 'Unnamed Fix Task')
                if progress_callback:
                    progress_callback(("INFO", f"Executing FIX task {self.fix_plan_cursor + 1}/{len(self.fix_plan)} for: {component_name}"))

                db = self.db_manager
                project_details = db.get_project_by_id(self.project_id)
                project_root_path = Path(project_details['project_root_folder'])

                self._execute_source_code_generation_task(task, project_root_path, db, progress_callback)
                self.fix_plan_cursor += 1

            logging.info("Automated fix plan executed successfully.")
            # Reset flags and re-attempt the original task to confirm the fix
            self.is_in_fix_mode = False
            self.fix_plan = None
            self.fix_plan_cursor = 0
            return self.handle_proceed_action(progress_callback=progress_callback)

        except Exception as e:
            logging.error(f"Failed during retry action: {e}", exc_info=True)
            self.escalate_for_manual_debug(str(e))
            raise # Re-raise to be caught by the worker's error handler

    def run_full_test_suite(self, progress_callback=None):
        """
        Triggers a full run of the project's automated test suite.

        Returns:
            A tuple (success: bool, output: str) with the test results.
        """
        if not self.project_id:
            raise Exception("Cannot run tests: No active project.")

        db = self.db_manager
        project_details = db.get_project_by_id(self.project_id)
        if not project_details:
            raise Exception("Cannot run tests: Project details not found.")

        project_root = project_details['project_root_folder']
        test_command = project_details['test_execution_command']

        # This new line retrieves the required setting
        version_control_enabled = project_details['version_control_enabled'] == 1

        if not project_root or not test_command:
            raise Exception("Cannot run tests: Project root or test command is not configured.")

        if progress_callback:
            progress_callback(("INFO", f"Executing test command: '{test_command}'..."))

        # The agent constructor is now called with the required second argument
        agent = BuildAndCommitAgentAppTarget(project_root, version_control_enabled)
        success, output = agent.run_test_suite_only(test_command)

        if progress_callback:
            progress_callback(("SUCCESS", "Test run complete."))

        return success, output

    def _run_final_sprint_verification(self, progress_callback=None):
        """
        Runs the full project test suite as a final quality gate for the sprint.
        Transitions to SPRINT_REVIEW on success or escalates on failure with new options.
        """
        logging.info("Sprint plan complete. Running mandatory final regression test suite...")
        if progress_callback:
            progress_callback(("INFO", "Running mandatory final regression test suite..."))

        try:
            success, output = self.run_full_test_suite(progress_callback)
            if success:
                logging.info("Final regression test suite PASSED. Proceeding to Sprint Review.")
                if progress_callback:
                    progress_callback(("SUCCESS", "All tests passed."))
                self.sprint_completed_with_failures = False
                self.set_phase("SPRINT_REVIEW")
            else:
                logging.error("Final regression test suite FAILED. Escalating to PM with options.")
                if progress_callback:
                    progress_callback(("ERROR", f"Regression test failed:\n{output}"))

                # This is the new logic to enable the flexible completion workflow
                self.task_awaiting_approval = {
                    "failure_log": f"A regression failure was detected during final sprint verification.\n\n--- TEST OUTPUT ---\n{output}",
                    "is_final_verification_failure": True # Flag to show the new option in the UI
                }
                self.set_phase("DEBUG_PM_ESCALATION")
        except Exception as e:
            logging.error(f"An unexpected error occurred during final sprint verification: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred during the final regression test run:\n{e}")

    def handle_complete_with_failures(self):
        """
        Handles the PM's choice to complete a sprint while acknowledging
        final verification test failures. It auto-creates bug reports
        for the failures and then proceeds with normal sprint completion.
        """
        logging.warning("PM acknowledged final test failures. Logging failures as bugs and completing sprint.")
        try:
            task_details = self.task_awaiting_approval or {}
            failure_log = task_details.get("failure_log", "No failure details provided.")
            sprint_id = self.get_active_sprint_id()
            if not sprint_id:
                raise ValueError("Cannot log failures; no active sprint ID found.")

            # For simplicity, create one bug report for the entire regression failure.
            new_bug_id = self.db_manager.add_change_request(
                project_id=self.project_id,
                title="Fix regression failure from sprint " + sprint_id,
                description=f"**Objective for Impact Analysis:** This is an auto-generated bug report for a regression failure detected during the final verification of sprint `{sprint_id}`.\n\n--- FAILURE LOG ---\n```\n{failure_log}\n```",
                request_type='BUG_REPORT',
                status='BUG_RAISED',
                priority='High'
            )
            logging.info(f"Successfully logged regression failure as BUG-{new_bug_id}.")

            self.sprint_completed_with_failures = True
            # Now, proceed with the standard sprint review
            self.set_phase("SPRINT_REVIEW")
        except Exception as e:
            logging.error(f"Critical error in handle_complete_with_failures: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred while logging failures: {e}")

    def handle_generate_technical_preview(self, cr_id: int) -> str:
        """
        Orchestrates the generation of a technical preview for a specific CR.
        This is designed to be called from a background worker.

        Returns:
            A string containing the Markdown summary of the preview, or an error message.
        """
        logging.info(f"Orchestrator: Generating technical preview for CR ID: {cr_id}.")
        try:
            if not self.project_id:
                raise Exception("Cannot generate preview; no active project.")
            if not self.llm_service:
                raise Exception("Cannot generate preview: LLM Service is not configured.")

            db = self.db_manager
            cr_details = db.get_cr_by_id(cr_id)
            project_details = db.get_project_by_id(self.project_id)
            all_artifacts = db.get_all_artifacts_for_project(self.project_id)

            if not cr_details or not project_details:
                raise Exception(f"Could not retrieve details for CR-{cr_id} or project.")

            rowd_json = json.dumps([dict(row) for row in all_artifacts], indent=2)

            agent = ImpactAnalysisAgent_AppTarget(llm_service=self.llm_service)
            preview_summary = agent.generate_technical_preview(
                change_request_desc=cr_details['description'],
                final_spec_text=project_details['final_spec_text'],
                rowd_json=rowd_json
            )

            # The summary is returned directly to the worker, not saved here.
            return preview_summary

        except Exception as e:
            error_msg = f"Failed to generate technical preview for CR-{cr_id}: {e}"
            logging.error(error_msg, exc_info=True)
            return f"### Error\n{error_msg}"

    def initiate_sprint_planning(self, selected_cr_ids: list, **kwargs):
        """
        Prepares the context for the SPRINT_PLANNING phase.
        This is called by the UI when the 'Plan Sprint' button is clicked.
        """
        logging.info(f"Initiating sprint planning for {len(selected_cr_ids)} items.")
        try:
            full_backlog_with_ids = self._get_backlog_with_hierarchical_numbers()

            # Create a flat map for easy lookup of the enriched data
            flat_backlog = {}
            def flatten_hierarchy(items):
                for item in items:
                    flat_backlog[item['cr_id']] = item
                    if "features" in item:
                        flatten_hierarchy(item["features"])
                    if "user_stories" in item:
                        flatten_hierarchy(item["user_stories"])
            flatten_hierarchy(full_backlog_with_ids)

            # Get the full data for the selected items
            selected_items = [flat_backlog[cr_id] for cr_id in selected_cr_ids if cr_id in flat_backlog]

            self.task_awaiting_approval = {
                "selected_sprint_items": selected_items
            }
            self.set_phase("SPRINT_PLANNING")
        except Exception as e:
            logging.error(f"Failed during sprint initiation: {e}", exc_info=True)
            self.set_phase("BACKLOG_VIEW") # Go back on error
            self.task_awaiting_approval = {"error": str(e)}

    def handle_start_sprint(self, sprint_items: list, **kwargs):
        """
        Finalizes sprint planning by creating a persistent sprint record,
        linking items to it, updating statuses, and transitioning to GENESIS.
        """
        logging.info(f"Starting sprint with {len(sprint_items)} items.")
        sprint_id = None  # Initialize sprint_id to None for the except block
        try:
            if not self.task_awaiting_approval or "sprint_plan_json" not in self.task_awaiting_approval:
                raise ValueError("Cannot start sprint: No implementation plan was generated or cached.")

            plan_json_str = self.task_awaiting_approval.pop("sprint_plan_json")
            self.active_plan = json.loads(plan_json_str)
            self.active_plan_cursor = 0
            self.is_executing_cr_plan = True

            sprint_id = f"sprint_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            self.active_sprint_id = sprint_id

            cr_ids_to_update = [item['cr_id'] for item in sprint_items]

            self.db_manager.create_sprint(self.project_id, sprint_id, plan_json_str)
            self.db_manager.link_items_to_sprint(sprint_id, cr_ids_to_update)
            self.db_manager.batch_update_cr_status(cr_ids_to_update, "IMPLEMENTATION_IN_PROGRESS")

            self.set_phase("GENESIS")
            logging.info(f"Sprint '{sprint_id}' started. Transitioning to GENESIS.")
        except Exception as e:
            logging.error(f"Failed to start sprint '{sprint_id}': {e}", exc_info=True)
            # Rollback partial sprint creation on failure
            if sprint_id:
                logging.warning(f"Rolling back failed sprint creation for sprint {sprint_id}.")
                self.db_manager.delete_sprint_links(sprint_id)
                self.db_manager.delete_sprint(sprint_id)
            self.active_sprint_id = None
            self.set_phase("SPRINT_PLANNING")
            self.task_awaiting_approval = {"selected_sprint_items": sprint_items, "error": str(e)}

    def handle_sprint_review_complete(self, **kwargs):
        """
        Handles the user's action to complete the sprint review, updates the
        status of completed items, and returns to the backlog.
        """
        logging.info("Sprint review complete. Finalizing sprint.")
        try:
            sprint_id = self.get_active_sprint_id()
            if not sprint_id: return

            items_in_sprint = self.db_manager.get_items_for_sprint(sprint_id)
            if items_in_sprint:
                # Only mark items as COMPLETED if they were still in progress.
                # This prevents overwriting a BLOCKED status.
                completed_ids = [item['cr_id'] for item in items_in_sprint if item['status'] == 'IMPLEMENTATION_IN_PROGRESS']
                if completed_ids:
                    self.db_manager.batch_update_cr_status(completed_ids, "COMPLETED")

            self.db_manager.update_sprint_status(sprint_id, "COMPLETED")
        except Exception as e:
            logging.error(f"Failed to update sprint statuses: {e}")
        finally:
            # Clear out the completed plan details
            self.active_plan = None
            self.active_plan_cursor = 0
            self.is_executing_cr_plan = False
            self.active_sprint_id = None
            self.task_awaiting_approval = {} # Clear any leftover task data
            self.set_phase("BACKLOG_VIEW")

    def handle_acknowledge_technical_preview(self, cr_id: int, preview_text: str):
        """
        Saves the acknowledged technical preview to the database and updates the
        CR status to indicate it is ready for sprint planning.
        """
        logging.info(f"Orchestrator: Acknowledging and saving technical preview for CR ID: {cr_id}.")
        try:
            self.db_manager.update_cr_technical_preview(cr_id, preview_text)
            self.is_project_dirty = True
        except Exception as e:
            logging.error(f"Failed to acknowledge technical preview for CR-{cr_id}: {e}", exc_info=True)
            # For now, logging is sufficient. We can add more robust UI error feedback later if needed.

    def run_full_analysis(self, cr_id: int, **kwargs):
        """
        Orchestrates a full analysis (impact + technical) for a CR item.
        Updates the database with all results and sets status to IMPACT_ANALYZED.
        """
        logging.info(f"Orchestrator: Running full analysis for CR ID: {cr_id}.")
        db = self.db_manager
        # Inside the run_full_analysis method...
        try:
            if not self.project_id:
                raise Exception("Cannot run analysis; no active project.")
            if not self.llm_service:
                raise Exception("Cannot run analysis: LLM Service is not configured.")

            # Get all necessary context for the analysis
            cr_details = db.get_cr_by_id(cr_id)
            project_details = db.get_project_by_id(self.project_id)
            all_artifacts = db.get_all_artifacts_for_project(self.project_id)

            if not cr_details or not project_details:
                raise Exception(f"Could not retrieve details for CR-{cr_id} or project.")

            rowd_json = json.dumps([dict(row) for row in all_artifacts], indent=2)
            agent = ImpactAnalysisAgent_AppTarget(llm_service=self.llm_service)

            # --- Reverted to Single, Robust Call ---
            analysis_result = agent.run_full_analysis(
                change_request_desc=cr_details['description'],
                final_spec_text=project_details['final_spec_text'],
                rowd_json=rowd_json
            )

            if not analysis_result:
                raise Exception("Analysis agent returned no result.")
            # --- End of Change ---

            # Use the single database method with the result
            db.update_cr_full_analysis(
                cr_id=cr_id,
                rating=analysis_result.get("impact_rating"),
                details=analysis_result.get("impact_summary"),
                artifact_ids=analysis_result.get("impacted_artifact_ids", []),
                preview_text=analysis_result.get("technical_preview")
            )
            logging.info(f"Successfully ran and saved full analysis for CR ID: {cr_id}. Status set to IMPACT_ANALYZED.")

        except Exception as e:
            error_msg = f"Failed to run full analysis for CR-{cr_id}: {e}"
            logging.error(error_msg, exc_info=True)
            # The status is not changed if the process fails, allowing the user to retry.
            raise  # Re-raise the exception to be caught by the UI worker handler

    def generate_sprint_implementation_plan(self, sprint_items: list) -> str:
        """
        Builds a context package for a set of sprint items and then generates a
        detailed, step-by-step implementation plan by calling the planning agent.
        This version includes parent cr_ids for traceability.
        """
        logging.info(f"Generating implementation plan for {len(sprint_items)} sprint items.")
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            project_root_path = Path(project_details['project_root_folder'])

            all_impacted_ids = set()
            analysis_agent = ImpactAnalysisAgent_AppTarget(llm_service=self.llm_service)
            all_artifacts_for_analysis = db.get_all_artifacts_for_project(self.project_id)
            rowd_json_for_analysis = json.dumps([dict(row) for row in all_artifacts_for_analysis])
            description_parts = []

            for item in sprint_items:
                description_parts.append(f"ITEM_ID: {item['cr_id']}\nTITLE: {item['title']}\nDESCRIPTION: {item['description']}\n")
                if item.get('status') == 'IMPACT_ANALYZED':
                    impacted_ids = json.loads(item.get('impacted_artifact_ids') or '[]')
                else:
                    analysis_result = analysis_agent.run_full_analysis(
                        change_request_desc=item['description'],
                        final_spec_text=project_details['final_spec_text'],
                        rowd_json=rowd_json_for_analysis
                    )
                    impacted_ids = analysis_result.get("impacted_artifact_ids", []) if analysis_result else []

                for artifact_id in impacted_ids:
                    all_impacted_ids.add(artifact_id)

            combined_description = "\n---\n".join(description_parts)

            source_code_files = {}
            for artifact_id in all_impacted_ids:
                artifact_record = db.get_artifact_by_id(artifact_id)
                if artifact_record and artifact_record['file_path']:
                    source_path = project_root_path / artifact_record['file_path']
                    if source_path.exists():
                        source_code_files[artifact_record['file_path']] = source_path.read_text(encoding='utf-8')

            core_docs = {"final_spec_text": project_details['final_spec_text']}
            self.context_package_summary = self._build_and_validate_context_package(core_docs, source_code_files)
            if self.context_package_summary.get("error"):
                raise Exception(f"Context Builder Error: {self.context_package_summary['error']}")

            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            rowd_json = json.dumps([dict(row) for row in all_artifacts])

            planner_agent = RefactoringPlannerAgent_AppTarget(llm_service=self.llm_service)
            new_plan_str = planner_agent.create_refactoring_plan(
                change_request_desc=combined_description,
                final_spec_text=project_details['final_spec_text'],
                tech_spec_text=project_details['tech_spec_text'],
                rowd_json=rowd_json,
                source_code_context=self.context_package_summary["source_code"]
            )

            response_data = json.loads(new_plan_str)
            if isinstance(response_data, list) and len(response_data) > 0 and response_data[0].get("error"):
                raise Exception(f"Planning agent failed: {response_data[0]['error']}")

            logging.info("Successfully generated sprint implementation plan.")
            return new_plan_str

        except Exception as e:
            logging.error(f"Failed to generate sprint implementation plan: {e}", exc_info=True)
            return json.dumps([{"error": f"Failed to generate plan: {e}"}])

    def run_sprint_plan_audit(self, audit_type: str, plan_json: str, **kwargs):
        """
        Orchestrates running a specific audit on a sprint implementation plan.

        Args:
            audit_type (str): The type of audit to run (e.g., "Security").
            plan_json (str): The JSON string of the implementation plan.

        Returns:
            A string containing the Markdown-formatted audit report.
        """
        logging.info(f"Orchestrator: Running '{audit_type}' audit on sprint plan.")
        try:
            if not self.project_id:
                raise Exception("Cannot run audit; no active project.")
            if not self.llm_service:
                raise Exception("Cannot run audit: LLM Service is not configured.")

            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details:
                raise Exception(f"Could not retrieve project details for audit.")

            tech_spec_text = project_details['tech_spec_text'] if project_details and project_details['tech_spec_text'] else ''

            agent = PlanAuditorAgent(llm_service=self.llm_service)
            audit_report = agent.run_audit(
                audit_type=audit_type,
                plan_json=plan_json,
                tech_spec=tech_spec_text
            )
            return audit_report

        except Exception as e:
            error_msg = f"Failed to run sprint plan audit for type '{audit_type}': {e}"
            logging.error(error_msg, exc_info=True)
            return f"### Error\n{error_msg}"

    def refine_sprint_implementation_plan(self, current_plan_json: str, pm_feedback: str, sprint_items: list) -> str:
        """
        Orchestrates the refinement of an existing sprint implementation plan,
        ensuring parent item context is passed to the agent for traceability.
        """
        logging.info("Orchestrator: Refining sprint implementation plan based on PM feedback.")
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            rowd_json = json.dumps([dict(row) for row in all_artifacts])
            # Re-create the structured description for context ---
            description_parts = []
            for item in sprint_items:
                description_parts.append(f"ITEM_ID: {item['cr_id']}\nTITLE: {item['title']}\nDESCRIPTION: {item['description']}\n")
            combined_description = "\n---\n".join(description_parts)

            agent = RefactoringPlannerAgent_AppTarget(llm_service=self.llm_service)
            refined_plan_json = agent.refine_refactoring_plan(
                current_plan_json=current_plan_json,
                pm_feedback=pm_feedback,
                change_request_desc=combined_description, # Pass the rich context
                tech_spec_text=project_details['tech_spec_text'],
                rowd_json=rowd_json
            )
            return refined_plan_json
        except Exception as e:
            error_msg = f"Failed to refine sprint plan: {e}"
            logging.error(error_msg, exc_info=True)
            return json.dumps([{"error": error_msg}])

    def prepend_standard_header(self, document_content: str, document_type: str) -> str:
        """
        Prepends a standard project header, including a version number
        and the current date, to a given document.
        """
        if not self.project_id:
            return document_content

        version_number = "1.0"
        match = re.search(r'(?:v|Version\s|Version number:\s)(\d+\.\d+)', document_content, re.IGNORECASE)
        if match:
            version_number = match.group(1)

        # Get the current date in YYYY-MM-DD format
        current_date = datetime.now().strftime('%x')

        header = (
            f"PROJECT NUMBER: {self.project_id}\n"
            f"{document_type.upper()}\n"
            f"Date: {current_date}\n"
            f"Version number: {version_number}\n"
            f"{'-' * 50}\n\n"
        )
        return header + document_content

    def _commit_document(self, file_path: Path, commit_message: str):
        """A helper method to stage and commit a single document, but only if version control is enabled."""
        if not self.project_id:
            return
        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                logging.error(f"Cannot commit {file_path.name}: project root folder not found.")
                return

            # --- THIS IS THE FIX ---
            # Check if version control is enabled before attempting any git operations.
            version_control_enabled = project_details['version_control_enabled'] == 1 if project_details else True
            if not version_control_enabled:
                logging.info(f"Skipping commit for {file_path.name}; version control is disabled for this project.")
                return
            # --- END OF FIX ---

            project_root = Path(project_details['project_root_folder'])
            repo = git.Repo(project_root)

            relative_path = file_path.relative_to(project_root)
            repo.index.add([str(relative_path)])
            repo.index.commit(commit_message)
            logging.info(f"Successfully committed document: {relative_path}")
        except Exception as e:
            logging.error(f"Failed to commit document {file_path.name}. Error: {e}")

    def _save_debug_log_and_get_path(self, failure_log: str, original_failing_task: dict) -> str | None:
        """
        Saves detailed failure information to a version-controlled Markdown file.

        Args:
            failure_log (str): The raw error log from the failure.
            original_failing_task (dict): The task object that failed.

        Returns:
            The relative path to the new log file, or None on failure.
        """
        if not self.project_id:
            return None
        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            project_root = Path(project_details['project_root_folder'])
            debug_logs_dir = project_root / "docs" / "debug_logs"
            debug_logs_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            task_name = original_failing_task.get('task', {}).get('component_name', 'UnknownTask')
            safe_task_name = re.sub(r'[^a-zA-Z0-9_-]', '', task_name)
            log_filename = f"debug_history_{safe_task_name}_{timestamp}.md"
            log_filepath = debug_logs_dir / log_filename

            # Format the content for the log file
            log_content = textwrap.dedent(f"""
                # Debug Log: {self.project_name}
                **Timestamp:** {datetime.now(timezone.utc).isoformat()}
                **Project ID:** {self.project_id}
                **Failed Task:** {task_name}

                ## Original Task Micro-Specification
                ```json
                {json.dumps(original_failing_task.get('task', {}), indent=2)}
                ```

                ## Failure Log
                ```
                {failure_log}
                ```
            """)

            log_filepath.write_text(log_content, encoding='utf-8')

            # Commit the new log file to version control
            relative_path = log_filepath.relative_to(project_root)
            self._commit_document(log_filepath, f"docs: Add debug log for failed task {task_name}")

            return str(relative_path)
        except Exception as e:
            logging.error(f"Failed to save debug log: {e}", exc_info=True)
            return None

    def _log_failure_as_bug_report_and_proceed(self):
        """
        Logs a failed task as a new BUG_REPORT, blocks the parent backlog
        item(s), and allows the sprint to continue with the next task.
        """
        logging.warning("Task failed. Logging as bug and continuing sprint.")
        try:
            task_details = self.task_awaiting_approval or {}
            failure_log = task_details.get("failure_log", "No details provided.")
            original_failing_task = task_details.get('original_failing_task', {})
            if not original_failing_task:
                raise ValueError("Could not find the original failing task context.")

            # 1. Save the detailed debug log and get its path
            log_file_path = self._save_debug_log_and_get_path(failure_log, original_failing_task)
            log_path_for_desc = log_file_path if log_file_path else "Not available."

            # 2. Identify parent backlog items from the task's traceability info
            parent_cr_ids = original_failing_task.get('task', {}).get('parent_cr_ids', [])
            if not parent_cr_ids:
                logging.error("Traceability Error: Cannot log bug as parent CR IDs were not found in the failed task. Aborting sprint.")
                self.escalate_for_manual_debug("Traceability link missing in failed task.")
                return

            # 3. Block parent items
            self.db_manager.batch_update_cr_status(parent_cr_ids, "BLOCKED")

            # --- START FIX: Look up user-facing hierarchical IDs ---
            full_backlog_with_ids = self._get_backlog_with_hierarchical_numbers()
            flat_backlog_map = {}
            def flatten_hierarchy(items):
                for item in items:
                    flat_backlog_map[item['cr_id']] = item
                    if "features" in item: flatten_hierarchy(item["features"])
                    if "user_stories" in item: flatten_hierarchy(item["user_stories"])
            flatten_hierarchy(full_backlog_with_ids)

            parent_hierarchical_ids = [
                flat_backlog_map.get(pid, {}).get('hierarchical_id', f'CR-{pid}')
                for pid in parent_cr_ids
            ]
            parent_ids_str = ', '.join(parent_hierarchical_ids)
            # --- END FIX ---

            # 4. Create and link the new bug report with the correct parent ID format
            task_name = original_failing_task.get('task', {}).get('component_name', 'Unknown Task')
            description = (
                f"**Objective for Impact Analysis:** This is an auto-generated bug report for a failed sprint task. "
                f"This bug is blocking the completion of parent item(s): {parent_ids_str}.\n\n"
                f"--- ORIGINAL TASK ---\n"
                f"```json\n{json.dumps(original_failing_task.get('task', {}), indent=2)}\n```\n\n"
                f"--- FAILURE LOG ---\n"
                f"```\n{failure_log}\n```\n\n"
                f"**Full Debug Log Path:** `{log_path_for_desc}`"
            )

            bug_data = {
                "request_type": "BUG_REPORT",
                "title": f"Fix failed sprint task: {task_name}",
                "description": description,
                "severity": "High",
                "parent_id": parent_cr_ids[0]
            }
            success, new_bug_id = self.add_new_backlog_item(bug_data)
            if not success:
                raise Exception(f"Failed to create new BUG_REPORT item in the database for task: {task_name}")

            # 5. Advance the plan and resume the sprint
            self.active_plan_cursor += 1
            self.task_awaiting_approval = None
            self.set_phase("GENESIS")
            logging.info(f"Successfully logged failure for '{task_name}' as BUG-{new_bug_id}. Sprint will continue.")
        except Exception as e:
            logging.error(f"Critical error in _log_failure_as_bug_report_and_proceed: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred while trying to log a bug and continue the sprint: {e}")

    def _save_current_state(self):
        """
        Saves the currently active project's detailed operational state to the
        database. This is called automatically on phase transitions.
        """
        if not self.project_id:
            return

        try:
            db = self.db_manager
            db.delete_orchestration_state_for_project(self.project_id)

            state_details_dict = {
                "active_plan": self.active_plan,
                "active_plan_cursor": self.active_plan_cursor,
                "debug_attempt_counter": self.debug_attempt_counter,
                "task_awaiting_approval": self.task_awaiting_approval,
                "active_spec_draft": self.active_spec_draft
            }
            state_details_json = json.dumps(state_details_dict)

            # --- ADD THIS LINE ---
            logging.info(f"DEBUG: Attempting to save state for phase: {self.current_phase.name}")
            # --- END OF ADDITION ---

            db.save_orchestration_state(
                project_id=self.project_id,
                current_phase=self.current_phase.name,
                current_step="auto_saved_state",
                state_details=state_details_json,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            logging.info(f"Project '{self.project_name}' state automatically saved.")

        except Exception as e:
            logging.error(f"Failed to auto-save state for project {self.project_id}: {e}")

    def pause_project(self):
        """
        Saves the project's current session state and resets the orchestrator to idle.
        This is the core of the non-destructive 'Close' operation.
        """
        logging.info("PM initiated Pause Project. Saving state and closing...")
        if not self.project_id:
            logging.warning("Pause project called, but no active project was found.")
            return

        try:
            self._save_current_state()
            self.reset()
        except Exception as e:
            logging.error(f"Failed to cleanly pause project {self.project_id}: {e}", exc_info=True)
            self.reset()

    def _clear_active_project_data(self, db, project_id: str):
        """Helper method to clear all data for a specific project."""
        if not project_id:
            return
        db.delete_all_artifacts_for_project(project_id)
        db.delete_all_change_requests_for_project(project_id)
        db.delete_orchestration_state_for_project(project_id)
        db.delete_project_by_id(project_id)
        logging.info(f"Cleared all active data for project ID: {project_id}")

    def _create_project_archive_and_history_record(self, override_cr_data=None):
        """
        A reusable helper method that exports the current project DB state to
        archive files and creates a corresponding history record.
        It can now accept an override for the CR data for in-memory states.
        """
        if not self.project_id:
            return

        db = self.db_manager

        archive_path_str = db.get_config_value("DEFAULT_ARCHIVE_PATH")
        if not archive_path_str:
            logging.error("Cannot create project archive: DEFAULT_ARCHIVE_PATH is not set in settings.")
            return

        archive_dir = Path(archive_path_str)
        archive_name = f"{self.project_name.replace(' ', '_')}_{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

        archive_dir.mkdir(parents=True, exist_ok=True)
        rowd_file = archive_dir / f"{archive_name}_rowd.json"
        cr_file = archive_dir / f"{archive_name}_cr.json"
        project_file = archive_dir / f"{archive_name}_project.json"

        try:
            artifacts = db.get_all_artifacts_for_project(self.project_id)
            project_details_row = db.get_project_by_id(self.project_id)

            # --- START FIX: Use override data if provided ---
            if override_cr_data is not None:
                cr_list = override_cr_data
                logging.info("Archiving with override CR data from in-memory state.")
            else:
                change_requests = db.get_all_change_requests_for_project(self.project_id)
                cr_list = [dict(row) for row in change_requests]
            # --- END FIX ---

            artifacts_list = [dict(row) for row in artifacts]
            with open(rowd_file, 'w', encoding='utf-8') as f:
                json.dump(artifacts_list, f, indent=4)

            with open(cr_file, 'w', encoding='utf-8') as f:
                json.dump(cr_list, f, indent=4)

            if project_details_row:
                project_details_dict = dict(project_details_row)
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump(project_details_dict, f, indent=4)

            root_folder_path = project_details_row['project_root_folder'] if project_details_row else "N/A"

            db.add_project_to_history(
                project_id=self.project_id,
                project_name=self.project_name,
                root_folder=root_folder_path,
                archive_path=str(rowd_file),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            logging.info(f"Successfully created archive and history record for '{self.project_name}'.")
        except Exception as e:
            logging.error(f"Failed during project archive and history creation: {e}", exc_info=True)

    def _clear_active_project_data(self, db, project_id: str):
        """Helper method to clear all data for a specific project."""
        if not project_id:
            return
        db.delete_all_artifacts_for_project(project_id)
        db.delete_all_change_requests_for_project(project_id)
        db.delete_orchestration_state_for_project(project_id)
        db.delete_project_by_id(project_id)
        logging.info(f"Cleared all active data for project ID: {project_id}")

    def stop_and_export_project(self, **kwargs):
        """
        Aborts the current sprint by reverting in-progress items, creates a
        final project archive, and resets the application.
        """
        if not self.project_id:
            logging.warning("No active project to stop and export.")
            return

        db = self.db_manager
        try:
            # This is the unique action for this method: revert in-progress items.
            in_progress_items = db.get_change_requests_by_statuses(
                self.project_id, ["IMPLEMENTATION_IN_PROGRESS"]
            )
            if in_progress_items:
                item_ids = [item['cr_id'] for item in in_progress_items]
                db.batch_update_cr_status(item_ids, "TO_DO")
                logging.info(f"Reverted {len(item_ids)} in-progress items back to 'TO_DO' for clean archive.")

            # Now, call the shared helper to do the archiving and history creation.
            self._create_project_archive_and_history_record()

            # Final cleanup
            self._clear_active_project_data(db, self.project_id)
            self.reset()
        except Exception as e:
            logging.error(f"Failed to stop and export project: {e}", exc_info=True)

    def _perform_preflight_checks(self, project_root_str: str, project_id: str) -> dict:
        """
        Performs a sequence of pre-flight checks on an existing project environment.
        This version now also reports if a development plan is active.
        """
        import os
        import subprocess
        import git
        project_root = Path(project_root_str)
        has_active_plan = self.active_plan is not None

        # 1. Path Validation
        if not project_root.exists() or not project_root.is_dir():
            return {"status": "PATH_NOT_FOUND", "message": f"The project folder could not be found or is not a directory. Please confirm the new location: {project_root_str}", "has_active_plan": has_active_plan}

        project_details = self.db_manager.get_project_by_id(project_id)
        version_control_enabled = project_details['version_control_enabled'] == 1 if project_details else True

        # 2. VCS Validation (Only if enabled for this project)
        if version_control_enabled:
            if not (project_root / '.git').is_dir():
                return {"status": "GIT_MISSING", "message": "The project folder was found, but the .git directory is missing. Version control is enabled for this project.", "has_active_plan": has_active_plan}
            try:
                repo = git.Repo(project_root)
            except git.InvalidGitRepositoryError:
                return {"status": "GIT_MISSING", "message": "The project folder is not a valid Git repository (GitPython check failed).", "has_active_plan": has_active_plan}

            if repo.is_dirty(untracked_files=True):
                return {"status": "STATE_DRIFT", "message": "Uncommitted local changes have been detected. To prevent conflicts, please resolve the state of the repository.", "has_active_plan": has_active_plan}

        # All checks passed
        return {"status": "ALL_PASS", "message": "Project environment successfully verified.", "vcs_enabled": version_control_enabled, "has_active_plan": has_active_plan}

    def handle_discard_changes(self, history_id: int):
        """
        Handles the 'Discard all local changes' option by resetting the git
        repository and then re-running the pre-flight check.
        """
        logging.warning(f"Executing 'git reset --hard' for project history ID: {history_id}")
        try:
            db = self.db_manager
            history_record = db.get_project_history_by_id(history_id)
            if not history_record:
                raise Exception(f"Could not find history record for ID {history_id} to get path.")

            project_root = Path(history_record['project_root_folder'])
            project_id = history_record['project_id'] # Get the project_id for the check

            agent = RollbackAgent()
            success, message = agent.discard_local_changes(project_root)

            if not success:
                raise Exception(f"RollbackAgent failed: {message}")

            logging.info(f"Successfully discarded changes at {project_root}")

            # After discarding, re-run the check and update the state. DO NOT reload the project.
            check_result = self._perform_preflight_checks(str(project_root), project_id)
            self.preflight_check_result = {**check_result, "history_id": history_id}

        except Exception as e:
            logging.error(f"Failed to discard changes for project history ID {history_id}: {e}")
            self.preflight_check_result = {"status": "ERROR", "message": str(e), "history_id": history_id}

    def handle_continue_with_uncommitted_changes(self, completed_task_ids: list):
        """
        Handles the 'Continue Project' action by committing all changes, and then
        creating RoWD records for each task the user selected as completed.
        """
        logging.info(f"Committing manual changes and creating RoWD records for {len(completed_task_ids)} tasks.")
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise FileNotFoundError("Project root folder not found for committing manual changes.")

            project_root = project_details['project_root_folder']
            build_agent = BuildAndCommitAgentAppTarget(project_root)

            commit_message = "feat: Apply and commit manual fixes from PM"
            success, message = build_agent.commit_all_changes(commit_message)

            if not success:
                raise Exception(f"Failed to commit changes: {message}")

            commit_hash = message.split(":")[-1].strip() if "New commit hash:" in message else "N/A"

            doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)

            for task_id in completed_task_ids:
                # Find the full task details from the active plan
                task_just_fixed = next((task for task in self.active_plan if task.get("micro_spec_id") == task_id), None)

                if task_just_fixed:
                    logging.info(f"Creating RoWD success record for manually fixed component: {task_just_fixed.get('component_name')}")
                    doc_agent.update_artifact_record({
                        "artifact_id": f"art_{uuid.uuid4().hex[:8]}",
                        "project_id": self.project_id,
                        "file_path": task_just_fixed.get("component_file_path"),
                        "artifact_name": task_just_fixed.get("component_name"),
                        "artifact_type": task_just_fixed.get("component_type"),
                        "short_description": task_just_fixed.get("task_description"),
                        "status": "UNIT_TESTS_PASSING", # We assume the PM's manual fix is correct
                        "unit_test_status": "TESTS_PASSING",
                        "commit_hash": commit_hash,
                        "version": 1,
                        "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
                        "micro_spec_id": task_just_fixed.get("micro_spec_id")
                    })
                else:
                    logging.warning(f"Could not find task details for micro_spec_id '{task_id}' in the active plan. Cannot create RoWD record.")

            logging.info("Manual changes committed and RoWD updated successfully. Resuming project.")
            resume_phase = self._determine_resume_phase_from_rowd(db)
            self.set_phase(resume_phase.name)

        except Exception as e:
            logging.error(f"Failed to continue project with uncommitted changes: {e}", exc_info=True)
            # If this process fails, we put the user back on the pre-flight page to try again
            self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")

    def commit_manual_changes_and_proceed(self, **kwargs):
        """
        Commits all uncommitted changes with a generic message. This is used
        when changes are detected between sprints (no active plan).
        """
        from agents.build_and_commit_agent_app_target import BuildAndCommitAgentAppTarget
        logging.info("Committing manual changes made between sprints.")
        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise FileNotFoundError("Project root folder not found for committing manual changes.")

            project_root = project_details['project_root_folder']
            version_control_enabled = project_details['version_control_enabled'] == 1
            if not version_control_enabled:
                logging.warning("Cannot commit changes; version control is disabled for this project.")
                # If VCS is disabled, there's nothing to commit. Just proceed with resumption.
                return True, "Changes saved locally (VCS disabled)."

            build_agent = BuildAndCommitAgentAppTarget(project_root, version_control_enabled)
            commit_message = "feat: Apply and commit manual changes from PM"
            success, message = build_agent.commit_all_changes(commit_message)

            if not success and "No changes detected" not in message:
                raise Exception(f"Failed to commit changes: {message}")

            return True, message
        except Exception as e:
            logging.error(f"Failed to commit manual changes: {e}", exc_info=True)
            return False, str(e)

    def delete_archived_project(self, history_id: int) -> tuple[bool, str]:
        """
        Permanently deletes an archived project's history record and its
        associated archive files from the filesystem.
        """
        logging.info(f"Attempting to delete archived project with history_id: {history_id}.")
        try:
            db = self.db_manager
            history_record = db.get_project_history_by_id(history_id)
            if not history_record:
                error_msg = f"No project history found for ID {history_id}."
                logging.error(error_msg)
                return False, error_msg

            archive_path_str = history_record['archive_file_path']
            rowd_file = Path(archive_path_str)
            cr_file = rowd_file.with_name(rowd_file.name.replace("_rowd.json", "_cr.json"))
            project_file = rowd_file.with_name(rowd_file.name.replace("_rowd.json", "_project.json"))

            for file_to_delete in [rowd_file, cr_file, project_file]:
                if file_to_delete.exists():
                    file_to_delete.unlink()
                    logging.info(f"Deleted archive file: {file_to_delete}")
                else:
                    logging.warning(f"Could not find archive file to delete at: {file_to_delete}")

            db.delete_project_from_history(history_id)
            success_msg = f"Successfully deleted archived project (History ID: {history_id})."
            logging.info(success_msg)
            return True, success_msg

        except Exception as e:
            error_msg = f"An unexpected error occurred while deleting project history {history_id}: {e}"
            logging.error(error_msg, exc_info=True)
            return False, error_msg

        except Exception as e:
            error_msg = f"An unexpected error occurred while deleting project history {history_id}: {e}"
            logging.error(error_msg, exc_info=True)
            return False, error_msg

    def delete_active_project(self, project_id: str) -> tuple[bool, str]:
        """
        Permanently deletes an active project and all its associated live data
        from the database.
        """
        logging.info(f"Attempting to delete active project with project_id: {project_id}.")
        try:
            self._clear_active_project_data(self.db_manager, project_id)
            success_msg = f"Successfully deleted active project (ID: {project_id})."
            logging.info(success_msg)
            return True, success_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred while deleting project {project_id}: {e}"
            logging.error(error_msg, exc_info=True)
            return False, error_msg

    def load_archived_project(self, history_id: int):
        """
        Loads an archived project's data, performs pre-flight checks,
        and sets the appropriate phase for UI resolution.
        """
        try:
            db = self.db_manager
            if self.project_id and self.is_project_dirty:
                logging.warning(f"An active, modified project '{self.project_name}' was found. Performing a safety export.")
                self._create_project_archive_and_history_record()

            history_record = db.get_project_history_by_id(history_id)
            if not history_record:
                raise FileNotFoundError(f"No project history found for ID {history_id}")

            project_id_to_load = history_record['project_id']

            rowd_file_path = Path(history_record['archive_file_path'])
            project_file_path = rowd_file_path.with_name(rowd_file_path.name.replace("_rowd.json", "_project.json"))
            cr_file_path = rowd_file_path.with_name(rowd_file_path.name.replace("_rowd.json", "_cr.json"))

            if project_file_path.exists():
                with open(project_file_path, 'r', encoding='utf-8') as f:
                    db.create_or_update_project_record(json.load(f))
            if rowd_file_path.exists():
                with open(rowd_file_path, 'r', encoding='utf-8') as f:
                    artifacts_to_load = json.load(f)
                    if artifacts_to_load: db.bulk_insert_artifacts(artifacts_to_load)
            if cr_file_path.exists():
                with open(cr_file_path, 'r', encoding='utf-8') as f:
                    crs_to_load = json.load(f)
                    if crs_to_load: db.bulk_insert_change_requests(crs_to_load)

            self.project_id = project_id_to_load
            self.project_name = history_record['project_name']
            self.project_root_path = history_record['project_root_folder']

            # Re-fetch the resumable state now that the project data is loaded
            self.resumable_state = db.get_any_paused_state()

            check_result = self._perform_preflight_checks(history_record['project_root_folder'], project_id_to_load)
            self.preflight_check_result = {**check_result, "history_id": history_id}

            self.is_project_dirty = False
            self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")

        except Exception as e:
            error_msg = f"A critical error occurred while loading the project: {e}"
            logging.error(error_msg, exc_info=True)
            self.preflight_check_result = {"status": "ERROR", "message": error_msg, "history_id": history_id}
            self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")


    def get_project_history(self):
        """Retrieves all records from the ProjectHistory table."""
        try:
            return self.db_manager.get_project_history()
        except Exception as e:
            logging.error(f"Failed to retrieve project history: {e}")
            return []

    def _plan_and_execute_fix(self, failure_log: str, context_package: dict) -> bool:
        """
        Invokes the FixPlannerAgent and loads the resulting plan into a separate
        'fix_plan' track for execution.
        Returns True on success, False on failure.
        """
        logging.info("Invoking FixPlannerAgent to generate a fix plan...")

        if not self.llm_service:
            raise Exception("Cannot plan fix: LLM Service is not configured.")

        relevant_code = next(iter(context_package.values()), "No code context available.")

        planner_agent = FixPlannerAgent_AppTarget(llm_service=self.llm_service)
        fix_plan_str = planner_agent.create_fix_plan(
            root_cause_hypothesis=failure_log,
            relevant_code=relevant_code
        )

        try:
            parsed_plan = json.loads(fix_plan_str)
            if isinstance(parsed_plan, list) and len(parsed_plan) > 0 and parsed_plan[0].get("error"):
                raise Exception(f"FixPlannerAgent failed to generate a plan: {parsed_plan[0]['error']}")

            if not parsed_plan:
                raise Exception("FixPlannerAgent returned an empty plan.")

            # --- THIS IS THE FIX ---
            # Load the new plan into the separate fix track and activate fix mode.
            self.fix_plan = parsed_plan
            self.fix_plan_cursor = 0
            self.is_in_fix_mode = True
            # --- END OF FIX ---

            self.set_phase("GENESIS")
            logging.info(f"Successfully generated a fix plan with {len(parsed_plan)} steps. Entering fix mode.")
            return True

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logging.error(f"Failed to create or parse a valid fix plan. Error: {e}. Response was: {fix_plan_str}")
            return False

    def _build_and_validate_context_package(self, core_documents: dict, source_code_files: dict) -> dict:
        """
        Gathers context using a "Hybrid Context Assembly" strategy. It checks
        the size of each file, adding the full code for small files and a
        pre-generated summary for large files. If a summary is missing for a
        large file, it generates one on-the-fly.

        Returns:
            A dictionary containing the assembled source code context, a flag
            indicating if trimming occurred, any errors, and a list of files
            represented by summaries instead of full code.
        """
        final_context = {}
        excluded_files = []
        summarized_files = []
        context_was_trimmed = False

        limit_str = self.db_manager.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "2500000"
        char_limit = int(limit_str)

        # 1. Add core documents first, as they are essential context.
        core_doc_chars = 0
        for name, content in core_documents.items():
            if content:
                final_context[name] = content
                core_doc_chars += len(content)

        if core_doc_chars > char_limit:
            msg = "Core documents alone exceed the context limit. Cannot proceed."
            logging.error(f"Context Builder Error: {msg}")
            return {"source_code": {}, "error": msg}

        remaining_chars = char_limit - core_doc_chars

        # 2. Iterate through source files to build the hybrid context.
        for file_path, content in source_code_files.items():
            content_len = len(content)

            if content_len <= remaining_chars:
                # File is small enough, add full source code.
                final_context[file_path] = content
                remaining_chars -= content_len
            else:
                # File is too large, use a summary instead.
                context_was_trimmed = True
                artifact = self.db_manager.get_artifact_by_path(self.project_id, file_path)

                if artifact and artifact['code_summary']:
                    # Summary exists, use it if it fits.
                    summary = artifact['code_summary']
                    if len(summary) <= remaining_chars:
                        final_context[file_path] = f"--- CODE SUMMARY FOR {file_path} ---\n{summary}"
                        remaining_chars -= len(summary)
                        summarized_files.append(file_path)
                    else:
                        excluded_files.append(file_path) # Summary is also too big
                else:
                    # On-demand summarization for legacy or missing summaries.
                    logging.info(f"Context Builder: On-demand summary needed for large file: {file_path}")
                    try:
                        from agents.agent_code_summarization import CodeSummarizationAgent
                        summarization_agent = CodeSummarizationAgent(llm_service=self.llm_service)
                        summary = summarization_agent.summarize_code(content)

                        if len(summary) <= remaining_chars:
                            final_context[file_path] = f"--- CODE SUMMARY FOR {file_path} ---\n{summary}"
                            remaining_chars -= len(summary)
                            summarized_files.append(file_path)

                            # Save the newly generated summary back to the DB.
                            if artifact:
                                from agents.doc_update_agent_rowd import DocUpdateAgentRoWD
                                doc_agent = DocUpdateAgentRoWD(self.db_manager, self.llm_service)
                                updated_data = dict(artifact)
                                updated_data['code_summary'] = summary
                                doc_agent.update_artifact_record(updated_data)
                        else:
                            excluded_files.append(file_path) # Generated summary is too big
                    except Exception as e:
                        logging.error(f"On-demand summarization failed for {file_path}: {e}")
                        excluded_files.append(file_path)

        if excluded_files:
            logging.warning(f"Context Builder: Excluded {len(excluded_files)} file(s) as they and their summaries were too large: {', '.join(excluded_files)}")

        # At the end of _build_and_validate_context_package...
        return {
            "source_code": final_context,
            "was_trimmed": context_was_trimmed,
            "error": None,
            "summarized_files": summarized_files,
            "files_in_context": list(source_code_files.keys())
        }

    def _plan_fix_from_description(self, description: str):
        """
        Takes a natural language description of a bug, forms a hypothesis,
        and generates a fix plan. This version is refactored to use the
        central llm_service.
        """
        logging.info(f"Attempting to plan fix from description: '{description[:100]}...'")
        try:
            if not self.llm_service:
                raise Exception("Cannot proceed with triage: LLM Service is not configured.")

            # Step 1: Use TriageAgent to refine the description into a testable hypothesis.
            triage_agent = TriageAgent_AppTarget(llm_service=self.llm_service, db_manager=self.db_manager)
            hypothesis = triage_agent.analyze_and_hypothesize(
                error_logs=description,
                relevant_code="No specific code context available; base analysis on user description.",
                test_report=""
            )
            if "An error occurred" in hypothesis:
                raise Exception(f"TriageAgent failed to form a hypothesis: {hypothesis}")
            logging.info(f"TriageAgent formed hypothesis: {hypothesis}")

            # Step 2: Use FixPlannerAgent to create a plan from the hypothesis.
            planner_agent = FixPlannerAgent_AppTarget(llm_service=self.llm_service)
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
        Handles the text input provided by the PM during interactive triage (Tier 3).
        """
        logging.info("Tier 3: Received manual error description from PM. Attempting to generate fix plan.")

        try:
            if not self.llm_service:
                raise Exception("Cannot proceed with triage: LLM Service is not configured.")

            triage_agent = TriageAgent_AppTarget(llm_service=self.llm_service, db_manager=self.db_manager)
            hypothesis = triage_agent.analyze_and_hypothesize(
                error_logs=pm_error_description,
                relevant_code="No specific code context available; base analysis on user description.",
                test_report=""
            )

            if "An error occurred" in hypothesis:
                 raise Exception(f"TriageAgent failed to form a hypothesis: {hypothesis}")

            logging.info(f"TriageAgent formed hypothesis: {hypothesis}")

            planner_agent = FixPlannerAgent_AppTarget(llm_service=self.llm_service)
            fix_plan_str = planner_agent.create_fix_plan(
                root_cause_hypothesis=hypothesis,
                relevant_code="No specific code context was automatically identified. Base the fix on the TriageAgent's hypothesis."
            )

            if "error" in fix_plan_str.lower():
                raise Exception(f"FixPlannerAgent failed to generate a plan: {fix_plan_str}")

            fix_plan = json.loads(fix_plan_str)
            if not fix_plan:
                 raise Exception("FixPlannerAgent returned an empty plan.")

            learning_agent = LearningCaptureAgent(self.db_manager)
            tags = self._extract_tags_from_text(hypothesis)
            learning_agent.add_learning_entry(
                context=f"During interactive triage (Tier 3) for project: {self.project_name}",
                problem=pm_error_description,
                solution=fix_plan_str,
                tags=tags
            )

            self.active_plan = fix_plan
            self.active_plan_cursor = 0
            self.set_phase("GENESIS")
            logging.info("Successfully generated a fix plan from PM description. Transitioning to GENESIS phase.")

        except Exception as e:
            logging.error(f"Tier 3 interactive triage failed. Error: {e}")
            self.set_phase("DEBUG_PM_ESCALATION")

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

    def start_test_environment_setup(self, progress_callback=None):
        """
        Calls the advisor agent to get a list of test environment setup tasks.
        """
        logging.info("Initiating test environment setup guidance.")
        try:
            if not self.llm_service:
                raise Exception("Cannot get setup tasks: LLM Service is not configured.")

            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details:
                raise Exception("Cannot get setup tasks: Project details not found.")

            tech_spec_text = project_details['tech_spec_text']
            # Corrected to handle missing key gracefully
            target_os = project_details['target_os'] if 'target_os' in project_details.keys() and project_details['target_os'] else 'Linux'

            if not tech_spec_text:
                raise Exception("Cannot get setup tasks: Technical Specification is missing.")

            agent = TestEnvironmentAdvisorAgent(llm_service=self.llm_service)
            tasks = agent.get_setup_tasks(tech_spec_text, target_os)
            return tasks

        except Exception as e:
            logging.error(f"Failed to start test environment setup: {e}")
            return None

    def get_help_for_setup_task(self, task_instructions: str, **kwargs):
        """
        Calls the advisor agent to get detailed help for a specific setup task.
        """
        logging.info("Getting help for a test environment setup task.")
        try:
            if not self.llm_service:
                raise Exception("Cannot get help: LLM Service is not configured.")

            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details:
                raise Exception("Cannot get help: Project details not found.")

            target_os = project_details['target_os'] if project_details and 'target_os' in project_details.keys() else 'Linux'

            agent = TestEnvironmentAdvisorAgent(llm_service=self.llm_service)
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
            self.db_manager.update_project_field(self.project_id, "test_execution_command", test_command)

            self.set_phase("CODING_STANDARD_GENERATION")
            logging.info("Test environment setup complete. Transitioning to Coding Standard Generation.")
            return True
        except Exception as e:
            logging.error(f"Failed to finalize test environment setup: {e}")
            return False

    def handle_ignore_setup_task(self, task: dict):
        """
        Creates a 'KNOWN_ISSUE' artifact to record a skipped setup task.
        """
        if not self.project_id:
            logging.error("Cannot log ignored setup task; no active project.")
            return

        logging.warning(f"PM chose to ignore setup task: {task.get('tool_name')}. Logging as KNOWN_ISSUE.")
        try:
            db = self.db_manager
            doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)
            artifact_name = f"Skipped Setup Task: {task.get('tool_name', 'Unnamed Step')}"
            description = f"The PM chose to ignore the setup/installation for the following tool or step: {task.get('instructions', 'No instructions provided.')}"

            doc_agent.update_artifact_record({
                "artifact_id": f"art_{uuid.uuid4().hex[:8]}",
                "project_id": self.project_id,
                "file_path": "N/A",
                "artifact_name": artifact_name,
                "artifact_type": "ENVIRONMENT_SETUP",
                "short_description": description,
                "status": "KNOWN_ISSUE",
                "unit_test_status": "NOT_APPLICABLE",
                "version": 1,
                "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
                "commit_hash": "N/A"
            })
            logging.info(f"Successfully created KNOWN_ISSUE artifact for '{artifact_name}'.")
        except Exception as e:
            logging.error(f"Failed to create KNOWN_ISSUE artifact for skipped setup task. Error: {e}")

    def handle_acknowledge_integration_failure(self):
        """
        Handles the PM's acknowledgment of a system-level integration failure.
        """
        logging.warning("PM acknowledged a system-level integration failure. Proceeding to manual testing.")
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)

            if not project_details:
                raise Exception("Cannot generate UI test plan: Project Details not found.")

            functional_spec_text = project_details['final_spec_text']
            technical_spec_text = project_details['tech_spec_text']

            if not functional_spec_text or not technical_spec_text:
                raise Exception("Cannot generate UI test plan: Missing specifications.")

            ui_test_planner = UITestPlannerAgent_AppTarget(llm_service=self.llm_service)
            ui_test_plan_content = ui_test_planner.generate_ui_test_plan(functional_spec_text, technical_spec_text)

            final_ui_test_plan = self.prepend_standard_header(
                document_content=ui_test_plan_content,
                document_type="UI Test Plan"
            )
            db.update_project_field(self.project_id, "ui_test_plan_text", final_ui_test_plan)

            self.task_awaiting_approval = None
            self.set_phase("MANUAL_UI_TESTING")

        except Exception as e:
            logging.error(f"Failed to handle integration failure acknowledgment. Error: {e}")
            self.set_phase("DEBUG_PM_ESCALATION")

    def _extract_and_save_primary_technology(self, tech_spec_text: str):
        """
        Uses the LLM service to extract the primary programming language from the
        technical specification text and saves it to the database.
        """
        logging.info("Extracting primary technology from technical specification...")
        try:
            if not self.llm_service:
                raise Exception("Cannot extract technology: LLM Service is not initialized.")

            prompt = f"""
            Analyze the following technical specification document. Your single task is to identify the primary, top-level programming language or technology stack.

            Your response MUST be only the name of the language (e.g., "Python", "Java", "C#", "Go"). Do not include any other words, explanations, or punctuation.

            --- Technical Specification ---
            {tech_spec_text}
            --- End Specification ---

            Primary Language:
            """

            primary_technology = self.llm_service.generate_text(prompt, task_complexity="simple").strip()

            if primary_technology and not primary_technology.startswith("Error:"):
                self.db_manager.update_project_field(self.project_id, "technology_stack", primary_technology)
                logging.info(f"Successfully extracted and saved primary technology: {primary_technology}")
            else:
                raise ValueError(f"LLM service returned an empty or error response for technology extraction: {primary_technology}")

        except Exception as e:
            logging.error(f"Failed to extract and save primary technology: {e}")

    def get_latest_commit_timestamp(self) -> datetime | None:
        """
        Retrieves the timestamp of the most recent commit in the project's repo.
        """
        import git
        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                logging.warning("Cannot get latest commit timestamp: project root folder not found.")
                return None

            project_root_path = str(project_details['project_root_folder'])
            repo = git.Repo(project_root_path)

            if not repo.heads or not repo.head.is_valid():
                return None

            latest_commit = repo.head.commit
            return latest_commit.committed_datetime
        except Exception as e:
            logging.error(f"Could not retrieve latest commit timestamp: {e}")
            return None

    def get_current_git_branch(self) -> str:
        """
        Safely retrieves the current Git branch name for the active project.
        Returns 'N/A' if not applicable or on error.
        """
        import git
        if not self.project_id:
            return "N/A"

        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                return "N/A"

            project_root_path = str(project_details['project_root_folder'])

            if not (Path(project_root_path) / '.git').exists():
                return "Not a Git repository"

            repo = git.Repo(project_root_path)

            if repo.head.is_detached:
                return "detached"
            else:
                return repo.active_branch.name
        except git.InvalidGitRepositoryError:
            return "Invalid repository"
        except Exception as e:
            logging.warning(f"Could not retrieve current git branch: {e}")
            return "N/A"

    def _debug_jump_to_phase(self, phase_name: str):
        """
        A debug-only method to jump the application to a specific phase.
        It will create a new project only if no project is currently active.
        """
        logging.warning(f"--- DEBUG: Jumping to phase: {phase_name} ---")

        db = self.db_manager

        # This is the fix: Only create a new project if one isn't already active.
        if not self.project_id:
            logging.info("No active project found, creating a new 'Debug Project'.")
            self.start_new_project("Debug Project")
            db.update_project_field(self.project_id, "project_root_folder", "data/debug_project")
            db.update_project_field(self.project_id, "final_spec_text", "Debug final spec.")
            db.update_project_field(self.project_id, "tech_spec_text", "Debug tech spec using Python.")
            db.update_project_field(self.project_id, "technology_stack", "Python")

        if phase_name == "GENESIS":
            # The rest of the logic for a direct jump to Genesis remains the same.
            dummy_plan_str = """
            {
                "main_executable_file": "main.py",
                "development_plan": [
                    {
                        "micro_spec_id": "DBG-001",
                        "task_description": "Create a main.py file that prints 'Hello, Debug World!' to the console.",
                        "component_name": "main.py",
                        "component_type": "FUNCTION",
                        "component_file_path": "src/main.py",
                        "test_file_path": "src/tests/test_main.py"
                    }
                ]
            }
            """
            self.finalize_and_save_dev_plan(dummy_plan_str)
            return

        self.set_phase(phase_name)

    def _create_llm_service(self) -> LLMService | None:
        """
        Factory method to create the appropriate LLM service adapter based on
        the configuration stored in the database.
        """
        from llm_service import (LLMService, GeminiAdapter, OpenAIAdapter,
                                 AnthropicAdapter, LocalPhi3Adapter, CustomEndpointAdapter)

        logging.info("Attempting to create and configure LLM service...")
        db = self.db_manager
        provider_name_from_db = db.get_config_value("SELECTED_LLM_PROVIDER") or "Gemini"

        if provider_name_from_db == "Gemini":
            api_key = db.get_config_value("GEMINI_API_KEY")
            reasoning_model = db.get_config_value("GEMINI_REASONING_MODEL")
            fast_model = db.get_config_value("GEMINI_FAST_MODEL")
            if not api_key:
                logging.warning("Gemini is selected, but GEMINI_API_KEY is not set.")
                return None
            return GeminiAdapter(api_key, reasoning_model, fast_model)

        elif provider_name_from_db == "ChatGPT":
            api_key = db.get_config_value("OPENAI_API_KEY")
            reasoning_model = db.get_config_value("OPENAI_REASONING_MODEL")
            fast_model = db.get_config_value("OPENAI_FAST_MODEL")
            if not api_key:
                logging.warning("ChatGPT (OpenAI) is selected, but OPENAI_API_KEY is not set.")
                return None
            return OpenAIAdapter(api_key, reasoning_model, fast_model)

        elif provider_name_from_db == "Claude":
            api_key = db.get_config_value("ANTHROPIC_API_KEY")
            reasoning_model = db.get_config_value("ANTHROPIC_REASONING_MODEL")
            fast_model = db.get_config_value("ANTHROPIC_FAST_MODEL")
            if not api_key:
                logging.warning("Claude (Anthropic) is selected, but ANTHROPIC_API_KEY is not set.")
                return None
            return AnthropicAdapter(api_key, reasoning_model, fast_model)

        elif provider_name_from_db == "Phi-3 (Local)":
            return LocalPhi3Adapter()

        elif provider_name_from_db == "Any Other":
            base_url = db.get_config_value("CUSTOM_ENDPOINT_URL")
            api_key = db.get_config_value("CUSTOM_ENDPOINT_API_KEY")
            reasoning_model = db.get_config_value("CUSTOM_REASONING_MODEL")
            fast_model = db.get_config_value("CUSTOM_FAST_MODEL")
            if not all([base_url, api_key, reasoning_model, fast_model]):
                logging.warning("Any Other provider selected, but one or more required settings are missing.")
                return None
            return CustomEndpointAdapter(base_url, api_key, reasoning_model, fast_model)

        else:
            logging.error(f"Invalid LLM provider configured: {provider_name_from_db}")
            return None

    def run_mid_project_reassessment(self):
        """
        Calculates the remaining work in a project and invokes the
        ProjectScopingAgent to perform a new risk and complexity analysis.
        """
        logging.info(f"Running mid-project re-assessment for project: {self.project_name}")
        if not self.project_id:
            logging.error("Cannot run re-assessment; no active project.")
            return

        remaining_work_spec = ""
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details:
                raise Exception("Project details not found for re-assessment.")

            dev_plan_text = project_details.get('development_plan_text')

            if not dev_plan_text:
                remaining_work_spec = project_details.get('final_spec_text', '')
            else:
                dev_plan = json.loads(dev_plan_text).get("development_plan", [])
                all_artifacts = db.get_all_artifacts_for_project(self.project_id)
                completed_spec_ids = {art['micro_spec_id'] for art in all_artifacts if art['micro_spec_id']}
                remaining_tasks = [task for task in dev_plan if task.get('micro_spec_id') not in completed_spec_ids]

                if not remaining_tasks:
                    remaining_work_spec = "Project development is complete. Assess risk of any final integration or bug fixing."
                else:
                    remaining_work_spec = "\n\n".join([task['task_description'] for task in remaining_tasks if 'task_description' in task])

            if not remaining_work_spec.strip():
                self.task_awaiting_approval = {"reassessment_result": {"error": "Could not determine remaining work."}}
                return

            scoping_agent = ProjectScopingAgent(llm_service=self.llm_service)
            analysis_result = scoping_agent.analyze_complexity(remaining_work_spec)
            self.task_awaiting_approval = {"reassessment_result": analysis_result}
            logging.info("Successfully completed mid-project re-assessment.")

        except Exception as e:
            logging.error(f"An error occurred during mid-project re-assessment: {e}")
            self.task_awaiting_approval = {"reassessment_result": {"error": f"An unexpected error occurred: {e}"}}

    def commit_pending_llm_change(self, new_provider: str) -> tuple[bool, str]:
        """
        Finalizes a pending LLM provider change after a successful
        re-assessment by saving it to the database and re-initializing
        the LLM service.
        """
        logging.info(f"Committing pending LLM change to: {new_provider}")
        try:
            db = self.db_manager
            db.set_config_value("SELECTED_LLM_PROVIDER", new_provider)

            provider_key_map = {
                "Gemini": "GEMINI_CONTEXT_LIMIT", "OpenAI": "OPENAI_CONTEXT_LIMIT",
                "Anthropic": "ANTHROPIC_CONTEXT_LIMIT", "LocalPhi3": "LOCALPHI3_CONTEXT_LIMIT",
                "Enterprise": "ENTERPRISE_CONTEXT_LIMIT"
            }
            provider_default_key = provider_key_map.get(new_provider)
            if provider_default_key:
                provider_default_value = db.get_config_value(provider_default_key)
                if provider_default_value:
                    db.set_config_value("CONTEXT_WINDOW_CHAR_LIMIT", provider_default_value)
                    logging.info(f"Active context limit updated to default for {new_provider}: {provider_default_value} chars.")

            self._llm_service = None # Clear the cached service to force re-initialization

            # Immediately try to re-initialize to catch any configuration errors
            if not self.llm_service:
                 raise Exception("Failed to re-initialize LLM service with new provider. Check API keys.")

            return True, f"Successfully switched to {new_provider}."
        except Exception as e:
            logging.error(f"Failed to commit pending LLM change: {e}")
            return False, f"Failed to commit LLM change: {e}"

    def _sanitize_path(self, raw_path: str | None) -> str | None:
        """
        Cleans and validates a file path string received from an LLM.

        - Returns None if the path is empty or 'N/A'.
        - Removes invalid characters for file names.
        - Handles cases where multiple files might be in one string.
        """
        if not raw_path or raw_path.lower().strip() in ["n/a", "none"]:
            return None

        # Take the first part if there are commas
        path = raw_path.split(',')[0].strip()

        # Remove characters invalid in most filesystems
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            path = path.replace(char, '')

        # Replace backslashes with forward slashes for consistency
        path = path.replace('\\', '/')

        # Ensure it's a relative path to prevent absolute path injections
        if Path(path).is_absolute():
            logging.warning(f"Sanitizer received an absolute path, which is not allowed: {path}. Ignoring.")
            return None

        return path

    def get_full_backlog_hierarchy(self) -> list:
        """
        Queries the database and builds a complete, nested list of dictionaries
        representing the entire project backlog hierarchy. This version is fully
        recursive to find children at any level.
        """
        if not self.project_id:
            return []

        def get_children_recursive(parent_id):
            """Helper function to recursively fetch children for any given parent."""
            children_rows = self.db_manager.get_children_of_cr(parent_id)
            if not children_rows:
                return []

            children_list = []
            for child_row in children_rows:
                child_dict = dict(child_row)
                # The UI expects sub-items under a 'user_stories' key for rendering
                child_dict['user_stories'] = get_children_recursive(child_dict['cr_id'])
                children_list.append(child_dict)
            return children_list

        try:
            top_level_items = self.db_manager.get_top_level_items_for_project(self.project_id)
            full_hierarchy = []

            for item_row in top_level_items:
                item_dict = dict(item_row)
                item_id = item_dict['cr_id']

                # The UI expects sub-items under a 'features' key for rendering top-level children
                item_dict['features'] = get_children_recursive(item_id)
                full_hierarchy.append(item_dict)

            return full_hierarchy
        except Exception as e:
            logging.error(f"Failed to build full backlog hierarchy: {e}", exc_info=True)
            return []

    def _get_backlog_with_hierarchical_numbers(self) -> list:
        """
        Traverses the full backlog and adds a user-facing 'hierarchical_id'
        to each item's dictionary representation.
        """
        full_hierarchy = self.get_full_backlog_hierarchy()

        def recurse_and_add_ids(items, prefix=""):
            for i, item in enumerate(items, 1):
                current_prefix = f"{prefix}{i}"
                item['hierarchical_id'] = current_prefix

                # The hierarchy can have features with user_stories, or items directly under epics
                children_key = "features" if "features" in item else "user_stories"
                if children_key in item:
                    recurse_and_add_ids(item[children_key], prefix=f"{current_prefix}.")

        recurse_and_add_ids(full_hierarchy)
        return full_hierarchy