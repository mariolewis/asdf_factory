
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

from agents.agent_environment_setup_app_target import EnvironmentSetupAgent_AppTarget
from agents.agent_project_bootstrap import ProjectBootstrapAgent
from agents.agent_spec_clarification import SpecClarificationAgent
from agents.agent_ux_triage import UX_Triage_Agent
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


class FactoryPhase(Enum):
    """Enumeration for the main factory F-Phases."""
    IDLE = auto()
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
    RAISING_CHANGE_REQUEST = auto()
    AWAITING_IMPACT_ANALYSIS_CHOICE = auto()
    AWAITING_INITIAL_IMPACT_ANALYSIS = auto()
    IMPLEMENTING_CHANGE_REQUEST = auto()
    EDITING_CHANGE_REQUEST = auto()
    REPORTING_OPERATIONAL_BUG = auto()
    AWAITING_LINKED_DELETE_CONFIRMATION = auto()
    DEBUG_PM_ESCALATION = auto()
    VIEWING_DOCUMENTS = auto()
    VIEWING_REPORTS = auto()
    VIEWING_PROJECT_HISTORY = auto()
    AWAITING_CONTEXT_REESTABLISHMENT = auto()
    AWAITING_PM_TRIAGE_INPUT = auto()
    AWAITING_REASSESSMENT_CONFIRMATION = auto()


class MasterOrchestrator:
    """
    The central state machine and workflow manager for the ASDF.
    It coordinates agents, manages project state, and handles project lifecycle.
    """

    def __init__(self, db_manager: ASDFDBManager):
        """
        Initializes the MasterOrchestrator with a shared DB manager instance.
        """
        self.db_manager = db_manager
        self.resumable_state = None

        # Corrected: Direct call to the db_manager
        self.resumable_state = self.db_manager.get_any_paused_state()

        if self.resumable_state:
            self.project_id = self.resumable_state['project_id']
            self.current_phase = FactoryPhase[self.resumable_state['current_phase']]
            # Corrected: Direct call to the db_manager
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details:
                self.project_name = project_details['project_name']
            logging.info(f"Orchestrator initialized into a resumable state for project: {self.project_name}")
        else:
            self.project_id: str | None = None
            self.project_name: str | None = None
            self.current_phase: FactoryPhase = FactoryPhase.IDLE

        # Initialize remaining in-memory attributes
        self.active_plan = None
        self.active_plan_cursor = 0
        self.task_awaiting_approval = None
        self.preflight_check_result = None
        self.debug_attempt_counter = 0
        self.resume_phase_after_load = None
        self.active_ux_spec = {}
        self.is_project_dirty = False
        self._llm_service = None
        logging.info("MasterOrchestrator instance created.")

    def reset(self):
        """
        Resets the orchestrator's state to its default, idle condition.
        """
        logging.info("Resetting MasterOrchestrator to idle state.")
        self.project_id = None
        self.project_name = None
        self.current_phase = FactoryPhase.IDLE
        self.active_plan = None
        self.active_plan_cursor = 0
        self.task_awaiting_approval = None
        self.preflight_check_result = None
        self.debug_attempt_counter = 0
        self.resume_phase_after_load = None
        self.active_ux_spec = {}
        self.is_project_dirty = False

    def close_active_project(self):
        """
        Closes the currently active project, returning to an idle state.
        """
        logging.info(f"Closing active project: {self.project_name}")
        if self.project_id:
            self.db_manager.delete_orchestration_state_for_project(self.project_id)
        self.reset()

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
        FactoryPhase.RAISING_CHANGE_REQUEST: "Raise New Change Request",
        FactoryPhase.AWAITING_IMPACT_ANALYSIS_CHOICE: "New CR - Impact Analysis Choice",
        FactoryPhase.AWAITING_INITIAL_IMPACT_ANALYSIS: "Initial Impact Analysis",
        FactoryPhase.IMPLEMENTING_CHANGE_REQUEST: "Implement Change Request",
        FactoryPhase.EDITING_CHANGE_REQUEST: "Edit Change Request",
        FactoryPhase.REPORTING_OPERATIONAL_BUG: "Report Operational Bug",
        FactoryPhase.AWAITING_LINKED_DELETE_CONFIRMATION: "Confirm Linked Deletion",
        FactoryPhase.DEBUG_PM_ESCALATION: "Debug Escalation to PM",
        FactoryPhase.VIEWING_DOCUMENTS: "Viewing Project Documents",
        FactoryPhase.VIEWING_REPORTS: "Viewing Project Reports",
        FactoryPhase.VIEWING_PROJECT_HISTORY: "Select and Load Archived Project",
        FactoryPhase.AWAITING_CONTEXT_REESTABLISHMENT: "Re-establishing Project Context",
        FactoryPhase.AWAITING_PM_TRIAGE_INPUT: "Interactive Triage - Awaiting Input",
        FactoryPhase.AWAITING_REASSESSMENT_CONFIRMATION: "LLM Re-assessment Confirmation"
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
        # Main development is complete if we are at the GENESIS checkpoint with no tasks left,
        # or if we have already moved on to a later phase.
        if self.current_phase == FactoryPhase.GENESIS and (not self.active_plan or self.active_plan_cursor >= len(self.active_plan)):
            return True

        # List of phases that occur after Genesis is complete
        post_genesis_phases = [
            FactoryPhase.AWAITING_INTEGRATION_CONFIRMATION,
            FactoryPhase.INTEGRATION_AND_VERIFICATION,
            FactoryPhase.MANUAL_UI_TESTING
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
        Initializes a new project, now with robust path handling and subdirectory creation.
        """
        if self.project_id and self.is_project_dirty:
            logging.warning(
                f"An active, modified project '{self.project_name}' was found. "
                "Performing a safety export before starting the new project."
            )
            archive_path_from_db = self.db_manager.get_config_value("DEFAULT_ARCHIVE_PATH")
            if not archive_path_from_db or not archive_path_from_db.strip():
                logging.error("Safety export failed: Default Project Archive Path is not set in Settings.")
            else:
                archive_path = Path(archive_path_from_db)
                archive_name = f"{self.project_name.replace(' ', '_')}_auto_export_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.stop_and_export_project(archive_path, archive_name)

        base_path_str = self.db_manager.get_config_value("DEFAULT_PROJECT_PATH")

        if not base_path_str or not base_path_str.strip():
            base_path = Path().resolve() / "projects"
            logging.warning(f"Default project path not set. Using fallback directory: {base_path}")
        else:
            base_path = Path(base_path_str)

        project_root = base_path / project_name.replace(' ', '_').lower()
        docs_dir = project_root / "_docs"
        uploads_dir = docs_dir / "_uploads"

        try:
            project_root.mkdir(parents=True, exist_ok=True)
            docs_dir.mkdir(exist_ok=True)
            uploads_dir.mkdir(exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to create project directory structure at {project_root}: {e}")
            raise

        self.project_id = f"proj_{uuid.uuid4().hex[:8]}"
        self.project_name = project_name
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            self.db_manager.create_project(self.project_id, self.project_name, timestamp)
            self.db_manager.update_project_field(self.project_id, "project_root_folder", str(project_root))
            logging.info(f"Successfully started new project: '{self.project_name}' (ID: {self.project_id}) at {project_root}")
            self.is_project_dirty = True

            self.set_phase("ENV_SETUP_TARGET_APP")

        except Exception as e:
            logging.error(f"Failed to start new project '{self.project_name}': {e}")
            self.reset()
            raise

    def save_uploaded_brief_files(self, uploaded_files: list) -> list[str]:
        """Copies uploaded brief files to the project's _docs/_uploads directory and commits them."""
        if not self.project_id: return []
        project_details = self.db_manager.get_project_by_id(self.project_id)
        if not project_details: return []

        project_root = Path(project_details['project_root_folder'])
        uploads_dir = project_root / "_docs" / "_uploads"
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
        """Saves a text-based project brief to a markdown file and commits it."""
        if not self.project_id: return None

        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details: return None

            project_root = Path(project_details['project_root_folder'])
            docs_dir = project_root / "_docs"
            docs_dir.mkdir(exist_ok=True)
            brief_file_path = docs_dir / "user_project_brief.md"
            brief_file_path.write_text(brief_content, encoding="utf-8")

            # Commit the new brief document
            commit_message = "docs: Add initial text-based project brief"
            self._commit_document(brief_file_path, commit_message)

            return str(brief_file_path)
        except Exception as e:
            logging.error(f"Failed to save text brief as file: {e}")
            return None

    def save_uploaded_brief_files(self, uploaded_files: list) -> list[str]:
        """Copies uploaded brief files to the project's _docs/_uploads directory."""
        if not self.project_id:
            logging.error("Cannot save uploaded files; no active project.")
            return []

        saved_paths = []
        project_details = self.db_manager.get_project_by_id(self.project_id)
        if not project_details or not project_details['project_root_folder']:
            logging.error(f"Could not find project root folder for project {self.project_id}.")
            return []

        project_root = Path(project_details['project_root_folder'])
        uploads_dir = project_root / "_docs" / "_uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        for uploaded_file_path in uploaded_files:
            try:
                source_path = Path(uploaded_file_path)
                destination_path = uploads_dir / source_path.name
                import shutil
                shutil.copy(source_path, destination_path)
                saved_paths.append(str(destination_path))
                logging.info(f"Copied uploaded brief file to: {destination_path}")
            except Exception as e:
                logging.error(f"Failed to copy uploaded file {uploaded_file_path}: {e}")

        return saved_paths

    def save_text_brief_as_file(self, brief_content: str) -> str | None:
        """Saves a text-based project brief to a markdown file."""
        if not self.project_id:
            logging.error("Cannot save text brief; no active project.")
            return None

        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                logging.error(f"Could not find project root folder for project {self.project_id}.")
                return None

            project_root = Path(project_details['project_root_folder'])
            docs_dir = project_root / "_docs"
            docs_dir.mkdir(exist_ok=True)
            brief_file_path = docs_dir / "user_project_brief.md"
            brief_file_path.write_text(brief_content, encoding="utf-8")
            logging.info(f"Saved text project brief to: {brief_file_path}")
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
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise FileNotFoundError("Project root folder not found in database.")
            project_root = Path(project_details['project_root_folder'])

            # Create a dedicated directory for project documents
            docs_dir = project_root / "_docs"
            docs_dir.mkdir(exist_ok=True)

            brief_content = ""
            original_filename = "project_brief.md" # Default for text input

            # --- Process and Save the Brief ---
            if isinstance(brief_input, str):
                brief_content = brief_input
            else: # Assumes it's a Streamlit UploadedFile-like object
                original_filename = getattr(brief_input, 'name', 'project_brief_uploaded.txt')
                if original_filename.endswith('.docx'):
                    import docx
                    doc = docx.Document(brief_input)
                    brief_content = "\n".join([p.text for p in doc.paragraphs])
                else: # For .txt and .md
                    brief_content = brief_input.getvalue().decode("utf-8")

            # Save the processed content as a markdown file
            brief_file_path = docs_dir / original_filename.replace('.txt', '.md').replace('.docx', '.md')
            brief_file_path.write_text(brief_content, encoding="utf-8")
            logging.info(f"Saved project brief to physical file: {brief_file_path}")

            # --- Save the path to the database ---
            self.db_manager.update_project_field(self.project_id, "project_brief_path", str(brief_file_path.relative_to(project_root)))

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
        Handles the PM's decision to either start the UX/UI phase or skip it.
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
            logging.info("PM chose to skip the UX/UI Design phase. Proceeding to Environment Setup.")
            self.task_awaiting_approval = None # Clear the approval task
            self.set_phase("ENV_SETUP_TARGET_APP")
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

            logging.info("Successfully generated and stored the Theming & Style Guide.")

            # Clear any previous error messages
            if 'error' in self.active_ux_spec:
                del self.active_ux_spec['error']

        except Exception as e:
            logging.error(f"Failed to handle style guide submission: {e}")
            self.active_ux_spec['error'] = str(e)

    def handle_ux_spec_completion(self) -> bool:
        """
        Compiles the final UX/UI Specification, saves it to the database and a file,
        and transitions to the next main phase.
        """
        if not self.project_id:
            return False

        try:
            final_spec_parts = []
            personas = self.active_ux_spec.get('confirmed_personas', [])
            if personas:
                final_spec_parts.append("## 1. User Personas\\n- " + "\\n- ".join(personas))
            journeys = self.active_ux_spec.get('confirmed_user_journeys', '')
            if journeys:
                final_spec_parts.append("## 2. Core User Journeys\\n" + journeys)
            blueprints = self.active_ux_spec.get('screen_blueprints', {})
            if blueprints:
                blueprint_section = ["## 3. Structural Blueprint (JSON)"]
                blueprint_section.append("```json")
                parsed_blueprints = {k: json.loads(v) for k, v in blueprints.items()}
                blueprint_section.append(json.dumps(parsed_blueprints, indent=2))
                blueprint_section.append("```")
                final_spec_parts.append("\\n".join(blueprint_section))
            style_guide = self.active_ux_spec.get('style_guide', '')
            if style_guide:
                final_spec_parts.append("## 4. Theming & Style Guide\\n" + style_guide)
            final_spec_doc = "\\n\\n---\\n\\n".join(final_spec_parts)

            final_doc_with_header = self._prepend_standard_header(
                document_content=final_spec_doc,
                document_type="UX/UI Specification"
            )

            db = self.db_manager
            db.update_project_field(self.project_id, "ux_spec_text", final_doc_with_header)

            project_details = db.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "_docs"
                ux_spec_file_path = docs_dir / "ux_ui_specification.md"
                ux_spec_file_path.write_text(final_doc_with_header, encoding="utf-8")

                # Commit the new document
                self._commit_document(ux_spec_file_path, "docs: Finalize UX/UI Specification")

            self.active_ux_spec = {}
            self.task_awaiting_approval = None
            self.set_phase("ENV_SETUP_TARGET_APP")
            return True

        except Exception as e:
            logging.error(f"Failed to complete UX/UI Specification: {e}")
            if 'error' not in self.active_ux_spec:
                 self.active_ux_spec['error'] = str(e)
            return False

    def finalize_and_save_app_spec(self, spec_draft: str):
        """
        Applies the standard header, saves the final application spec to the
        database and a file, and transitions to the next phase.
        """
        if not self.project_id:
            logging.error("Cannot save application spec; no active project.")
            return

        try:
            final_doc_with_header = self._prepend_standard_header(
                document_content=spec_draft,
                document_type="Application Specification"
            )

            self.db_manager.update_project_field(self.project_id, "final_spec_text", final_doc_with_header)

            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "_docs"
                spec_file_path = docs_dir / "application_spec.md"
                spec_file_path.write_text(final_doc_with_header, encoding="utf-8")

                # Commit the new document
                self._commit_document(spec_file_path, "docs: Finalize Application Specification")

            self.set_phase("TECHNICAL_SPECIFICATION")

        except Exception as e:
            logging.error(f"Failed to finalize and save application spec: {e}")

    def finalize_and_save_complexity_assessment(self, assessment_json_str: str):
        """
        Applies the standard header, saves the complexity assessment to the DB,
        and writes the raw assessment to a JSON file.
        """
        if not self.project_id:
            logging.error("Cannot save complexity assessment; no active project.")
            return

        try:
            footnote = "\n\nNote: This assessment applies to the current version of project specifications."
            content_with_footnote = assessment_json_str + footnote

            final_doc_with_header = self._prepend_standard_header(
                document_content=content_with_footnote,
                document_type="Complexity & Risk Assessment"
            )

            self.db_manager.update_project_field(self.project_id, "complexity_assessment_text", final_doc_with_header)
            logging.info(f"Successfully saved Complexity & Risk Assessment to database for project {self.project_id}")

            # This is the new logic to save and commit the file
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "_docs"
                assessment_file_path = docs_dir / "complexity_and_risk_assessment.json"
                assessment_file_path.write_text(assessment_json_str, encoding="utf-8")

                # Commit the new document
                self._commit_document(assessment_file_path, "docs: Add Complexity and Risk Assessment")

        except Exception as e:
            logging.error(f"Failed to finalize and save complexity assessment: {e}")

    def finalize_and_save_tech_spec(self, tech_spec_draft: str, target_os: str):
        """
        Saves the final technical spec to the database and a file,
        extracts key info, and transitions to the next phase.
        """
        if not self.project_id:
            logging.error("Cannot save technical spec; no active project.")
            return

        try:
            final_doc_with_header = self._prepend_standard_header(
                document_content=tech_spec_draft,
                document_type="Technical Specification"
            )

            db = self.db_manager
            db.update_project_field(self.project_id, "target_os", target_os)
            db.update_project_field(self.project_id, "tech_spec_text", final_doc_with_header)

            project_details = db.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "_docs"
                spec_file_path = docs_dir / "technical_spec.md"
                spec_file_path.write_text(final_doc_with_header, encoding="utf-8")

                # Commit the new document
                self._commit_document(spec_file_path, "docs: Finalize Technical Specification")

            self._extract_and_save_primary_technology(final_doc_with_header)
            self.set_phase("BUILD_SCRIPT_SETUP")

        except Exception as e:
            logging.error(f"Failed to finalize and save technical spec: {e}")

    def finalize_and_save_coding_standard(self, standard_draft: str):
        """
        Saves the final coding standard to the database and a file,
        and transitions to the next phase.
        """
        if not self.project_id:
            logging.error("Cannot save coding standard; no active project.")
            return

        try:
            final_doc_with_header = self._prepend_standard_header(
                document_content=standard_draft,
                document_type="Coding Standard"
            )

            db = self.db_manager
            db.update_project_field(self.project_id, "coding_standard_text", final_doc_with_header)

            project_details = db.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "_docs"
                standard_file_path = docs_dir / "coding_standard.md"
                standard_file_path.write_text(final_doc_with_header, encoding="utf-8")

                # Commit the new document
                self._commit_document(standard_file_path, "docs: Finalize Coding Standard")

            self.set_phase("PLANNING")

        except Exception as e:
            logging.error(f"Failed to finalize and save coding standard: {e}")

    def finalize_and_save_dev_plan(self, plan_json_string: str) -> tuple[bool, str]:
        """
        Saves the final dev plan to the database and a file,
        loads it into the active state, and transitions to Genesis.
        """
        if not self.project_id:
            return False, "No active project."

        try:
            final_doc_with_header = self._prepend_standard_header(
                document_content=plan_json_string,
                document_type="Sequential Development Plan"
            )

            db = self.db_manager
            db.update_project_field(self.project_id, "development_plan_text", final_doc_with_header)

            project_details = db.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "_docs"
                plan_file_path = docs_dir / "development_plan.json"
                plan_file_path.write_text(plan_json_string, encoding="utf-8")

                # Commit the new document
                self._commit_document(plan_file_path, "docs: Finalize Development Plan")

            full_plan_data = json.loads(plan_json_string)
            dev_plan_list = full_plan_data.get("development_plan")
            if dev_plan_list is None:
                raise ValueError("The plan JSON is missing the 'development_plan' key.")

            self.load_development_plan(json.dumps(dev_plan_list))
            self.set_phase("GENESIS")
            return True, "Plan approved! Starting development..."

        except Exception as e:
            logging.error(f"Failed to finalize and save development plan: {e}")
            return False, f"Failed to process the development plan: {e}"

    def set_phase(self, phase_name: str):
        """
        Sets the current project phase and automatically saves the new state.
        Also handles setting the project's dirty flag based on the transition.
        """
        try:
            new_phase = FactoryPhase[phase_name]

            # If a project is active, check if this phase transition should mark it as dirty.
            # We don't mark as dirty for non-modifying states.
            non_dirtying_phases = [
                FactoryPhase.IDLE,
                FactoryPhase.VIEWING_PROJECT_HISTORY,
                FactoryPhase.AWAITING_PREFLIGHT_RESOLUTION
            ]
            if self.project_id and new_phase not in non_dirtying_phases:
                logging.info(f"Project marked as dirty due to phase transition to {new_phase.name}")

            self.current_phase = new_phase
            logging.info(f"Transitioning to phase: {self.current_phase.name}")

            # If a project is active, save its new state to the database.
            if self.project_id:
                self._save_current_state()

        except KeyError:
            logging.error(f"Attempted to set an invalid phase: {phase_name}")

    def handle_proceed_action(self, progress_callback=None):
        """
        Handles the logic for the Genesis Pipeline, now with a progress callback.
        """
        if self.current_phase != FactoryPhase.GENESIS:
            logging.warning(f"Received 'Proceed' action in an unexpected phase: {self.current_phase.name}")
            return

        db = self.db_manager
        pm_behavior = db.get_config_value("PM_CHECKPOINT_BEHAVIOR") or "ALWAYS_ASK"
        is_auto_proceed = (pm_behavior == "AUTO_PROCEED")

        while True:
            if not self.active_plan or self.active_plan_cursor >= len(self.active_plan):
                if progress_callback: progress_callback("Development plan is empty or complete.")
                return

            task = self.active_plan[self.active_plan_cursor]
            component_name = task.get('component_name')
            logging.info(f"Executing task {self.active_plan_cursor + 1} for component: {component_name}")
            if progress_callback:
                progress_callback(f"Executing task {self.active_plan_cursor + 1}/{len(self.active_plan)} for component: {component_name}")

            try:
                project_details = db.get_project_by_id(self.project_id)
                project_root_path = Path(project_details['project_root_folder'])
                component_type = task.get("component_type", "CLASS")

                if component_type in ["DB_MIGRATION_SCRIPT", "BUILD_SCRIPT_MODIFICATION", "CONFIG_FILE_UPDATE"]:
                    self._execute_declarative_modification_task(task, project_root_path, db, progress_callback)
                else:
                    self._execute_source_code_generation_task(task, project_root_path, db, progress_callback)

                self.active_plan_cursor += 1

                if self.active_plan_cursor >= len(self.active_plan):
                    if self.is_genesis_complete:
                        self._run_post_implementation_doc_update()

                    logging.info("Development plan is complete. Performing pre-integration check.")
                    if progress_callback: progress_callback("Development plan complete. Checking for issues...")

                    non_passing_statuses = ["KNOWN_ISSUE", "UNIT_TESTS_FAILING", "DEBUG_PM_ESCALATION"]
                    known_issues = db.get_artifacts_by_statuses(self.project_id, non_passing_statuses)

                    if known_issues:
                        self.task_awaiting_approval = {"known_issues": [dict(row) for row in known_issues]}
                        self.set_phase("AWAITING_INTEGRATION_CONFIRMATION")
                    else:
                        self._run_integration_and_ui_testing_phase(progress_callback=progress_callback)
                    return

                if not is_auto_proceed:
                    break

            except Exception as e:
                logging.error(f"Genesis Pipeline failed for {component_name}. Error: {e}")
                self.escalate_for_manual_debug(str(e))
                return

    def _execute_source_code_generation_task(self, task: dict, project_root_path: Path, db: ASDFDBManager, progress_callback=None):
        """
        Handles the 'generate -> review -> correct -> verify -> commit -> update docs' workflow.
        """
        # --- DIAGNOSTIC STEP 1: Pre-Execution Check ---
        component_name = task.get("component_name")
        logging.info(f"--- GENESIS DIAGNOSTICS for component: {component_name} ---")
        existing_artifacts = self.db_manager.get_all_artifacts_for_project(self.project_id)
        for art in existing_artifacts:
            if art['artifact_name'] == component_name:
                logging.warning(f"[!! DUPLICATE WARNING !!] An artifact named '{component_name}' already exists in the database before execution begins. Artifact ID: {art['artifact_id']}")
        logging.info("--- Pre-Execution Check Complete ---")
        # --- END DIAGNOSTIC ---

        component_name = task.get("component_name")
        if progress_callback: progress_callback(f"Executing source code generation for: {component_name}")

        if not self.llm_service:
            raise Exception("Cannot generate code: LLM Service is not configured.")

        project_details = db.get_project_by_id(self.project_id)
        coding_standard = project_details['coding_standard_text']
        target_language = project_details['technology_stack']
        test_command = project_details['test_execution_command']

        all_artifacts_rows = db.get_all_artifacts_for_project(self.project_id)
        rowd_json = json.dumps([dict(row) for row in all_artifacts_rows])
        micro_spec_content = task.get("task_description")

        if progress_callback: progress_callback(f"Generating logic plan for {component_name}...")
        # CORRECTED: Typo in class name fixed
        logic_agent = LogicAgent_AppTarget(llm_service=self.llm_service)
        code_agent = CodeAgent_AppTarget(llm_service=self.llm_service)
        review_agent = CodeReviewAgent(llm_service=self.llm_service)
        test_agent = TestAgent_AppTarget(llm_service=self.llm_service)

        logic_plan = logic_agent.generate_logic_for_component(micro_spec_content)
        if progress_callback: progress_callback(f"Generating source code for {component_name}...")

        style_guide_to_use = project_details['ux_spec_text'] or project_details['final_spec_text']
        source_code = code_agent.generate_code_for_component(logic_plan, coding_standard, target_language, style_guide=style_guide_to_use)

        MAX_REVIEW_ATTEMPTS = 2
        for attempt in range(MAX_REVIEW_ATTEMPTS):
            if progress_callback: progress_callback(f"Reviewing code for {component_name} (Attempt {attempt + 1})...")
            review_status, review_output = review_agent.review_code(micro_spec_content, logic_plan, source_code, rowd_json, coding_standard)
            if review_status == "pass":
                break
            elif review_status == "pass_with_fixes":
                source_code = review_output
                break
            elif review_status == "fail":
                if attempt < MAX_REVIEW_ATTEMPTS - 1:
                    if progress_callback: progress_callback(f"Re-writing code for {component_name} based on feedback...")
                    source_code = code_agent.generate_code_for_component(logic_plan, coding_standard, target_language, feedback=review_output)
                else:
                    raise Exception(f"Component '{component_name}' failed code review after all attempts.")

        if progress_callback: progress_callback(f"Generating unit tests for {component_name}...")
        unit_tests = test_agent.generate_unit_tests_for_component(source_code, micro_spec_content, coding_standard, target_language)

        if progress_callback: progress_callback(f"Writing files, testing, and committing {component_name}...")
        build_agent = BuildAndCommitAgentAppTarget(str(project_root_path))
        success, result_message = build_agent.build_and_commit_component(
            task.get("component_file_path"), source_code,
            task.get("test_file_path"), unit_tests, test_command, self.llm_service
        )

        if not success:
            raise Exception(f"BuildAndCommitAgent failed for {component_name}: {result_message}")

        commit_hash = result_message.split(":")[-1].strip() if "New commit hash:" in result_message else "N/A"

        if progress_callback: progress_callback(f"Updating project records for {component_name}...")
        doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)
        doc_agent.update_artifact_record({
            "artifact_id": f"art_{uuid.uuid4().hex[:8]}", "project_id": self.project_id,
            "file_path": task.get("component_file_path"), "artifact_name": component_name,
            "artifact_type": task.get("component_type"), "short_description": micro_spec_content,
            "status": "UNIT_TESTS_PASSING", "unit_test_status": "TESTS_PASSING",
            "commit_hash": commit_hash, "version": 1,
            "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
            "micro_spec_id": task.get("micro_spec_id")
        })
        # --- DIAGNOSTIC STEP 2: Post-Execution Log ---
        logging.info(f"--- GENESIS DIAGNOSTICS for component: {component_name} (Post-Save) ---")
        final_artifacts = self.db_manager.get_all_artifacts_for_project(self.project_id)
        count = 0
        for art in final_artifacts:
            if art['artifact_name'] == component_name:
                count += 1
        logging.info(f"Found {count} artifact(s) named '{component_name}' in the database after saving.")
        logging.info("--------------------------------------------------")
        # --- END DIAGNOSTIC ---

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
        After a CR/bug fix plan is fully implemented, this method updates all
        relevant project documents using its own database connection.
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

            implementation_plan_for_update = json.dumps(self.active_plan, indent=4)
            doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)

            def update_document(doc_key: str, doc_name: str, save_func):
                original_doc = project_details[doc_key]
                if original_doc:
                    logging.info(f"Checking for {doc_name} updates...")
                    updated_content = doc_agent.update_specification_text(
                        original_spec=original_doc,
                        implementation_plan=implementation_plan_for_update
                    )
                    if updated_content != original_doc:
                        doc_with_header = self._prepend_standard_header(updated_content, doc_name)
                        # This uses a generic field update now
                        db.update_project_field(self.project_id, doc_key, doc_with_header)
                        logging.info(f"Successfully updated and saved the {doc_name}.")

            update_document('final_spec_text', 'Application Specification', lambda pid, val: db.update_project_field(pid, 'final_spec_text', val))
            update_document('tech_spec_text', 'Technical Specification', lambda pid, val: db.update_project_field(pid, 'tech_spec_text', val))
            update_document('ux_spec_text', 'UX/UI Specification', lambda pid, val: db.update_project_field(pid, 'ux_spec_text', val))
            update_document('ui_test_plan_text', 'UI Test Plan', lambda pid, val: db.update_project_field(pid, 'ui_test_plan_text', val))
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

    def _determine_resume_phase_from_rowd(self, db: ASDFDBManager) -> FactoryPhase:
        """
        Analyzes the loaded project documents to determine the correct logical
        phase to resume from.
        """
        logging.info("Analyzing loaded project state to determine the correct resume phase...")
        project_details = self.db_manager.get_project_by_id(self.project_id)

        if not project_details:
            return FactoryPhase.SPEC_ELABORATION

        if project_details['ui_test_plan_text']:
            logging.info("Resume point determined: MANUAL_UI_TESTING (UI test plan exists).")
            return FactoryPhase.MANUAL_UI_TESTING
        if project_details['integration_plan_text']:
            logging.info("Resume point determined: INTEGRATION_AND_VERIFICATION (Integration plan exists).")
            return FactoryPhase.INTEGRATION_AND_VERIFICATION
        if project_details['development_plan_text']:
            logging.info("Resume point determined: GENESIS (Development plan exists).")
            return FactoryPhase.GENESIS
        if project_details['coding_standard_text']:
            logging.info("Resume point determined: PLANNING (Coding standard exists).")
            return FactoryPhase.PLANNING
        if project_details['tech_spec_text']:
            logging.info("Resume point determined: CODING_STANDARD_GENERATION (Tech spec exists).")
            return FactoryPhase.CODING_STANDARD_GENERATION
        if project_details['final_spec_text']:
            logging.info("Resume point determined: TECHNICAL_SPECIFICATION (App spec exists).")
            return FactoryPhase.TECHNICAL_SPECIFICATION
        if project_details['ux_spec_text']:
            logging.info("Resume point determined: ENV_SETUP_TARGET_APP (UX spec exists).")
            return FactoryPhase.ENV_SETUP_TARGET_APP

        logging.info("Resume point determined: SPEC_ELABORATION (Default).")
        return FactoryPhase.SPEC_ELABORATION

    def _run_integration_and_ui_testing_phase(self, progress_callback=None):
        """
        Executes the full Integration and UI Testing workflow, including planning,
        execution, and final test plan generation.
        """
        logging.info("Starting Phase: Automated Integration & Verification.")
        if progress_callback:
            progress_callback("Starting Phase: Automated Integration & Verification.")

        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise FileNotFoundError("Project root folder not found for integration phase.")

            project_root_path = Path(project_details['project_root_folder'])
            docs_dir = project_root_path / "_docs"

            if progress_callback: progress_callback("Analyzing project for integration points...")

            # For this version, we assume all new artifacts are potential integration points
            # A more advanced version could be more selective.
            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            new_artifacts_for_integration = [dict(row) for row in all_artifacts]

            # Determine which existing files are the most likely integration points
            integration_files_to_load = self._get_integration_context_files(db, new_artifacts_for_integration)
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

            # --- This is the new, crucial execution logic ---
            if progress_callback: progress_callback("Executing Integration Plan...")
            orchestration_agent = OrchestrationCodeAgent(llm_service=self.llm_service)
            integration_plan = json.loads(integration_plan_json)

            for file_path_str, modifications in integration_plan.items():
                target_file_path = project_root_path / file_path_str
                original_code = target_file_path.read_text(encoding='utf-8') if target_file_path.exists() else ""

                modified_code = orchestration_agent.apply_modifications(original_code, json.dumps(modifications))
                target_file_path.write_text(modified_code, encoding='utf-8')
                logging.info(f"Applied integration modifications to {file_path_str}")
            # --- End of new logic ---

            final_integration_plan = self._prepend_standard_header(
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

            final_ui_test_plan = self._prepend_standard_header(
                document_content=ui_test_plan_content,
                document_type="UI Test Plan"
            )
            db.update_project_field(self.project_id, "ui_test_plan_text", final_ui_test_plan)

            test_plan_file_path = docs_dir / "ui_test_plan.md"
            test_plan_file_path.write_text(final_ui_test_plan, encoding="utf-8")
            self._commit_document(test_plan_file_path, "docs: Add UI Test Plan")

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
                self.set_phase("IDLE")
            else:
                logging.warning("UI test result evaluation complete: Failures detected.")
                self.escalate_for_manual_debug(failure_summary, is_functional_bug=True)

        except Exception as e:
            logging.error(f"An unexpected error occurred during UI test result evaluation: {e}")
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
        """
        if not self.project_id:
            logging.error("Cannot save change request; no active project.")
            return

        try:
            # Corrected: Direct call to the db_manager
            self.db_manager.add_change_request(self.project_id, description, request_type)
            self.set_phase("AWAITING_INITIAL_IMPACT_ANALYSIS")
            logging.info("Successfully saved new Functional Enhancement CR.")
        except Exception as e:
            logging.error(f"Failed to save new change request: {e}")

    def save_spec_correction_cr(self, new_spec_text: str):
        """
        Saves a 'Specification Correction' CR, runs an immediate impact analysis
        and auto-generates a linked CR for the required code changes.
        """
        if not self.project_id:
            logging.error("Cannot save spec correction; no active project.")
            return

        try:
            if not self.llm_service:
                raise Exception("Cannot run impact analysis: LLM Service is not configured.")

            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            original_spec_text = project_details['final_spec_text']

            spec_cr_description = "Correction to Application Specification. See linked CR for code implementation."
            spec_cr_id = db.add_change_request(
                project_id=self.project_id,
                description=spec_cr_description,
                request_type='SPEC_CORRECTION'
            )
            db.update_cr_status(spec_cr_id, "COMPLETED")

            db.update_project_field(self.project_id, "final_spec_text", new_spec_text)
            logging.info(f"Saved new specification text for CR-{spec_cr_id}.")

            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            rowd_json = json.dumps([dict(row) for row in all_artifacts])

            cr_desc_for_agent = (
                "Analyze the difference between the 'Original Specification' and the 'New Specification' "
                "to identify the necessary code changes. The 'New Specification' is the source of truth."
                f"\n\n--- Original Specification ---\n{original_spec_text}"
                f"\n\n--- New Specification ---\n{new_spec_text}"
            )

            impact_agent = ImpactAnalysisAgent_AppTarget(llm_service=self.llm_service)
            _, summary, impacted_ids = impact_agent.analyze_impact(
                change_request_desc=cr_desc_for_agent,
                final_spec_text=new_spec_text,
                rowd_json=rowd_json
            )

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

            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

        except Exception as e:
            logging.error(f"Failed to process specification correction CR: {e}")
            self.set_phase("RAISING_CHANGE_REQUEST")

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
        """
        if not self.project_id:
            logging.error("Cannot save bug report; no active project.")
            return False

        if not description or not description.strip():
            logging.warning("Cannot save empty bug report description.")
            return False

        try:
            # Corrected: Direct call to the db_manager
            self.db_manager.add_bug_report(self.project_id, description, severity)

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
        # This action is allowed from any post-genesis phase.
        logging.info("PM chose to 'Manage CRs / Bugs'. Transitioning to selection screen.")
        self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

    def handle_implement_cr_action(self, cr_id: int):
        """
        Handles the logic for when the PM confirms a CR for implementation.
        """
        logging.info(f"PM has confirmed implementation for Change Request ID: {cr_id}.")

        try:
            if not self.llm_service:
                raise Exception("Cannot implement CR: LLM Service is not configured.")

            db = self.db_manager
            cr_details = db.get_cr_by_id(cr_id)
            if not cr_details:
                raise Exception(f"CR-{cr_id} not found in the database.")

            analysis_timestamp_str = cr_details['last_modified_timestamp']
            last_commit_timestamp = self.get_latest_commit_timestamp()

            if analysis_timestamp_str and last_commit_timestamp:
                analysis_time = datetime.fromisoformat(analysis_timestamp_str)
                if last_commit_timestamp > analysis_time:
                    logging.warning(f"Impact analysis for CR-{cr_id} is stale. Awaiting PM confirmation.")
                    self.task_awaiting_approval = {"cr_id_for_reanalysis": cr_id}
                    self.set_phase("AWAITING_IMPACT_ANALYSIS_CHOICE")
                    return

            project_details = db.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise FileNotFoundError("Project root folder not found for CR implementation.")

            project_root_path = Path(project_details['project_root_folder'])
            impacted_ids = json.loads(cr_details['impacted_artifact_ids'] or '[]')
            source_code_files = {}
            for artifact_id in impacted_ids:
                artifact_record = db.get_artifact_by_id(artifact_id)
                if artifact_record and artifact_record['file_path']:
                    try:
                        source_path = project_root_path / artifact_record['file_path']
                        if source_path.exists():
                            source_code_files[artifact_record['file_path']] = source_path.read_text(encoding='utf-8')
                    except Exception:
                        pass

            core_docs = {"final_spec_text": project_details['final_spec_text']}
            context_package = self._build_and_validate_context_package(db, core_docs, source_code_files)

            if context_package.get("error"):
                raise Exception(f"Context Builder Error: {context_package['error']}")

            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            rowd_json = json.dumps([dict(row) for row in all_artifacts])
            db.update_cr_status(cr_id, "PLANNING_IN_PROGRESS")

            planner_agent = RefactoringPlannerAgent_AppTarget(llm_service=self.llm_service)
            new_plan_str = planner_agent.create_refactoring_plan(
                cr_details['description'], project_details['final_spec_text'], rowd_json, context_package["source_code"]
            )

            if "error" in new_plan_str:
                raise Exception(f"RefactoringPlannerAgent failed: {new_plan_str}")

            self.active_plan = json.loads(new_plan_str)
            self.active_plan_cursor = 0
            logging.info("Successfully generated new development plan from Change Request.")
            self.set_phase("GENESIS")

        except Exception as e:
            logging.error(f"Failed to process implementation for CR-{cr_id}. Error: {e}")
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

    def handle_stale_analysis_choice(self, choice: str, cr_id: int):
        """
        Handles the PM's choice on how to proceed with a stale impact analysis.
        """
        self.task_awaiting_approval = None # Always clear the approval task

        if choice == "RE-RUN":
            logging.info(f"PM chose to re-run stale impact analysis for CR-{cr_id}.")
            # Trigger the analysis and then immediately try to implement again.
            self.handle_run_impact_analysis_action(cr_id)
            self.handle_implement_cr_action(cr_id)

        elif choice == "PROCEED":
            logging.warning(f"PM chose to proceed with a stale impact analysis for CR-{cr_id}. Returning to CR Register.")
            # This is the pragmatic choice: return the user to the register,
            # where they can re-trigger the implementation.
            self.set_phase("IMPLEMENTING_CHANGE_REQUEST")

    def handle_run_impact_analysis_action(self, cr_id: int):
        """
        Orchestrates the running of an impact analysis for a specific CR.
        """
        logging.info(f"PM has requested to run impact analysis for CR ID: {cr_id}.")
        try:
            if not self.llm_service:
                raise Exception("Cannot run impact analysis: LLM Service is not configured.")

            db = self.db_manager
            cr_details = db.get_cr_by_id(cr_id)
            project_details = db.get_project_by_id(self.project_id)
            all_artifacts = db.get_all_artifacts_for_project(self.project_id)

            rowd_json = json.dumps([dict(row) for row in all_artifacts], indent=4)

            agent = ImpactAnalysisAgent_AppTarget(llm_service=self.llm_service)
            rating, summary, impacted_ids = agent.analyze_impact(
                change_request_desc=cr_details['description'],
                final_spec_text=project_details['final_spec_text'],
                rowd_json=rowd_json
            )

            if rating is None:
                raise Exception(f"ImpactAnalysisAgent failed: {summary}")

            db.update_cr_impact_analysis(cr_id, rating, summary, impacted_ids)
            logging.info(f"Successfully ran and saved impact analysis for CR ID: {cr_id}.")

        except Exception as e:
            logging.error(f"Failed to run impact analysis for CR ID {cr_id}: {e}")

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
        """
        if self.active_cr_id_for_edit is None:
            logging.error("Attempted to save an edited CR but no active_cr_id_for_edit is set.")
            return False

        if not new_description or not new_description.strip():
            logging.warning("Cannot save empty change request description.")
            return False

        try:
            cr_id_to_update = self.active_cr_id_for_edit
            self.db_manager.update_change_request(cr_id_to_update, new_description)

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

    def resume_project(self):
        """
        Resumes a paused project by loading its last saved detailed state and
        then clearing the saved state from the database.
        """
        if not self.resumable_state:
            logging.warning("Resume called but no resumable state was found on initialization.")
            return False

        try:
            state_details_json = self.resumable_state['state_details']
            if state_details_json:
                details = json.loads(state_details_json)
                self.active_plan = details.get("active_plan")
                self.active_plan_cursor = details.get("active_plan_cursor", 0)
                self.debug_attempt_counter = details.get("debug_attempt_counter", 0)
                self.task_awaiting_approval = details.get("task_awaiting_approval")

            logging.info(f"Project '{self.project_name}' resumed successfully.")

            # Corrected: Direct call to the db_manager
            self.db_manager.delete_orchestration_state_for_project(self.project_id)

            self.resumable_state = None # Clear the in-memory flag
            return True

        except Exception as e:
            logging.error(f"An error occurred while resuming project {self.project_id}: {e}")
            return False

    def escalate_for_manual_debug(self, failure_log: str, is_functional_bug: bool = False):
        """
        Initiates the multi-tiered triage and debug process.
        """
        logging.info("A failure has triggered the debugging pipeline.")

        if is_functional_bug:
            self._plan_fix_from_description(failure_log)
            return

        self.debug_attempt_counter += 1
        logging.info(f"Technical debug attempt counter is now: {self.debug_attempt_counter}")

        try:
            db = self.db_manager
            max_attempts_str = db.get_config_value("MAX_DEBUG_ATTEMPTS") or "2"
            max_attempts = int(max_attempts_str)

            if self.debug_attempt_counter > max_attempts:
                logging.warning(f"Automated debug attempts have exceeded the limit of {max_attempts}. Escalating to PM.")
                self.task_awaiting_approval = {"failure_log": failure_log}
                self.set_phase("DEBUG_PM_ESCALATION")
                return

            if not self.llm_service:
                raise Exception("Cannot proceed with debugging: LLM Service is not configured.")

            project_details = db.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                raise FileNotFoundError("Project root folder not found for debugging.")

            project_root_path = Path(project_details['project_root_folder'])

            triage_agent = TriageAgent_AppTarget(llm_service=self.llm_service, db_manager=self.db_manager)
            context_package = {}

            logging.info("Applying Adaptive Context Strategy for debugging...")
            limit_str = db.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "2000000"
            context_limit = int(limit_str)

            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            all_source_files = {}
            total_chars = 0

            for artifact in all_artifacts:
                file_path_str = artifact['file_path']
                if file_path_str and file_path_str.lower() != 'n/a':
                    full_path = project_root_path / file_path_str
                    if full_path.exists() and full_path.is_file():
                        try:
                            content = full_path.read_text(encoding='utf-8')
                            all_source_files[file_path_str] = content
                            total_chars += len(content)
                        except Exception as e:
                            logging.warning(f"Could not read file for debug context: {full_path}. Error: {e}")

            if total_chars > 0 and total_chars < context_limit:
                logging.info(f"Full project source code ({total_chars:,} chars) fits within the context limit ({context_limit:,} chars). Using rich context for triage.")
                context_package = all_source_files
            else:
                if total_chars > 0:
                     logging.warning(f"Full project source ({total_chars:,} chars) exceeds limit ({context_limit:,} chars). Falling back to heuristic triage.")

                logging.info("Attempting Tier 1 analysis: Parsing stack trace.")
                file_paths_from_trace = triage_agent.parse_stack_trace(failure_log)

                if file_paths_from_trace:
                    logging.info(f"Tier 1 Success: Found {len(file_paths_from_trace)} files in stack trace.")
                    for file_path in file_paths_from_trace:
                        full_path = project_root_path / file_path
                        if full_path.exists():
                            context_package[file_path] = full_path.read_text(encoding='utf-8')
                        else:
                            logging.warning(f"File '{file_path}' from stack trace not found at '{full_path}'.")

                if not context_package:
                    logging.warning("Tier 1 Failed. Proceeding to Tier 2 analysis: Apex Trace.")
                    apex_file_name = project_details.get('apex_executable_name')
                    failing_task = self.get_current_task_details()
                    failing_component_name = failing_task.get('component_name') if failing_task else None

                    if apex_file_name and failing_component_name:
                        all_artifacts_json = json.dumps([dict(row) for row in all_artifacts])
                        file_paths_from_trace_json = triage_agent.perform_apex_trace_analysis(all_artifacts_json, apex_file_name, failing_component_name)
                        file_paths_from_trace = json.loads(file_paths_from_trace_json)

                        if file_paths_from_trace:
                            logging.info(f"Tier 2 Success: Found {len(file_paths_from_trace)} files in apex trace.")
                            for file_path in file_paths_from_trace:
                                full_path = project_root_path / file_path
                                if full_path.exists():
                                    context_package[file_path] = full_path.read_text(encoding='utf-8')
                                else:
                                    logging.warning(f"File '{file_path}' from apex trace not found at '{full_path}'.")
                    else:
                        logging.warning("Tier 2 skipped: Apex executable name or failing component name not available.")

            if context_package:
                logging.info("Automated Triage Success: Context gathered. Proceeding to plan a fix.")
                self._plan_and_execute_fix(failure_log, context_package)
                return
            else:
                logging.warning("Automated Triage (Tiers 1 & 2) failed to gather context. Escalating to PM for Tier 3.")
                self.task_awaiting_approval = {"failure_log": failure_log}
                self.set_phase("AWAITING_PM_TRIAGE_INPUT")

        except Exception as e:
            logging.error(f"A critical error occurred during the triage process: {e}")
            self.task_awaiting_approval = {"failure_log": str(e)}
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
            if self.task_awaiting_approval:
                self.debug_attempt_counter = 0
                failure_log_from_state = self.task_awaiting_approval.get('failure_log', "PM-initiated retry after escalation.")
                self.task_awaiting_approval = None
                self.escalate_for_manual_debug(failure_log_from_state)
            else:
                logging.warning("Retry clicked, but no failure context found. Returning to GENESIS.")
                self.set_phase("GENESIS")

        elif choice == "MANUAL_PAUSE":
            self.set_phase("IDLE")
            logging.info("Project paused for manual PM investigation. State has been saved.")

        elif choice == "IGNORE":
            logging.warning("Acknowledging and ignoring bug. Updating artifact status to 'KNOWN_ISSUE'.")
            try:
                if self.task_awaiting_approval:
                    failing_artifact_id = self.task_awaiting_approval.get('failing_artifact_id')
                    if failing_artifact_id:
                        timestamp = datetime.now(timezone.utc).isoformat()
                        self.db_manager.update_artifact_status(failing_artifact_id, "KNOWN_ISSUE", timestamp)
                        logging.info(f"Status of artifact {failing_artifact_id} set to KNOWN_ISSUE.")
                    else:
                        logging.error("Could not identify the specific failing artifact to mark as 'KNOWN_ISSUE'.")

                self.set_phase("GENESIS")
                self.active_plan_cursor += 1
                self.task_awaiting_approval = None

            except Exception as e:
                logging.error(f"Failed to update artifact status to 'KNOWN_ISSUE': {e}")
                self.set_phase("GENESIS")
                self.task_awaiting_approval = None

    def _prepend_standard_header(self, document_content: str, document_type: str) -> str:
        """
        Prepends a standard project header, including a version number
        extracted from the content, to a given document.
        """
        if not self.project_id:
            return document_content # Cannot add header without a project ID

        # Attempt to find a version number like vX.X or Version X.X in the content
        version_number = "1.0" # Default to 1.0 if not found
        # Regex to find patterns like v0.7, v1.0, Version 1.2, etc., case-insensitively
        match = re.search(r'(?:v|Version\s)(\d+\.\d+)', document_content, re.IGNORECASE)
        if match:
            version_number = match.group(1)

        header = (
            f"PROJECT NUMBER: {self.project_id}\\n"
            f"{document_type.upper()}\\n"
            f"Version number: {version_number}\\n"
            f"{'-' * 50}\\n\\n"
        )
        return header + document_content

    def _commit_document(self, file_path: Path, commit_message: str):
        """A helper method to stage and commit a single document."""
        if not self.project_id:
            return
        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                logging.error(f"Cannot commit {file_path.name}: project root folder not found.")
                return

            project_root = Path(project_details['project_root_folder'])
            repo = git.Repo(project_root)

            relative_path = file_path.relative_to(project_root)
            repo.index.add([str(relative_path)])
            repo.index.commit(commit_message)
            logging.info(f"Successfully committed document: {relative_path}")
        except Exception as e:
            logging.error(f"Failed to commit document {file_path.name}. Error: {e}")

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
                "task_awaiting_approval": self.task_awaiting_approval
            }
            state_details_json = json.dumps(state_details_dict)

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


    def _clear_active_project_data(self, db):
        """Helper method to clear all data for the current project."""
        if not self.project_id:
            return
        db.delete_all_artifacts_for_project(self.project_id)
        db.delete_all_change_requests_for_project(self.project_id)
        db.delete_orchestration_state_for_project(self.project_id)
        db.delete_project_by_id(self.project_id)
        logging.info(f"Cleared all active data for project ID: {self.project_id}")


    def stop_and_export_project(self, archive_dir: str | Path, archive_name: str) -> str | None:
        """
        Exports all project data to files, adds a record to history,
        and clears the active project from the database.
        """
        if not self.project_id:
            logging.warning("No active project to stop and export.")
            return None

        archive_dir = Path(archive_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)

        rowd_file = archive_dir / f"{archive_name}_rowd.json"
        cr_file = archive_dir / f"{archive_name}_cr.json"
        project_file = archive_dir / f"{archive_name}_project.json"

        try:
            db = self.db_manager
            artifacts = db.get_all_artifacts_for_project(self.project_id)
            change_requests = db.get_all_change_requests_for_project(self.project_id)
            project_details_row = db.get_project_by_id(self.project_id)

            artifacts_list = [dict(row) for row in artifacts]
            with open(rowd_file, 'w', encoding='utf-8') as f:
                json.dump(artifacts_list, f, indent=4)

            cr_list = [dict(row) for row in change_requests]
            with open(cr_file, 'w', encoding='utf-8') as f:
                json.dump(cr_list, f, indent=4)

            if project_details_row:
                project_details_dict = dict(project_details_row)
                with open(project_file, 'w', encoding='utf-8') as f:
                    json.dump(project_details_dict, f, indent=4)

            root_folder_path = "N/A"
            if project_details_row and project_details_row['project_root_folder']:
                root_folder_path = project_details_row['project_root_folder']

            db.add_project_to_history(
                project_id=self.project_id,
                project_name=self.project_name,
                root_folder=root_folder_path,
                archive_path=str(rowd_file),
                timestamp=datetime.now(timezone.utc).isoformat()
            )

            self._clear_active_project_data(db)

            self.reset()
            logging.info(f"Successfully exported project '{self.project_name}' to {archive_dir}")
            return str(rowd_file)

        except Exception as e:
            logging.error(f"Failed to stop and export project: {e}", exc_info=True)
            return None

    def _perform_preflight_checks(self, project_root_str: str) -> dict:
        """
        Performs a sequence of pre-flight checks on an existing project environment.
        This version includes a more robust Git repository check.
        """
        import os
        import subprocess
        import git
        project_root = Path(project_root_str)

        # 1. Path Validation
        if not project_root.exists() or not project_root.is_dir():
            return {"status": "PATH_NOT_FOUND", "message": f"The project folder could not be found or is not a directory. Please confirm the new location: {project_root_str}"}

        # 2. VCS Validation (Multi-tiered check for robustness)
        # Check 2a: Directory existence
        if not (project_root / '.git').is_dir():
            return {"status": "GIT_MISSING", "message": "The project folder was found, but the .git directory is missing. Please re-initialize the repository."}

        # Check 2b: GitPython validation
        try:
            repo = git.Repo(project_root)
        except git.InvalidGitRepositoryError:
            return {"status": "GIT_MISSING", "message": "The project folder is not a valid Git repository (GitPython check failed)."}

        # Check 2c: Subprocess command validation (most robust)
        try:
            result = subprocess.run(
                ['git', 'status'],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
                startupinfo=subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW) if os.name == 'nt' else None
            )
            if result.returncode != 0:
                return {"status": "GIT_MISSING", "message": "The project folder is not a valid Git repository (command-line check failed)."}
        except FileNotFoundError:
            return {"status": "GIT_MISSING", "message": "Git command not found. Please ensure Git is installed and in your system's PATH."}

        # 3. State Drift Validation
        if repo.is_dirty(untracked_files=True):
            return {"status": "STATE_DRIFT", "message": "Uncommitted local changes have been detected. To prevent conflicts, please resolve the state of the repository."}

        # All checks passed
        return {"status": "ALL_PASS", "message": "Project environment successfully verified."}

    def handle_discard_changes(self, history_id: int):
        """
        Handles the 'Discard all local changes' expert option for a project
        with state drift. Resets the git repository and then re-runs the
        entire project loading sequence to ensure a clean state.
        """
        logging.warning(f"Executing 'git reset --hard' for project history ID: {history_id}")
        try:
            db = self.db_manager
            history_record = db.get_project_history_by_id(history_id)
            if not history_record:
                raise Exception(f"Could not find history record for ID {history_id} to get path.")

            project_root = Path(history_record['project_root_folder'])
            agent = RollbackAgent()
            success, message = agent.discard_local_changes(project_root)

            if not success:
                raise Exception(f"RollbackAgent failed: {message}")

            logging.info(f"Successfully discarded changes at {project_root}")

            # After successfully discarding changes, re-trigger the load process
            self.load_archived_project(history_id)

        except Exception as e:
            logging.error(f"Failed to discard changes for project history ID {history_id}: {e}")
            self.preflight_check_result = {"status": "ERROR", "message": str(e)}

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

    def load_archived_project(self, history_id: int):
        """
        Loads an archived project's data, performs pre-flight checks,
        and sets the appropriate phase for UI resolution.
        """
        try:
            db = self.db_manager
            if self.project_id and self.is_project_dirty:
                logging.warning(f"An active, modified project '{self.project_name}' was found. Performing a safety export.")
                archive_path_from_db = db.get_config_value("DEFAULT_ARCHIVE_PATH")
                if not archive_path_from_db or not archive_path_from_db.strip():
                    logging.error("Safety export failed: Default Project Archive Path is not set in Settings.")
                else:
                    archive_path = Path(archive_path_from_db)
                    archive_name = f"{self.project_name.replace(' ', '_')}_auto_export_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    self.stop_and_export_project(archive_path, archive_name)

            history_record = db.get_project_history_by_id(history_id)
            if not history_record:
                raise FileNotFoundError(f"No project history found for ID {history_id}")

            project_id_to_load = history_record['project_id']
            logging.info(f"Preparing to load project {project_id_to_load}. Clearing any lingering active data for this ID first.")
            self._clear_active_project_data(db) # Pass the db instance

            rowd_file_path = Path(history_record['archive_file_path'])
            project_file_path = rowd_file_path.with_name(rowd_file_path.name.replace("_rowd.json", "_project.json"))
            cr_file_path = rowd_file_path.with_name(rowd_file_path.name.replace("_rowd.json", "_cr.json"))

            if project_file_path.exists():
                with open(project_file_path, 'r', encoding='utf-8') as f:
                    project_data_to_load = json.load(f)
                db.create_or_update_project_record(project_data_to_load)

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
            check_result = self._perform_preflight_checks(history_record['project_root_folder'])
            self.preflight_check_result = {**check_result, "history_id": history_id}

            if check_result['status'] != "ALL_PASS":
                self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")
                return

            self.is_project_dirty = False
            self.resume_phase_after_load = self._determine_resume_phase_from_rowd(db)
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

    def _plan_and_execute_fix(self, failure_log: str, context_package: dict):
        """
        A helper method that invokes the FixPlannerAgent and prepares the
        resulting plan for execution by the Genesis pipeline.
        """
        logging.info("Invoking FixPlannerAgent with rich context to generate a fix plan...")

        if not self.llm_service:
            raise Exception("Cannot plan fix: LLM Service is not configured.")

        relevant_code = next(iter(context_package.values()), "No code context available.")

        planner_agent = FixPlannerAgent_AppTarget(llm_service=self.llm_service)
        fix_plan_str = planner_agent.create_fix_plan(
            root_cause_hypothesis=failure_log,
            relevant_code=relevant_code
        )

        try:
            # FIX: More robust check for a specific error structure
            parsed_plan = json.loads(fix_plan_str)
            if isinstance(parsed_plan, list) and len(parsed_plan) > 0 and parsed_plan[0].get("error"):
                raise Exception(f"FixPlannerAgent failed to generate a plan: {parsed_plan[0]['error']}")

            if not parsed_plan:
                raise Exception("FixPlannerAgent returned an empty plan.")

            self.active_plan = parsed_plan
            self.active_plan_cursor = 0
            self.set_phase("GENESIS")
            logging.info("Successfully generated a fix plan. Transitioning to GENESIS phase to apply the fix.")

        except (json.JSONDecodeError, TypeError) as e:
            raise Exception(f"FixPlannerAgent returned invalid JSON. Error: {e}. Response was: {fix_plan_str}")

    def _build_and_validate_context_package(self, core_documents: dict, source_code_files: dict) -> dict:
        """
        Gathers context, checks size, trims if necessary by prioritizing core
        documents and smaller source files, and reports on any excluded files.
        """
        final_context = {}
        excluded_files = []
        context_was_trimmed = False

        limit_str = self.db_manager.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "200000"
        char_limit = int(limit_str)

        core_doc_chars = 0
        for name, content in core_documents.items():
            final_context[name] = content
            core_doc_chars += len(content) if content else 0

        if core_doc_chars > char_limit:
            logging.error(f"Context Builder: Core documents ({core_doc_chars} chars) alone exceed the context limit of {char_limit}. Cannot proceed.")
            return {"source_code": {}, "was_trimmed": True, "error": "Core documents are too large for the context window.", "excluded_files": list(source_code_files.keys())}

        remaining_chars = char_limit - core_doc_chars
        sorted_source_files = sorted(source_code_files.items(), key=lambda item: len(item[1]))

        for file_path, content in sorted_source_files:
            if len(content) <= remaining_chars:
                final_context[file_path] = content
                remaining_chars -= len(content)
            else:
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

    def get_help_for_setup_task(self, task_instructions: str):
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

            target_os = project_details.get('target_os', 'Linux')

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

            doc_agent.add_or_update_artifact({
                "artifact_id": f"art_{uuid.uuid4().hex[:8]}",
                "project_id": self.project_id,
                "file_path": "N/A",
                "artifact_name": artifact_name,
                "artifact_type": "ENVIRONMENT_SETUP",
                "signature": "N/A",
                "short_description": description,
                "version": 1,
                "status": "KNOWN_ISSUE",
                "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
                "commit_hash": None,
                "micro_spec_id": None,
                "dependencies": None,
                "unit_test_status": "NOT_APPLICABLE"
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

            final_ui_test_plan = self._prepend_standard_header(
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