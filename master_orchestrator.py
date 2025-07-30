
import logging
import docx
import uuid
import json
import re
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
import git
import google.generativeai as genai
from llm_service import LLMService, GeminiAdapter, OpenAIAdapter, AnthropicAdapter, LocalPhi3Adapter, CustomEndpointAdapter
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
from agents.agent_orchestration_code_app_target import OrchestrationCodeAgent
from agents.agent_ui_test_planner_app_target import UITestPlannerAgent_AppTarget
from agents.agent_test_result_evaluation_app_target import TestResultEvaluationAgent_AppTarget
from agents.agent_fix_planner_app_target import FixPlannerAgent_AppTarget
from agents.agent_learning_capture import LearningCaptureAgent
from agents.agent_impact_analysis_app_target import ImpactAnalysisAgent_AppTarget
from agents.agent_test_environment_advisor import TestEnvironmentAdvisorAgent
from agents.agent_verification_app_target import VerificationAgent_AppTarget
from agents.agent_rollback_app_target import RollbackAgent


# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    VIEWING_PROJECT_HISTORY = auto()
    AWAITING_CONTEXT_REESTABLISHMENT = auto()
    AWAITING_PM_TRIAGE_INPUT = auto()
    AWAITING_REASSESSMENT_CONFIRMATION = auto()
    # Add other phases as they are developed

class MasterOrchestrator:
    """
    The central state machine and workflow manager for the ASDF.
    It coordinates agents, manages project state, and handles project lifecycle.
    """

    def __init__(self, db_path: str):
        """
        Initializes the MasterOrchestrator, now with self-aware state checking.
        """
        self.db_manager = ASDFDBManager(db_path)

        # Default empty state
        self.project_id: str | None = None
        self.project_name: str | None = None
        self.current_phase: FactoryPhase = FactoryPhase.IDLE
        self.active_plan = None
        self.active_plan_cursor = 0
        self.task_awaiting_approval = None
        self.preflight_check_result = None
        self.debug_attempt_counter = 0
        self.resume_phase_after_load = None
        self.active_ux_spec = {}

        # --- CORRECTED: Self-initialization from database ---
        # Upon creation, immediately check the DB for a resumable state.
        self.resumable_state = None
        with self.db_manager as db:
            db.create_tables()
            self.resumable_state = db.get_any_paused_state()
            if self.resumable_state:
                # If a paused state exists, adopt its identity immediately.
                self.project_id = self.resumable_state['project_id']
                self.current_phase = FactoryPhase[self.resumable_state['current_phase']]
                project_details = db.get_project_by_id(self.project_id)
                if project_details:
                    self.project_name = project_details['project_name']
                logging.info(f"Orchestrator initialized into a resumable state for project: {self.project_name}")

            # Configure logging based on DB settings
            log_level_str = db.get_config_value("LOGGING_LEVEL") or "Standard"
            if not db.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT"):
                db.set_config_value("CONTEXT_WINDOW_CHAR_LIMIT", "2000000")

            # --- Populate default context limits if they don't exist ---
            default_limits = {
                "GEMINI_CONTEXT_LIMIT": "6000000",
                "OPENAI_CONTEXT_LIMIT": "380000",
                "ANTHROPIC_CONTEXT_LIMIT": "600000",
                "LOCALPHI3_CONTEXT_LIMIT": "380000",
                "ENTERPRISE_CONTEXT_LIMIT": "128000"
            }
            for key, value in default_limits.items():
                if not db.get_config_value(key):
                    db.set_config_value(key, value, f"Default context character limit for {key.split('_')[0]}.")

            # --- Ensure active context limit is correctly initialized on startup ---
            if not db.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT"):
                logging.info("Active context limit not found. Initializing from provider default.")
                current_provider = db.get_config_value("SELECTED_LLM_PROVIDER") or "Gemini"
                provider_key_map = {
                    "Gemini": "GEMINI_CONTEXT_LIMIT", "OpenAI": "OPENAI_CONTEXT_LIMIT",
                    "Anthropic": "ANTHROPIC_CONTEXT_LIMIT", "LocalPhi3": "LOCALPHI3_CONTEXT_LIMIT",
                    "Enterprise": "ENTERPRISE_CONTEXT_LIMIT"
                }
                default_key = provider_key_map.get(current_provider)
                if default_key:
                    default_value = db.get_config_value(default_key)
                    if default_value:
                        db.set_config_value("CONTEXT_WINDOW_CHAR_LIMIT", default_value)
            # --- End of Bugfix ---

        log_level_map = {"Standard": logging.INFO, "Detailed": logging.DEBUG, "Debug": logging.DEBUG}
        log_level = log_level_map.get(log_level_str, logging.INFO)
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s', force=True)

        # --- Initialize the LLM Service ---
        self.llm_service = self._create_llm_service()
        if not self.llm_service:
            logging.error("MasterOrchestrator failed to initialize LLM service. Check configuration.")

        logging.info("MasterOrchestrator initialized.")

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

    def handle_ux_ui_brief_submission(self, brief_input):
        """
        Handles the initial project brief submission from either text or a file,
        saves the brief as a project artifact, stores its path, calls the
        triage agent, and prepares for the PM's decision.
        """
        if not self.project_id:
            logging.error("Cannot handle brief submission; no active project.")
            return

        try:
            # Create a dedicated directory for the project's internal documents
            project_data_dir = Path(f"data/projects/{self.project_id}")
            project_data_dir.mkdir(parents=True, exist_ok=True)

            brief_content = ""
            brief_file_path = ""

            # --- Step 1: Process and Save the Brief ---
            if isinstance(brief_input, str):
                brief_content = brief_input
                brief_file_path_obj = project_data_dir / "project_brief.md"
                with open(brief_file_path_obj, "w", encoding="utf-8") as f:
                    f.write(brief_content)
                brief_file_path = str(brief_file_path_obj)
                logging.info(f"Saved text brief to: {brief_file_path}")
            else: # Assumes it's a Streamlit UploadedFile object
                file_name = getattr(brief_input, 'name', 'project_brief_uploaded')
                brief_file_path_obj = project_data_dir / file_name

                # Read content for the agent
                if file_name.endswith('.docx'):
                    doc = docx.Document(brief_input)
                    brief_content = "\n".join([p.text for p in doc.paragraphs])
                    # Reset buffer after reading for the save operation below
                    brief_input.seek(0)
                else: # For .txt and .md
                    brief_content = brief_input.getvalue().decode("utf-8")

                # Save the original file
                with open(brief_file_path_obj, "wb") as f:
                    f.write(brief_input.getvalue())
                brief_file_path = str(brief_file_path_obj)
                logging.info(f"Saved uploaded brief to: {brief_file_path}")

            # --- Step 2: Save the path to the database ---
            with self.db_manager as db:
                db.update_project_brief_path(self.project_id, brief_file_path)

            # --- Step 3: Proceed with Analysis using the llm_service ---
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
            logging.error(f"Failed to handle UX/UI brief submission: {e}")
            self.task_awaiting_approval = {"analysis_error": str(e)}
            self.set_phase("AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION")

    def handle_ux_ui_phase_decision(self, decision: str):
        """
        Handles the PM's decision to either start the UX/UI phase or skip it.
        """
        # Persist the is_gui flag regardless of the decision, as it's now known.
        analysis_result = self.task_awaiting_approval.get("analysis", {})
        is_gui = analysis_result.get("requires_gui", False)
        with self.db_manager as db:
            db.update_project_is_gui_flag(self.project_id, is_gui)

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
        Compiles the final UX/UI Specification from all collected parts,
        saves it to the database, and transitions to the next main phase.

        Returns:
            bool: True on success, False on failure.
        """
        if not self.project_id:
            logging.error("Cannot complete UX spec; no active project.")
            return False

        try:
            # Part 1: Compile the final document
            final_spec_parts = []

            personas = self.active_ux_spec.get('confirmed_personas', [])
            if personas:
                final_spec_parts.append("## 1. User Personas\n- " + "\n- ".join(personas))

            journeys = self.active_ux_spec.get('confirmed_user_journeys', '')
            if journeys:
                final_spec_parts.append("## 2. Core User Journeys\n" + journeys)

            blueprints = self.active_ux_spec.get('screen_blueprints', {})
            if blueprints:
                blueprint_section = ["## 3. Structural Blueprint (JSON)"]
                blueprint_section.append("```json")
                # We need to load each JSON string before dumping the whole collection
                parsed_blueprints = {k: json.loads(v) for k, v in blueprints.items()}
                blueprint_section.append(json.dumps(parsed_blueprints, indent=2))
                blueprint_section.append("```")
                final_spec_parts.append("\n".join(blueprint_section))

            style_guide = self.active_ux_spec.get('style_guide', '')
            if style_guide:
                final_spec_parts.append("## 4. Theming & Style Guide\n" + style_guide)

            final_spec_doc = "\n\n---\n\n".join(final_spec_parts)

            # Prepend the standard header before saving
            final_doc_with_header = self._prepend_standard_header(
                document_content=final_spec_doc,
                document_type="UX/UI Specification"
            )

            # Part 2: Save to the database
            with self.db_manager as db:
                db.save_ux_specification(self.project_id, final_doc_with_header)

            logging.info("Successfully compiled and saved the final UX/UI Specification.")

            # Part 3: Clean up and transition
            self.active_ux_spec = {} # Clear the in-progress spec
            self.task_awaiting_approval = None # Clear any leftover data
            self.set_phase("ENV_SETUP_TARGET_APP")

            return True

        except Exception as e:
            logging.error(f"Failed to complete UX/UI Specification: {e}")
            # Store error for the UI to potentially display
            if 'error' not in self.active_ux_spec:
                 self.active_ux_spec['error'] = str(e)
            return False

    def finalize_and_save_app_spec(self, spec_draft: str):
        """
        Applies the standard header to the final application spec, saves it to
        the database, and transitions to the next phase.
        """
        if not self.project_id:
            logging.error("Cannot save application spec; no active project.")
            return

        try:
            # Prepend the standard header
            final_doc_with_header = self._prepend_standard_header(
                document_content=spec_draft,
                document_type="Application Specification"
            )

            # Save to the database
            with self.db_manager as db:
                db.save_final_specification(self.project_id, final_doc_with_header)

            logging.info("Successfully finalized and saved the Application Specification.")

            # Transition to the next phase
            self.set_phase("TECHNICAL_SPECIFICATION")

        except Exception as e:
            logging.error(f"Failed to finalize and save application spec: {e}")

    def finalize_and_save_tech_spec(self, tech_spec_draft: str, target_os: str):
        """
        Applies the standard header to the final technical spec, saves it,
        extracts key info, and transitions to the next phase.
        """
        if not self.project_id:
            logging.error("Cannot save technical spec; no active project.")
            return

        try:
            # Prepend the standard header
            final_doc_with_header = self._prepend_standard_header(
                document_content=tech_spec_draft,
                document_type="Technical Specification"
            )

            # Save to the database and update related fields
            with self.db_manager as db:
                db.update_project_os(self.project_id, target_os)
                db.save_tech_specification(self.project_id, final_doc_with_header)

            # Extract and save the primary technology for agent use
            self._extract_and_save_primary_technology(final_doc_with_header)

            logging.info("Successfully finalized and saved the Technical Specification.")

            # Transition to the next phase
            self.set_phase("BUILD_SCRIPT_SETUP")

        except Exception as e:
            logging.error(f"Failed to finalize and save technical spec: {e}")

    def finalize_and_save_coding_standard(self, standard_draft: str):
        """
        Applies the standard header to the final coding standard, saves it,
        and transitions to the next phase.
        """
        if not self.project_id:
            logging.error("Cannot save coding standard; no active project.")
            return

        try:
            # Prepend the standard header
            final_doc_with_header = self._prepend_standard_header(
                document_content=standard_draft,
                document_type="Coding Standard"
            )

            # Save to the database
            with self.db_manager as db:
                db.save_coding_standard(self.project_id, final_doc_with_header)

            logging.info("Successfully finalized and saved the Coding Standard.")

            # Transition to the next phase
            self.set_phase("PLANNING")

        except Exception as e:
            logging.error(f"Failed to finalize and save coding standard: {e}")

    def finalize_and_save_dev_plan(self, plan_json_string: str) -> tuple[bool, str]:
        """
        Applies the standard header to the final dev plan, saves it,
        loads it into the active state, and transitions to Genesis.
        """
        if not self.project_id:
            logging.error("Cannot save development plan; no active project.")
            return False, "No active project."

        try:
            # Prepend the standard header
            final_doc_with_header = self._prepend_standard_header(
                document_content=plan_json_string,
                document_type="Sequential Development Plan"
            )

            # Save to the database
            with self.db_manager as db:
                db.save_development_plan(self.project_id, final_doc_with_header)

            # Load the plan for execution
            full_plan_data = json.loads(plan_json_string)
            dev_plan_list = full_plan_data.get("development_plan")
            if dev_plan_list is None:
                raise ValueError("The plan JSON is missing the 'development_plan' key.")

            self.load_development_plan(json.dumps(dev_plan_list))

            logging.info("Successfully finalized and saved the Development Plan.")

            # Transition to the next phase
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

            if new_phase in [FactoryPhase.VIEWING_PROJECT_HISTORY, FactoryPhase.AWAITING_PREFLIGHT_RESOLUTION]:
                self.current_phase = new_phase
                logging.info(f"Transitioning to phase: {self.current_phase.name}")
                # We don't save state when just viewing history
                return

            if not self.project_id:
                logging.error("Cannot set phase; no active project.")
                return

            self.current_phase = new_phase
            logging.info(f"Project '{self.project_name}' phase changed to: {self.current_phase.name}")

            # Automatically save the state on every phase transition
            self._save_current_state()

        except KeyError:
            logging.error(f"Attempted to set an invalid phase: {phase_name}")

    def handle_proceed_action(self, status_ui_object=None):
        """
        Handles the logic for the Genesis Pipeline.
        This version is refactored to remove the outdated api_key dependency.
        """
        if self.current_phase != FactoryPhase.GENESIS:
            logging.warning(f"Received 'Proceed' action in an unexpected phase: {self.current_phase.name}")
            return

        with self.db_manager as db:
            pm_behavior = db.get_config_value("PM_CHECKPOINT_BEHAVIOR") or "ALWAYS_ASK"
            is_auto_proceed = (pm_behavior == "AUTO_PROCEED")

        while True:
            if not self.active_plan or self.active_plan_cursor >= len(self.active_plan):
                logging.info("Development plan is complete. Performing pre-integration check for known issues.")
                with self.db_manager as db:
                    non_passing_statuses = ["KNOWN_ISSUE", "UNIT_TESTS_FAILING", "DEBUG_PM_ESCALATION"]
                    known_issues = db.get_artifacts_by_statuses(self.project_id, non_passing_statuses)

                if known_issues:
                    logging.warning(f"Found {len(known_issues)} component(s) with known issues. Awaiting PM confirmation to proceed.")
                    self.task_awaiting_approval = {"known_issues": [dict(row) for row in known_issues]}
                    self.set_phase("AWAITING_INTEGRATION_CONFIRMATION")
                else:
                    logging.info("No known issues found. Proceeding directly to integration.")
                    self._run_integration_and_ui_testing_phase()
                return

            task = self.active_plan[self.active_plan_cursor]
            component_type = task.get("component_type", "CLASS")
            logging.info(f"Executing task {self.active_plan_cursor + 1} for component: {task.get('component_name')}")

            try:
                with self.db_manager as db:
                    project_details = db.get_project_by_id(self.project_id)
                    project_root_path = Path(project_details['project_root_folder'])

                    if component_type in ["DB_MIGRATION_SCRIPT", "BUILD_SCRIPT_MODIFICATION", "CONFIG_FILE_UPDATE"]:
                        # Note: We will fix the called method in the next step.
                        self._execute_declarative_modification_task(task, project_root_path, db, None)
                    else:
                        if component_type not in ["FUNCTION", "CLASS", "Model"]:
                            logging.warning(f"Unknown component_type '{component_type}' found. Defaulting to source code generation pipeline.")
                        self._execute_source_code_generation_task(task, project_root_path, db, status_ui_object)

                    self.active_plan_cursor += 1

                    if self.active_plan_cursor >= len(self.active_plan) and self.is_genesis_complete:
                        self._run_post_implementation_doc_update(db)

                if not is_auto_proceed:
                    break

            except Exception as e:
                logging.error(f"Genesis Pipeline failed while executing plan for {task.get('component_name')}. Error: {e}")
                self.escalate_for_manual_debug(str(e))
                return

    def _execute_source_code_generation_task(self, task: dict, project_root_path: Path, db: ASDFDBManager, status_ui_object=None):
        """
        Handles the 'generate -> review -> correct -> verify -> commit -> update docs' workflow.
        This version is refactored to use the central llm_service.
        """
        component_name = task.get("component_name")
        if status_ui_object: status_ui_object.update(label=f"Executing source code generation for: {component_name}")
        logging.info(f"Executing source code generation for: {component_name}")

        if not self.llm_service:
            raise Exception("Cannot generate code: LLM Service is not configured.")

        project_details = db.get_project_by_id(self.project_id)
        coding_standard = project_details['coding_standard_text']
        target_language = project_details['technology_stack']
        test_command = project_details['test_execution_command']
        is_build_automated = bool(project_details['is_build_automated'])

        if not target_language:
            raise Exception(f"Cannot generate code for '{component_name}': Target Language is not set for this project.")
        if is_build_automated and not test_command:
            raise Exception(f"Cannot verify component '{component_name}': Test Execution Command is not set for this project.")

        all_artifacts_rows = db.get_all_artifacts_for_project(self.project_id)
        rowd_json = json.dumps([dict(row) for row in all_artifacts_rows])
        micro_spec_content = task.get("task_description")

        # --- Code Generation and Review Loop ---
        if status_ui_object: status_ui_object.update(label=f"Generating logic plan for {component_name}...")
        logic_agent = LogicAgent_AppTarget(llm_service=self.llm_service)
        code_agent = CodeAgent_AppTarget(llm_service=self.llm_service)
        review_agent = CodeReviewAgent(llm_service=self.llm_service)
        test_agent = TestAgent_AppTarget(llm_service=self.llm_service)

        logic_plan = logic_agent.generate_logic_for_component(micro_spec_content)
        if status_ui_object: status_ui_object.update(label=f"Generating source code for {component_name}...")

        style_guide_to_use = project_details.get('ux_spec_text') or project_details.get('final_spec_text')

        source_code = code_agent.generate_code_for_component(
            logic_plan=logic_plan,
            coding_standard=coding_standard,
            target_language=target_language,
            style_guide=style_guide_to_use
        )

        MAX_REVIEW_ATTEMPTS = 2
        review_status = "fail"
        for attempt in range(MAX_REVIEW_ATTEMPTS):
            if status_ui_object: status_ui_object.update(label=f"Reviewing code for {component_name} (Attempt {attempt + 1})...")
            review_status, review_output = review_agent.review_code(micro_spec_content, logic_plan, source_code, rowd_json, coding_standard)
            if review_status == "pass":
                logging.info(f"Component '{component_name}' passed code review on attempt {attempt + 1}.")
                break
            elif review_status == "pass_with_fixes":
                logging.info(f"Component '{component_name}' passed code review on attempt {attempt + 1} with automated fixes.")
                source_code = review_output
                break
            elif review_status == "fail":
                logging.warning(f"Component '{component_name}' failed code review on attempt {attempt + 1}. Feedback: {review_output}")
                if attempt < MAX_REVIEW_ATTEMPTS - 1:
                    if status_ui_object: status_ui_object.update(label=f"Re-writing code for {component_name} based on feedback...")
                    logging.info("Attempting to rewrite the code based on feedback...")
                    source_code = code_agent.generate_code_for_component(logic_plan, coding_standard, target_language, feedback=review_output)
                else:
                    raise Exception(f"Component '{component_name}' failed code review after all attempts.")

        if review_status == "fail":
            raise Exception(f"Component '{component_name}' failed code review after all attempts.")

        if status_ui_object: status_ui_object.update(label=f"Generating unit tests for {component_name}...")
        unit_tests = test_agent.generate_unit_tests_for_component(source_code, micro_spec_content, coding_standard, target_language)

        if status_ui_object: status_ui_object.update(label=f"Writing files, testing, and committing {component_name}...")
        build_agent = BuildAndCommitAgentAppTarget(str(project_root_path))
        component_path_str = task.get("component_file_path")
        test_path_str = task.get("test_file_path")

        success, result_message = build_agent.build_and_commit_component(
            component_path_str=component_path_str,
            component_code=source_code,
            test_path_str=test_path_str,
            test_code=unit_tests,
            test_command=test_command,
            llm_service=self.llm_service
        )

        if not success:
            raise Exception(f"BuildAndCommitAgent failed for component {component_name}: {result_message}")

        if "New commit hash:" in result_message:
            commit_hash = result_message.split(":")[-1].strip()
        else:
            commit_hash = "N/A"

        if status_ui_object: status_ui_object.update(label=f"Updating project records for {component_name}...")
        doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)
        doc_agent.update_artifact_record({
            "artifact_id": f"art_{uuid.uuid4().hex[:8]}", "project_id": self.project_id,
            "file_path": component_path_str, "artifact_name": component_name,
            "artifact_type": task.get("component_type"), "short_description": micro_spec_content,
            "status": "UNIT_TESTS_PASSING", "unit_test_status": "TESTS_PASSING",
            "commit_hash": commit_hash, "version": 1,
            "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
            "micro_spec_id": task.get("micro_spec_id")
        })

    def _execute_declarative_modification_task(self, task: dict, project_root_path: Path, db: ASDFDBManager, status_ui_object=None):
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
        This version is refactored to use the central llm_service.
        """
        if not self.task_awaiting_approval:
            logging.error("Received a checkpoint decision, but no task is awaiting approval.")
            self.set_phase("GENESIS")
            return

        task = self.task_awaiting_approval
        component_name = task.get("component_name")
        logging.info(f"PM made decision '{decision}' for component '{component_name}'.")

        try:
            with self.db_manager as db:
                project_details = db.get_project_by_id(self.project_id)
                project_root_path = str(project_details['project_root_folder'])

                if decision == "EXECUTE_AUTOMATICALLY":
                    file_to_modify_path_str = task.get("component_file_path")
                    change_snippet = task.get("task_description")

                    if not file_to_modify_path_str or file_to_modify_path_str == "N/A":
                        raise ValueError(f"Invalid file path for declarative task '{component_name}'.")

                    file_to_modify = Path(project_root_path) / file_to_modify_path_str
                    file_to_modify.parent.mkdir(parents=True, exist_ok=True)

                    # For declarative changes, we append the snippet directly. This is more robust.
                    with open(file_to_modify, 'a', encoding='utf-8') as f:
                        f.write("\n" + change_snippet)

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

    def _run_post_implementation_doc_update(self, db: ASDFDBManager):
        """
        After a CR/bug fix plan is fully implemented, this method updates all
        relevant project documents.
        """
        logging.info("Change implementation complete. Running post-implementation documentation update...")
        project_details = db.get_project_by_id(self.project_id)
        if not project_details:
            logging.error("Could not run doc update; project details not found.")
            return

        if not self.llm_service:
            logging.error("Could not run doc update; LLM Service is not configured.")
            return

        implementation_plan_for_update = json.dumps(self.active_plan, indent=4)
        doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)

        # Helper function to process each document type
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
                    save_func(self.project_id, doc_with_header)
                    logging.info(f"Successfully updated and saved the {doc_name}.")

        # Update all relevant documents using the helper function
        update_document('final_spec_text', 'Application Specification', db.save_final_specification)
        update_document('tech_spec_text', 'Technical Specification', db.save_tech_specification)
        update_document('ux_spec_text', 'UX/UI Specification', db.save_ux_specification)
        update_document('ui_test_plan_text', 'UI Test Plan', db.save_ui_test_plan)

    def _get_integration_context_files(self, db: ASDFDBManager, new_artifacts: list[dict]) -> list[str]:
        """
        Uses the LLM service to determine which existing files are the most
        likely integration points.
        """
        logging.info("AI is analyzing the project to identify relevant integration files...")
        all_artifacts_rows = db.get_all_artifacts_for_project(self.project_id)
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
        project_details = db.get_project_by_id(self.project_id)

        if not project_details:
            # If for some reason project details don't exist, default to the start.
            return FactoryPhase.SPEC_ELABORATION

        # Logic flows from latest phase to earliest.
        # If a UI test plan exists, the project was in or past the final testing phase.
        if project_details['ui_test_plan_text']:
            logging.info("Resume point determined: MANUAL_UI_TESTING (UI test plan exists).")
            return FactoryPhase.MANUAL_UI_TESTING

        # If an integration plan exists, it was in or past the integration phase.
        if project_details['integration_plan_text']:
            logging.info("Resume point determined: INTEGRATION_AND_VERIFICATION (Integration plan exists).")
            return FactoryPhase.INTEGRATION_AND_VERIFICATION

        # If a development plan exists, it was in the development phase.
        if project_details['development_plan_text']:
            logging.info("Resume point determined: GENESIS (Development plan exists).")
            return FactoryPhase.GENESIS

        # If a tech spec exists, but no dev plan, it was in the planning phase.
        if project_details['tech_spec_text']:
            logging.info("Resume point determined: PLANNING (Tech spec exists).")
            return FactoryPhase.PLANNING

        # Default to the earliest phase if only the app spec exists.
        logging.info("Resume point determined: SPEC_ELABORATION (Default).")
        return FactoryPhase.SPEC_ELABORATION

    def _run_integration_and_ui_testing_phase(self):
        """
        Executes the full Integration and UI Testing workflow.
        This version is refactored to use the central llm_service.
        """
        logging.info("Starting Phase: Automated Integration & Verification.")
        self.set_phase("INTEGRATION_AND_VERIFICATION")

        try:
            if not self.llm_service:
                raise Exception("Cannot run integration: LLM Service is not configured.")

            with self.db_manager as db:
                project_details = db.get_project_by_id(self.project_id)
                if not project_details:
                    raise Exception(f"Could not retrieve project details for project ID: {self.project_id}")

                project_root_path = Path(project_details['project_root_folder'])
                statuses_to_integrate = ["UNIT_TESTS_PASSING", "UNIT_TESTS_FAILING", "KNOWN_ISSUE"]
                new_artifacts_rows = db.get_artifacts_by_statuses(self.project_id, statuses_to_integrate)

                if not new_artifacts_rows:
                    logging.warning("Integration phase started, but no new artifacts found to integrate. Skipping to UI Test Plan generation.")

                new_artifacts = [dict(row) for row in new_artifacts_rows]
                existing_files_context = {}

                logging.info("Applying Adaptive Context Strategy for integration planning...")
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
                                logging.warning(f"Could not read file for context: {full_path}. Error: {e}")

                if total_chars < context_limit:
                    logging.info(f"Full project source code ({total_chars:,} chars) fits within the context limit ({context_limit:,} chars). Using rich context.")
                    existing_files_context = all_source_files
                else:
                    logging.warning(f"Full project source ({total_chars:,} chars) exceeds limit ({context_limit:,} chars). Falling back to heuristic file selection.")
                    if new_artifacts:
                        integration_file_paths = self._get_integration_context_files(db, new_artifacts)
                        if not integration_file_paths:
                            raise Exception("AI could not identify any files for integration. Cannot proceed.")

                        for file_path_str in integration_file_paths:
                            full_path = project_root_path / file_path_str
                            if full_path.exists():
                                existing_files_context[file_path_str] = full_path.read_text(encoding='utf-8')
                            else:
                                logging.warning(f"AI identified integration file '{file_path_str}' but it was not found on disk. Skipping.")

                if new_artifacts:
                    new_artifacts_json = json.dumps(new_artifacts, indent=4)

                    logging.info("Invoking IntegrationPlannerAgent...")
                    planner_agent = IntegrationPlannerAgent(llm_service=self.llm_service)
                    integration_plan_str = planner_agent.create_integration_plan(new_artifacts_json, existing_files_context)
                    integration_plan = json.loads(integration_plan_str)

                    if "error" in integration_plan:
                        raise Exception(f"IntegrationPlannerAgent failed: {integration_plan['error']}")

                    plan_with_header = self._prepend_standard_header(integration_plan_str, "Integration Plan")
                    db.save_integration_plan(self.project_id, plan_with_header)

                    logging.info("Invoking OrchestrationCodeAgent to apply integration plan...")
                    code_agent = OrchestrationCodeAgent(llm_service=self.llm_service)
                    for file_path, modifications in integration_plan.items():
                        full_file_path = project_root_path / file_path
                        if not full_file_path.exists():
                            logging.warning(f"Integration plan specifies modifications for non-existent file: {file_path}. Skipping.")
                            continue
                        original_code = full_file_path.read_text(encoding='utf-8')
                        modified_code = code_agent.apply_modifications(original_code, json.dumps(modifications))
                        full_file_path.write_text(modified_code, encoding='utf-8')
                        logging.info(f"Successfully applied integration modifications to {file_path}.")

                logging.info("Invoking VerificationAgent for final verification...")
                verification_agent = VerificationAgent_AppTarget(llm_service=self.llm_service)

                test_command = project_details['test_execution_command']
                if not test_command:
                     raise Exception("Cannot run verification tests: Test command is not set.")

                status, test_output = verification_agent.run_all_tests(project_root_path, test_command)

                if status == 'CODE_FAILURE':
                    logging.error("Integration verification failed due to test failures. Triggering debug pipeline.")
                    self.escalate_for_manual_debug(test_output)
                    return
                elif status == 'ENVIRONMENT_FAILURE':
                    logging.error(f"Integration verification failed due to an environment error. Awaiting PM resolution.")
                    self.task_awaiting_approval = {"failure_reason": test_output}
                    self.set_phase("AWAITING_INTEGRATION_RESOLUTION")
                    return

                repo = git.Repo(project_root_path)
                if repo.is_dirty(untracked_files=True):
                    repo.git.add(A=True)
                    repo.index.commit(f"feat: Integrate all components for {self.project_name}")
                    logging.info("Successfully integrated all components and passed verification tests.")
                else:
                    logging.info("No changes to commit after integration. Verification tests passed.")

                functional_spec_text = project_details['final_spec_text']
                technical_spec_text = project_details['tech_spec_text']
                ui_test_planner = UITestPlannerAgent_AppTarget(llm_service=self.llm_service)
                ui_test_plan_content = ui_test_planner.generate_ui_test_plan(functional_spec_text, technical_spec_text)

                plan_with_header = self._prepend_standard_header(ui_test_plan_content, "UI Test Plan")
                db.save_ui_test_plan(self.project_id, plan_with_header)
                self.set_phase("MANUAL_UI_TESTING")

        except Exception as e:
            logging.error(f"Integration & Verification Phase failed. Awaiting PM resolution. Error: {e}")
            self.task_awaiting_approval = {"failure_reason": str(e)}
            self.set_phase("AWAITING_INTEGRATION_RESOLUTION")

    def handle_ui_test_result_upload(self, test_result_content: str):
        """
        Orchestrates the evaluation of an uploaded UI test results file.
        This version is refactored to use the central llm_service.
        """
        if not self.project_id:
            logging.error("Cannot handle test result upload; no active project.")
            return

        logging.info(f"Handling UI test result upload for project {self.project_id}.")
        try:
            if not self.llm_service:
                raise Exception("Cannot evaluate test results: LLM Service is not configured.")

            # 1. Evaluate the results using the dedicated agent.
            eval_agent = TestResultEvaluationAgent_AppTarget(llm_service=self.llm_service)
            failure_summary = eval_agent.evaluate_ui_test_results(test_result_content)

            # 2. Check the agent's response for failures.
            if "ALL_TESTS_PASSED" in failure_summary:
                logging.info("UI test result evaluation complete: All tests passed.")
            else:
                # 3. If failures are found, trigger the debug pipeline as a functional bug.
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
            self.set_phase("AWAITING_INITIAL_IMPACT_ANALYSIS")
            logging.info("Successfully saved new Functional Enhancement CR.")
        except Exception as e:
            logging.error(f"Failed to save new change request: {e}")

    def save_spec_correction_cr(self, new_spec_text: str):
        """
        Saves a 'Specification Correction' CR, runs an immediate impact analysis
        and auto-generates a linked CR for the required code changes.
        This version is refactored to use the central llm_service.
        """
        if not self.project_id:
            logging.error("Cannot save spec correction; no active project.")
            return

        try:
            if not self.llm_service:
                raise Exception("Cannot run impact analysis: LLM Service is not configured.")

            with self.db_manager as db:
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

                cr_desc_for_agent = (
                    "Analyze the difference between the 'Original Specification' and the 'New Specification' "
                    "to identify the necessary code changes. The 'New Specification' is the source of truth."
                    f"\n\n--- Original Specification ---\n{original_spec_text}"
                    f"\n\n--- New Specification ---\n{new_spec_text}"
                )

                impact_agent = ImpactAnalysisAgent_AppTarget(llm_service=self.llm_service)
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
            self.set_phase("RAISING_CHANGE_REQUEST")

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
        This version is refactored to use the central llm_service.
        """
        logging.info(f"PM has confirmed implementation for Change Request ID: {cr_id}.")

        try:
            if not self.llm_service:
                raise Exception("Cannot implement CR: LLM Service is not configured.")

            with self.db_manager as db:
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

                if context_package.get("was_trimmed"):
                    logging.warning(f"Context for CR-{cr_id} was trimmed.")

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
        This version is refactored to use the central llm_service.
        """
        logging.info(f"PM has requested to run impact analysis for CR ID: {cr_id}.")
        try:
            if not self.llm_service:
                raise Exception("Cannot run impact analysis: LLM Service is not configured.")

            with self.db_manager as db:
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
        bug_pending_statuses = ["UNIT_TESTS_FAILING", "DEBUG_IN_PROGRESS", "AWAITING_PM_TRIAGE_INPUT", "DEBUG_PM_ESCALATION", "KNOWN_ISSUE"]

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

            # CRITICAL: Delete the state from the DB after successfully resuming
            # to prevent being stuck in a "resume loop".
            with self.db_manager as db:
                db.delete_orchestration_state_for_project(self.project_id)

            self.resumable_state = None # Clear the in-memory flag
            return True

        except Exception as e:
            logging.error(f"An error occurred while resuming project {self.project_id}: {e}")
            return False

    def escalate_for_manual_debug(self, failure_log: str, is_functional_bug: bool = False):
        """
        Initiates the multi-tiered triage and debug process.
        This version is refactored to use the central llm_service.
        """
        logging.info("A failure has triggered the debugging pipeline.")

        if is_functional_bug:
            self._plan_fix_from_description(failure_log)
            return

        self.debug_attempt_counter += 1
        logging.info(f"Technical debug attempt counter is now: {self.debug_attempt_counter}")

        try:
            with self.db_manager as db:
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
                        apex_file_name = project_details['apex_executable_name'] if 'apex_executable_name' in project_details else None
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
        This version correctly preserves context during a manual pause.
        """
        logging.info(f"PM selected debug escalation option: {choice}")

        # This method should only be called when task_awaiting_approval is set.
        # The logic is now moved inside each choice block.
        if choice == "RETRY":
            if self.task_awaiting_approval:
                self.debug_attempt_counter = 0
                failure_log_from_state = self.task_awaiting_approval.get('failure_log', "PM-initiated retry after escalation.")
                self.task_awaiting_approval = None # Clean up context
                self.escalate_for_manual_debug(failure_log_from_state)
            else:
                logging.warning("Retry clicked, but no failure context found. Returning to GENESIS.")
                self.set_phase("GENESIS")

        elif choice == "MANUAL_PAUSE":
            # The orchestrator now saves its state automatically when the phase is set.
            # We just need to log the action and set the phase to idle for the user.
            self.set_phase("IDLE")
            logging.info("Project paused for manual PM investigation. State has been saved.")

        elif choice == "IGNORE":
            logging.warning("Acknowledging and ignoring bug. Updating artifact status to 'KNOWN_ISSUE'.")
            try:
                if self.task_awaiting_approval:
                    failing_artifact_id = self.task_awaiting_approval.get('failing_artifact_id')
                    if failing_artifact_id:
                        with self.db_manager as db:
                            timestamp = datetime.now(timezone.utc).isoformat()
                            db.update_artifact_status(failing_artifact_id, "KNOWN_ISSUE", timestamp)
                        logging.info(f"Status of artifact {failing_artifact_id} set to KNOWN_ISSUE.")
                    else:
                        logging.error("Could not identify the specific failing artifact to mark as 'KNOWN_ISSUE'.")

                self.set_phase("GENESIS") # Proceed to next task
                self.active_plan_cursor += 1
                self.task_awaiting_approval = None # Clean up context

            except Exception as e:
                logging.error(f"Failed to update artifact status to 'KNOWN_ISSUE': {e}")
                self.set_phase("GENESIS")
                self.task_awaiting_approval = None # Clean up context

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

    def _save_current_state(self):
        """
        Saves the currently active project's detailed operational state to the
        database. This is called automatically on phase transitions.
        """
        if not self.project_id:
            # This can happen during initial phase transitions, which is normal.
            return

        try:
            # First, delete any pre-existing state to ensure atomicity.
            with self.db_manager as db:
                db.delete_orchestration_state_for_project(self.project_id)

            state_details_dict = {
                "active_plan": self.active_plan,
                "active_plan_cursor": self.active_plan_cursor,
                "debug_attempt_counter": self.debug_attempt_counter,
                "task_awaiting_approval": self.task_awaiting_approval
            }
            state_details_json = json.dumps(state_details_dict)

            # Save the new state to the database
            with self.db_manager as db:
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
                    archive_path=str(rowd_file),
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

    def handle_discard_changes(self, history_id: int):
        """
        Handles the 'Discard all local changes' expert option for a project
        with state drift. Resets the git repository and then re-runs the
        entire project loading sequence to ensure a clean state.
        """
        logging.warning(f"Executing 'git reset --hard' for project history ID: {history_id}")
        try:
            with self.db_manager as db:
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
            # to re-run checks and correctly load the project into state.
            self.load_archived_project(history_id)

        except Exception as e:
            logging.error(f"Failed to discard changes for project history ID {history_id}: {e}")
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

                # Perform the checks BEFORE loading data
                project_root_str = history_record['project_root_folder']
                check_result = self._perform_preflight_checks(project_root_str)
                self.preflight_check_result = check_result

                # If checks fail fatally, we don't bother loading the data yet.
                if check_result['status'] in ["PATH_NOT_FOUND", "GIT_MISSING", "STATE_DRIFT"]:
                    self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")
                    logging.info(f"Pre-flight checks failed ({check_result['status']}). Pausing for user resolution.")
                    return

                # --- If checks pass, proceed to load data ---
                self._clear_active_project_data(db)

                rowd_file_path = Path(history_record['archive_file_path'])
                cr_file_path = rowd_file_path.with_name(rowd_file_path.name.replace("_rowd.json", "_cr.json"))

                if not rowd_file_path.exists():
                    raise FileNotFoundError(f"Archive file not found at path: {rowd_file_path}")

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

                # Determine and store the correct resume phase before transitioning.
                self.resume_phase_after_load = self._determine_resume_phase_from_rowd(db)
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

    def _plan_and_execute_fix(self, failure_log: str, context_package: dict):
        """
        A helper method that invokes the FixPlannerAgent and prepares the
        resulting plan for execution by the Genesis pipeline.
        This version is refactored to use the central llm_service.
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

        limit_str = db.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "200000"
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
        This version is refactored to use the central llm_service.
        """
        logging.info("Initiating test environment setup guidance.")
        try:
            if not self.llm_service:
                raise Exception("Cannot get setup tasks: LLM Service is not configured.")

            with self.db_manager as db:
                project_details = db.get_project_by_id(self.project_id)
                tech_spec_text = project_details['tech_spec_text']
                target_os = project_details['target_os'] if project_details and 'target_os' in project_details else 'Linux'

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
        This version is refactored to use the central llm_service.
        """
        logging.info("Getting help for a test environment setup task.")
        try:
            if not self.llm_service:
                raise Exception("Cannot get help: LLM Service is not configured.")

            with self.db_manager as db:
                project_details = db.get_project_by_id(self.project_id)
                target_os = project_details['target_os'] if project_details and 'target_os' in project_details else 'Linux'

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
            with self.db_manager as db:
                db.update_project_test_command(self.project_id, test_command)

            self.set_phase("CODING_STANDARD_GENERATION")
            logging.info("Test environment setup complete. Transitioning to Coding Standard Generation.")
            return True
        except Exception as e:
            logging.error(f"Failed to finalize test environment setup: {e}")
            return False

    def handle_ignore_setup_task(self, task: dict):
        """
        Creates a 'KNOWN_ISSUE' artifact to record a skipped setup task.
        This makes the decision persistent and trackable as per the PRD.

        Args:
            task (dict): A dictionary containing the details of the skipped task.
        """
        if not self.project_id:
            logging.error("Cannot log ignored setup task; no active project.")
            return

        logging.warning(f"PM chose to ignore setup task: {task.get('tool_name')}. Logging as KNOWN_ISSUE.")
        try:
            with self.db_manager as db:
                # Use the DocUpdateAgent to create the new artifact record
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

        This method generates the UI test plan and transitions the state to
        MANUAL_UI_TESTING, allowing the workflow to proceed.
        """
        logging.warning("PM acknowledged a system-level integration failure. Proceeding to manual testing.")
        try:
            with self.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                project_details = db.get_project_by_id(self.project_id)

                if not api_key or not project_details:
                    raise Exception("Cannot generate UI test plan: Missing API Key or Project Details.")

                # Generate the UI Test Plan, as this step was previously skipped.
                functional_spec_text = project_details['final_spec_text']
                technical_spec_text = project_details['tech_spec_text']
                ui_test_planner = UITestPlannerAgent_AppTarget(api_key=api_key)
                ui_test_plan_content = ui_test_planner.generate_ui_test_plan(functional_spec_text, technical_spec_text)

                db.save_ui_test_plan(self.project_id, ui_test_plan_content)

            self.task_awaiting_approval = None
            self.set_phase("MANUAL_UI_TESTING")

        except Exception as e:
            logging.error(f"Failed to handle integration failure acknowledgment. Error: {e}")
            # If even this fails, escalate to prevent getting stuck
            self.set_phase("DEBUG_PM_ESCALATION")

    def _extract_and_save_primary_technology(self, tech_spec_text: str):
        """
        Uses the LLM service to extract the primary programming language from the
        technical specification text and saves it to the database.

        Args:
            tech_spec_text (str): The full text of the approved technical spec.
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
                with self.db_manager as db:
                    db.update_project_technology(self.project_id, primary_technology)
                logging.info(f"Successfully extracted and saved primary technology: {primary_technology}")
            else:
                raise ValueError(f"LLM service returned an empty or error response for technology extraction: {primary_technology}")

        except Exception as e:
            # Log the error but don't halt the entire process.
            # A potential manual correction might be needed if this fails.
            logging.error(f"Failed to extract and save primary technology: {e}")

    def get_latest_commit_timestamp(self) -> datetime | None:
        """
        Retrieves the timestamp of the most recent commit in the project's repo.
        """
        try:
            with self.db_manager as db:
                project_details = db.get_project_by_id(self.project_id)
                project_root_path = str(project_details['project_root_folder'])

            repo = git.Repo(project_root_path)
            if not repo.heads: # Check if there are any commits
                return None

            latest_commit = repo.head.commit
            return latest_commit.committed_datetime
        except Exception as e:
            logging.error(f"Could not retrieve latest commit timestamp: {e}")
            return None

    def _create_llm_service(self) -> LLMService | None:
        """
        Factory method to create the appropriate LLM service adapter based on
        the configuration stored in the database. Now uses new provider names.
        """
        logging.info("Attempting to create and configure LLM service...")
        with self.db_manager as db:
            # The database now stores the user-facing name, which we map back
            # to the original key for creating the correct adapter.
            provider_name_from_db = db.get_config_value("SELECTED_LLM_PROVIDER") or "Gemini"

            provider_map = {
                "Gemini": "Gemini",
                "ChatGPT": "OpenAI",
                "Claude": "Anthropic",
                "Phi-3 (Local)": "LocalPhi3",
                "Any Other": "Enterprise"
            }
            # Find the internal key (e.g., "OpenAI") from the name stored in the DB (e.g., "ChatGPT")
            provider = provider_map.get(provider_name_from_db, "Gemini")

            if provider == "Gemini":
                api_key = db.get_config_value("GEMINI_API_KEY")
                reasoning_model = db.get_config_value("GEMINI_REASONING_MODEL") or "gemini-2.5-pro"
                fast_model = db.get_config_value("GEMINI_FAST_MODEL") or "gemini-2.5-flash-preview-05-20"
                if not api_key:
                    logging.warning("Gemini is selected, but GEMINI_API_KEY is not set.")
                    return None
                return GeminiAdapter(api_key, reasoning_model, fast_model)

            elif provider == "OpenAI":
                api_key = db.get_config_value("OPENAI_API_KEY")
                reasoning_model = db.get_config_value("OPENAI_REASONING_MODEL") or "gpt-4-turbo"
                fast_model = db.get_config_value("OPENAI_FAST_MODEL") or "gpt-3.5-turbo"
                if not api_key:
                    logging.warning("ChatGPT (OpenAI) is selected, but OPENAI_API_KEY is not set.")
                    return None
                return OpenAIAdapter(api_key, reasoning_model, fast_model)

            elif provider == "Anthropic":
                api_key = db.get_config_value("ANTHROPIC_API_KEY")
                reasoning_model = db.get_config_value("ANTHROPIC_REASONING_MODEL") or "claude-3-opus-20240229"
                fast_model = db.get_config_value("ANTHROPIC_FAST_MODEL") or "claude-3-haiku-20240307"
                if not api_key:
                    logging.warning("Claude (Anthropic) is selected, but ANTHROPIC_API_KEY is not set.")
                    return None
                return AnthropicAdapter(api_key, reasoning_model, fast_model)

            elif provider == "LocalPhi3":
                return LocalPhi3Adapter()

            elif provider == "Enterprise":
                base_url = db.get_config_value("CUSTOM_ENDPOINT_URL")
                api_key = db.get_config_value("CUSTOM_ENDPOINT_API_KEY")
                reasoning_model = db.get_config_value("CUSTOM_REASONING_MODEL")
                fast_model = db.get_config_value("CUSTOM_FAST_MODEL")
                if not all([base_url, api_key, reasoning_model, fast_model]):
                    logging.warning("Enterprise provider selected, but one or more required settings are missing.")
                    return None
                return CustomEndpointAdapter(base_url, api_key, reasoning_model, fast_model)

            else:
                logging.error(f"Invalid LLM provider configured: {provider_name_from_db}")
                return None

    def run_mid_project_reassessment(self):
        """
        Calculates the remaining work in a project and invokes the
        ProjectScopingAgent to perform a new risk and complexity analysis.
        (F-Dev 12.2)
        """
        logging.info(f"Running mid-project re-assessment for project: {self.project_name}")
        if not self.project_id:
            logging.error("Cannot run re-assessment; no active project.")
            return

        remaining_work_spec = ""
        try:
            with self.db_manager as db:
                project_details = db.get_project_by_id(self.project_id)
                dev_plan_text = project_details['development_plan_text'] if 'development_plan_text' in project_details else None

                if not dev_plan_text:
                    # If no dev plan exists, the 'remaining work' is the entire spec
                    remaining_work_spec = project_details['final_spec_text'] if 'final_spec_text' in project_details else ''
                    logging.info("No development plan found. Using full application spec for re-assessment.")
                else:
                    # If a dev plan exists, find uncompleted tasks
                    dev_plan = json.loads(dev_plan_text).get("development_plan", [])
                    all_artifacts = db.get_all_artifacts_for_project(self.project_id)

                    completed_spec_ids = {
                        artifact['micro_spec_id'] for artifact in all_artifacts
                        if artifact['micro_spec_id']
                    }

                    remaining_tasks = [
                        task for task in dev_plan
                        if task.get('micro_spec_id') not in completed_spec_ids
                    ]

                    if not remaining_tasks:
                        logging.info("No remaining tasks found in the development plan.")
                        remaining_work_spec = "Project development is complete. Assess risk of any final integration or bug fixing."
                    else:
                        remaining_work_descriptions = [
                            task['task_description'] for task in remaining_tasks
                            if 'task_description' in task
                        ]
                        remaining_work_spec = "\n\n".join(remaining_work_descriptions)
                        logging.info(f"Found {len(remaining_tasks)} remaining tasks for re-assessment.")

            if not remaining_work_spec.strip():
                logging.warning("Remaining work specification is empty. Cannot perform re-assessment.")
                self.task_awaiting_approval = {
                    "reassessment_result": {"error": "Could not determine remaining work."}
                }
                return

            # Invoke the scoping agent
            scoping_agent = ProjectScopingAgent(llm_service=self.llm_service)
            analysis_result = scoping_agent.analyze_complexity(remaining_work_spec)

            # Store the result for the UI to display
            self.task_awaiting_approval = {"reassessment_result": analysis_result}
            logging.info("Successfully completed mid-project re-assessment.")

        except Exception as e:
            logging.error(f"An error occurred during mid-project re-assessment: {e}")
            self.task_awaiting_approval = {
                "reassessment_result": {"error": f"An unexpected error occurred: {e}"}
            }

    def commit_pending_llm_change(self, new_provider: str) -> tuple[bool, str]:
        """
        Finalizes a pending LLM provider change after a successful
        re-assessment by saving it to the database and re-initializing
        the LLM service.
        (F-Dev 12.3)

        Args:
            new_provider (str): The name of the new provider to commit.

        Returns:
            A tuple containing a success boolean and a status message.
        """
        logging.info(f"Committing pending LLM change to: {new_provider}")
        try:
            with self.db_manager as db:
                # Save the new provider selection
                db.set_config_value("SELECTED_LLM_PROVIDER", new_provider)

                # Update the active context limit to the new provider's default
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

            # Re-initialize the LLM service with the new settings
            self.llm_service = self._create_llm_service()
            if not self.llm_service:
                 raise Exception("Failed to re-initialize LLM service with new provider.")

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