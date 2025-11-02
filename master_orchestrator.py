
import logging
import uuid
import json
import os
import shutil
import re
from typing import Optional
from datetime import datetime, timezone
from enum import Enum, auto
from llm_service import (LLMService, GeminiAdapter, OpenAIAdapter,
                         AnthropicAdapter, GrokAdapter, DeepseekAdapter, LlamaAdapter,
                         LocalPhi3Adapter, CustomEndpointAdapter)
from pathlib import Path
import textwrap
import git
import hashlib
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox, QInputDialog, QLineEdit
import matplotlib
matplotlib.use('Agg') # Ensure backend is set for thread safety
import matplotlib.pyplot as plt
from io import BytesIO # For image data

from agents.agent_project_bootstrap import ProjectBootstrapAgent
from agents.agent_integration_pmt import IntegrationAgentPMT
from agents.agent_automated_ui_test_script import AutomatedUITestScriptAgent
from agents.agent_backend_test_plan_extractor import BackendTestPlanExtractorAgent
from agents.agent_automated_test_result_parser import AutomatedTestResultParserAgent
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
from agents.agent_impact_analysis_app_target import ImpactAnalysisAgent_AppTarget
from agents.agent_test_environment_advisor import TestEnvironmentAdvisorAgent
from agents.agent_verification_app_target import VerificationAgent_AppTarget
from agents.agent_rollback_app_target import RollbackAgent
from agents.agent_project_scoping import ProjectScopingAgent
from agents.build_and_commit_agent_app_target import BuildAndCommitAgentAppTarget
from agents.agent_plan_auditor import PlanAuditorAgent
from agents.agent_code_summarization import CodeSummarizationAgent
from agents.agent_test_report_formatting import TestReportFormattingAgent
from gui.utils import format_timestamp_for_display
from agents.agent_dev_environment_advisor import DevEnvironmentAdvisorAgent
from agents.agent_project_intake_advisor import ProjectIntakeAdvisorAgent
from agents.agent_sprint_integration_test import SprintIntegrationTestAgent
from agents.agent_traceability_report import RequirementTraceabilityAgent

class EnvironmentFailureException(Exception):
    """Custom exception for unrecoverable environment errors."""
    pass

class FactoryPhase(Enum):
    """Enumeration for the main factory F-Phases."""
    IDLE = auto()
    ANALYZING_CODEBASE = auto()
    AWAITING_BROWNFIELD_STRATEGY = auto()
    GENERATING_BACKLOG = auto()
    PROJECT_INTAKE_ASSESSMENT = auto()
    BACKLOG_VIEW = auto()
    SPRINT_PLANNING = auto()
    AWAITING_SPRINT_VALIDATION_CHECK = auto()
    AWAITING_SPRINT_VALIDATION_APPROVAL = auto()
    SPRINT_IN_PROGRESS = auto()
    SPRINT_REVIEW = auto()
    AWAITING_SPRINT_INTEGRATION_TEST_DECISION = auto()
    AWAITING_SPRINT_INTEGRATION_TEST_APPROVAL = auto()
    SPRINT_INTEGRATION_TEST_EXECUTION = auto()
    AWAITING_INTEGRATION_TEST_RESULT_ACK = auto()
    POST_SPRINT_DOC_UPDATE = auto()
    BACKLOG_RATIFICATION = auto()
    VIEWING_ACTIVE_PROJECTS = auto()
    UX_UI_DESIGN = auto()
    AWAITING_UX_UI_PHASE_DECISION = auto()
    AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION = auto()
    ENV_SETUP_TARGET_APP = auto()
    SPEC_ELABORATION = auto()
    GENERATING_UX_UI_SPEC_DRAFT = auto()
    GENERATING_APP_SPEC_AND_RISK_ANALYSIS = auto()
    # AWAITING_RISK_ASSESSMENT_APPROVAL = auto()
    AWAITING_DELIVERY_ASSESSMENT_APPROVAL = auto()
    AWAITING_SPEC_REFINEMENT_SUBMISSION = auto()
    AWAITING_SPEC_FINAL_APPROVAL = auto()
    TECHNICAL_SPECIFICATION = auto()
    AWAITING_TECH_SPEC_GUIDELINES = auto()
    AWAITING_TECH_SPEC_RECTIFICATION = auto()
    TEST_ENVIRONMENT_SETUP = auto()
    BUILD_SCRIPT_SETUP = auto()
    DOCKERIZATION_SETUP = auto()
    CODING_STANDARD_GENERATION = auto()
    AWAITING_BACKLOG_GATEWAY_DECISION = auto()
    PLANNING = auto()
    GENESIS = auto()
    AWAITING_INTEGRATION_CONFIRMATION = auto()
    INTEGRATION_AND_VERIFICATION = auto()
    ON_DEMAND_AUTOMATED_UI_TESTS = auto()
    AWAITING_INTEGRATION_RESOLUTION = auto()
    MANUAL_UI_TESTING = auto()
    GENERATING_MANUAL_TEST_PLAN = auto()
    AWAITING_UI_TEST_DECISION = auto()
    AWAITING_SCRIPT_FAILURE_RESOLUTION = auto()
    AWAITING_PM_DECLARATIVE_CHECKPOINT = auto()
    AWAITING_PREFLIGHT_RESOLUTION = auto()
    AWAITING_IMPACT_ANALYSIS_CHOICE = auto()
    IMPLEMENTING_CHANGE_REQUEST = auto()
    UPDATING_SPECIFICATION_DOCUMENTS = auto()
    AWAITING_LINKED_DELETE_CONFIRMATION = auto()
    DEBUG_PM_ESCALATION = auto()
    VIEWING_DOCUMENTS = auto()
    VIEWING_REPORTS = auto()
    VIEWING_PROJECT_HISTORY = auto()
    VIEWING_SPRINT_HISTORY = auto()
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
        self.resumable_state = None # Initialize as None

        # Default initial state
        self.project_id: str | None = None
        self.project_name: str | None = None
        self.current_phase: FactoryPhase = FactoryPhase.IDLE
        self.active_plan = None
        self.active_plan_cursor = 0
        self.task_awaiting_approval = None
        self.preflight_check_result = None
        self.debug_attempt_counter = 0
        self.active_ux_spec = {}
        self.is_project_dirty = False
        self.is_executing_cr_plan = False
        self.is_in_fix_mode = False
        self.is_resuming_from_manual_fix = False
        self.is_task_processing = False
        self.fix_plan = None
        self.fix_plan_cursor = 0
        self.sprint_completed_with_failures = False
        self._llm_service = None
        self.current_task_confidence = 0
        self.active_spec_draft = None
        self.active_sprint_id = None
        self.post_fix_reverification_path = None
        self.is_on_demand_test_cycle = False
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
        self.is_resuming_from_manual_fix = False
        self.fix_plan = None
        self.fix_plan_cursor = 0
        self.current_task_confidence = 0
        self.active_spec_draft = None
        self.active_sprint_id = None
        self.active_sprint_goal = None
        self.post_fix_reverification_path = None

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
        FactoryPhase.ANALYZING_CODEBASE: "Analyzing Codebase",
        FactoryPhase.AWAITING_BROWNFIELD_STRATEGY: "Awaiting Project Strategy",
        FactoryPhase.GENERATING_BACKLOG: "Generating Project Backlog...",
        FactoryPhase.BACKLOG_VIEW: "Backlog Overview",
        FactoryPhase.SPRINT_PLANNING: "Sprint Planning",
        FactoryPhase.AWAITING_SPRINT_VALIDATION_CHECK: "Validating Sprint Scope",
        FactoryPhase.AWAITING_SPRINT_VALIDATION_APPROVAL: "Sprint Validation Report",
        FactoryPhase.SPRINT_IN_PROGRESS: "Sprint in Progress",
        FactoryPhase.SPRINT_REVIEW: "Sprint Review",
        FactoryPhase.AWAITING_SPRINT_INTEGRATION_TEST_DECISION: "Generating Sprint Integration Test",
        FactoryPhase.AWAITING_SPRINT_INTEGRATION_TEST_APPROVAL: "Sprint Integration Test Checkpoint",
        FactoryPhase.SPRINT_INTEGRATION_TEST_EXECUTION: "Running Sprint Integration Test",
        FactoryPhase.AWAITING_INTEGRATION_TEST_RESULT_ACK: "Sprint Integration Test Results",
        FactoryPhase.POST_SPRINT_DOC_UPDATE: "Finalizing Sprint",
        FactoryPhase.BACKLOG_RATIFICATION: "Backlog Ratification",
        FactoryPhase.VIEWING_ACTIVE_PROJECTS: "Open Project",
        FactoryPhase.UX_UI_DESIGN: "User Experience & Interface Design",
        FactoryPhase.AWAITING_UX_UI_PHASE_DECISION: "Awaiting UX/UI Phase Decision",
        FactoryPhase.AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION: "UX/UI Phase Recommendation",
        FactoryPhase.ENV_SETUP_TARGET_APP: "New Application Setup",
        FactoryPhase.SPEC_ELABORATION: "Application Specification",
        FactoryPhase.GENERATING_APP_SPEC_AND_RISK_ANALYSIS: "Generating App Spec & Risk Analysis",
        # FactoryPhase.AWAITING_RISK_ASSESSMENT_APPROVAL: "Project Complexity & Risk Assessment",
        FactoryPhase.AWAITING_DELIVERY_ASSESSMENT_APPROVAL: "Delivery Assessment",
        FactoryPhase.AWAITING_SPEC_REFINEMENT_SUBMISSION: "Review Application Specification Draft",
        FactoryPhase.AWAITING_SPEC_FINAL_APPROVAL: "Refine Application Specification",
        FactoryPhase.TECHNICAL_SPECIFICATION: "Technical Specification",
        FactoryPhase.TEST_ENVIRONMENT_SETUP: "Environment Setup",
        FactoryPhase.BUILD_SCRIPT_SETUP: "Build Script Generation",
        FactoryPhase.DOCKERIZATION_SETUP: "Dockerization",
        FactoryPhase.CODING_STANDARD_GENERATION: "Coding Standard Generation",
        FactoryPhase.AWAITING_BACKLOG_GATEWAY_DECISION: "Backlog Gateway",
        FactoryPhase.PLANNING: "Development Planning",
        FactoryPhase.GENESIS: "Iterative Development",
        FactoryPhase.AWAITING_INTEGRATION_CONFIRMATION: "Awaiting Integration Confirmation",
        FactoryPhase.INTEGRATION_AND_VERIFICATION: "Integration & Verification",
        FactoryPhase.AWAITING_INTEGRATION_RESOLUTION: "Awaiting Integration Resolution",
        FactoryPhase.MANUAL_UI_TESTING: "Testing & Validation",
        FactoryPhase.GENERATING_MANUAL_TEST_PLAN: "Generating Manual Test Plan",
        FactoryPhase.AWAITING_UI_TEST_DECISION: "UI Test Decision",
        FactoryPhase.AWAITING_SCRIPT_FAILURE_RESOLUTION: "Automated Test Script Failure",
        FactoryPhase.AWAITING_PM_DECLARATIVE_CHECKPOINT: "Checkpoint: High-Risk Change Approval",
        FactoryPhase.AWAITING_PREFLIGHT_RESOLUTION: "Pre-flight Check",
        FactoryPhase.AWAITING_IMPACT_ANALYSIS_CHOICE: "New CR - Impact Analysis",
        FactoryPhase.IMPLEMENTING_CHANGE_REQUEST: "Implement Change Request",
        FactoryPhase.UPDATING_SPECIFICATION_DOCUMENTS: "Updating Project Documents",
        FactoryPhase.AWAITING_LINKED_DELETE_CONFIRMATION: "Confirm Linked Deletion",
        FactoryPhase.DEBUG_PM_ESCALATION: "Debug Escalation to PM",
        FactoryPhase.VIEWING_DOCUMENTS: "Viewing Project Documents",
        FactoryPhase.VIEWING_REPORTS: "Viewing Project Reports",
        FactoryPhase.VIEWING_PROJECT_HISTORY: "Select and Load Archived Project",
        FactoryPhase.VIEWING_SPRINT_HISTORY: "Viewing Sprint History",
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
        """
        Dynamically retrieves all items for the active sprint and constructs the
        sprint goal string from their titles. This avoids caching issues.
        """
        if not self.active_sprint_id:
            return "N/A"

        try:
            sprint_items = self.db_manager.get_items_for_sprint(self.active_sprint_id)
            if not sprint_items:
                return "No items defined for the current sprint."

            # Construct the goal from the titles of the items
            goal_titles = [item['title'] for item in sprint_items if item['title']]
            return ", ".join(f"'{title}'" for title in goal_titles)

        except Exception as e:
            logging.error(f"Failed to dynamically get sprint goal for sprint '{self.active_sprint_id}': {e}")
            return "Error retrieving sprint goal."

    def _get_user_story_context_for_task(self, parent_cr_ids: list) -> str:
        """
        Finds the full hierarchical ID and title of the parent backlog item for a given task.
        """
        if not self.project_id or not parent_cr_ids:
            return "N/A"
        try:
            # Re-use the established pattern to get the full backlog with hierarchical numbers.
            full_backlog_with_ids = self._get_backlog_with_hierarchical_numbers()
            flat_backlog_map = {item['cr_id']: item for item in self._flatten_hierarchy(full_backlog_with_ids)}

            # For simplicity, we use the first parent ID for context.
            parent_id = parent_cr_ids[0]
            parent_item = flat_backlog_map.get(parent_id)

            if parent_item:
                hierarchical_id = parent_item.get('hierarchical_id', f'CR-{parent_id}')
                title = parent_item.get('title', 'Untitled Item')
                return f"{hierarchical_id}: {title}"

            return "Parent item not found"
        except Exception as e:
            logging.error(f"Failed to get user story context for parent_cr_ids {parent_cr_ids}: {e}")
            return "Error retrieving context"

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

    def manually_update_cr_status(self, cr_id: int, new_status: str):
        """
        Handles the UI request to manually change the status of any CR item.
        """
        if not self.project_id:
            logging.error(f"Cannot update status for CR-{cr_id}; no active project.")
            return

        self.db_manager.update_cr_status(cr_id, new_status)
        self.is_project_dirty = True
        logging.info(f"Manually updated status for CR-{cr_id} to '{new_status}'.")

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
        Prepares a new project in memory but does NOT save it to the database.
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

        # Prepare details in memory only
        self.project_id = f"proj_{uuid.uuid4().hex[:8]}"
        self.project_name = project_name
        self.project_root_path = str(suggested_root)
        self.is_project_dirty = True # Mark as dirty to prevent loss if user starts another new project

        logging.info(f"Initialized new project '{self.project_name}' in memory. Awaiting path confirmation from UI.")
        self.set_phase("ENV_SETUP_TARGET_APP")
        return str(suggested_root)

    def start_brownfield_project(self, project_name: str, project_path: str):
        """
        Prepares an existing (Brownfield) project in memory without modification.
        """
        if self.project_id and self.is_project_dirty:
            logging.warning(f"An active, modified project '{self.project_name}' was found. Performing a safety export.")
            self.stop_and_export_project()

        # Directly use the provided path and name without sanitization or modification
        self.project_id = f"proj_{uuid.uuid4().hex[:8]}"
        self.project_name = project_name
        self.project_root_path = project_path
        self.is_project_dirty = True

        logging.info(f"Initialized brownfield project '{self.project_name}' in memory from path '{project_path}'.")
        self.set_phase("ENV_SETUP_TARGET_APP")

    def _check_and_route_to_coding_standards(self, next_phase: FactoryPhase) -> FactoryPhase:
        """
        Checks if standards are generated for all detected techs.
        Routes to CODING_STANDARD_GENERATION if not, otherwise to the next_phase.
        """
        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details:
                logging.warning("Cannot check coding standards, project details not found.")
                return next_phase

            technologies_json = project_details['detected_technologies'] if project_details and 'detected_technologies' in project_details.keys() and project_details['detected_technologies'] else '[]'
            detected_technologies = json.loads(technologies_json)

            if not detected_technologies:
                logging.info("No technologies detected, skipping coding standard check.")
                return next_phase

            # Find all existing coding standard artifacts
            all_artifacts = self.db_manager.get_all_artifacts_for_project(self.project_id)
            completed_standards = set()
            for art in all_artifacts:
                if art['artifact_type'] == 'CODING_STANDARD':
                    # Extract language from name, e.g., "Coding Standard (Python)"
                    match = re.search(r'\((.*?)\)', art['artifact_name'])
                    if match:
                        completed_standards.add(match.group(1))

            # Check if any detected technology is missing a standard
            missing_standards = False
            for tech in detected_technologies:
                if tech not in completed_standards:
                    missing_standards = True
                    break

            if missing_standards:
                logging.info(f"Coding standards are incomplete ({completed_standards} vs {detected_technologies}). Routing to F-Phase 9.")
                self.task_awaiting_approval = {'next_phase_after_standards': next_phase.name}
                return FactoryPhase.CODING_STANDARD_GENERATION
            else:
                logging.info("All coding standards are present. Proceeding.")
                return next_phase

        except Exception as e:
            logging.error(f"Error in _check_and_route_to_coding_standards: {e}", exc_info=True)
            return next_phase # Fail safe by proceeding

    def handle_brownfield_maintain_path(self):
        """
        Kicks off the asynchronous backlog generation process. It first deletes
        any existing reference backlog items to prevent duplication before setting
        the phase to start the generation.
        """
        logging.info("PM chose 'Maintain & Enhance' path. Deleting existing reference backlog...")
        try:
            self.db_manager.delete_change_requests_by_status(self.project_id, ["EXISTING"])
            logging.info("Transitioning to backlog generation.")
            self.set_phase(self._check_and_route_to_coding_standards(FactoryPhase.GENERATING_BACKLOG).name)
        except Exception as e:
            logging.error(f"Failed to handle 'Maintain & Enhance' path: {e}", exc_info=True)
            QMessageBox.critical(None, "Error", f"An error occurred while preparing to generate the backlog:\n{e}")
            # Fallback to the dashboard on error
            self.set_phase("AWAITING_BROWNFIELD_STRATEGY")

    def run_backlog_generation_task(self, progress_callback, worker_instance):
        """
        This is the long-running task that generates the reference backlog.
        It constructs dictionaries to pass to the database manager and correctly
        links parent-child relationships using their integer primary keys.
        """
        try:
            # 1. Get the necessary specs from the database
            project_details = self.db_manager.get_project_by_id(self.project_id)
            final_spec_text = project_details['final_spec_text']
            tech_spec_text = project_details['tech_spec_text']
            ux_spec_text = project_details['ux_spec_text']

            if not final_spec_text:
                logging.warning("Cannot generate backlog; final spec text is missing.")
                self.set_phase("BACKLOG_VIEW")
                return

            # 2. Call the Planning Agent
            from agents.agent_planning_app_target import PlanningAgent_AppTarget
            planner_agent = PlanningAgent_AppTarget(self.llm_service, self.db_manager)
            backlog_json_str = planner_agent.generate_reference_backlog_from_specs(final_spec_text, tech_spec_text, ux_spec_text)
            backlog_structure = json.loads(backlog_json_str)

            # 3. Populate the database
            timestamp = datetime.now(timezone.utc).isoformat()
            epic_counter = 1
            for epic in backlog_structure:
                # Construct the dictionary for the epic
                epic_data = {
                    # "cr_id": f"E{epic_counter}", # This will be mapped to external_id
                    "project_id": self.project_id,
                    "title": epic.get('title'),
                    "request_type": 'EPIC',
                    "status": 'EXISTING',
                    "description": epic.get('description'),
                    "creation_timestamp": timestamp,
                    "last_modified_timestamp": timestamp,
                    "display_order": epic_counter
                }
                # Insert the epic and capture its new integer primary key
                new_epic_pk = self.db_manager.add_brownfield_change_request(epic_data)

                feature_counter = 1
                for feature in epic.get('features', []):
                    # Construct the dictionary for the feature
                    feature_data = {
                        # "cr_id": f"E{epic_counter}.F{feature_counter}", # Mapped to external_id
                        "project_id": self.project_id,
                        "title": feature.get('title'),
                        "request_type": 'FEATURE',
                        "status": 'EXISTING',
                        "description": feature.get('description'),
                        "parent_cr_id": new_epic_pk, # Use the integer PK of the parent
                        "creation_timestamp": timestamp,
                        "last_modified_timestamp": timestamp,
                        "display_order": feature_counter
                    }
                    self.db_manager.add_brownfield_change_request(feature_data)
                    feature_counter += 1
                epic_counter += 1

            self.db_manager.update_project_field(self.project_id, "is_backlog_generated", 1)
            logging.info("Reference backlog generation complete.")
            self.update_dashboard_metrics()

        except Exception as e:
            logging.error(f"Failed to generate reference backlog: {e}", exc_info=True)
            QTimer.singleShot(0, lambda: QMessageBox.critical(None, "Error", f"An error occurred while generating the backlog:\n{e}"))

        finally:
            # 4. Transition to the backlog view regardless of success
            self.set_phase("BACKLOG_VIEW")

    def update_dashboard_metrics(self):
        """
        Calculates and saves the dashboard metrics (file count, technologies)
        to the database. This should be called after a reference backlog is generated.
        """
        logging.info("Updating dashboard metrics in the database...")
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details:
                raise Exception("Could not find project details to update metrics.")

            # Calculate file count from RoWD
            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            file_count = len(all_artifacts)
            db.update_project_field(self.project_id, "scanned_file_count", file_count)

            # Detect and save technologies
            tech_spec_text = project_details['tech_spec_text'] or ''
            languages = self.detect_technologies_in_spec(tech_spec_text)
            db.update_project_field(self.project_id, "detected_technologies", json.dumps(languages))

            logging.info(f"Successfully updated dashboard metrics: {file_count} files, {len(languages)} technologies.")

        except Exception as e:
            # We log the error but don't crash the parent process.
            logging.error(f"Failed to update dashboard metrics: {e}", exc_info=True)

    def cancel_and_cleanup_analysis(self):
        """Cancels an in-progress analysis and deletes all created artifacts."""
        if not self.project_id:
            logging.warning("Attempted to cancel analysis, but no project is active.")
            return

        logging.info(f"Cancelling analysis for project {self.project_id} and cleaning up artifacts.")
        try:
            self.db_manager.delete_all_artifacts_for_project(self.project_id)
            # We don't delete the project itself, just the artifacts from the partial scan.
        except Exception as e:
            logging.error(f"An error occurred during artifact cleanup: {e}")

    def handle_brownfield_quickfix_path(self):
        """
        Handles the PM's choice to navigate to the backlog from the dashboard
        to add new items like quick fixes or features.
        """
        logging.info("PM chose 'Quick Fix / Go to Backlog' path. Transitioning to BACKLOG_VIEW.")
        self.set_phase(self._check_and_route_to_coding_standards(FactoryPhase.BACKLOG_VIEW).name)

    def finalize_project_creation(self, project_id: str, project_name: str, project_root: str):
        """
        Creates the permanent project record in the database. This is the first
        official save point for a new project.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            self.db_manager.create_project(project_id, project_name, timestamp)
            self.db_manager.update_project_field(project_id, "project_root_folder", project_root)
            logging.info(f"Successfully created and saved project '{project_name}' to database.")
        except Exception as e:
            logging.error(f"Failed to finalize project creation for '{project_name}': {e}")
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

    def handle_initial_brief_submission(self, brief_text: str):
        """
        Handles the initial brief submission from the UI, calls the
        ProjectIntakeAdvisorAgent to perform an analysis, and sets the state
        to await the PM's strategic decision.
        """
        if not self.project_id:
            logging.error("Cannot handle brief submission; no active project.")
            return

        try:
            if not self.llm_service:
                raise Exception("Cannot analyze brief: LLM Service is not configured.")

            # Instantiate and run the new advisor agent
            intake_agent = ProjectIntakeAdvisorAgent(llm_service=self.llm_service)
            assessment_json_str = intake_agent.assess_brief_completeness(brief_text)
            assessment_data = json.loads(assessment_json_str)

            if "error" in assessment_data:
                raise Exception(f"Agent failed to process the brief: {assessment_data.get('details')}")

            # Store the result and the original brief for the next step
            self.task_awaiting_approval = {
                "assessment_data": assessment_data,
                "original_brief": brief_text
            }

            # Set the new phase to display the assessment page
            self.set_phase("PROJECT_INTAKE_ASSESSMENT")

        except Exception as e:
            logging.error(f"Failed to handle initial brief submission: {e}", exc_info=True)
            # Create an error state for the UI to display
            self.task_awaiting_approval = {
                "assessment_data": {
                    "project_summary_markdown": "### Error\nAn unexpected error occurred during analysis.",
                    "completeness_assessment": str(e)
                }
            }
            self.set_phase("PROJECT_INTAKE_ASSESSMENT")

    def handle_intake_assessment_decision(self, decision: str, **kwargs):
        """
        Executes the PM's strategic choice from the intake assessment page,
        routing the project to either the full lifecycle or directly to
        backlog generation.
        """
        if not self.task_awaiting_approval or "original_brief" not in self.task_awaiting_approval:
            logging.error("Cannot handle intake decision: original brief is missing from the task context.")
            self.set_phase("SPEC_ELABORATION") # Go back to a safe state
            return

        original_brief = self.task_awaiting_approval.get("original_brief")

        if decision == "FULL_LIFECYCLE":
            logging.info("PM chose Full Lifecycle path. Handing off to UX Triage workflow.")
            # This existing method will trigger the UX Triage agent and set the next phase.
            self.handle_ux_ui_brief_submission(original_brief)

        elif decision == "DIRECT_TO_DEVELOPMENT":
            logging.info("PM chose Direct to Development path. Bypassing specification phases.")
            try:
                # Use a more intelligent agent to synthesize the specs from the brief.
                from agents.agent_spec_clarification import SpecClarificationAgent
                spec_agent = SpecClarificationAgent(self.llm_service, self.db_manager)

                # Generate the Application Spec
                app_spec = spec_agent.expand_brief_description(original_brief)
                if not app_spec or app_spec.strip().startswith("Error:"):
                    raise ValueError(f"The AI failed to synthesize an Application Specification from the brief. Details: {app_spec}")

                # Generate the Technical Spec based on the newly created App Spec
                from agents.agent_tech_stack_proposal import TechStackProposalAgent
                tech_agent = TechStackProposalAgent(self.llm_service)
                tech_spec = tech_agent.propose_stack(app_spec, "Windows") # Assuming a default OS
                if not tech_spec or tech_spec.strip().startswith("Error:"):
                    raise ValueError(f"The AI failed to synthesize a Technical Specification. Details: {tech_spec}")

                # Save the synthesized specs to the database
                db = self.db_manager
                db.update_project_field(self.project_id, "final_spec_text", app_spec)
                db.update_project_field(self.project_id, "tech_spec_text", tech_spec)

                # Proceed to generate the backlog
                self.handle_backlog_generation()

            except Exception as e:
                logging.error(f"Direct to Development path failed: {e}", exc_info=True)
                # This is the improved, graceful error handling
                if 'assessment_data' in self.task_awaiting_approval:
                    self.task_awaiting_approval['assessment_data']['error'] = str(e)
                else:
                    self.task_awaiting_approval['assessment_data'] = {"error": str(e)}
                self.set_phase("PROJECT_INTAKE_ASSESSMENT")

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
                self.task_awaiting_approval = {
                    "analysis_error": analysis_result.get('details'),
                    "pending_brief": brief_content
                }
            else:
                self.active_ux_spec['inferred_personas'] = analysis_result.get("inferred_personas", [])
                self.task_awaiting_approval = {
                    "analysis": analysis_result,
                    "pending_brief": brief_content
                }

            self.set_phase("AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION")
            logging.debug(f"DATA SET: handle_ux_ui_brief_submission populated self.active_ux_spec: {self.active_ux_spec}")

        except Exception as e:
            logging.error(f"Failed to handle UX/UI brief submission: {e}", exc_info=True)
            self.task_awaiting_approval = {"analysis_error": str(e)}
            self.set_phase("AWAITING_UX_UI_RECOMMENDATION_CONFIRMATION")

    def handle_ux_ui_phase_decision(self, decision: str, **kwargs):
        """
        Handles the PM's decision to either start the UX/UI phase or skip it,
        ensuring the project brief is correctly handed off.
        """
        # Retrieve the necessary data from the completed triage task before clearing it.
        analysis_result = self.task_awaiting_approval.get("analysis", {})
        brief_content = self.task_awaiting_approval.get("pending_brief", "")

        # Persist the is_gui flag regardless of the decision.
        is_gui = analysis_result.get("requires_gui", False)
        self.db_manager.update_project_field(self.project_id, "is_gui_project", 1 if is_gui else 0)

        if decision == "START_UX_UI_PHASE":
            logging.info("PM chose to start the dedicated UX/UI Design phase.")
            # Explicitly set up the context for the generation phase.
            self.active_ux_spec['project_brief'] = brief_content
            self.active_ux_spec['inferred_personas'] = analysis_result.get("inferred_personas", [])
            self.task_awaiting_approval = None # Now it's safe to clear the old task
            self.set_phase("GENERATING_UX_UI_SPEC_DRAFT")

        elif decision == "SKIP_TO_SPEC":
            logging.info("PM chose to skip the UX/UI Design phase. Proceeding to Application Specification.")
            # Hand off the brief to the next phase (Application Spec generation).
            self.task_awaiting_approval = {"pending_brief": brief_content}
            self.set_phase("GENERATING_APP_SPEC_AND_RISK_ANALYSIS")

    def _task_generate_ux_spec_draft(self, **kwargs):
        """Background task wrapper for generating the UX spec draft."""
        draft = self.generate_initial_ux_spec_draft()

        # Store the result for the next page to use
        self.task_awaiting_approval = {"ux_spec_draft": draft}

        # Set the final state now that the task is complete
        self.set_phase("UX_UI_DESIGN")
        return True # Indicate success

    def handle_tech_spec_validation_failure(self, pm_guidelines: str, ai_analysis: str):
        """
        Handles a failed validation of PM-provided tech guidelines.
        """
        logging.warning("PM-provided tech guidelines failed validation. Awaiting rectification.")
        self.task_awaiting_approval = {
            "draft_spec_from_guidelines": pm_guidelines,
            "ai_analysis": ai_analysis
        }
        self.set_phase("AWAITING_TECH_SPEC_RECTIFICATION")

    def handle_tech_spec_refinement(self, current_draft: str, pm_feedback: str, target_os: str, iteration_count: int, ai_issues_text: str, template_content: str | None = None):
        """
        Handles the iterative refinement loop for the technical specification.
        """
        from agents.agent_tech_stack_proposal import TechStackProposalAgent
        agent = TechStackProposalAgent(self.llm_service)

        project_details = self.db_manager.get_project_by_id(self.project_id)
        final_spec_text = project_details['final_spec_text'] if project_details else ""

        pure_content = self._strip_header_from_document(current_draft)
        refined_content = agent.refine_stack(pure_content, pm_feedback, target_os, final_spec_text, ai_issues_text, template_content=template_content)

        # unescaped_content = html.unescape(refined_content)
        clean_refined_body = self._strip_header_from_document(refined_content)
        refined_draft_with_header = self.prepend_standard_header(clean_refined_body, "Technical Specification")

        # Pass the previous analysis (ai_issues_text) to the agent for convergence
        ai_analysis = agent.analyze_draft(refined_draft_with_header, iteration_count, ai_issues_text)

        self.task_awaiting_approval = {
            "draft_spec_from_guidelines": refined_draft_with_header,
            "ai_analysis": ai_analysis
        }
        self.set_phase("AWAITING_TECH_SPEC_RECTIFICATION")

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

    def handle_ux_spec_completion(self, final_spec_markdown: str, final_spec_plaintext: str) -> bool:
        """
        Finalizes the UX/UI Specification, saves it in two formats, generates the JSON blueprint,
        and then triggers the Application Specification draft generation.
        """
        if not self.project_id:
            logging.error("Cannot complete UX Spec: No active project.")
            return False

        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not (project_details and project_details['project_root_folder']):
                 raise FileNotFoundError("Project root folder not found for saving UX spec.")

            # Strip the header to get the pure content for DB and agent use.
            pure_ux_spec_content_plaintext = self._strip_header_from_document(final_spec_plaintext)

            project_root = Path(project_details['project_root_folder'])
            docs_dir = project_root / "docs"

            # Save the HEADED version to the Markdown file.
            ux_spec_file_path_md = docs_dir / "ux_ui_specification.md"
            ux_spec_file_path_md.write_text(final_spec_markdown, encoding="utf-8")
            self._commit_document(ux_spec_file_path_md, "docs: Finalize UX/UI Specification (Markdown)")

            # Generate and save the formatted .docx file for human use.
            from agents.agent_report_generator import ReportGeneratorAgent
            ux_spec_file_path_docx = docs_dir / "ux_ui_specification.docx"
            report_generator = ReportGeneratorAgent()
            docx_bytes = report_generator.generate_text_document_docx(
                title=f"UX/UI Specification - {self.project_name}",
                content=pure_ux_spec_content_plaintext
            )
            with open(ux_spec_file_path_docx, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            self._commit_document(ux_spec_file_path_docx, "docs: Add formatted UX/UI Specification (docx)")

            # Generate the blueprint using the PURE content.
            agent = UX_Spec_Agent(llm_service=self.llm_service)
            # Use the plain text for the agent, as it's cleaner for parsing
            json_blueprint = agent.parse_final_spec_and_generate_blueprint(pure_ux_spec_content_plaintext)
            if '"error":' in json_blueprint:
                raise Exception(f"Failed to generate JSON blueprint from final spec: {json_blueprint}")

            blueprint_file_path_json = docs_dir / "ux_ui_blueprint.json"
            blueprint_file_path_json.write_text(json_blueprint, encoding="utf-8")
            self._commit_document(blueprint_file_path_json, "docs: Add UX/UI JSON Blueprint")

            # Create a composite spec using the PURE content for the database.
            composite_spec_for_db = (
                f"{pure_ux_spec_content_plaintext}\n\n"
                f"{'='*80}\n"
                f"MACHINE-READABLE JSON BLUEPRINT\n"
                f"{'='*80}\n\n"
                f"```json\n{json_blueprint}\n```"
            )
            # Use the PLAIN TEXT version for the database
            #"composite_spec_for_db = (
            #    f"{pure_ux_spec_content_plaintext}\n\n"
            #    f"{'='*80}\n"
            #    f"MACHINE-READABLE JSON BLUEPRINT\n"
            #    f"{'='*80}\n\n"
            #    f"```json\n{json_blueprint}\n```"
            #)
            db.update_project_field(self.project_id, "ux_spec_text", composite_spec_for_db)
            self.active_ux_spec = {}

            # Hand off the PURE content to the next phase.
            self.task_awaiting_approval = {"pending_brief": pure_ux_spec_content_plaintext}
            self.set_phase("GENERATING_APP_SPEC_AND_RISK_ANALYSIS")
            return True

        except Exception as e:
            logging.error(f"Failed to complete UX/UI Specification: {e}", exc_info=True)
            self.task_awaiting_approval = {"error": str(e)}
            return False

    def generate_application_spec_draft_and_risk_analysis(self, initial_spec_text: str, **kwargs):
        """
        Runs in a background thread. It generates the initial app spec draft,
        immediately runs the complexity analysis on it, stores both results,
        and sets the state to await the PM's approval of the risk report.
        """
        try:
            if not self.project_id:
                raise Exception("Cannot generate application spec; no active project.")

            # 1. Consolidate all requirement sources into a single input document
            consolidated_requirements = self._consolidate_specification_inputs()

            # 2. Load the default template for this document type, if it exists.
            template_content = None
            try:
                template_record = self.db_manager.get_template_by_name("Default Application Specification")
                if template_record:
                    template_path = Path(template_record['file_path'])
                    if template_path.exists():
                        template_content = template_path.read_text(encoding='utf-8')
                        logging.info("Found and loaded 'Default Application Specification' template.")
            except Exception as e:
                logging.warning(f"Could not load default Application Spec template: {e}")

            # 3. Generate the raw spec content from the consolidated document, now using the template.
            spec_agent = SpecClarificationAgent(self.llm_service, self.db_manager)
            app_spec_draft_content = spec_agent.expand_brief_description(
                brief_description=consolidated_requirements,
                template_content=template_content
            )

            # 4. Add the standard document header to the draft
            full_app_spec_draft = self.prepend_standard_header(
                document_content=app_spec_draft_content,
                document_type="Application Specification"
            )

            # 5. Read the dynamic context limit from the database before calling the agent.
            limit_str = self.db_manager.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "1000000"
            context_limit = int(limit_str)

            # 6. Analyze the generated draft for complexity and risk, now with correct metrics
            scoping_agent = ProjectScopingAgent(self.llm_service)
            analysis_result = scoping_agent.analyze_complexity(app_spec_draft_content)
            if "error" in analysis_result:
                raise Exception(f"Failed to analyze project complexity: {analysis_result.get('details')}")

            # 7. Store BOTH results for the next steps and set the new phase
            self.task_awaiting_approval = {
                "generated_spec_draft": full_app_spec_draft,
                "complexity_analysis": analysis_result.get("complexity_analysis"),
                "risk_assessment": analysis_result.get("risk_assessment")
            }
            self.set_phase("AWAITING_DELIVERY_ASSESSMENT_APPROVAL")

        except Exception as e:
            logging.error(f"Background task for spec/risk generation failed: {e}", exc_info=True)
            # Store the error so the UI can display it
            self.task_awaiting_approval = {"error": str(e)}
            self.set_phase("SPEC_ELABORATION") # Go back to the starting phase on error

    def handle_risk_assessment_approval(self):
        """
        Called when the user approves the risk report. This finalizes the
        risk assessment and transitions to the first spec review screen.
        """
        if not self.project_id or not self.task_awaiting_approval:
            logging.error("Cannot handle risk approval, state is invalid.")
            return

        # Reconstruct the full analysis dictionary for the saving/exporting function
        full_analysis_for_export = {
            "complexity_analysis": self.task_awaiting_approval.get('complexity_analysis'),
            "risk_assessment": self.task_awaiting_approval.get('risk_assessment')
        }
        analysis_json_str = json.dumps(full_analysis_for_export)
        self.finalize_and_save_complexity_assessment(analysis_json_str)

        # The 'generated_spec_draft' is already stored in task_awaiting_approval.
        # We just need to change the phase so the UI knows to display it.
        self.set_phase("AWAITING_SPEC_REFINEMENT_SUBMISSION")

    def handle_spec_refinement_submission(self, current_draft: str, pm_feedback: str, template_content: str | None = None):
        """
        Called when the user submits feedback. This triggers the refinement and
        analysis, then transitions to the 3-tab view.
        """
        if not self.project_id:
            logging.error("Cannot handle spec refinement, no active project.")
            return

        from agents.agent_spec_clarification import SpecClarificationAgent
        spec_agent = SpecClarificationAgent(self.llm_service, self.db_manager)

        # FIX: Strip the existing header before sending to the agent
        pure_content = self._strip_header_from_document(current_draft)

        # Refine the spec based on feedback using the pure content
        refined_content = spec_agent.refine_specification(pure_content, "", pm_feedback, template_content=template_content)

        # Prepend a fresh, updated header to the refined content
        refined_draft_with_header = self.prepend_standard_header(refined_content, "Application Specification")

        # Analyze the *newly refined* spec for issues
        ai_analysis = spec_agent.identify_potential_issues(refined_draft_with_header, iteration_count=2)

        # Store the results for the 3-tab UI to display
        self.task_awaiting_approval = {
            "refined_spec_draft": refined_draft_with_header,
            "ai_analysis": ai_analysis
        }
        self.set_phase("AWAITING_SPEC_FINAL_APPROVAL")

    def generate_application_spec_draft(self, initial_spec_text: str, **kwargs) -> str:
        """
        Takes an initial specification (like a completed UX spec) and generates the
        full Application Spec draft. This version's sole responsibility is the
        generation of the draft content.
        """
        if not self.project_id:
            raise Exception("Cannot generate application spec; no active project.")

        # The agent generates the raw content of the specification.
        spec_agent = SpecClarificationAgent(self.llm_service, self.db_manager)
        app_spec_draft_content = spec_agent.expand_brief_description(initial_spec_text)

        # Add the standard header to the raw draft before returning it to the UI.
        full_app_spec_draft = self.prepend_standard_header(
            document_content=app_spec_draft_content,
            document_type="Application Specification"
        )

        return full_app_spec_draft

    def run_complexity_assessment(self, spec_draft_with_header: str) -> dict:
        """
        Takes a spec draft, runs the complexity analysis, saves the result,
        and transitions the factory to await the PM's confirmation.
        """
        if not self.project_id:
            raise Exception("Cannot run complexity assessment; no active project.")

        # First, strip the header to ensure the agent gets pure content.
        pure_spec_content = self._strip_header_from_document(spec_draft_with_header)

        # The scoping agent analyzes the pure content.
        scoping_agent = ProjectScopingAgent(self.llm_service)
        analysis_result = scoping_agent.analyze_complexity(pure_spec_content)
        if "error" in analysis_result:
            raise Exception(f"Failed to analyze project complexity: {analysis_result.get('details')}")

        # Save the assessment JSON and formatted .docx to the file system.
        analysis_json_str = json.dumps(analysis_result)
        self.finalize_and_save_complexity_assessment(analysis_json_str)

        # Save the full draft to a temporary instance variable for the next phase.
        self.active_spec_draft = spec_draft_with_header

        # Set the phase to await the user's confirmation of this analysis.
        self.set_phase("AWAITING_COMPLEXITY_ASSESSMENT")

        return analysis_result

    def generate_coding_standard(self, tech_spec_text: str, technology_name: str):
        """
        Generates the coding standard by calling the appropriate agent with the
        pure technical specification text.
        """
        if not self.project_id:
            raise Exception("Cannot generate coding standard; no active project.")
        if not tech_spec_text:
            raise ValueError("Cannot generate coding standard; the technical specification is empty.")
        try:
            # --- THIS IS THE FIX ---
            # The code now correctly calls the agent.
            from agents.agent_coding_standard_app_target import CodingStandardAgent_AppTarget
            agent = CodingStandardAgent_AppTarget(self.llm_service)
            standard_draft = agent.generate_standard(tech_spec_text, technology_name)
            return standard_draft
            # --- END OF FIX ---
        except Exception as e:
            logging.error(f"Failed to generate coding standard: {e}", exc_info=True)
            return f"### Error\nAn unexpected error occurred during coding standard generation: {e}"

    def generate_standard_from_guidelines(self, tech_spec_text: str, pm_guidelines: str) -> str:
        """
        Generates a coding standard by calling the agent with additional
        PM-provided guidelines, which are treated as a mandatory template.
        """
        if not self.project_id:
            raise Exception("Cannot generate coding standard; no active project.")
        if not tech_spec_text:
            raise ValueError("Cannot generate coding standard; the technical specification is empty.")
        try:
            from agents.agent_coding_standard_app_target import CodingStandardAgent_AppTarget
            agent = CodingStandardAgent_AppTarget(self.llm_service)
            # We reuse the generate_standard method, passing the PM's guidelines
            # as a high-priority template for the AI to follow.
            standard_draft = agent.generate_standard(tech_spec_text, template_content=pm_guidelines)
            return standard_draft
        except Exception as e:
            logging.error(f"Failed to generate coding standard from guidelines: {e}", exc_info=True)
            return f"### Error\nAn unexpected error occurred during guided generation: {e}"

    def finalize_and_save_app_spec(self, final_spec_markdown: str, final_spec_plaintext: str):
        """
        Saves the final application spec in two formats:
        - Markdown to the .md file (for viewing)
        - Plain text to the database (for downstream agents)
        """
        if not self.project_id:
            logging.error("Cannot save application spec; no active project.")
            return

        try:
            # 1. Process and save the PLAIN TEXT to the database for agents
            # Strip the header (which is also plain text) to get the pure content
            pure_spec_content = self._strip_header_from_document(final_spec_plaintext)
            logging.debug(f"DATA PERSISTENCE: Saving PLAIN TEXT to DB: {pure_spec_content[:200]}...")
            self.db_manager.update_project_field(self.project_id, "final_spec_text", pure_spec_content)
            logging.info(f"Successfully saved final Application Specification to database for project {self.project_id}")

            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "docs"

                # Save the HEADED version to the Markdown file for human review.
                spec_file_path_md = docs_dir / "application_spec.md"
                spec_file_path_md.write_text(final_spec_markdown, encoding="utf-8")
                self._commit_document(spec_file_path_md, "docs: Finalize Application Specification (Markdown)")

                # Generate and save the formatted .docx file for human use,
                # using the PURE content for the body of the document.
                spec_file_path_docx = docs_dir / "application_spec.docx"
                from agents.agent_report_generator import ReportGeneratorAgent
                report_generator = ReportGeneratorAgent()
                docx_bytes = report_generator.generate_text_document_docx(
                    title=f"Application Specification - {self.project_name}",
                    content=pure_spec_content
                )
                with open(spec_file_path_docx, 'wb') as f:
                    f.write(docx_bytes.getbuffer())
                self._commit_document(spec_file_path_docx, "docs: Add formatted Application Specification (docx)")

            self.active_spec_draft = None
            self.set_phase("TECHNICAL_SPECIFICATION")

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

    def get_project_settings(self) -> dict:
        """
        Retrieves a consolidated dictionary of all editable project settings.
        """
        if not self.project_id:
            return {}
        project_details = self.db_manager.get_project_by_id(self.project_id)
        if not project_details:
            return {}

        settings = {
            "test_execution_command": project_details['test_execution_command'] or "",
            "ui_test_execution_command": project_details['ui_test_execution_command'] or ""
        }

        integration_settings_json = project_details['integration_settings']
        try:
            if integration_settings_json:
                integration_settings = json.loads(integration_settings_json)
                settings.update(integration_settings)
        except json.JSONDecodeError:
            logging.warning(f"Could not parse integration_settings for project {self.project_id}")
        return settings

    def save_project_settings(self, settings_dict: dict):
        """
        Separates and saves a dictionary of project settings to the correct
        database columns and JSON blobs.
        """
        if not self.project_id:
            logging.error("Cannot save project settings; no active project.")
            return
        db = self.db_manager

        # Extract and save direct-column values first
        backend_cmd = settings_dict.pop("test_execution_command", None)
        integration_cmd = settings_dict.pop("integration_test_command", None)
        ui_cmd = settings_dict.pop("ui_test_execution_command", None)

        if backend_cmd is not None:
            db.update_project_field(self.project_id, "test_execution_command", backend_cmd)
        if integration_cmd is not None:
            db.update_project_field(self.project_id, "integration_test_command", integration_cmd)
        if ui_cmd is not None:
            db.update_project_field(self.project_id, "ui_test_execution_command", ui_cmd)

        # The remaining items in the dictionary are for the integration settings JSON blob
        try:
            integration_settings_json = json.dumps(settings_dict)
            db.update_project_field(self.project_id, "integration_settings", integration_settings_json)
            logging.info(f"Successfully saved project settings for project {self.project_id}")
        except Exception as e:
            logging.error(f"Failed to save project settings: {e}")
            raise

    def get_traceability_report_data(self, project_id: str) -> list:
        """
        Orchestrates the generation of the requirements traceability report data.

        Args:
            project_id (str): The ID of the project for which to generate the report.

        Returns:
            A list of dictionaries representing the traceability links,
            or an empty list on error.
        """
        logging.info(f"Orchestrator: Getting traceability report data for project {project_id}")
        if not project_id or project_id != self.project_id:
            logging.error("Invalid project_id provided to get_traceability_report_data.")
            return []

        try:
            # Instantiate the new agent
            agent = RequirementTraceabilityAgent(self.db_manager, self)

            # Call the agent's core method to generate the data
            trace_data = agent.generate_trace_data(project_id)

            logging.info(f"Successfully retrieved {len(trace_data)} traceability records.")
            return trace_data

        except Exception as e:
            logging.error(f"Failed to get traceability report data for project {project_id}: {e}", exc_info=True)
            return [] # Return empty list on failure

    def get_health_snapshot_data(self) -> dict:
        """Gathers data for the health snapshot from the DAO."""
        if not self.project_id:
            return {}
        try:
            backlog_summary = self.db_manager.get_backlog_status_summary(self.project_id)
            test_summary = self.db_manager.get_component_test_status_summary(self.project_id)
            return {
                'backlog_summary': backlog_summary,
                'test_summary': test_summary
            }
        except Exception as e:
            logging.error(f"Failed to get health snapshot data: {e}", exc_info=True)
            return {}

    def get_sprint_list_for_report(self) -> list[tuple[str, str]]:
        """
        Fetches completed and in-progress sprints for report filtering dropdowns.

        Returns:
            A list of tuples, where each tuple is (display_text, sprint_id).
            Returns an empty list if no project is active or no sprints are found.
        """
        if not self.project_id:
            return []
        try:
            # Fetch sprints with relevant statuses, newest first
            sprints = self.db_manager.get_sprints_by_status(self.project_id, statuses=['COMPLETED', 'IN_PROGRESS', 'PAUSED'])
            if not sprints:
                return []

            # Format for the UI dropdown
            sprint_list = []
            for sprint in sprints:
                start_time_str = format_timestamp_for_display(sprint['start_timestamp'])
                status = sprint['status'].replace('_', ' ').title()
                display_text = f"{start_time_str} ({status}) - Goal: {sprint['sprint_goal'][:30]}..."
                sprint_list.append((display_text, sprint['sprint_id']))
            return sprint_list
        except Exception as e:
            logging.error(f"Failed to get sprint list for reporting: {e}", exc_info=True)
            return []

    def generate_filtered_backlog_report(self, statuses: list[str] | None = None, types: list[str] | None = None, **kwargs) -> BytesIO | str:
        """
        Generates an XLSX report of the backlog, filtered by status and/or type.

        Returns:
            BytesIO object containing XLSX data, or an error string.
        """
        logging.info(f"Orchestrator: Generating filtered backlog report (Statuses: {statuses}, Types: {types})")
        if not self.project_id:
            return "Error: No active project."
        try:
            # 1. Fetch filtered flat list from DB
            filtered_items_flat = self.db_manager.get_change_requests_filtered(self.project_id, statuses, types)
            if not filtered_items_flat:
                logging.warning("No backlog items matched the filters.")
                # We still generate an empty report for consistency
                # return "Info: No backlog items matched the selected filters."

            # 2. Reconstruct hierarchy *only* with filtered items (simplified approach)
            # A more complex approach might fetch all and filter the hierarchy in memory.
            # For simplicity, we'll report the filtered flat list with hierarchical IDs if available.
            # We need the full hierarchy first to get the correct IDs.
            full_hierarchy = self._get_backlog_with_hierarchical_numbers()
            flat_map = {item['cr_id']: item for item in self._flatten_hierarchy(full_hierarchy)}

            report_data = []
            for item_row in filtered_items_flat:
                item_dict = dict(item_row)
                full_item_data = flat_map.get(item_dict['cr_id'])
                if full_item_data:
                    item_dict['hierarchical_id'] = full_item_data.get('hierarchical_id', f"CR-{item_dict['cr_id']}")
                else:
                    item_dict['hierarchical_id'] = f"CR-{item_dict['cr_id']}" # Fallback
                report_data.append(item_dict)

            # 3. Call ReportGeneratorAgent
            report_agent = ReportGeneratorAgent()
            xlsx_bytes_io = report_agent.generate_backlog_xlsx(report_data) # Use existing method with potentially filtered data
            if not xlsx_bytes_io:
                raise Exception("ReportGeneratorAgent failed to create XLSX data.")
            return xlsx_bytes_io
        except Exception as e:
            logging.error(f"Failed to generate filtered backlog report: {e}", exc_info=True)
            return f"Error: {e}"

    def generate_sprint_deliverables_report(self, sprint_id: str, **kwargs) -> BytesIO | str:
        """
        Generates an XLSX report listing backlog items and implemented artifacts for a sprint.

        Returns:
            BytesIO object containing XLSX data, or an error string.
        """
        logging.info(f"Orchestrator: Generating sprint deliverables report for sprint '{sprint_id}'")
        if not self.project_id:
            return "Error: No active project."
        if not sprint_id:
            return "Error: No sprint selected."
        try:
            # 1. Get sprint details (plan JSON)
            sprint_details = self.db_manager._execute_query("SELECT sprint_plan_json FROM Sprints WHERE sprint_id = ?", (sprint_id,), fetch="one")
            if not sprint_details or not sprint_details['sprint_plan_json']:
                return f"Error: Could not find implementation plan for sprint {sprint_id}."

            sprint_plan_tasks = self._parse_plan_json(sprint_details['sprint_plan_json'])
            if not sprint_plan_tasks:
                return f"Info: Sprint {sprint_id} has no defined implementation tasks."

            # 2. Get all micro_spec_ids from the plan
            micro_spec_ids_in_plan = {task['micro_spec_id'] for task in sprint_plan_tasks if 'micro_spec_id' in task}
            if not micro_spec_ids_in_plan:
                return f"Info: No trackable tasks found in the plan for sprint {sprint_id}."

            # 3. Get artifacts linked to those micro_spec_ids
            linked_artifacts = self.db_manager.get_artifacts_by_micro_spec_ids(self.project_id, list(micro_spec_ids_in_plan))
            artifact_map = {art['micro_spec_id']: dict(art) for art in linked_artifacts}

            # 4. Get backlog items for the sprint
            sprint_items = self.db_manager.get_items_for_sprint(sprint_id)
            full_hierarchy = self._get_backlog_with_hierarchical_numbers()
            flat_map = {item['cr_id']: item for item in self._flatten_hierarchy(full_hierarchy)}

            report_data = []
            processed_cr_ids = set() # Track items already added

            # Map artifacts back to tasks and then to CRs
            for task in sprint_plan_tasks:
                ms_id = task.get("micro_spec_id")
                parent_cr_ids = task.get("parent_cr_ids", [])
                artifact = artifact_map.get(ms_id)

                for cr_id in parent_cr_ids:
                    if cr_id not in processed_cr_ids:
                        backlog_item = flat_map.get(cr_id)
                        if backlog_item:
                                report_data.append({
                                    'backlog_id': backlog_item.get('hierarchical_id', f'CR-{cr_id}'),
                                    'backlog_title': backlog_item.get('title', 'N/A'),
                                    'backlog_status': backlog_item.get('status', 'N/A'),
                                    'artifact_path': artifact['file_path'] if artifact else 'N/A (No artifact generated)',
                                    'artifact_name': artifact['artifact_name'] if artifact else 'N/A'
                                })
                                processed_cr_ids.add(cr_id)
                        else:
                                logging.warning(f"Could not find backlog item details for CR ID {cr_id} linked from sprint {sprint_id}")

            # Include any sprint items that didn't have trackable tasks
            for item_row in sprint_items:
                cr_id = item_row['cr_id']
                if cr_id not in processed_cr_ids:
                    backlog_item = flat_map.get(cr_id)
                    if backlog_item:
                        report_data.append({
                                'backlog_id': backlog_item.get('hierarchical_id', f'CR-{cr_id}'),
                                'backlog_title': backlog_item.get('title', 'N/A'),
                                'backlog_status': backlog_item.get('status', 'N/A'),
                                'artifact_path': 'N/A (No trackable tasks)',
                                'artifact_name': 'N/A'
                        })

            # 5. Call ReportGeneratorAgent
            report_agent = ReportGeneratorAgent()
            xlsx_bytes_io = report_agent.generate_sprint_deliverables_xlsx(sprint_id, report_data) # New method needed
            if not xlsx_bytes_io:
                raise Exception("ReportGeneratorAgent failed to create XLSX data.")
            return xlsx_bytes_io

        except Exception as e:
            logging.error(f"Failed to generate sprint deliverables report: {e}", exc_info=True)
            return f"Error: {e}"

    def generate_burndown_chart_data(self, sprint_id: str, **kwargs) -> BytesIO | str:
        """
        Generates data/image for the Complexity Point Burndown Chart.

        Returns:
            BytesIO object containing PNG image data, or an error string.
        """
        logging.info(f"Orchestrator: Generating burndown chart data for sprint '{sprint_id}'")
        if not self.project_id: return "Error: No active project."
        if not sprint_id: return "Error: No sprint selected."
        try:
            complexity_map = {"Small": 1, "Medium": 3, "Large": 5}
            sprint_items = self.db_manager.get_items_for_sprint(sprint_id)
            if not sprint_items: return "Info: No items found for this sprint."

            total_points = sum(complexity_map.get(item['complexity'], 0) for item in sprint_items)
            # Placeholder: Need actual completion history (timestamps/task order)
            # For now, simulate based on current status
            completed_points = sum(complexity_map.get(item['complexity'], 0) for item in sprint_items if item['status'] == 'COMPLETED')
            remaining_points = total_points - completed_points
            burndown_data = {'total': total_points, 'remaining': remaining_points, 'sprint_id': sprint_id}

            report_agent = ReportGeneratorAgent()
            image_bytes_io = report_agent.generate_burndown_chart_image(burndown_data) # New method needed
            if not image_bytes_io:
                raise Exception("ReportGeneratorAgent failed to create chart image.")
            return image_bytes_io
        except Exception as e:
            logging.error(f"Failed to generate burndown chart data: {e}", exc_info=True)
            return f"Error: {e}"

    def generate_workflow_efficiency_data(self, **kwargs) -> BytesIO | str:
        """
        Generates data/image for the Workflow Efficiency (CFD) chart.

        Returns:
            BytesIO object containing PNG image data, or an error string.
        """
        logging.info("Orchestrator: Generating workflow efficiency (CFD) data.")
        if not self.project_id: return "Error: No active project."
        try:
            # Placeholder: Need historical status data over time.
            # This requires logging status changes with timestamps or querying git history if available.
            # For now, we'll use the current snapshot.
            current_status_counts = self.db_manager.get_backlog_status_summary(self.project_id)
            cfd_data = {'current_snapshot': current_status_counts} # Simplified data structure

            report_agent = ReportGeneratorAgent()
            image_bytes_io = report_agent.generate_cfd_chart_image(cfd_data) # New method needed
            if not image_bytes_io:
                raise Exception("ReportGeneratorAgent failed to create CFD chart image.")
            return image_bytes_io
        except Exception as e:
            logging.error(f"Failed to generate workflow efficiency data: {e}", exc_info=True)
            return f"Error: {e}"

    def generate_code_quality_trend_data(self, **kwargs) -> BytesIO | str:
        """
        Generates data/image for the Code Quality Trend chart.

        Returns:
            BytesIO object containing PNG image data, or an error string.
        """
        logging.info("Orchestrator: Generating code quality trend data.")
        if not self.project_id: return "Error: No active project."
        try:
            # Placeholder: Need historical test status data across sprints/time.
            # This requires snapshotting Artifacts.unit_test_status at sprint ends or over time.
            # For now, use the current snapshot.
            current_test_status_counts = self.db_manager.get_component_test_status_summary(self.project_id)
            trend_data = {'current_snapshot': current_test_status_counts} # Simplified

            report_agent = ReportGeneratorAgent()
            image_bytes_io = report_agent.generate_quality_trend_chart_image(trend_data) # New method needed
            if not image_bytes_io:
                raise Exception("ReportGeneratorAgent failed to create quality trend chart image.")
            return image_bytes_io
        except Exception as e:
            logging.error(f"Failed to generate code quality trend data: {e}", exc_info=True)
            return f"Error: {e}"

    def generate_ai_assistance_rate_data(self, **kwargs) -> BytesIO | str:
        """
        Generates data for the AI Assistance Rate report.

        Returns:
            String containing formatted report data or an error message.
        """
        logging.info("Orchestrator: Generating AI assistance rate data.")
        if not self.project_id: return "Error: No active project."
        try:
            # Placeholder: Need historical tracking of DEBUG_PM_ESCALATION phase entries.
            # This could involve querying logs or a dedicated event table if implemented.
            # Simulate a simple calculation for now.
            # Assume 5 escalations happened over 2 sprints.
            assistance_data = {
                "total_sprints_analyzed": 2,
                "total_escalations": 5,
                "average_escalations_per_sprint": 2.5
            }

            report_agent = ReportGeneratorAgent()
            report_text = report_agent.generate_ai_assistance_report(assistance_data) # New method needed
            return report_text
        except Exception as e:
            logging.error(f"Failed to generate AI assistance rate data: {e}", exc_info=True)
            return f"Error: {e}"

    # Helper method used by Sprint Deliverables Report
    def _parse_plan_json(self, plan_json_str: str | None) -> list:
        """Safely parses a plan JSON string into a list of tasks."""
        if not plan_json_str:
            return []
        try:
            plan_data = json.loads(plan_json_str)
            if isinstance(plan_data, dict):
                # Handle old format where plan is under "development_plan" key
                return plan_data.get("development_plan", [])
            elif isinstance(plan_data, list):
                # Handle new format where the list is the plan itself
                # Check for the error object structure
                if plan_data and isinstance(plan_data[0], dict) and "error" in plan_data[0]:
                    logging.warning(f"Parsed plan JSON contains an error: {plan_data[0]['error']}")
                    return []
                return plan_data
            else:
                logging.warning(f"Plan JSON is neither a dict nor list: {type(plan_data)}")
                return []
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse plan JSON: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error parsing plan JSON: {e}", exc_info=True)
            return []

    def get_project_reports_dir(self) -> Path:
        """
        Gets the path to the project's 'docs/test_reports' directory, creating it if necessary.
        """
        if not self.project_id:
            raise Exception("Cannot get reports directory; no active project.")

        project_details = self.db_manager.get_project_by_id(self.project_id)
        if not project_details or not project_details['project_root_folder']:
            raise Exception("Cannot get reports directory; project root folder not found.")

        project_root = Path(project_details['project_root_folder'])
        reports_dir = project_root / "docs" / "project_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        return reports_dir

    def generate_health_snapshot_report(self, **kwargs) -> BytesIO | str:
        """
        Orchestrates the generation of the Project Health Snapshot .docx file.
        Returns the path to the generated file, or an error string.
        """
        if not self.project_id or not self.project_name:
            return "Error: No active project."

        try:
            snapshot_data = self.get_health_snapshot_data()
            if not snapshot_data.get('backlog_summary') and not snapshot_data.get('test_summary'):
                logging.warning("No data found for Project Pulse report. Generating report with 'No Data' entries.")
                # We proceed, the agent method handles empty dicts

            agent = ReportGeneratorAgent()
            docx_bytes_io = agent.generate_health_snapshot_docx(self.project_name, snapshot_data)

            # The file saving is done by the helper method save_report_file
            # report_filename = f"{self.project_name}_Health_Snapshot.docx"
            # save_path = self.get_project_reports_dir() / report_filename

            # with open(save_path, 'wb') as f:
            #     f.write(docx_bytes_io.getbuffer())

            # logging.info(f"Health Snapshot report saved to: {save_path}")
            return docx_bytes_io
        except Exception as e:
            logging.error(f"Failed to generate Project Pulse report: {e}", exc_info=True)
            return f"Error: Failed generating Project Pulse - {e}"

    def generate_traceability_matrix_report(self, **kwargs) -> BytesIO | str:
        """
        Orchestrates the generation of the .xlsx Traceability Matrix.
        Returns the path to the generated file, or an error string.
        """
        if not self.project_id or not self.project_name:
            return "Error: No active project."

        try:
            # 1. Reuse the data-gathering logic we already built for the .docx report
            trace_data = self.get_traceability_report_data(self.project_id)

            if not trace_data:
                logging.info("No traceability data found to generate .xlsx matrix.")
                # We proceed, the agent method handles empty lists

            # 2. Call the new agent method to generate the .xlsx
            agent = ReportGeneratorAgent()
            xlsx_bytes_io = agent.generate_traceability_xlsx(trace_data, self.project_name)

            # 3. Save the file
            report_filename = f"{self.project_name}_Backlog_Traceability_Report.xlsx"
            save_path = self.get_project_reports_dir() / report_filename

            with open(save_path, 'wb') as f:
                f.write(xlsx_bytes_io.getbuffer())

            logging.info(f"Traceability Matrix .xlsx report saved to: {save_path}")
            return xlsx_bytes_io
        except Exception as e:
            logging.error(f"Failed to generate Backlog Traceability Matrix report: {e}", exc_info=True)
            return f"Error: {e}"

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
            logging.info(f"Successfully saved Complexity & Risk Assessment to database for project {self.project_id}")

            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "docs"
                docs_dir.mkdir(exist_ok=True)

                # Save the raw JSON file for system use
                # assessment_file_path_json = docs_dir / "automated_delivery_risk_assessment.json"
                # assessment_file_path_json.write_text(assessment_json_str, encoding="utf-8")
                # self._commit_document(assessment_file_path_json, "docs: Add Complexity and Risk Assessment (JSON)")

                # Generate and save the formatted .docx report
                assessment_file_path_docx = docs_dir / "automated_delivery_risk_assessment.docx"
                report_generator = ReportGeneratorAgent()
                assessment_data = json.loads(assessment_json_str)
                docx_bytes = report_generator.generate_assessment_docx(assessment_data, self.project_name)

                with open(assessment_file_path_docx, 'wb') as f:
                    f.write(docx_bytes.getbuffer())

                self._commit_document(assessment_file_path_docx, "docs: Add formatted Complexity and Risk Assessment (docx)")

        except Exception as e:
            logging.error(f"Failed to finalize and save complexity assessment: {e}")

    def finalize_and_save_tech_spec(self, final_tech_spec_markdown: str, final_tech_spec_plaintext: str, target_os: str):
        """
        Saves the final technical spec in two formats:
        - Markdown to the .md file (for viewing)
        - Plain text to the database (for downstream agents)
        """
        if not self.project_id:
            logging.error("Cannot save technical spec; no active project.")
            return

        try:
            # 1. Process and save the PLAIN TEXT to the database for agents
            pure_tech_spec_content = self._strip_header_from_document(final_tech_spec_plaintext)

            db = self.db_manager
            db.update_project_field(self.project_id, "target_os", target_os)
            db.update_project_field(self.project_id, "tech_spec_text", pure_tech_spec_content)
            logging.info(f"Successfully saved final Technical Specification to database for project {self.project_id}")

            project_details = db.get_project_by_id(self.project_id)
            if project_details and project_details['project_root_folder']:
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "docs"

                # Save the HEADED version to the Markdown file.
                spec_file_path_md = docs_dir / "technical_spec.md"
                spec_file_path_md.write_text(final_tech_spec_markdown, encoding="utf-8")
                self._commit_document(spec_file_path_md, "docs: Finalize Technical Specification (Markdown)")

                # Generate and save the formatted .docx file using the PURE content.
                from agents.agent_report_generator import ReportGeneratorAgent
                spec_file_path_docx = docs_dir / "technical_spec.docx"
                report_generator = ReportGeneratorAgent()
                docx_bytes = report_generator.generate_text_document_docx(
                    title=f"Technical Specification - {self.project_name}",
                    content=pure_tech_spec_content
                )
                with open(spec_file_path_docx, 'wb') as f:
                    f.write(docx_bytes.getbuffer())
                self._commit_document(spec_file_path_docx, "docs: Add formatted Technical Specification (docx)")

            # This can still use the headed version as it's a separate analysis.
            try:
                logging.info("Detecting technologies from finalized tech spec...")
                # We use final_tech_spec_with_header as it's the full-context version
                technologies = self.detect_technologies_in_spec(pure_tech_spec_content)
                if technologies:
                    self.db_manager.update_project_field(
                        self.project_id,
                        "detected_technologies",
                        json.dumps(technologies)
                    )
                    logging.info(f"Saved detected technologies to DB (Greenfield): {technologies}")
            except Exception as e:
                logging.error(f"Failed to detect and save technologies from tech spec: {e}", exc_info=True)

            self.active_spec_draft = None
            self.set_phase("TEST_ENVIRONMENT_SETUP")

        except Exception as e:
            logging.error(f"Failed to finalize and save technical spec: {e}")
            self.task_awaiting_approval = {"error": str(e)}

    def finalize_and_save_coding_standard(self, technology: str, standard_content: str, status: str = "COMPLETED"):
        """
        Saves the final coding standard as a distinct artifact in both .md and .docx
        formats. This method *only* saves the artifact and does not transition the phase.
        """
        if not self.project_id:
            logging.error("Cannot save coding standard; no active project.")
            return

        try:
            # FIX: The argument is 'standard_content', not 'final_standard_with_header'
            pure_standard_content = self._strip_header_from_document(standard_content)
            db = self.db_manager

            # FIX: Convert sqlite3.Row to a dict to prevent .get() errors
            project_details_row = db.get_project_by_id(self.project_id)
            if not project_details_row:
                raise Exception("Could not retrieve project details.")
            project_details = dict(project_details_row)

            if project_details and project_details.get('project_root_folder'):
                project_root = Path(project_details['project_root_folder'])
                docs_dir = project_root / "docs"
                docs_dir.mkdir(exist_ok=True)

                safe_tech_name = technology.lower().replace('#', 'sharp').replace('+', 'plus')

                md_artifact_name = f"coding_standard_{safe_tech_name}.md"
                standard_file_path_md = docs_dir / md_artifact_name

                standard_file_path_md.write_text(standard_content, encoding="utf-8")

                self._commit_document(standard_file_path_md, f"docs: Add coding standard for {technology} (Markdown)")

                from agents.agent_report_generator import ReportGeneratorAgent
                report_generator = ReportGeneratorAgent()
                docx_bytes = report_generator.generate_text_document_docx(
                    # FIX: The argument is 'technology', not 'technology_name'
                    title=f"Coding Standard ({technology}) - {project_details.get('project_name', 'ASDF Project')}",
                    content=pure_standard_content
                )
                docx_artifact_name = f"coding_standard_{safe_tech_name}.docx"
                standard_file_path_docx = docs_dir / docx_artifact_name
                with open(standard_file_path_docx, 'wb') as f:
                    f.write(docx_bytes.getbuffer())

                self._commit_document(standard_file_path_docx, f"docs: Add formatted coding standard for {technology} (docx)")

                # --- Save the record for the .md artifact to the Artifacts table ---
                artifact_data = {
                    "artifact_id": f"art_{uuid.uuid4().hex[:8]}",
                    "project_id": self.project_id,
                    "status": status,
                    "file_path": str(standard_file_path_md.relative_to(project_root)),
                    "artifact_name": f"Coding Standard ({technology})",
                    "artifact_type": "CODING_STANDARD",
                    "last_modified_timestamp": datetime.now(timezone.utc).isoformat()
                }
                db.add_or_update_artifact(artifact_data)

                logging.info(f"Successfully saved coding standard for {technology} as an artifact.")

            # The calling GUI page is responsible for checking if all items are done.

        except Exception as e:
            logging.error(f"Failed to finalize and save coding standard: {e}", exc_info=True)
            self.task_awaiting_approval = {"error": str(e)}

    def handle_backlog_generation(self, **kwargs):
        """
        Generates the initial project backlog, now conditionally providing UX and DB
        specs to the planning agent for richer context.
        """
        if not self.project_id:
            logging.error("Cannot generate backlog; no active project.")
            return

        try:
            logging.info("Starting initial backlog generation...")
            db = self.db_manager
            project_details_row = db.get_project_by_id(self.project_id)
            if not project_details_row:
                raise Exception("Could not retrieve project details from the database.")

            # Convert sqlite3.Row to a dict to safely use .get()
            project_details = dict(project_details_row)

            from agents.agent_planning_app_target import PlanningAgent_AppTarget
            planning_agent = PlanningAgent_AppTarget(self.llm_service, db)

            # Conditionally gather all available specifications
            final_spec = project_details.get('final_spec_text')
            tech_spec = project_details.get('tech_spec_text')
            ux_spec = project_details.get('ux_spec_text')
            db_spec = project_details.get('db_schema_spec_text')

            cleaned_tech_spec = self._strip_environment_setup_from_spec(tech_spec) if tech_spec else ""

            backlog_items_json = planning_agent.generate_backlog_items(
                final_spec_text=final_spec,
                tech_spec_text=cleaned_tech_spec,
                ux_spec_text=ux_spec,
                db_schema_spec_text=db_spec
            )

            self.task_awaiting_approval = {"generated_backlog_items": backlog_items_json}

            db.update_project_field(self.project_id, "is_backlog_generated", 1)
            logging.info(f"Successfully generated backlog and set 'is_backlog_generated' flag for project {self.project_id}.")

            self.set_phase("BACKLOG_RATIFICATION")

        except Exception as e:
            logging.error(f"Failed to generate project backlog: {e}", exc_info=True)
            self.task_awaiting_approval = {"error": str(e)}
            self.set_phase("AWAITING_BACKLOG_GATEWAY_DECISION")

    def finalize_and_save_dev_plan(self, plan_json_string: str) -> tuple[bool, str]:
        """
        Saves the final dev plan to the database, a .json file, and a formatted
        .docx file, loads it into the active state, and transitions to Genesis. This
        version saves only the pure, raw content to the database.
        """
        if not self.project_id:
            return False, "No active project."

        try:
            # --- THIS IS THE FIX ---
            # Save the PURE JSON content directly to the database.
            self.db_manager.update_project_field(self.project_id, "development_plan_text", plan_json_string)

            # Generate the headed version only for the file system artifacts.
            final_doc_with_header = self.prepend_standard_header(
                document_content=plan_json_string,
                document_type="Sequential Development Plan"
            )
            # --- END OF FIX ---

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
                from agents.agent_report_generator import ReportGeneratorAgent
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

            if self.project_id and new_phase not in non_dirtying_phases:
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

    def handle_proceed_action(self, **kwargs):
        """
        Handles the logic for the Genesis Pipeline. Its signature is now robust
        to accept any keyword arguments from the Worker class.
        """
        progress_callback = kwargs.get('progress_callback')
        self.is_task_processing = True

        # --- FIX MODE LOGIC ---
        if self.is_in_fix_mode:
            logging.info("--- In Fix Mode: Executing from fix plan. ---")
            if not self.fix_plan or self.fix_plan_cursor >= len(self.fix_plan):
                logging.info("Fix plan is now complete. Exiting fix mode and re-attempting original task.")
                self.is_in_fix_mode = False
                self.fix_plan = None
                self.fix_plan_cursor = 0
                # Re-enter the loop to re-attempt the original task that prompted the fix.
                return self.handle_proceed_action(**kwargs)
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
                    if progress_callback:
                        progress_callback(("ERROR", f"Fix task failed for {component_name}. Initiating debug protocol..."))
                    logging.error(f"A task within the fix plan failed for {component_name}. Error: {e}")
                    self.escalate_for_manual_debug(str(e))
                    return f"Error during fix execution: {e}"

        # --- REGULAR PLAN LOGIC ---
        if self.current_phase not in [FactoryPhase.GENESIS, FactoryPhase.SPRINT_IN_PROGRESS]:
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
            self.escalate_for_manual_debug(str(e), is_phase_failure_override=True)

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

    def handle_ui_test_decision(self, decision: str):
        """
        Handles the PM's choice from the end-of-sprint UI testing decision page.
        """
        logging.info(f"PM selected UI testing option: {decision}")
        if decision == "SKIP":
            self.post_fix_reverification_path = None # Ensure flag is clear
            self.set_phase("SPRINT_REVIEW")
        elif decision == "MANUAL":
            self.set_phase("GENERATING_MANUAL_TEST_PLAN")
        elif decision == "AUTOMATED":
            self.post_fix_reverification_path = decision
            # This will be a background task, so we set an intermediate phase
            self.set_phase("INTEGRATION_AND_VERIFICATION") # Reuse this phase for a generic "processing" state
            self.task_awaiting_approval = {"task_to_run": "automated_ui_tests"}
        else:
            logging.warning(f"Received unknown UI test decision: {decision}")
            self.set_phase("SPRINT_REVIEW") # Default to a safe state

    def _generate_manual_ui_test_plan_phase(self, progress_callback=None, **kwargs):
        """
        Generates and saves all artifacts for the manual UI test plan.
        This is designed to be run in a background worker.
        """
        if progress_callback: progress_callback(("INFO", "Generating manual UI test plan..."))
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details:
                raise Exception("Project details not found.")

            # Use bracket notation and provide defaults to avoid errors
            final_spec_text = project_details['final_spec_text'] or ""
            tech_spec_text = project_details['tech_spec_text'] or ""
            ux_spec_text = project_details['ux_spec_text'] or ""

            if not ux_spec_text:
                raise Exception("Cannot generate UI test plan: The UX/UI Specification is missing.")

            agent = UITestPlannerAgent_AppTarget(self.llm_service)
            plan_markdown = agent.generate_ui_test_plan(final_spec_text, tech_spec_text, ux_spec_text)

            if "Error:" in plan_markdown:
                raise Exception(f"Agent failed to generate test plan: {plan_markdown}")

            if progress_callback: progress_callback(("SUCCESS", "Test plan content generated."))

            # Save to DB
            final_plan_with_header = self.prepend_standard_header(plan_markdown, "UI Test Plan")
            db.update_project_field(self.project_id, "ui_test_plan_text", final_plan_with_header)

            # Save to Filesystem (.md and .docx)
            if progress_callback: progress_callback(("INFO", "Saving report documents..."))
            project_root = Path(project_details['project_root_folder'])
            docs_dir = project_root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)

            # Use a specific filename to ensure consistency
            plan_path_md = docs_dir / "manual_ui_test_plan.md"
            plan_path_md.write_text(final_plan_with_header, encoding="utf-8")

            report_generator = ReportGeneratorAgent()
            docx_bytes = report_generator.generate_text_document_docx(
                title=f"Manual UI Test Plan - {self.project_name}",
                content=plan_markdown
            )
            plan_path_docx = docs_dir / "manual_ui_test_plan.docx"
            with open(plan_path_docx, 'wb') as f:
                f.write(docx_bytes.getbuffer())

            # Commit the new documents if version control is enabled
            if project_details['version_control_enabled'] == 1:
                if progress_callback: progress_callback(("INFO", "Committing documents to version control..."))
                self._commit_document(plan_path_md, "docs: Add manual UI test plan (Markdown)")
                self._commit_document(plan_path_docx, "docs: Add formatted manual UI test plan (docx)")

            # Set the final phase to show the UI page
            self.set_phase("MANUAL_UI_TESTING")
            # return "MANUAL_UI_TESTING"
            return True

        except Exception as e:
            logging.error(f"Failed to generate manual UI test plan: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred during test plan generation:\n{e}", is_phase_failure_override=True)
            return False
            # return "Error"

    def _execute_source_code_generation_task(self, task: dict, project_root_path: Path, db: ASDFDBManager, progress_callback=None):
        """
        Handles the 'generate -> review -> correct -> verify -> commit -> update docs' workflow.
        """
        component_name = task.get("component_name")
        if progress_callback: progress_callback(("INFO", f"Executing source code generation for: {component_name}"))

        # --- RoWD-Enforced Path Integrity Check  ---
        if task.get("artifact_id"):
            artifact_record = db.get_artifact_by_id(task["artifact_id"])
            if artifact_record and artifact_record['file_path']:
                canonical_path = artifact_record['file_path']
                plan_path = task.get("component_file_path")
                if plan_path != canonical_path:
                    logging.warning(f"Path mismatch for artifact {task['artifact_id']}. Overriding plan path '{plan_path}' with canonical RoWD path '{canonical_path}'.")
                    task["component_file_path"] = canonical_path
        # --- End of Integrity Check ---

        if not self.llm_service:
            raise Exception("Cannot generate code: LLM Service is not configured.")

        project_details = db.get_project_by_id(self.project_id)
        # --- NEW MULTI-LANGUAGE LOGIC ---
        task_languages = task.get("relevant_languages", [])
        if not task_languages:
            # Fallback in case the plan is missing the new key
            logging.warning(f"Task {component_name} is missing 'relevant_languages' key. Falling back to technology_stack.")
            task_languages = [project_details['technology_stack']] if project_details['technology_stack'] else ['Python'] # Default fallback

        # The primary language for the component is the first one in the list
        primary_language = task_languages[0]

        # Consolidate all relevant coding standards
        standards_to_apply = []
        # Get all standards once to reduce DB calls
        all_standards_artifacts = [dict(row) for row in db.get_all_artifacts_for_project(self.project_id) if row['artifact_type'] == 'CODING_STANDARD']

        for lang in task_languages:
            standard_artifact = None
            for art in all_standards_artifacts:
                # Match "Python" in "Coding Standard (Python)"
                if lang.lower() in art['artifact_name'].lower():
                    standard_artifact = art
                    break

            if standard_artifact:
                # We need to read the content of the standard from its .md file
                try:
                    standard_file_path = project_root_path / standard_artifact['file_path']
                    standard_content = standard_file_path.read_text(encoding='utf-8')
                    # Strip the header to get the raw rules
                    pure_standard = self._strip_header_from_document(standard_content)
                    standards_to_apply.append(f"--- Coding Standard for {lang} ---\n{pure_standard}")
                except Exception as e:
                    logging.warning(f"Could not read coding standard file for {lang} at {standard_artifact['file_path']}: {e}")
            else:
                logging.warning(f"No coding standard artifact found for language: {lang}")

        if not standards_to_apply:
            logging.error(f"No coding standards found for component {component_name}. Proceeding without standards.")
            combined_coding_standard = "No coding standard provided."
        else:
            combined_coding_standard = "\n\n---\n\n".join(standards_to_apply)
        # --- END NEW LOGIC ---
        test_command = project_details['test_execution_command']
        version_control_enabled = project_details['version_control_enabled'] == 1 if project_details else True
        logging.warning(f"DEBUG PRE-FLIGHT: version_control_enabled is '{version_control_enabled}' for project {self.project_id}")

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
        # MODIFIED: Removed target_language, passed combined_coding_standard
        source_code = code_agent.generate_code_for_component(logic_plan, combined_coding_standard, style_guide=style_guide_to_use)
        if progress_callback: progress_callback(("SUCCESS", "... Source code generated."))

        # This block validates the AI's output
        if not source_code or not source_code.strip():
            raise Exception("Code generation failed: The AI returned empty source code for the component.")

        MAX_REVIEW_ATTEMPTS = 2
        for attempt in range(MAX_REVIEW_ATTEMPTS):
            if progress_callback: progress_callback(("INFO", f"Reviewing code for {component_name} (Attempt {attempt + 1})..."))
            review_status, review_output = review_agent.review_code(micro_spec_content, logic_plan, source_code, rowd_json, combined_coding_standard)
            if review_status == "pass":
                break
            elif review_status == "pass_with_fixes":
                source_code = review_output
                break
            elif review_status == "fail":
                if attempt < MAX_REVIEW_ATTEMPTS - 1:
                    if progress_callback: progress_callback(("INFO", f"Re-writing code for {component_name} based on feedback..."))
                    # MODIFIED: Removed target_language, passed combined_coding_standard
                    source_code = code_agent.generate_code_for_component(logic_plan, combined_coding_standard, style_guide=style_guide_to_use, feedback=review_output)
                else:
                    raise Exception(f"Component '{component_name}' failed code review after all attempts.")
        if progress_callback: progress_callback(("SUCCESS", "... Code review process complete."))

        unit_tests = None
        test_path = task.get("test_file_path")

        # Only generate tests if the plan includes a path for the test file
        if test_path:
            if progress_callback: progress_callback(("INFO", f"Generating unit tests for {component_name}..."))
            # MODIFIED: Passed combined_coding_standard and primary_language
            unit_tests = test_agent.generate_unit_tests_for_component(source_code, micro_spec_content, combined_coding_standard, primary_language)
            if progress_callback: progress_callback(("SUCCESS", "... Unit tests generated."))

        if progress_callback:
            commit_action_text = "and committing" if version_control_enabled else "for"
            log_message = f"Writing files, running regression tests, {commit_action_text} {component_name}..."
            progress_callback(("INFO", log_message))
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

        # --- Hash Calculation ---
        file_hash = hashlib.sha256(source_code.encode('utf-8')).hexdigest()
        logging.info(f"Calculated SHA-256 hash for {component_name}: {file_hash}")
        # --- End of Hash Calculation ---

        if progress_callback: progress_callback(("INFO", f"Updating project records for {component_name}..."))
        doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)
        doc_agent.update_artifact_record({
            "artifact_id": f"art_{uuid.uuid4().hex[:8]}", "project_id": self.project_id,
            "file_path": task.get("component_file_path"), "artifact_name": component_name,
            "artifact_type": task.get("component_type"), "short_description": micro_spec_content,
            "status": "UNIT_TESTS_PASSING", "unit_test_status": "TESTS_PASSING",
            "commit_hash": commit_hash,
            "file_hash": file_hash,
            "version": 1,
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

    def _run_post_implementation_doc_update(self, progress_callback=None):
        """
        After a sprint, this method updates all relevant project documents,
        clears the completed sprint's state, and transitions to the backlog.
        This is designed to be run in a background worker.
        """
        logging.info("Sprint complete. Running post-sprint documentation update...")
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details:
                raise Exception("Could not run doc update; project details not found.")

            if not self.llm_service:
                raise Exception("Could not run doc update; LLM Service is not configured.")

            project_root = Path(project_details['project_root_folder'])
            docs_dir = project_root / "docs"
            implementation_plan_for_update = json.dumps(self.active_plan, indent=4)
            doc_agent = DocUpdateAgentRoWD(db, llm_service=self.llm_service)

            def update_and_save_document(doc_key: str, doc_name: str, file_name: str):
                original_doc = project_details[doc_key]
                if original_doc:
                    if progress_callback: progress_callback(("INFO", f"Updating {doc_name}..."))
                    current_date = datetime.now().strftime('%x')
                    updated_content = doc_agent.update_specification_text(
                        original_spec=original_doc,
                        implementation_plan=implementation_plan_for_update,
                        current_date=current_date
                    )
                    db.update_project_field(self.project_id, doc_key, updated_content)
                    doc_path = docs_dir / file_name
                    doc_path.write_text(updated_content, encoding="utf-8")
                    self._commit_document(doc_path, f"docs: Update {doc_name} after sprint {self.active_sprint_id}")
                    if progress_callback: progress_callback(("SUCCESS", f"Successfully updated the {doc_name}."))

            update_and_save_document('final_spec_text', 'Application Specification', 'application_spec.md')
            update_and_save_document('tech_spec_text', 'Technical Specification', 'technical_spec.md')
            update_and_save_document('ux_spec_text', 'UX/UI Specification', 'ux_ui_specification.md')
            # We don't update the UI Test Plan here as it's sprint-specific, not a core spec.

        except Exception as e:
            logging.error(f"Failed during post-implementation doc update: {e}")
            if progress_callback: progress_callback(("ERROR", f"Failed during document update: {e}"))
            # We still proceed to the finally block to avoid getting stuck.
        finally:
            # This logic is moved here from handle_sprint_review_complete
            # It runs after the update is attempted, successful or not.
            if progress_callback: progress_callback(("INFO", "Finalizing sprint and returning to backlog..."))
            self.active_plan = None
            self.active_plan_cursor = 0
            self.post_fix_reverification_path = None
            self.is_executing_cr_plan = False
            self.active_sprint_id = None
            self.task_awaiting_approval = {}
            self.set_phase("BACKLOG_VIEW")
            logging.info("Post-sprint cleanup complete. Returned to BACKLOG_VIEW.")

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
        logging.info("Starting Phase: Automated Integration & Verification.")
        if progress_callback:
            progress_callback("Starting Phase: Automated Integration & Verification.")

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
                target_file_path.parent.mkdir(parents=True, exist_ok=True)
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

            # --- THIS IS THE FIX ---
            # Save the PURE content to the database.
            db.update_project_field(self.project_id, "ui_test_plan_text", ui_test_plan_content)

            # Generate the headed version for file system artifacts.
            final_ui_test_plan_with_header = self.prepend_standard_header(
                document_content=ui_test_plan_content,
                document_type="UI Test Plan"
            )

            # Save the HEADED version to the Markdown file.
            test_plan_file_path_md = docs_dir / "ui_test_plan.md"
            test_plan_file_path_md.write_text(final_ui_test_plan_with_header, encoding="utf-8")
            self._commit_document(test_plan_file_path_md, "docs: Add UI Test Plan (Markdown)")

            # Generate and save the formatted .docx file using the PURE content.
            from agents.agent_report_generator import ReportGeneratorAgent
            test_plan_file_path_docx = docs_dir / "ui_test_plan.docx"
            report_generator = ReportGeneratorAgent()
            docx_bytes = report_generator.generate_text_document_docx(
                title=f"Manual UI Test Plan - {self.project_name}",
                content=ui_test_plan_content
            )
            with open(test_plan_file_path_docx, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            self._commit_document(test_plan_file_path_docx, "docs: Add formatted UI Test Plan (docx)")
            # --- END OF FIX ---

            if progress_callback: progress_callback("Integration phase complete. Proceeding to manual testing.")

            self.set_phase("MANUAL_UI_TESTING")

        except Exception as e:
            logging.error(f"Failed during integration and testing phase: {e}", exc_info=True)
            self.escalate_for_manual_debug(str(e))

    def handle_ui_test_result_upload(self, test_result_content: str):
        """
        Orchestrates the evaluation of an uploaded UI test results file.
        Now context-aware for on-demand vs. end-of-sprint cycles.
        """
        if not self.project_id:
            logging.error("Cannot handle test result upload; no active project.")
            return

        logging.info(f"Handling UI test result upload for project {self.project_id}.")
        try:
            if not self.llm_service:
                raise Exception("Cannot evaluate test results: LLM Service is not configured.")

            self.is_project_dirty = True

            eval_agent = TestResultEvaluationAgent_AppTarget(llm_service=self.llm_service)
            failure_summary = eval_agent.evaluate_ui_test_results(test_result_content)

            if "ALL_TESTS_PASSED" in failure_summary:
                logging.info("UI test result evaluation complete: All tests passed.")
                # If on-demand, return to previous workflow. Otherwise, proceed to sprint review.
                if self.is_on_demand_test_cycle:
                    main_window = self.get_main_window_instance()
                    if main_window and main_window.previous_phase:
                        self.set_phase(main_window.previous_phase.name)
                    else:
                        self.set_phase("BACKLOG_VIEW") # Safe fallback
                    self.is_on_demand_test_cycle = False
                else:
                    self.set_phase("SPRINT_REVIEW")
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

            project_details_row = db.get_project_by_id(self.project_id)
            if not project_details_row:
                raise Exception("Could not retrieve project details.")
            # Convert sqlite3.Row to a dict to safely use .get()
            project_details = dict(project_details_row)

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
            detected_technologies_json = project_details.get('detected_technologies', '[]')
            new_plan_str = planner_agent.create_refactoring_plan(
                cr_details['description'], project_details['final_spec_text'],
                project_details['tech_spec_text'], rowd_json, context_package["source_code"],
                detected_technologies_json=detected_technologies_json
            )

            response_data = json.loads(new_plan_str)
            if "error" in response_data:
                raise Exception(f"RefactoringPlannerAgent failed: {response_data['error']}")

            self.active_plan = response_data
            self.active_plan_cursor = 0
            self.is_executing_cr_plan = True

            # After the plan is successfully generated, update the status to reflect this.
            db.update_cr_status(cr_id, "IMPLEMENTATION_IN_PROGRESS")

            logging.info("Successfully generated new development plan from Change Request.")
            self.set_phase("GENESIS")

        except Exception as e:
            logging.error(f"Failed to process implementation for CR-{cr_id}. Error: {e}")
            db.update_cr_status(cr_id, "RAISED") # Revert status on failure
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

    def handle_backlog_item_moved(self, moved_cr_id: int, new_parent_cr_id: int | None, new_row: int):
        """
        Handles the re-parenting and re-ordering of a backlog item after a
        successful drag-and-drop operation. Updates parent_id, display_order,
        and request_type based on the new hierarchy.
        """
        logging.info(f"Handling moved backlog item. CR_ID: {moved_cr_id}, New Parent_ID: {new_parent_cr_id}, New Row: {new_row}") #
        try:
            db = self.db_manager
            moved_item = db.get_cr_by_id(moved_cr_id) #
            if not moved_item:
                logging.error(f"Cannot process move: Moved item CR-{moved_cr_id} not found.")
                return

            original_type = moved_item['request_type'] #
            new_request_type = original_type # Default to original type

            # Determine the type of the new parent
            new_parent_type = None
            if new_parent_cr_id is not None:
                new_parent_item = db.get_cr_by_id(new_parent_cr_id) #
                if new_parent_item:
                    new_parent_type = new_parent_item['request_type'] #
                else:
                    logging.warning(f"Could not find new parent item CR-{new_parent_cr_id}. Assuming root drop.")
                    new_parent_cr_id = None # Correct the ID if parent not found

            # --- Type Promotion Logic ---
            if new_parent_type is None: # Dropped at root level
                if original_type == 'FEATURE':
                    new_request_type = 'EPIC'
            elif new_parent_type == 'EPIC': # Dropped onto an Epic
                if original_type in ['BACKLOG_ITEM', 'BUG_REPORT']: # Should not happen with validation, but handle defensively
                     new_request_type = 'FEATURE'
                elif original_type == 'EPIC': # Cannot drop Epic onto Epic
                    logging.warning(f"Invalid move: Cannot make EPIC {moved_cr_id} child of EPIC {new_parent_cr_id}. Type not changed.")
                    new_request_type = 'EPIC'
                else: # Feature onto Epic is valid, type remains FEATURE
                    new_request_type = 'FEATURE'
            elif new_parent_type == 'FEATURE': # Dropped onto a Feature
                if original_type == 'EPIC': # Cannot drop Epic onto Feature
                    logging.warning(f"Invalid move: Cannot make EPIC {moved_cr_id} child of FEATURE {new_parent_cr_id}. Type not changed.")
                    new_request_type = 'EPIC'
                elif original_type == 'FEATURE': # Cannot drop Feature onto Feature
                     logging.warning(f"Invalid move: Cannot make FEATURE {moved_cr_id} child of FEATURE {new_parent_cr_id}. Type not changed.")
                     new_request_type = 'FEATURE'
                else: # Item or Bug onto Feature is valid
                    new_request_type = original_type # Keep as BACKLOG_ITEM or BUG_REPORT

            # Update the type of the moved item if it changed
            if new_request_type != original_type:
                db.update_cr_type(moved_cr_id, new_request_type) #

                # If the item became an EPIC, promote its direct children to FEATURE
                if new_request_type == 'EPIC':
                    db.update_child_types(moved_cr_id, 'FEATURE') #

            # --- Re-ordering Logic (remains the same) ---
            db.update_cr_field(moved_cr_id, 'parent_cr_id', new_parent_cr_id) #

            if new_parent_cr_id is None:
                siblings = db.get_top_level_items_for_project(self.project_id) #
            else:
                siblings = db.get_children_of_cr(new_parent_cr_id) #

            sibling_ids = [s['cr_id'] for s in siblings] #
            if moved_cr_id in sibling_ids: sibling_ids.remove(moved_cr_id) #

            if new_row < 0 or new_row > len(sibling_ids): sibling_ids.append(moved_cr_id) #
            else: sibling_ids.insert(new_row, moved_cr_id) #

            order_mapping = [(i + 1, cr_id) for i, cr_id in enumerate(sibling_ids)] #
            db.batch_update_cr_order(order_mapping) #

            logging.info(f"Successfully processed move for {moved_cr_id}. New type: {new_request_type}. Re-ordered {len(order_mapping)} siblings.") #
            self.is_project_dirty = True

        except Exception as e:
            logging.error(f"Failed to handle backlog item move: {e}", exc_info=True) #
            # Re-raise the exception so the UI layer knows it failed and can refresh
            raise

    def resume_project(self):
        """
        Resumes a project using the detailed state loaded into self.resumable_state.
        """
        # Highest Priority: Attempt to load a detailed, formally saved session state.
        if self.resumable_state:
            try:
                logging.info(f"Found a saved session state for project {self.project_id}. Resuming...")

                # Load the details first
                details = json.loads(self.resumable_state['state_details'])
                if "task_awaiting_approval" in details:
                    # Handles the existing format (e.g., from a manual pause)
                    self.task_awaiting_approval = details.get("task_awaiting_approval")
                else:
                    # Handles our test case's format without breaking the old way
                    self.task_awaiting_approval = details

                # Check for our special condition
                if self.task_awaiting_approval and self.task_awaiting_approval.get("resuming_from_manual_fix"):
                    self.is_resuming_from_manual_fix = True
                    self.current_phase = FactoryPhase.GENESIS #<-- THIS IS THE FIX
                    logging.info("Detected 'resuming_from_manual_fix' flag. Overriding phase to GENESIS.")
                else:
                    # If not our special condition, resume to the phase that was saved
                    self.current_phase = FactoryPhase[self.resumable_state['current_phase']]

                # Load the rest of the state
                self.active_plan = details.get("active_plan")
                self.active_plan_cursor = details.get("active_plan_cursor", 0)
                self.debug_attempt_counter = details.get("debug_attempt_counter", 0)
                self.active_spec_draft = details.get("active_spec_draft")
                self.active_sprint_id = details.get("active_sprint_id")

                self.db_manager.delete_orchestration_state_for_project(self.project_id)
                self.resumable_state = None
                logging.info(f"Project '{self.project_name}' resumed successfully to phase {self.current_phase.name}.")
                return
            except Exception as e:
                logging.error(f"Failed to load saved session state, proceeding to fallback. Error: {e}")

        # Lowest Priority: Fallback based on most recently completed document.
        logging.info("No active session or sprint found. Performing intelligent fallback based on project documents.")
        project_details = self.db_manager.get_project_by_id(self.project_id)
        if not project_details:
            logging.error(f"Cannot resume project {self.project_id}: project details not found.")
            self.reset()
            return

        all_artifacts = self.db_manager.get_all_artifacts_for_project(self.project_id)
        has_coding_standard = any(art['artifact_type'] == 'CODING_STANDARD' for art in all_artifacts)

        if project_details['development_plan_text'] or has_coding_standard:
            self.set_phase(FactoryPhase.BACKLOG_VIEW.name)
        elif project_details['tech_spec_text']:
            self.set_phase(FactoryPhase.CODING_STANDARD_GENERATION.name)
        elif project_details['final_spec_text']:
            self.set_phase(FactoryPhase.TECHNICAL_SPECIFICATION.name)
        else:
            self.set_phase(FactoryPhase.SPEC_ELABORATION.name)

        logging.info(f"Project '{self.project_name}' will resume at the most logical phase: {self.current_phase.name}")


    def resume_from_idle(self, project_id: str):
        """Resumes an active project by first loading its state and then running pre-flight checks."""
        if self.project_id:
            logging.warning("Resuming from idle, but a project is already active. Performing a safety reset.")
            self.reset()

        project_details = self.db_manager.get_project_by_id(project_id)
        if not project_details:
            logging.error(f"Cannot resume project {project_id}: Not found in database.")
            self.preflight_check_result = {"status": "ERROR", "message": f"Project with ID {project_id} not found."}
            self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")
            return

        self.project_id = project_id
        self.project_name = project_details['project_name']
        self.project_root_path = project_details['project_root_folder']

        # CORRECTED LOGIC: Use the new, project-specific query.
        self.resumable_state = self.db_manager.get_orchestration_state_for_project(self.project_id)

        # Now, run pre-flight checks and set the phase to display the pre-flight page.
        check_result = self._perform_preflight_checks(self.project_root_path, self.project_id)
        self.preflight_check_result = {**check_result, "history_id": None}

        self.is_project_dirty = False
        self.set_phase("AWAITING_PREFLIGHT_RESOLUTION")

    def escalate_for_manual_debug(self, failure_log: str, is_functional_bug: bool = False, is_phase_failure_override: bool = False):
        """
        Handles the escalation process for a task failure. It increments a
        counter, and if the maximum attempts are exceeded, it sets the phase
        to escalate to the PM.
        """
        logging.info("A failure has triggered the escalation pipeline.")

        # If this is a functional bug from UI testing, it's a direct escalation.
        if is_functional_bug:
            self.task_awaiting_approval = {
                "failure_log": failure_log,
                "original_failing_task": None,
                "is_phase_failure": True
            }
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
                "original_failing_task": original_failing_task,
                "is_phase_failure": is_phase_failure_override or (original_failing_task is None)
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

    def acknowledge_manual_fix_and_advance(self, **kwargs):
        """
        Handles the PM's confirmation that a manual fix is complete.
        This workflow trusts the PM's fix, updates the RoWD, and advances the plan.
        """
        logging.info("PM has acknowledged a manual fix. Updating records and proceeding.")
        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            project_root = Path(project_details['project_root_folder'])

            # Get the details of the task that was just fixed
            task_details = self.get_current_task_details()
            if not task_details or not task_details.get('task'):
                raise Exception("Could not retrieve details for the current task.")
            task = task_details['task']

            # --- THIS IS THE FIX ---
            # Check if the plan is already complete. If so, there's no task to process.
            if "micro_spec_id" not in task:
                logging.info("Development plan is complete. Acknowledging manual fix for end-of-sprint verification.")
                self.is_resuming_from_manual_fix = False
                self.set_phase("GENESIS")
                return True
            # --- END OF FIX ---

            # 2. Read the manually fixed code from the file
            component_file = project_root / task['component_file_path']
            if not component_file.exists():
                raise FileNotFoundError(f"Could not find the manually fixed file at: {component_file}")
            source_code = component_file.read_text(encoding='utf-8')

            # 3. Generate a summary for the fixed code
            summarization_agent = CodeSummarizationAgent(llm_service=self.llm_service)
            summary = summarization_agent.summarize_code(source_code)

            # 4. Get the latest commit hash and file hash (NOW CONDITIONAL)
            version_control_enabled = project_details['version_control_enabled'] == 1
            commit_hash = "N/A"  # Default value for local workspaces

            if version_control_enabled:
                try:
                    repo = git.Repo(project_root)
                    commit_hash = repo.head.commit.hexsha
                except git.exc.InvalidGitRepositoryError:
                    logging.warning(f"Project {self.project_name} has version control enabled but is not a valid Git repo. Skipping commit hash.")
                    commit_hash = "ERROR_NO_REPO"

            file_hash = hashlib.sha256(source_code.encode('utf-8')).hexdigest()

            # 5. Create the success record in the RoWD
            from agents.doc_update_agent_rowd import DocUpdateAgentRoWD
            doc_agent = DocUpdateAgentRoWD(db, self.llm_service)
            doc_agent.update_artifact_record({
                "artifact_id": f"art_{uuid.uuid4().hex[:8]}",
                "project_id": self.project_id,
                "file_path": task.get("component_file_path"),
                "artifact_name": task.get("component_name"),
                "artifact_type": task.get("component_type"),
                "short_description": task.get("task_description"),
                "status": "UNIT_TESTS_PASSING",
                "unit_test_status": "TESTS_PASSING",
                "commit_hash": commit_hash,
                "file_hash": file_hash,
                "version": 1,
                "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
                "micro_spec_id": task.get("micro_spec_id"),
                "code_summary": summary
            })

            # 6. Advance the plan and reset the flag
            self.active_plan_cursor += 1
            self.is_resuming_from_manual_fix = False
            self.set_phase("GENESIS")
            logging.info("Successfully recorded manual fix and advanced sprint plan.")
            return True

        except Exception as e:
            logging.error(f"Failed to process manual fix acknowledgement: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred while trying to process your manual fix:\n{e}")

    def skip_and_log_manually_handled_task(self, **kwargs):
        """
        Skips the current task after a manual fix attempt, logs it as a new bug,
        blocks the parent items, and advances the sprint plan.
        """
        logging.warning("PM chose to skip task after manual fix attempt. Logging as bug and continuing sprint.")
        try:
            task_details = self.get_current_task_details()
            if not task_details or not task_details.get('task'):
                raise ValueError("Could not find the current task context to skip.")
            task_to_skip = task_details['task']

            parent_cr_ids = task_to_skip.get('parent_cr_ids', [])
            if not parent_cr_ids:
                logging.error("Traceability Error: Cannot log bug as parent CR IDs were not found in the skipped task.")
            else:
                self.db_manager.batch_update_cr_status(parent_cr_ids, "BLOCKED")

            # Get user-facing hierarchical IDs for the description
            full_backlog_with_ids = self._get_backlog_with_hierarchical_numbers()
            flat_backlog_map = {}
            def flatten_hierarchy(items):
                for item in items:
                    flat_backlog_map[item['cr_id']] = item
                    if "features" in item: flatten_hierarchy(item["features"])
                    if "user_stories" in item: flatten_hierarchy(item["user_stories"])
            flatten_hierarchy(full_backlog_with_ids)

            parent_hierarchical_ids = [flat_backlog_map.get(pid, {}).get('hierarchical_id', f'CR-{pid}') for pid in parent_cr_ids]
            parent_ids_str = ', '.join(parent_hierarchical_ids) if parent_hierarchical_ids else "N/A"

            task_name = task_to_skip.get('component_name', 'Unknown Task')
            description = (
                f"**Objective for Impact Analysis:** This is an auto-generated bug report for a sprint task that was skipped after a manual fix attempt failed. "
                f"This bug is blocking the completion of parent item(s): {parent_ids_str}.\n\n"
                f"--- SKIPPED TASK ---\n"
                f"```json\n{json.dumps(task_to_skip, indent=2)}\n```"
            )

            bug_data = {
                "request_type": "BUG_REPORT",
                "title": f"Fix skipped sprint task: {task_name}",
                "description": description,
                "severity": "High",
                "parent_id": parent_cr_ids[0] if parent_cr_ids else None
            }
            success, new_bug_id = self.add_new_backlog_item(bug_data)
            if not success:
                raise Exception(f"Failed to create new BUG_REPORT item in the database for skipped task: {task_name}")

            # Advance the plan and reset flags
            self.active_plan_cursor += 1
            self.is_resuming_from_manual_fix = False
            self.set_phase("GENESIS")
            logging.info(f"Successfully logged failure for '{task_name}' as BUG-{new_bug_id}. Sprint will continue.")
            return True
        except Exception as e:
            logging.error(f"Critical error in skip_and_log_manually_handled_task: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred while trying to log a bug: {e}")
            return False

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

            # Set a flag to indicate why this pause is happening.
            self.task_awaiting_approval = {"resuming_from_manual_fix": True}

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

    def handle_retry_fix_action(self, failure_log: str, progress_callback=None, **kwargs):
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

    def run_full_test_suite(self, test_type: str = "regression", progress_callback=None, **kwargs):
        """
        Triggers a full run of the project's automated test suite.

        Args:
            test_type (str): The type of test to run ("regression" or "integration").

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

        if test_type == "integration":
            test_command = project_details['integration_test_command']
        else: # Default to regression
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
        Runs the full project test suite as a final quality gate and generates
        a detailed test report.
        """
        logging.info("Sprint plan complete. Running Backend Testing and generating report...")
        if progress_callback:
            progress_callback(("INFO", "Running Backend Testing..."))

        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details: raise Exception("Project details not found.")
            project_root = Path(project_details['project_root_folder'])
            technologies_json = project_details['detected_technologies'] or '[]'
            try:
                technology_list = json.loads(technologies_json)
            except (json.JSONDecodeError, TypeError):
                technology_list = ['python'] # Fallback
            if not technology_list:
                technology_list = ['python'] # Fallback

            # Step 1: Find and read all test files to build a plan.
            if progress_callback: progress_callback(("INFO", "Scanning for test files to build plan..."))
            test_files_content = {}
            # A simple glob for common test patterns. A future enhancement could make this language-specific.
            for pattern in ['test_*.py', '*_test.py', '*Test.java', '*Tests.cs']:
                # Search in common locations like 'tests/' or 'src/tests/'
                for test_dir in [project_root / 'tests', project_root / 'src' / 'tests']:
                    if test_dir.exists():
                        for test_file in test_dir.rglob(pattern):
                            relative_path = test_file.relative_to(project_root)
                            test_files_content[str(relative_path)] = test_file.read_text(encoding='utf-8')

            # Step 2: Extract the test plan from the files.
            plan_json = "[]"
            if test_files_content:
                if progress_callback: progress_callback(("INFO", "Extracting test plan from source code..."))
                extractor_agent = BackendTestPlanExtractorAgent(self.llm_service)
                plan_json = extractor_agent.extract_plan(technology_list, test_files_content)

            # Step 3: Run the actual tests.
            if progress_callback: progress_callback(("INFO", "Executing test suite..."))
            success, raw_output = self.run_full_test_suite(progress_callback)

            # Step 4 & 5: Format and generate the .docx report.
            if progress_callback: progress_callback(("INFO", "Formatting and saving test report..."))
            report_formatter = TestReportFormattingAgent(self.llm_service)
            report_markdown = report_formatter.format_report(plan_json, raw_output)

            report_generator = ReportGeneratorAgent()
            docx_bytes = report_generator.generate_text_document_docx(
                title=f"Backend Test Report - {self.project_name}",
                content=report_markdown
            )

            reports_dir = project_root / "docs" / "test_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"backend_test_report_{timestamp}.docx"

            with open(report_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())

            # Step 6: Handle the outcome based on test success/failure.
            if success:
                logging.info("Final backend regression test suite PASSED.")
                if progress_callback:
                    progress_callback(("SUCCESS", "All backend tests passed. Report saved."))
                self.sprint_completed_with_failures = False
                self.active_plan = None # Explicitly conclude the development plan

                # Set the next phase based on project type
                project_details = self.db_manager.get_project_by_id(self.project_id)
                self.set_phase("AWAITING_SPRINT_INTEGRATION_TEST_DECISION")
                return True # Return simple success
            else:
                logging.error("Final backend regression test suite FAILED. Report saved. Escalating to PM.")
                if progress_callback:
                    progress_callback(("ERROR", f"Regression test failed. Report saved.\n{raw_output}"))
                self.task_awaiting_approval = {
                    "failure_log": f"A regression failure was detected during Backend Testing.\n\n--- TEST OUTPUT ---\n{raw_output}",
                    "is_final_verification_failure": True
                }
                self.set_phase("DEBUG_PM_ESCALATION")
        except Exception as e:
            logging.error(f"An unexpected error occurred during final sprint verification: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred during Backend Testing:\n{e}", is_phase_failure_override=True)

    def _run_sprint_integration_test_generation(self, progress_callback=None, **kwargs):
        """
        Background task to generate the sprint-specific integration test and command.
        """
        self.task_awaiting_approval = {}
        logging.info("Starting sprint-specific integration test generation...")
        try:
            agent = SprintIntegrationTestAgent(self.llm_service, self.db_manager)
            sprint_id = self.active_sprint_id
            if not sprint_id:
                raise ValueError("Could not determine the active sprint ID for test generation.")

            if progress_callback: progress_callback(("INFO", "Generating integration test script and command..."))

            result = agent.generate_test(self.project_id, sprint_id)

            if result:
                script_path, command = result
                self.task_awaiting_approval['sprint_integ_script_path'] = script_path
                self.task_awaiting_approval['sprint_integ_command'] = command
                self.set_phase("AWAITING_SPRINT_INTEGRATION_TEST_APPROVAL")
            else:
                logging.warning("SprintIntegrationTestAgent failed to generate a test. Skipping this step.")
                self.set_phase("AWAITING_UI_TEST_DECISION") # Skip to next step on failure

        except Exception as e:
            logging.error(f"Failed during sprint integration test generation: {e}", exc_info=True)
            # Fallback to the next major phase on error
            self.set_phase("AWAITING_UI_TEST_DECISION")

    def handle_sprint_integration_test_decision(self, decision: str, command: str = None):
        """
        Handles the PM's decision from the sprint integration test checkpoint.
        """
        logging.info(f"PM made sprint integration test decision: {decision}")
        if decision == "SKIP":
            self.set_phase("AWAITING_UI_TEST_DECISION")
        elif decision == "PAUSE":
            self._pause_sprint_for_manual_fix()
        elif decision == "RUN":
            if not command:
                logging.error("Run decision received, but no command was provided.")
                self.set_phase("AWAITING_UI_TEST_DECISION") # Fail safely
                return
            self.task_awaiting_approval['sprint_integ_command_to_run'] = command
            self.set_phase("SPRINT_INTEGRATION_TEST_EXECUTION")
        else:
            logging.warning(f"Received unknown sprint integration test decision: {decision}")
            self.set_phase("AWAITING_UI_TEST_DECISION") # Default to a safe state

    def _task_run_sprint_integration_test(self, progress_callback=None, **kwargs):
        """
        Background worker task that executes the test and transitions to a results page.
        """
        if progress_callback: progress_callback(("INFO", "Preparing to execute sprint integration test..."))
        command = self.task_awaiting_approval.get("sprint_integ_command_to_run")
        project_root = self.db_manager.get_project_by_id(self.project_id)['project_root_folder']

        agent = VerificationAgent_AppTarget(self.llm_service)
        if progress_callback: progress_callback(("INFO", f"Executing command: {command}"))
        status, output = agent.run_all_tests(project_root, command)
        if progress_callback: progress_callback(("INFO", f"Execution finished with status: {status}"))

        # Generate and save the report regardless of outcome
        try:
            report_generator = ReportGeneratorAgent()
            report_markdown = f"# Sprint Integration Test Report\n\n**Command Executed:** `{command}`\n\n**Status:** {status}\n\n## Test Runner Output\n\n```\n{output}\n```"
            docx_bytes = report_generator.generate_text_document_docx(
                title=f"Sprint Integration Test Report - {self.project_name}",
                content=report_markdown
            )
            reports_dir = Path(project_root) / "docs" / "test_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"sprint_integration_test_report_{timestamp}.docx"
            with open(report_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            self._commit_document(report_path, f"docs: Add sprint integration test report for sprint {self.active_sprint_id}")
        except Exception as e:
            logging.error(f"Failed to generate and save sprint integration test report: {e}")

        # THIS IS THE FIX: Save results and transition to the new checkpoint
        self.task_awaiting_approval['sprint_test_status'] = status
        self.task_awaiting_approval['sprint_test_output'] = output
        self.set_phase("AWAITING_INTEGRATION_TEST_RESULT_ACK")

        return status # The worker still needs a return value

    def handle_sprint_test_result_ack(self):
        """
        Handles the user's acknowledgement of the sprint test results and proceeds.
        """
        status = self.task_awaiting_approval.get("sprint_test_status", "FAILURE")
        if status == 'SUCCESS':
            self.set_phase("AWAITING_UI_TEST_DECISION")
        else:
            output = self.task_awaiting_approval.get("sprint_test_output", "No output available.")
            self.escalate_for_manual_debug(output, is_phase_failure_override=True)

    def _run_automated_ui_test_phase(self, progress_callback=None):
        """
        Orchestrates the entire automated UI testing workflow, including the
        generation of a final, human-readable test report.
        """
        logging.info("Starting automated UI testing phase with reporting...")
        if progress_callback: progress_callback(("INFO", "Starting automated Front-end Testing phase..."))

        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details: raise Exception("Project details not found.")
            project_root = Path(project_details['project_root_folder'])

            # 1. Generate Scripts and Structured Plan
            if progress_callback: progress_callback(("INFO", "Generating UI test scripts and plan..."))
            sprint_items = db.get_items_for_sprint(self.active_sprint_id)
            sprint_items_json = json.dumps([dict(row) for row in sprint_items])
            ux_blueprint_json = project_details['ux_spec_text'] or '{}'

            script_agent = AutomatedUITestScriptAgent(self.llm_service)
            script_code, plan_json = script_agent.generate_scripts(sprint_items_json, ux_blueprint_json, project_details['project_root_folder'])

            if not script_code or not plan_json:
                if progress_callback: progress_callback(("ERROR", "AI failed to generate test scripts or a valid plan."))
                self.task_awaiting_approval = {"error": "The Automated UI Test Script Agent failed to generate a valid script or test plan."}
                self.set_phase("AWAITING_SCRIPT_FAILURE_RESOLUTION")
                return

            # 2. Execute Tests
            if progress_callback: progress_callback(("SUCCESS", "Scripts generated. Executing automated Front-end tests..."))
            ui_test_command = project_details['ui_test_execution_command']
            if not ui_test_command:
                raise Exception("Cannot run automated UI tests: The UI Test Execution Command is not configured for this project.")

            verification_agent = VerificationAgent_AppTarget(self.llm_service)
            status, raw_output = verification_agent.run_all_tests(project_details['project_root_folder'], ui_test_command)

            if status == 'ENVIRONMENT_FAILURE':
                if progress_callback: progress_callback(("ERROR", "Front-end test execution failed due to an environment error."))
                self.escalate_for_manual_debug(raw_output, is_env_failure=True, is_phase_failure_override=True)
                return

            # 3. Parse Raw Results
            if progress_callback: progress_callback(("INFO", "Parsing test results..."))
            parser_agent = AutomatedTestResultParserAgent(self.llm_service)
            parsed_result = parser_agent.parse_results(raw_output)

            # 4. Format the Final Report
            if progress_callback: progress_callback(("INFO", "Formatting final test report..."))
            report_formatter = TestReportFormattingAgent(self.llm_service)
            report_markdown = report_formatter.format_report(plan_json, raw_output)

            # 5. Generate and Save .docx Report
            if progress_callback: progress_callback(("INFO", "Saving test report to file..."))
            report_generator = ReportGeneratorAgent()
            # First, create the final report content with a proper header
            final_report_with_header = self.prepend_standard_header(report_markdown, "Automated Front-end Test Report")

            # Then, generate the .docx file from that final content
            docx_bytes = report_generator.generate_text_document_docx(
                title=f"Automated Front-end Test Report - {self.project_name}",
                content=final_report_with_header
            )

            reports_dir = project_root / "docs" / "test_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"automated_fe_test_report_{timestamp}.docx"

            with open(report_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            # self._commit_document(report_path, f"docs: Add automated front-end test report for sprint {self.active_sprint_id}")

            # 6. Conclude the Phase
            if parsed_result.get("success"):
                if progress_callback: progress_callback(("SUCCESS", "All automated Front-end tests passed. Report saved."))
                self.set_phase("SPRINT_REVIEW")
            else:
                if progress_callback: progress_callback(("ERROR", "One or more Front-end tests failed. Report saved."))
                self.escalate_for_manual_debug(parsed_result.get("summary", "No summary available."), is_functional_bug=True, is_phase_failure_override=True)

        except Exception as e:
            logging.error(f"Automated UI testing phase failed: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred during Front-end Testing:\n{e}", is_phase_failure_override=True)

    def run_on_demand_automated_ui_test(self, return_phase: str, progress_callback=None, worker_instance=None):
        """
        Orchestrates a self-contained, on-demand automated UI testing workflow.
        This is a dedicated method, separate from the sprint lifecycle.
        """
        logging.info("Starting ON-DEMAND automated UI testing phase...")
        if progress_callback: progress_callback(("INFO", "Starting on-demand automated Front-end Testing phase..."))

        try:
            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details: raise Exception("Project details not found.")
            project_root = Path(project_details['project_root_folder'])

            if progress_callback: progress_callback(("INFO", "Generating UI test scripts and plan..."))
            # For on-demand tests, we pass an empty list for sprint items as none are formally scoped.
            sprint_items = []
            sprint_items_json = json.dumps([dict(row) for row in sprint_items])
            ux_blueprint_json = project_details['ux_spec_text'] or '{}'

            from agents.agent_automated_ui_test_script import AutomatedUITestScriptAgent
            script_agent = AutomatedUITestScriptAgent(self.llm_service)
            script_code, plan_json = script_agent.generate_scripts(sprint_items_json, ux_blueprint_json, project_details['project_root_folder'])

            if not script_code or not plan_json:
                if progress_callback: progress_callback(("ERROR", "AI failed to generate test scripts or a valid plan."))
                self.task_awaiting_approval = {"error": "The Automated UI Test Script Agent failed to generate a valid script or test plan."}
                self.set_phase("AWAITING_SCRIPT_FAILURE_RESOLUTION")
                return

            if progress_callback: progress_callback(("SUCCESS", "Scripts generated. Executing automated Front-end tests..."))
            ui_test_command = project_details['ui_test_execution_command']
            if not ui_test_command:
                raise Exception("Cannot run automated UI tests: The UI Test Execution Command is not configured for this project.")

            from agents.agent_verification_app_target import VerificationAgent_AppTarget
            verification_agent = VerificationAgent_AppTarget(self.llm_service)
            status, raw_output = verification_agent.run_all_tests(project_details['project_root_folder'], ui_test_command)

            if status == 'ENVIRONMENT_FAILURE':
                if progress_callback: progress_callback(("ERROR", "Front-end test execution failed due to an environment error."))
                self.escalate_for_manual_debug(raw_output, is_env_failure=True, is_phase_failure_override=True)
                return

            if progress_callback: progress_callback(("INFO", "Parsing test results..."))
            from agents.agent_automated_test_result_parser import AutomatedTestResultParserAgent
            parser_agent = AutomatedTestResultParserAgent(self.llm_service)
            parsed_result = parser_agent.parse_results(raw_output)

            if progress_callback: progress_callback(("INFO", "Formatting final test report..."))
            from agents.agent_test_report_formatting import TestReportFormattingAgent
            report_formatter = TestReportFormattingAgent(self.llm_service)
            report_markdown = report_formatter.format_report(plan_json, raw_output)

            if progress_callback: progress_callback(("INFO", "Saving test report to file..."))
            from agents.agent_report_generator import ReportGeneratorAgent
            report_generator = ReportGeneratorAgent()
            final_report_with_header = self.prepend_standard_header(report_markdown, "On-Demand Automated Front-end Test Report")

            docx_bytes = report_generator.generate_text_document_docx(
                title=f"On-Demand Automated Front-end Test Report - {self.project_name}",
                content=final_report_with_header
            )

            reports_dir = project_root / "docs" / "test_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"on_demand_fe_test_report_{timestamp}.docx"

            with open(report_path, 'wb') as f:
                f.write(docx_bytes.getbuffer())
            self._commit_document(report_path, f"docs: Add on-demand automated front-end test report")

            if parsed_result.get("success"):
                if progress_callback: progress_callback(("SUCCESS", "All on-demand automated Front-end tests passed. Report saved."))
                self.set_phase(return_phase)
                logging.info(f"On-demand test complete. Returning to phase: {return_phase}")
            else:
                if progress_callback: progress_callback(("ERROR", "One or more on-demand Front-end tests failed. Report saved."))
                self.escalate_for_manual_debug(parsed_result.get("summary", "No summary available."), is_functional_bug=True, is_phase_failure_override=True)

        except Exception as e:
            logging.error(f"On-demand automated UI testing phase failed: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred during On-Demand Front-end Testing:\n{e}", is_phase_failure_override=True)

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

    def _task_run_sprint_validation_checks(self, **kwargs):
        """Background task to run all sprint pre-execution validation checks."""
        from agents.agent_sprint_pre_execution_check import SprintPreExecutionCheckAgent
        logging.info("Running sprint validation checks...")
        task_data = self.task_awaiting_approval or {}
        selected_items = task_data.get("selected_sprint_items", [])
        if not selected_items:
            raise ValueError("Cannot run validation check: No items selected.")

        final_report = {
            "scope_guardrail": {"status": "NOT_RUN", "details": ""},
            "stale_analysis": {"status": "NOT_RUN", "details": ""},
            "technical_risk": {"status": "NOT_RUN", "details": ""}
        }

        # 1. Scope Guardrail Check
        limit = int(self.db_manager.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "2500000") * 0.40
        total_chars = sum(len(item.get('description', '')) + len(item.get('title', '')) for item in selected_items)
        if total_chars > limit:
            large_items = [f"- {item.get('hierarchical_id')}: {item.get('title')}" for item in selected_items if item.get('complexity') == 'Large']
            details = f"The combined text of the selected items ({total_chars:,} characters) exceeds the recommended limit of {int(limit):,} for reliable plan generation. "
            if large_items:
                details += "Consider removing one or more 'Large' complexity items to reduce the scope:\n" + "\n".join(large_items)
            else:
                details += "Consider reducing the number of items in the sprint."
            final_report["scope_guardrail"] = {"status": "FAIL", "details": details}
            self.task_awaiting_approval["sprint_validation_report"] = final_report
            self.set_phase("AWAITING_SPRINT_VALIDATION_APPROVAL")
            return
        else:
            final_report["scope_guardrail"] = {"status": "PASS", "details": "Sprint scope size is within acceptable limits."}

        # 2. Stale Analysis Check
        project_details = self.db_manager.get_project_by_id(self.project_id)
        if project_details and project_details['version_control_enabled'] == 1:
            stale_items_found = []
            latest_commit_time = self.get_latest_commit_timestamp()
            if latest_commit_time:
                for item in selected_items:
                    if item['status'] == 'IMPACT_ANALYZED' and item['last_modified_timestamp']:
                        analysis_time = datetime.fromisoformat(item['last_modified_timestamp'])
                        if latest_commit_time > analysis_time:
                            stale_items_found.append(f"- {item.get('hierarchical_id')}: {item.get('title')}")
            if stale_items_found:
                details = "The following items have a stale impact analysis because the codebase has been modified since they were last analyzed:\n" + "\n".join(stale_items_found)
                stale_ids = [item['cr_id'] for item in selected_items if f"- {item.get('hierarchical_id')}" in details]
                final_report["stale_analysis"] = {"status": "FAIL", "details": details, "stale_item_ids": stale_ids}
                self.task_awaiting_approval["sprint_validation_report"] = final_report
                self.set_phase("AWAITING_SPRINT_VALIDATION_APPROVAL")
                return
            else:
                final_report["stale_analysis"] = {"status": "PASS", "details": "All analyzed items are up-to-date with the latest codebase."}
        else:
             final_report["stale_analysis"] = {"status": "NOT_RUN", "details": "Version control is not enabled for this project; check was skipped."}

        # 3. Technical Risk Check
        full_backlog = self._get_backlog_with_hierarchical_numbers()
        rowd = self.db_manager.get_all_artifacts_for_project(self.project_id)
        agent = SprintPreExecutionCheckAgent(self.llm_service)
        report_json = agent.run_check(
            selected_items_json=json.dumps(selected_items, indent=2),
            rowd_json=json.dumps([dict(r) for r in rowd], indent=2),
            full_backlog_json=json.dumps(full_backlog, indent=2)
        )
        report_data = json.loads(report_json).get("pre_execution_report", {})
        missing_deps = report_data.get("missing_dependencies", [])
        tech_conflicts = report_data.get("technical_conflicts", [])
        if missing_deps or tech_conflicts:
            details = ""
            if missing_deps:
                details += "Missing Dependencies Found:\n" + "\n".join([f"- {dep}" for dep in missing_deps]) + "\n\n"
            if tech_conflicts:
                details += "Potential Technical Conflicts Found:\n" + "\n".join([f"- {con}" for con in tech_conflicts])
            final_report["technical_risk"] = {"status": "FAIL", "details": details.strip()}
        else:
            final_report["technical_risk"] = {"status": "PASS", "details": "No technical conflicts or missing dependencies were found."}

        self.task_awaiting_approval["sprint_validation_report"] = final_report
        self.set_phase("AWAITING_SPRINT_VALIDATION_APPROVAL")

    def handle_sprint_validation_decision(self, decision: str):
        """Handles the PM's decision after reviewing the sprint validation report."""
        if decision == "PROCEED":
            logging.info("PM approved sprint validation report. Proceeding to Sprint Planning.")
            self.set_phase("SPRINT_PLANNING")
        elif decision == "CANCEL":
            logging.info("PM cancelled sprint after validation. Returning to Backlog.")
            self.task_awaiting_approval = None # Clear the pending task
            self.set_phase("BACKLOG_VIEW")

    def rerun_stale_sprint_analysis(self, stale_item_ids: list, progress_callback=None, **kwargs):
        """
        Runs full analysis on a list of stale items and then re-initiates
        the sprint planning process. Designed for a background worker.
        """
        try:
            if not stale_item_ids:
                raise ValueError("Stale items list cannot be empty for re-run.")

            # Get the original full list of selected item IDs from the cached task data
            task_data = self.task_awaiting_approval or {}
            original_sprint_items = task_data.get("selected_sprint_items", [])
            original_cr_ids = [item['cr_id'] for item in original_sprint_items]

            if not original_cr_ids:
                raise ValueError("Could not find original list of sprint items to resume planning.")

            for i, cr_id in enumerate(stale_item_ids):
                if progress_callback:
                    progress_callback(("INFO", f"({i+1}/{len(stale_item_ids)}) Re-running analysis for CR-{cr_id}..."))
                self.run_full_analysis(cr_id)

            if progress_callback:
                progress_callback(("SUCCESS", "All stale analyses complete. Resuming sprint planning..."))

            # Re-trigger the planning process now that analyses are fresh
            self.initiate_sprint_planning(original_cr_ids)
        except Exception as e:
            logging.error(f"Failed during batch re-analysis of stale items: {e}", exc_info=True)
            self.task_awaiting_approval = {"error": str(e)}
            self.set_phase("BACKLOG_VIEW")
            raise # Re-raise to be caught by the worker's error handler

    def initiate_sprint_planning(self, selected_items_or_ids: list, **kwargs):
        """
        Prepares the context for the sprint workflow. It can accept a list of
        cr_ids (standard workflow) or a list of item dictionaries (for Quick Fix).
        """
        logging.info(f"Initiating sprint planning for {len(selected_items_or_ids)} items.")
        try:
            selected_items = []
            if selected_items_or_ids and isinstance(selected_items_or_ids[0], dict):
                # Path for Quick Fix: a list of item dictionaries is passed directly.
                selected_items = selected_items_or_ids
            else:
                # Existing path: a list of cr_ids is passed, requiring lookup.
                full_backlog_with_ids = self._get_backlog_with_hierarchical_numbers()
                flat_backlog = {item['cr_id']: item for item in self._flatten_hierarchy(full_backlog_with_ids)}
                selected_items = [flat_backlog[cr_id] for cr_id in selected_items_or_ids if cr_id in flat_backlog]

            self.task_awaiting_approval = {
                "selected_sprint_items": selected_items
            }
            # This correctly transitions to the asynchronous validation phase.
            self.set_phase("AWAITING_SPRINT_VALIDATION_CHECK")
        except Exception as e:
            logging.error(f"Failed during sprint initiation: {e}", exc_info=True)
            self.set_phase("BACKLOG_VIEW") # Go back on error
            self.task_awaiting_approval = {"error": str(e)}

    def handle_start_sprint(self, sprint_items: list, **kwargs):
        """
        Finalizes sprint planning by creating a persistent sprint record,
        linking items to it, updating statuses, and transitioning to SPRINT_IN_PROGRESS.
        """
        # Check for an existing active sprint before creating a new one
        latest_sprint = self.db_manager.get_latest_sprint_for_project(self.project_id)
        if latest_sprint and latest_sprint['status'] in ['IN_PROGRESS', 'PAUSED']:
            logging.info(f"Resuming existing active sprint: {latest_sprint['sprint_id']}")
            self.active_sprint_id = latest_sprint['sprint_id']
            self.load_development_plan(latest_sprint['sprint_plan_json'])
            self.set_phase("SPRINT_IN_PROGRESS")
            return # Exit early to avoid creating a new sprint

        logging.info(f"Starting sprint with {len(sprint_items)} items.")
        sprint_id = None
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
            sprint_goal_text = ", ".join(f"'{item['title']}'" for item in sprint_items if item.get('title'))
            self.db_manager.create_sprint(self.project_id, sprint_id, plan_json_str, sprint_goal_text)
            self.db_manager.link_items_to_sprint(sprint_id, cr_ids_to_update)
            self.db_manager.batch_update_cr_status(cr_ids_to_update, "IMPLEMENTATION_IN_PROGRESS")

            self.set_phase("SPRINT_IN_PROGRESS")
            logging.info(f"Sprint '{sprint_id}' started. Transitioning to SPRINT_IN_PROGRESS.")
        except Exception as e:
            logging.error(f"Failed to start sprint '{sprint_id}': {e}", exc_info=True)
            if sprint_id:
                logging.warning(f"Rolling back failed sprint creation for sprint {sprint_id}.")
                self.db_manager.delete_sprint_links(sprint_id)
                self.db_manager.delete_sprint(sprint_id)
            self.active_sprint_id = None
            self.set_phase("SPRINT_PLANNING")
            self.task_awaiting_approval = {"selected_sprint_items": sprint_items, "error": str(e)}

    def handle_sprint_review_complete(self, **kwargs) -> bool:
        """
        Handles the user's action to complete the sprint review. This method
        updates the status of the sprint and its items, and now returns a
        boolean indicating if a document update is required.
        """
        logging.info("Sprint review acknowledged. Finalizing sprint item statuses.")
        needs_doc_update = False  # Assume no update needed
        try:
            sprint_id = self.get_active_sprint_id()
            if not sprint_id:
                return False

            items_in_sprint = self.db_manager.get_items_for_sprint(sprint_id)
            if items_in_sprint:
                completed_ids = []
                for item in items_in_sprint:
                    item_data = dict(item) # Convert from sqlite3.Row
                    if item_data['status'] == 'IMPLEMENTATION_IN_PROGRESS':
                        completed_ids.append(item_data['cr_id'])

                    # --- BEGIN FIX ---
                    # Check if any completed item is a change request
                    if item_data['request_type'] == 'CHANGE_REQUEST_ITEM':
                        needs_doc_update = True
                    # --- END FIX ---

                if completed_ids:
                    self.db_manager.batch_update_cr_status(completed_ids, "COMPLETED")

            self.db_manager.update_sprint_status(sprint_id, "COMPLETED")
            return needs_doc_update # Return the flag
        except Exception as e:
            logging.error(f"Failed to update sprint statuses during finalization: {e}")
            raise # Re-raise to notify the UI

    def initiate_on_demand_manual_testing(self, **kwargs) -> bool:
        """
        Initiates the on-demand manual UI testing workflow, first checking
        if a sprint is active or if any code exists to be tested.

        Returns:
            bool: True if the workflow was started, False if not.
        """
        if not self.project_id:
            logging.warning("Cannot initiate manual testing; no active project.")
            return False

        # Guardrail: Do not allow if a sprint is already in progress.
        if self.is_sprint_active():
            logging.warning("Attempted to start on-demand testing while a sprint is active. Action blocked.")
            return False

        # Guardrail: Check if any code artifacts exist in the RoWD.
        all_artifacts = self.db_manager.get_all_artifacts_for_project(self.project_id)
        if not all_artifacts:
            logging.warning("Cannot initiate UI testing; no code has been generated for this project yet.")
            return False

        logging.info("PM initiated on-demand manual UI testing workflow.")
        main_window = self.get_main_window_instance()
        if main_window:
            main_window.previous_phase = self.current_phase

        # Set a persistent flag in the resumable state
        self.task_awaiting_approval = {"is_on_demand_test_cycle": True}
        self._save_current_state()

        self.set_phase("GENERATING_MANUAL_TEST_PLAN")
        return True

    def get_main_window_instance(self):
        """Helper to find the ASDFMainWindow instance."""
        from PySide6.QtWidgets import QApplication
        for widget in QApplication.topLevelWidgets():
            if 'ASDFMainWindow' in str(type(widget)):
                return widget
        return None

    def run_doc_update_and_finalize_sprint(self, progress_callback=None, skip_doc_update=False, **kwargs):
        """
        A single method for a background worker that conditionally runs the doc update,
        then finalizes the sprint state.
        """
        try:
            if not skip_doc_update:
                # First, run the document update process.
                self._run_post_implementation_doc_update(progress_callback)
            else:
                logging.info("Skipping doc update as requested.")
        except Exception as e:
            logging.error(f"An error occurred during the doc update portion of finalization: {e}")
        finally:
            # After the update is attempted (even if it fails), finalize the state.
            logging.info("Finalizing sprint state and returning to backlog...")
            self.active_plan = None
            self.active_plan_cursor = 0
            self.post_fix_reverification_path = None
            self.is_executing_cr_plan = False
            self.active_sprint_id = None
            self.task_awaiting_approval = {}
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

    def handle_coding_standard_complete(self):
        """
        Called when the coding standard page signals completion.
        Transitions to the backlog gateway.
        """
        logging.info("All coding standards finalized. Proceeding to Backlog Gateway.")
        self.set_phase("AWAITING_BACKLOG_GATEWAY_DECISION")

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
        This version now conditionally includes UX and DB specs for enhanced context.
        """
        logging.info(f"Generating implementation plan for {len(sprint_items)} sprint items.")
        try:
            db = self.db_manager
            project_details_row = db.get_project_by_id(self.project_id)
            if not project_details_row:
                raise Exception("Could not retrieve project details.")

            # Convert sqlite3.Row to a dict to safely use .get()
            project_details = dict(project_details_row)

            project_root_path = Path(project_details.get('project_root_folder'))

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
                        final_spec_text=project_details.get('final_spec_text'),
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
                        source_code_files[artifact_record['file_path']] = source_path.read_text(encoding='utf-8', errors='ignore')

            # Gather all available specs using the safe .get() method on the dictionary
            core_docs = {"final_spec_text": project_details.get('final_spec_text')}
            ux_spec = project_details.get('ux_spec_text')
            db_spec = project_details.get('db_schema_spec_text')

            self.context_package_summary = self._build_and_validate_context_package(core_docs, source_code_files)
            if self.context_package_summary.get("error"):
                raise Exception(f"Context Builder Error: {self.context_package_summary['error']}")

            all_artifacts = db.get_all_artifacts_for_project(self.project_id)
            rowd_json = json.dumps([dict(row) for row in all_artifacts])

            planner_agent = RefactoringPlannerAgent_AppTarget(llm_service=self.llm_service)
            detected_technologies_json = project_details.get('detected_technologies', '[]')
            new_plan_str = planner_agent.create_refactoring_plan(
                change_request_desc=combined_description,
                final_spec_text=project_details.get('final_spec_text'),
                tech_spec_text=project_details.get('tech_spec_text'),
                rowd_json=rowd_json,
                source_code_context=self.context_package_summary["source_code"],
                ux_spec_text=ux_spec,
                db_schema_spec_text=db_spec,
                detected_technologies_json=detected_technologies_json
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

        # Generate a standard UTC timestamp string and format it using the new utility
        timestamp_str = datetime.now(timezone.utc).isoformat()
        formatted_date = format_timestamp_for_display(timestamp_str)

        header = (
            f"PROJECT NUMBER: {self.project_id}\n"
            f"{document_type.upper()}\n"
            f"Date: {formatted_date}\n"
            f"Version number: {version_number}\n"
            f"{'-' * 50}\n\n"
        )
        return header + document_content

    def _extract_specifications_from_consolidated_text(self, brief_text: str) -> dict:
        """
        Uses an LLM to parse a consolidated text block and extract distinct
        specification documents into a structured dictionary.
        """
        logging.info("Orchestrator: Extracting distinct specifications from consolidated text...")

        prompt = textwrap.dedent(f"""
            You are an expert document parser. Your task is to analyze the provided text, which may contain multiple software specification documents, and extract each one verbatim into a JSON object.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            2.  **Verbatim Extraction:** You MUST perform a verbatim, exact copy of the text for each section. Do NOT summarize, alter, omit, or rephrase any content.
            3.  **Find Sections:** Identify the start of each distinct document (e.g., "Application Specification", "Technical Specification", "Coding Standard"). Copy all text from that heading until the start of the next major specification heading or the end of the input.
            4.  **JSON Schema:** The JSON object MUST have the following keys. If a corresponding section is not found in the input text, the value for that key MUST be an empty string "".
                - "application_spec"
                - "technical_spec"
                - "coding_standard"
            5.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON object itself.

            **--- CONSOLIDATED DOCUMENT TEXT ---**
            {brief_text}
            **--- END OF TEXT ---**

            **JSON OUTPUT:**
        """)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            specs = json.loads(cleaned_response)
            if all(k in specs for k in ["application_spec", "technical_spec", "coding_standard"]):
                return specs
            else:
                raise ValueError("LLM response was missing one or more required specification keys.")
        except Exception as e:
            logging.error(f"Failed to extract specifications from consolidated text: {e}")
            # Return a dict with an error to be handled by the calling function
            return {"error": str(e)}

    def _get_blueprint_from_ux_spec(self, ux_spec_text: str) -> dict | None:
        """Extracts the JSON blueprint from the composite UX spec field."""
        if not ux_spec_text:
            return None
        # Use regex to find the json block, accommodating potential whitespace
        match = re.search(r"```json\s*(\{.*?\})\s*```", ux_spec_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logging.error("Failed to parse JSON blueprint from ux_spec_text in DB.")
                return None
        return None

    def _calculate_asdf_effort_metrics(self, spec_text: str) -> dict:
        """
        Performs a non-LLM, heuristic analysis on a spec text to generate
        objective metrics that anchor the ProjectScopingAgent's analysis.
        """
        logging.info("Calculating ASDF Effort metrics for spec text...")
        metrics = {
            "context_pressure_score": len(spec_text),
            "component_density_score": 0,
            "ui_score": 0,
            "backend_score": 0
        }

        # Use more specific phrases to avoid ambiguity
        component_keywords = [
            # UI Components
            "screen", "view", "page", "window", "form", "dialog", "dashboard",
            "input field", "text field", "button", "dropdown",
            # API Components
            "api endpoint", "rest endpoint", "graphql query", "microservice",
            # Data Components
            "database table", "data model", "schema", "data pipeline", "etl job",
            # Logical Components
            "service", "module", "component", "class", "function", "worker",
            "algorithm", "engine",
            # AI/ML Components
            "ml model", "prediction service", "training pipeline",
            # Security Components
            "authentication service", "authorization rule"
        ]
        ui_keywords = [
            # Core & Paradigms
            "gui", "ui", "user interface", "front-end", "view",
            # Desktop & Web
            "window", "form", "dialog", "desktop", "wpf", "pyside6", "qt", "web page",
            "website", "react", "angular", "vue", "html", "css",
            # Mobile
            "mobile app", "android", "ios", "swift", "kotlin", "screen", "activity",
            # Components
            "button", "grid", "table", "chart", "graph", "menu", "dashboard", "report",
            "field", "input box", "text field", "input field", "dropdown", "combo box",
            # Digital & AI
            "chatbot", "voice interface", "virtual assistant", "visualization",
            "digital twin", "ar", "vr", "augmented reality", "virtual reality"
        ]
        backend_keywords = [
            # Core Backend
            "backend", "server", "api", "database", "algorithm",
            # Data & AI
            "sql", "database", "data pipeline", "etl", "query", "schema",
            "machine learning", "ml model", "data science", "analytics", "prediction",
            # Web Services
            "rest", "graphql", "microservice", "endpoint", "lambda", "function", "serverless",
            # Architecture & Security
            "architecture", "authentication", "authorization", "cache", "message queue",
            "encryption", "security", "firewall", "iam",
            # Cloud Computing
            "cloud", "aws", "azure", "gcp", "docker", "kubernetes", "container",
            "vm", "virtual machine"
        ]

        lower_spec = spec_text.lower()
        for keyword in component_keywords:
            metrics["component_density_score"] += lower_spec.count(keyword)
        for keyword in ui_keywords:
            metrics["ui_score"] += lower_spec.count(keyword)
        for keyword in backend_keywords:
            metrics["backend_score"] += lower_spec.count(keyword)

        logging.info(f"ASDF Effort Metrics calculated: {metrics}")
        return metrics

    def _consolidate_specification_inputs(self) -> str:
        """
        It intelligently merges the project brief, the UX/UI spec,
        and any external changes to the UI blueprint.
        """
        if not self.project_id:
            raise Exception("Cannot consolidate inputs; no active project.")

        logging.info("Consolidating specification inputs...")
        db = self.db_manager
        project_details = db.get_project_by_id(self.project_id)
        project_root = Path(project_details['project_root_folder'])

        # 1. Get all three input sources
        # Lowest priority: Project Brief
        brief_path_str = project_details['project_brief_path'] or ""
        brief_path = project_root / brief_path_str if brief_path_str else None
        project_brief_text = ""
        if brief_path and brief_path.exists():
            project_brief_text = brief_path.read_text(encoding='utf-8')

        # Medium priority: UX/UI Spec from DB
        ux_spec_text_from_db = project_details['ux_spec_text'] or ""
        db_blueprint_json = self._get_blueprint_from_ux_spec(ux_spec_text_from_db)

        # Highest priority: External ux_ui_blueprint.json file
        external_blueprint_path = project_root / "docs" / "ux_ui_blueprint.json"
        external_blueprint_json = None
        if external_blueprint_path.exists():
            try:
                external_blueprint_json = json.loads(external_blueprint_path.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Could not read or parse external blueprint file: {e}")

        # If there's no UX spec at all, just return the brief
        if not ux_spec_text_from_db and not external_blueprint_json:
             logging.info("No UX/UI specification found. Using project brief as is.")
             return project_brief_text

        # 2. Compare and update if necessary
        final_blueprint_for_consolidation = db_blueprint_json or {}
        if external_blueprint_json and external_blueprint_json != db_blueprint_json:
            logging.info("External ux_ui_blueprint.json differs from database version. Updating...")
            ux_spec_markdown_part = self._strip_header_from_document(ux_spec_text_from_db).split("MACHINE-READABLE JSON BLUEPRINT")[0]

            composite_spec_for_db = (
                f"{ux_spec_markdown_part.strip()}\n\n"
                f"{'='*80}\n"
                f"MACHINE-READABLE JSON BLUEPRINT\n"
                f"{'='*80}\n\n"
                f"```json\n{json.dumps(external_blueprint_json, indent=2)}\n```"
            )
            db.update_project_field(self.project_id, "ux_spec_text", composite_spec_for_db)
            final_blueprint_for_consolidation = external_blueprint_json
            # ux_spec_text_from_db = composite_spec_for_db

        # 3. Call the agent to perform the intelligent merge
        from agents.agent_spec_clarification import SpecClarificationAgent
        agent = SpecClarificationAgent(self.llm_service, db)
        consolidated_requirements = agent.consolidate_requirements(
            project_brief=project_brief_text,
            ux_spec_markdown=ux_spec_text_from_db,
            ui_blueprint_json=json.dumps(final_blueprint_for_consolidation, indent=2)
        )

        return consolidated_requirements

    def _strip_header_from_document(self, document_content: str) -> str:
        """
        A helper method to reliably remove the ASDF-standard plain text header
        from a document, returning only the raw content. This version uses a
        regular expression to be more resilient to whitespace or encoding issues.
        """
        if not document_content:
            return ""

        # Regex to find the header block:
        # - Starts with "PROJECT NUMBER:"
        # - Ends with a line of 50+ hyphens, followed by newlines
        # - re.DOTALL allows '.' to match newlines
        # - re.IGNORECASE makes the search case-insensitive
        header_pattern = re.compile(
            r"^\s*PROJECT NUMBER:.*?-{50,}\s*\n",
            re.DOTALL | re.IGNORECASE
        )

        # Replace the first match of the header pattern with an empty string
        stripped_content = re.sub(header_pattern, '', document_content, count=1)

        # If the content length is the same, the pattern didn't match.
        if len(stripped_content) == len(document_content):
            logging.warning("_strip_header_from_document: Header pattern not found. Returning original content.")
            return document_content
        else:
            return stripped_content.lstrip() # Remove any leading whitespace

    def _commit_document(self, file_path: Path, commit_message: str):
        """A helper method to stage and commit a single document, but only if version control is enabled."""
        if not self.project_id:
            return
        try:
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if not project_details or not project_details['project_root_folder']:
                logging.error(f"Cannot commit {file_path.name}: project root folder not found.")
                return

            # Check if version control is enabled before attempting any git operations.
            version_control_enabled = project_details['version_control_enabled'] == 1 if project_details else True
            if not version_control_enabled:
                logging.info(f"Skipping commit for {file_path.name}; version control is disabled for this project.")
                return

            project_root = Path(project_details['project_root_folder'])
            repo = git.Repo(project_root)

            relative_path = file_path.relative_to(project_root)
            repo.index.add([str(relative_path)])
            repo.index.commit(commit_message)
            logging.info(f"Successfully committed document: {relative_path}")
        except Exception as e:
            logging.error(f"Failed to commit document {file_path.name}. Error: {e}")

    def get_project_reports_dir(self) -> Path:
        """
        Gets the path to the project's 'docs/project_reports' directory, creating it if necessary.
        (Copied from previous implementation for clarity, ensure it exists or add it)
        """
        if not self.project_id:
            raise Exception("Cannot get reports directory; no active project.")

        project_details = self.db_manager.get_project_by_id(self.project_id)
        if not project_details or not project_details['project_root_folder']:
            raise Exception("Cannot get reports directory; project root folder not found.")

        project_root = Path(project_details['project_root_folder'])
        # Corrected path to use 'project_reports' sub-directory
        reports_dir = project_root / "docs" / "project_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        return reports_dir

    def save_report_file(self, report_data: BytesIO, report_name: str, file_extension: str) -> str | None:
        """
        Saves generated report data (from BytesIO) to a uniquely named file
        in the project's report directory.

        Args:
            report_data (BytesIO): The in-memory report data.
            report_name (str): The base name for the report (e.g., "Project Pulse").
            file_extension (str): The file extension (e.g., ".docx", ".xlsx").

        Returns:
            The absolute path to the saved file as a string, or None on failure.
        """
        if not self.project_id or not self.project_name:
            logging.error("Cannot save report file: No active project.")
            return None
        if not isinstance(report_data, BytesIO):
            logging.error(f"Cannot save report file: Invalid data type received ({type(report_data)}). Expected BytesIO.")
            return None

        try:
            reports_dir = self.get_project_reports_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize report name for filename
            safe_report_name = report_name.replace(" ", "_").replace("&", "and").replace("/", "-")
            filename = f"{self.project_name}_{safe_report_name}_{timestamp}{file_extension}"
            save_path = reports_dir / filename

            with open(save_path, 'wb') as f:
                f.write(report_data.getbuffer())

            logging.info(f"Report '{report_name}' saved successfully to: {save_path}")
            return str(save_path) # Return the absolute path as a string

        except Exception as e:
            logging.error(f"Failed to save report file '{report_name}': {e}", exc_info=True)
            return None

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

            log_file_path = self._save_debug_log_and_get_path(failure_log, original_failing_task)
            log_path_for_desc = log_file_path if log_file_path else "Not available."

            parent_cr_ids = original_failing_task.get('task', {}).get('parent_cr_ids', [])
            if not parent_cr_ids:
                logging.error("Traceability Error: Cannot log bug as parent CR IDs were not found. Aborting sprint.")
                self.escalate_for_manual_debug("Traceability link missing in failed task.")
                return

            self.db_manager.batch_update_cr_status(parent_cr_ids, "BLOCKED")

            full_backlog_with_ids = self._get_backlog_with_hierarchical_numbers()
            flat_backlog_map = {item['cr_id']: item for item in self._flatten_hierarchy(full_backlog_with_ids)}
            parent_hierarchical_ids = [flat_backlog_map.get(pid, {}).get('hierarchical_id', f'CR-{pid}') for pid in parent_cr_ids]
            parent_ids_str = ', '.join(parent_hierarchical_ids)

            task_name = original_failing_task.get('task', {}).get('component_name', 'Unknown Task')
            description = (
                f"**Objective for Impact Analysis:** This is an auto-generated bug report for a failed sprint task. "
                f"This bug is blocking the completion of parent item(s): {parent_ids_str}.\n\n"
                f"--- ORIGINAL TASK ---\n```json\n{json.dumps(original_failing_task.get('task', {}), indent=2)}\n```\n\n"
                f"--- FAILURE LOG ---\n```\n{failure_log}\n```\n\n"
                f"**Full Debug Log Path:** `{log_path_for_desc}`"
            )
            bug_data = {
                "request_type": "BUG_REPORT", "title": f"Fix failed sprint task: {task_name}",
                "description": description, "severity": "High", "parent_id": parent_cr_ids[0]
            }
            success, new_bug_id = self.add_new_backlog_item(bug_data)
            if not success:
                raise Exception(f"Failed to create new BUG_REPORT item for task: {task_name}")

            if success:
                full_backlog_with_ids = self._get_backlog_with_hierarchical_numbers()
                flat_backlog_map = {item['cr_id']: item for item in self._flatten_hierarchy(full_backlog_with_ids)}
                new_bug_details = flat_backlog_map.get(new_bug_id)
                if new_bug_details:
                    new_bug_hierarchical_id = new_bug_details.get('hierarchical_id', f'CR-{new_bug_id}')
                    for parent_id in parent_cr_ids:
                        parent_details = self.db_manager.get_cr_by_id(parent_id)
                        if parent_details:
                            current_description = parent_details['description']
                            traceability_note = f"\n\n---\n**Blocked by:** Auto-generated Bug Report `{new_bug_hierarchical_id}`"
                            new_description = current_description + traceability_note
                            self.db_manager.update_cr_field(parent_id, 'description', new_description)
                            logging.info(f"Updated parent CR-{parent_id} with link to bug {new_bug_hierarchical_id}.")

            self.active_plan_cursor += 1
            self.task_awaiting_approval = None
            self.set_phase("GENESIS")
            logging.info(f"Successfully logged failure for '{task_name}' as BUG-{new_bug_id}. Sprint will continue.")
        except Exception as e:
            logging.error(f"Critical error in _log_failure_as_bug_report_and_proceed: {e}", exc_info=True)
            self.escalate_for_manual_debug(f"A system error occurred while logging a bug: {e}")

    def _flatten_hierarchy(self, items: list) -> list:
        """Helper to flatten the nested backlog into a simple list."""
        flat_list = []
        for item in items:
            flat_list.append(item)
            if "features" in item:
                flat_list.extend(self._flatten_hierarchy(item["features"]))
            if "user_stories" in item:
                flat_list.extend(self._flatten_hierarchy(item["user_stories"]))
        return flat_list

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
                "active_spec_draft": self.active_spec_draft,
                "active_sprint_id": self.active_sprint_id
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

    def _clear_active_project_data(self, db: ASDFDBManager, project_id: str):
        """Helper method to clear all data for a specific project."""
        if not project_id:
            return

        # Explicitly find and delete sprint data first
        try:
            sprints_to_delete = db._execute_query("SELECT sprint_id FROM Sprints WHERE project_id = ?", (project_id,), fetch="all")
            if sprints_to_delete:
                sprint_ids = [row['sprint_id'] for row in sprints_to_delete]
                placeholders = ', '.join('?' for _ in sprint_ids)

                # Delete links from SprintItems first
                db._execute_query(f"DELETE FROM SprintItems WHERE sprint_id IN ({placeholders})", tuple(sprint_ids))

                # Then delete from Sprints
                db._execute_query(f"DELETE FROM Sprints WHERE sprint_id IN ({placeholders})", tuple(sprint_ids))
                logging.info(f"Deleted {len(sprint_ids)} sprint(s) and their linked items for project {project_id}.")
        except Exception as e:
            logging.error(f"An error occurred while trying to delete sprint data for project {project_id}: {e}")

        # Delete other project data
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
        This version uses the most robust GitPython introspection methods.
        """
        print("\n--- DEBUG: ENTERING _perform_preflight_checks (FINAL VERSION) ---")
        import os
        import subprocess
        import git
        project_root = Path(project_root_str)
        has_active_plan = self.active_plan is not None

        # 1. Path Validation
        if not project_root.exists() or not project_root.is_dir():
            return {"status": "PATH_NOT_FOUND", "message": f"The project folder could not be found or is not a directory. Please confirm the new location: {project_root_str}", "has_active_plan": has_active_plan}

        project_details = self.db_manager.get_project_by_id(project_id)
        version_control_enabled = project_details['version_control_enabled'] == 1 if project_details else False

        print(f"--- DEBUG: Calculated boolean for version_control_enabled: {version_control_enabled}")

        # 2. VCS Validation (Only if enabled for this project)
        if version_control_enabled:
            print("--- DEBUG: version_control_enabled is True. Proceeding with GitPython checks.")
            if not (project_root / '.git').is_dir():
                return {"status": "GIT_MISSING", "message": "The project folder was found, but the .git directory is missing.", "has_active_plan": has_active_plan}

            try:
                repo = git.Repo(project_root)

                # Direct and robust checks using GitPython's properties
                is_dirty_tracked = repo.is_dirty()
                has_untracked_files = bool(repo.untracked_files)

                print(f"--- DEBUG: repo.is_dirty() check returned: {is_dirty_tracked}")
                print(f"--- DEBUG: repo.untracked_files check returned: {repo.untracked_files}")

                if is_dirty_tracked or has_untracked_files:
                    print("--- DEBUG: State drift detected.")
                    print("--- DEBUG: EXITING _perform_preflight_checks ---")
                    return {"status": "STATE_DRIFT", "message": "Uncommitted local changes have been detected. To prevent conflicts, please resolve the state of the repository.", "has_active_plan": has_active_plan}

            except git.InvalidGitRepositoryError as e:
                return {"status": "GIT_MISSING", "message": f"The project folder is not a valid Git repository. Error: {e}", "has_active_plan": has_active_plan}
            except Exception as e:
                 return {"status": "GIT_MISSING", "message": f"An unexpected error occurred with GitPython. Error: {e}", "has_active_plan": has_active_plan}
        else:
            print("--- DEBUG: version_control_enabled is False. Skipping Git checks.")

        # All checks passed
        print("--- DEBUG: All checks passed.")
        print("--- DEBUG: EXITING _perform_preflight_checks ---")
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
        Gathers context using a "Hybrid Context Assembly" strategy with
        "Just-in-Time (JIT) Hash Validation" to ensure context is never stale.
        """
        final_context = {}
        summarized_files = []
        context_was_trimmed = False

        limit_str = self.db_manager.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "2500000"
        char_limit = int(limit_str)

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

        for file_path, content in source_code_files.items():
            content_len = len(content)

            if content_len <= remaining_chars:
                final_context[file_path] = content
                remaining_chars -= content_len
            else:
                context_was_trimmed = True
                summary_to_use = None

                # JIT Hash Validation Logic
                current_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                artifact = self.db_manager.get_artifact_by_path(self.project_id, file_path)

                is_stale = True # Assume stale by default
                if artifact and artifact['file_hash'] == current_hash and artifact['code_summary']:
                    is_stale = False
                    summary_to_use = artifact['code_summary']
                    logging.info(f"Context Builder: Using valid summary for {file_path}.")

                if is_stale:
                    logging.warning(f"Context Builder: Stale or missing summary for {file_path}. Generating on-demand.")
                    try:
                        summarization_agent = CodeSummarizationAgent(llm_service=self.llm_service)
                        new_summary = summarization_agent.summarize_code(content)
                        summary_to_use = new_summary

                        # Save the new summary and hash back to the RoWD for future use
                        if artifact:
                            doc_agent = DocUpdateAgentRoWD(self.db_manager, self.llm_service)
                            updated_data = dict(artifact)
                            updated_data['code_summary'] = new_summary
                            updated_data['file_hash'] = current_hash
                            doc_agent.update_artifact_record(updated_data)
                        else:
                             logging.warning(f"Could not find artifact for {file_path} to save new summary.")
                    except Exception as e:
                        logging.error(f"On-demand summarization failed for {file_path}: {e}")

                if summary_to_use and len(summary_to_use) <= remaining_chars:
                    final_context[file_path] = f"--- CODE SUMMARY FOR {file_path} ---\n{summary_to_use}"
                    remaining_chars -= len(summary_to_use)
                    summarized_files.append(file_path)
                else:
                    logging.warning(f"Context Builder: Excluded large file '{file_path}' as its summary was also too large.")

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

            self.active_plan = fix_plan
            self.active_plan_cursor = 0
            self.set_phase("GENESIS")
            logging.info("Successfully generated a fix plan from PM description. Transitioning to GENESIS phase.")

        except Exception as e:
            logging.error(f"Tier 3 interactive triage failed. Error: {e}")
            self.set_phase("DEBUG_PM_ESCALATION")

    def start_test_environment_setup(self, progress_callback=None, **kwargs):
        """
        Calls both the dev and test advisor agents to get a consolidated list
        of environment setup tasks.
        """
        logging.info("Initiating unified development and test environment setup guidance.")
        try:
            if not self.llm_service:
                raise Exception("Cannot get setup tasks: LLM Service is not configured.")

            db = self.db_manager
            project_details = db.get_project_by_id(self.project_id)
            if not project_details:
                raise Exception("Cannot get setup tasks: Project details not found.")

            tech_spec_text = project_details['tech_spec_text']
            target_os = project_details['target_os'] if project_details and 'target_os' in project_details.keys() and project_details['target_os'] else 'Linux'

            if not tech_spec_text:
                raise Exception("Cannot get setup tasks: Technical Specification is missing.")

            # Step 1: Get Development environment steps
            dev_agent = DevEnvironmentAdvisorAgent(llm_service=self.llm_service)
            dev_tasks = dev_agent.get_setup_tasks(tech_spec_text, target_os) or []

            # Step 2: Get Test environment steps
            test_agent = TestEnvironmentAdvisorAgent(llm_service=self.llm_service)
            test_tasks = test_agent.get_setup_tasks(tech_spec_text, target_os) or []

            # Step 3: Combine and tag the tasks
            combined_tasks = []
            for task in dev_tasks:
                combined_tasks.append({'type': 'development', **task})
            for task in test_tasks:
                combined_tasks.append({'type': 'test', **task})

            logging.info(f"Generated {len(dev_tasks)} dev steps and {len(test_tasks)} test steps.")
            return combined_tasks

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

    def finalize_test_environment_setup(self, backend_test_command: str, ui_test_command: str):
        """
        Saves the confirmed backend and UI test commands and transitions to the next phase,
        conditionally skipping the build script phase if not required.
        """
        logging.info(f"Finalizing test environment setup. Backend command: '{backend_test_command}', UI command: '{ui_test_command}'")
        try:
            db = self.db_manager
            db.update_project_field(self.project_id, "test_execution_command", backend_test_command)
            db.update_project_field(self.project_id, "ui_test_execution_command", ui_test_command)

            # --- Conditional Phase Logic ---
            project_details = db.get_project_by_id(self.project_id)

            # NEW: Read the list of all technologies
            technologies_json = project_details['detected_technologies'] if project_details else '[]'
            try:
                detected_technologies = json.loads(technologies_json)
            except (json.JSONDecodeError, TypeError):
                detected_technologies = []

            # Define technologies that do not require a formal build script
            build_script_not_required = ["Shell Script", "Bash", "PowerShell"]

            # NEW: Check if *any* detected tech requires a build script
            requires_build_script = False
            if detected_technologies:
                for tech in detected_technologies:
                    if tech not in build_script_not_required:
                        requires_build_script = True
                        break

            if not requires_build_script:
                logging.info(f"No detected technologies require a build script ({detected_technologies}). Skipping to Dockerization.")
                self.set_phase("DOCKERIZATION_SETUP")
            else:
                logging.info(f"Detected technologies ({detected_technologies}) require a build script. Proceeding to Build Script phase.")
                self.set_phase("BUILD_SCRIPT_SETUP")

            logging.info("Test environment setup complete.")
            return True
        except Exception as e:
            logging.error(f"Failed to finalize test environment setup: {e}")
            return False

    def finalize_build_script(self):
        """
        Transitions the factory to the Dockerization phase after the build script is handled.
        """
        logging.info("Build script phase complete. Transitioning to Dockerization setup.")
        self.set_phase("DOCKERIZATION_SETUP")
        # In a real scenario, you might pass a success flag or data back.
        # For this workflow, the UI's continuation implies success.
        return True

    def finalize_dockerization_setup(self):
        """
        Transitions the factory to the Coding Standard phase after Dockerization is handled.
        """
        logging.info("Dockerization phase complete. Transitioning to Coding Standard generation.")
        self.set_phase("CODING_STANDARD_GENERATION")
        return True

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

    def detect_technologies_in_spec(self, tech_spec_text: str) -> list[str]:
        """
        Uses an LLM to parse a technical specification and identify all distinct
        programming languages, returning them as a list.
        """
        logging.info("Detecting technologies from technical specification...")
        if not tech_spec_text:
            logging.warning("Cannot detect technologies: tech_spec_text is empty.")
            return []
        try:
            prompt = textwrap.dedent(f"""
                Analyze the following technical specification document. Your single task is to identify every distinct programming language (e.g., Python, JavaScript, C#, HTML, CSS, SQL) mentioned.

                **MANDATORY INSTRUCTIONS:**
                1.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array of strings.
                2.  **One Language Per String:** Each string in the array must be the name of one programming language.
                3.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON array itself. If no languages are found, return an empty array `[]`.

                **--- Technical Specification ---**
                {tech_spec_text}
                **--- End Specification ---**

                **--- REQUIRED OUTPUT: JSON Array of Language Names ---**
            """)

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")

            technologies = json.loads(cleaned_response)
            if isinstance(technologies, list):
                logging.info(f"Detected technologies: {technologies}")
                return technologies

            logging.warning("LLM response for technology detection was not a list.")
            return []
        except Exception as e:
            logging.error(f"Failed to detect technologies from spec: {e}")
            return []

    def is_sprint_active(self) -> bool:
        """
        Checks the database for the latest sprint and returns True if its
        status is 'IN_PROGRESS' or 'PAUSED'. This is the reliable source of
        truth for the sprint state, independent of the current UI phase.
        """
        if not self.project_id:
            return False
        try:
            latest_sprint = self.db_manager.get_latest_sprint_for_project(self.project_id)
            if latest_sprint and latest_sprint['status'] in ['IN_PROGRESS', 'PAUSED']:
                return True
        except Exception as e:
            logging.error(f"Failed to check for active sprint: {e}")
            return False
        return False

    def set_task_processing_complete(self):
        """Resets the flag indicating a task is processing."""
        self.is_task_processing = False
        logging.info("Task processing flag has been reset.")

    def debug_jump_to_phase(self, phase_name: str):
        """
        A debug-only method to jump the application to a specific phase.
        It will create a new project only if no project is currently active.
        """
        logging.warning(f"--- DEBUG: Jumping to phase: {phase_name} ---")

        db = self.db_manager

        if not self.project_id:
            logging.info("No active project found, creating a new 'Debug Project'.")
            # This sets up the orchestrator state in memory
            self.start_new_project("Debug Project")

            # This creates the actual database record
            timestamp = datetime.now(timezone.utc).isoformat()
            db.create_project(self.project_id, self.project_name, timestamp)

            # This is the new, corrective logic: create the physical directories
            project_root_str = "data/debug_project"
            project_root = Path(project_root_str)
            docs_dir = project_root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Debug mode: Ensured project directory exists at {docs_dir}")

            # Now these updates will work correctly
            db.update_project_field(self.project_id, "project_root_folder", project_root_str)
            db.update_project_field(self.project_id, "final_spec_text", "Debug final spec.")
            db.update_project_field(self.project_id, "tech_spec_text", "This is a debug tech spec for a project using Python for the backend and JavaScript with HTML for the frontend.")
            db.update_project_field(self.project_id, "technology_stack", "Python")

        if phase_name == "GENESIS":
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

    def run_auto_calibration(self, progress_callback=None) -> tuple[bool, str]:
        """
        Queries the active LLM by asking it to browse the web for its own
        token limit, then saves the calibrated value to the database.
        Includes fallback to pre-configured defaults on failure.
        """
        import textwrap
        import json
        import re

        if progress_callback:
            progress_callback(("INFO", "Starting auto-calibration..."))

        try:
            if not self.llm_service:
                raise Exception("LLM Service is not initialized.")

            prompt = textwrap.dedent("""
                You are a helpful assistant with web browsing capabilities. Your only task is to browse the internet to find the standard, published maximum context window size in tokens for your own model.

                **MANDATORY INSTRUCTIONS:**
                1.  **Web Search:** You MUST perform a web search to find the official documentation for your model's context window.
                2.  **NUMERIC OUTPUT ONLY:** Your entire response MUST be ONLY the integer representing the token limit.
                3.  **DO NOT INCLUDE:** Do not include commas, units (like "tokens"), explanations, caveats, or any other words or characters. Just the raw number.

                **Example of a PERFECT response:**
                2048000

                **Example of a FAILED response:**
                The context window is 2,048,000 tokens.

                **Your Numeric-Only Response:**
            """)

            if progress_callback:
                progress_callback(("INFO", "Determining appropriate character context window..."))

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            if response_text.strip().startswith("Error:"):
                raise Exception(f"LLM service returned an error during calibration: {response_text}")

            if "Error:" in response_text:
                logging.error(f"Auto-calibration failed: LLM returned an error. Response: {response_text}")
                # Return a failure tuple instead of raising an exception that gets caught by the fallback
                return False, response_text

            # Extract all digits from the response, ignoring commas or other text
            numeric_string = re.sub(r'[^\d]', '', response_text)
            if not numeric_string:
                raise ValueError("LLM response contained no numbers.")

            max_tokens = int(numeric_string)

            if progress_callback:
                progress_callback(("SUCCESS", f"LLM reported a max of {max_tokens:,} tokens."))

            # Convert to characters (4 chars/token) and apply 20% safety margin (multiply by 0.8)
            safe_char_limit = int((max_tokens * 4) * 0.8)

            self.db_manager.set_config_value("CONTEXT_WINDOW_CHAR_LIMIT", str(safe_char_limit))

            success_msg = f"Auto-calibration complete. Context limit set to {safe_char_limit:,} characters."
            logging.info(success_msg)
            if progress_callback:
                progress_callback(("SUCCESS", success_msg))
            return True, str(safe_char_limit)

        except (json.JSONDecodeError, ValueError) as e:
            logging.warning(f"Web-sourced auto-calibration failed: {e}. Attempting to fall back to pre-configured default.")
            if progress_callback:
                progress_callback(("WARNING", f"Web-sourced calibration failed: {e}. Falling back to default."))

            try:
                provider_name = self.db_manager.get_config_value("SELECTED_LLM_PROVIDER")
                provider_key_map = {
                    "Gemini": "GEMINI_CONTEXT_LIMIT", "ChatGPT": "OPENAI_CONTEXT_LIMIT",
                    "Claude": "ANTHROPIC_CONTEXT_LIMIT", "Grok": "GROK_CONTEXT_LIMIT",
                    "Deepseek": "DEEPSEEK_CONTEXT_LIMIT", "Llama": "LLAMA_CONTEXT_LIMIT",
                    "Phi-3 (Local)": "LOCALPHI3_CONTEXT_LIMIT",
                    "Any Other": "ENTERPRISE_CONTEXT_LIMIT"
                }
                default_key = provider_key_map.get(provider_name)
                if default_key:
                    default_value = self.db_manager.get_config_value(default_key)
                    if default_value:
                        self.db_manager.set_config_value("CONTEXT_WINDOW_CHAR_LIMIT", default_value)
                        success_msg = f"Used pre-configured default limit: {int(default_value):,} characters."
                        logging.info(success_msg)
                        if progress_callback:
                            progress_callback(("SUCCESS", success_msg))
                        return True, default_value

                # If all else fails, raise the original error
                raise e

            except Exception as final_e:
                error_msg = f"Auto-calibration and fallback failed: {final_e}"
                logging.error(error_msg, exc_info=True)
                if progress_callback:
                    progress_callback(("ERROR", error_msg))
                return False, error_msg

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
                raise ValueError("Gemini is selected, but the connection attempt failed.")
                # return None
            return GeminiAdapter(api_key, reasoning_model, fast_model)

        elif provider_name_from_db == "ChatGPT":
            api_key = db.get_config_value("OPENAI_API_KEY")
            reasoning_model = db.get_config_value("OPENAI_REASONING_MODEL")
            fast_model = db.get_config_value("OPENAI_FAST_MODEL")
            if not api_key:
                raise ValueError("ChatGPT (OpenAI) is selected, but the connection attempt failed.")
                # return None
            return OpenAIAdapter(api_key, reasoning_model, fast_model)

        elif provider_name_from_db == "Claude":
            api_key = db.get_config_value("ANTHROPIC_API_KEY")
            reasoning_model = db.get_config_value("ANTHROPIC_REASONING_MODEL")
            fast_model = db.get_config_value("ANTHROPIC_FAST_MODEL")
            if not api_key:
                raise ValueError("Claude (Anthropic) is selected, but the connection attempt failed.")
                # return None
            return AnthropicAdapter(api_key, reasoning_model, fast_model)

        elif provider_name_from_db == "Grok":
            api_key = db.get_config_value("GROK_API_KEY")
            reasoning_model = db.get_config_value("GROK_REASONING_MODEL")
            fast_model = db.get_config_value("GROK_FAST_MODEL")
            if not api_key:
                raise ValueError("Grok is selected, but the connection attempt failed.")
                # return None
            return GrokAdapter(api_key, reasoning_model, fast_model)

        elif provider_name_from_db == "Deepseek":
            api_key = db.get_config_value("DEEPSEEK_API_KEY")
            reasoning_model = db.get_config_value("DEEPSEEK_REASONING_MODEL")
            fast_model = db.get_config_value("DEEPSEEK_FAST_MODEL")
            if not api_key:
                raise ValueError("Deepseek is selected, but the connection attempt failed.")
                # return None
            return DeepseekAdapter(api_key, reasoning_model, fast_model)

        elif provider_name_from_db == "Llama":
            api_key = db.get_config_value("LLAMA_API_KEY")
            reasoning_model = db.get_config_value("LLAMA_REASONING_MODEL")
            fast_model = db.get_config_value("LLAMA_FAST_MODEL")
            if not api_key:
                raise ValueError("Llama is selected, but the connection attempt failed.")
                # return None
            return LlamaAdapter(api_key, reasoning_model, fast_model)

        elif provider_name_from_db == "Phi-3 (Local)":
            return LocalPhi3Adapter()

        elif provider_name_from_db == "Any Other":
            base_url = db.get_config_value("CUSTOM_ENDPOINT_URL")
            api_key = db.get_config_value("CUSTOM_ENDPOINT_API_KEY")
            reasoning_model = db.get_config_value("CUSTOM_REASONING_MODEL")
            fast_model = db.get_config_value("CUSTOM_FAST_MODEL")
            if not all([base_url, api_key, reasoning_model, fast_model]):
                raise ValueError("Other provider selected, but one or more required settings are missing.")
                # return None
            return CustomEndpointAdapter(base_url, api_key, reasoning_model, fast_model)

        else:
            logging.error(f"Invalid LLM provider configured: {provider_name_from_db}")
            return None

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

    def get_project_documents(self) -> tuple[list[dict], list[str]]:
        """
        Gets a classified list of documents for the Document Hub.
        - "Specs" are pulled from the database (Projects and Artifacts tables).
        - "Other" are found by recursively scanning the project root.

        Returns:
            A tuple containing:
            (spec_documents, other_documents)
            - spec_documents: A list of dicts: [{'name': str, 'path': str}]
            - other_documents: A list of strings (relative paths)
        """
        if not self.project_id or not self.project_root_path:
            return [], []

        spec_docs = []
        spec_paths_set = set() # To prevent duplicates in the "Other" list

        try:
            # 1. Get Core Specs from Projects table
            project_details_row = self.db_manager.get_project_by_id(self.project_id)
            if project_details_row:
                project_details = dict(project_details_row)
                # This map now correctly links the spec name to its REAL file path
                # and the DB column that confirms it exists.
                spec_map = {
                    "Application Specification": ("docs/application_spec.md", "final_spec_text"),
                    "Technical Specification": ("docs/technical_spec.md", "tech_spec_text"),
                    "UX/UI Specification": ("docs/ux_ui_specification.md", "ux_spec_text"),
                    "Database Schema Specification": ("docs/db_schema_spec.md", "db_schema_spec_text")
                }

                for name, (path_str, db_key) in spec_map.items():
                    # Check if the spec exists in the database
                    if project_details.get(db_key):
                        spec_docs.append({"name": name, "path": path_str})
                        spec_paths_set.add(path_str)

            # 2. Get Coding Standards from Artifacts table
            artifacts = self.db_manager.get_all_artifacts_for_project(self.project_id)
            for art_row in artifacts:
                art = dict(art_row)
                if art.get('artifact_type') == 'CODING_STANDARD' and art.get('status') in ('COMPLETED', 'SKIPPED'):
                    path_str = art.get('file_path')
                    if path_str:
                        spec_docs.append({"name": art.get('artifact_name'), "path": path_str})
                        spec_paths_set.add(path_str)

            # 3. Scan filesystem for "Other Documents"
            other_docs = []
            root_path = Path(self.project_root_path)
            excluded_dirs = {'.git', 'venv', '.venv', '__pycache__', 'node_modules', '.asdf_project'}
            # Add .xlsx as requested
            allowed_extensions = {'.pdf', '.docx', '.txt', '.md', '.xlsx', '.json'}

            for file_path in root_path.rglob('*'):
                if file_path.is_file():
                    # Check if any part of the path is an excluded directory
                    if any(part in excluded_dirs for part in file_path.parts):
                        continue

                    if file_path.suffix.lower() in allowed_extensions:
                        relative_path_str = str(file_path.relative_to(root_path)).replace('\\', '/')

                        # Add to "Other" list ONLY if it's not a spec we already found
                        if relative_path_str not in spec_paths_set:
                            other_docs.append(relative_path_str)

            return spec_docs, sorted(list(other_docs))

        except Exception as e:
            logging.error(f"Failed to get project documents: {e}", exc_info=True)
            return [], []

    def add_other_document(self, source_path: Path, **kwargs) -> Optional[Path]:
        """
        Copies a new, generic document into the project's docs folder.

        Args:
            source_path: The path of the file to be copied.

        Returns:
            The relative destination path of the new document, or None on failure.
        """
        if not self.project_root_path:
            logging.error("Cannot add document: No project path loaded.")
            return None
        try:
            root_path = Path(self.project_root_path)
            docs_dir = root_path / "docs" / "uploads"
            docs_dir.mkdir(parents=True, exist_ok=True)

            destination_path = docs_dir / source_path.name

            # Handle name conflicts
            counter = 1
            base_name = destination_path.stem
            extension = destination_path.suffix
            while destination_path.exists():
                destination_path = docs_dir / f"{base_name}_{counter}{extension}"
                counter += 1

            shutil.copy(source_path, destination_path)
            rel_path = destination_path.relative_to(root_path)
            logging.info(f"Successfully added new document: {rel_path}")
            return rel_path
        except Exception as e:
            logging.error(f"Failed to add other document: {e}", exc_info=True)
            return None

    def upload_new_document_version(self, source_path: Path, old_doc_rel_path: str, **kwargs) -> Optional[Path]:
        """
        Handles the upload of a new version of an existing document.

        Args:
            source_path: The path of the new file to be copied.
            old_doc_rel_path: The relative path (from project root) of the document being replaced.

        Returns:
            The relative path to the newly versioned document, or None on failure.
        """
        if not self.project_root_path or not self.project_id:
            logging.error("Cannot upload new version: Project state is not fully loaded.")
            return None
        try:
            root_path = Path(self.project_root_path)
            old_doc_path = root_path / old_doc_rel_path

            # Determine the next version number
            base_name, extension = os.path.splitext(old_doc_path.name)
            version_match = re.search(r'_v(\d+)$', base_name)

            if version_match:
                current_version = int(version_match.group(1))
                next_version = current_version + 1
                new_base_name = re.sub(r'_v\d+$', f'_v{next_version}', base_name)
            else:
                # If no version tag exists, append '_v2'
                next_version = 2
                new_base_name = f"{base_name}_v{next_version}"

            new_doc_name = f"{new_base_name}{extension}"
            destination_path = old_doc_path.parent / new_doc_name

            # Copy the new file
            shutil.copy(source_path, destination_path)
            new_rel_path = destination_path.relative_to(root_path)

            # Add a system log entry for the version change
            self.db_manager.add_document_log_entry(
                project_id=self.project_id,
                document_path=str(new_rel_path).replace('\\', '/'),
                author="SYSTEM",
                log_text=f"Version {next_version} uploaded. Replaces '{old_doc_rel_path}'.",
                status="VERSION_UPDATE"
            )
            logging.info(f"Successfully uploaded new version: {new_rel_path}")
            return new_rel_path
        except Exception as e:
            logging.error(f"Failed to upload new document version: {e}", exc_info=True)
            return None

    def get_document_content(self, relative_path: str, **kwargs) -> tuple[str, str]:
        """
        Reads and returns the title and content of a document from the project root.
        Returns: (title, content)
        """
        if not self.project_root_path:
            logging.error("Cannot read document: No project path loaded.")
            raise Exception("Project not loaded.")
        try:
            full_path = Path(self.project_root_path) / relative_path
            title = f"View: {relative_path}"

            if not full_path.exists():
                return title, f"## Error\n\nFile not found: `{relative_path}`"

            # Handle non-previewable files gracefully
            if full_path.suffix.lower() in ['.pdf', '.docx', '.xlsx']:
                return title, f"## Non-Previewable Document\n\n**File:** `{relative_path}`\n\nThis file type (`{full_path.suffix}`) cannot be previewed within the application. Please open it using an external editor."

            # Read as text, ignoring errors for potential binary files
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                content = self._strip_header_from_document(content)
                # If it's not markdown, wrap it in a code block for plain text display
                if full_path.suffix.lower() != '.md':
                     content = f"```\n{content}\n```"
                return title, content

        except Exception as e:
            logging.error(f"Failed to read document content for {relative_path}: {e}", exc_info=True)
            return f"Error: {relative_path}", f"## File Read Error\n\nCould not read file `{relative_path}`.\n\n**Error:**\n```\n{e}\n```"