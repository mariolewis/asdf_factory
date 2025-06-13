import streamlit as st
from pathlib import Path
import time
import pandas as pd
from datetime import datetime
import logging

# Imports from the project's root directory
from master_orchestrator import MasterOrchestrator
from agent_environment_setup_app_target import EnvironmentSetupAgent_AppTarget
from agent_project_bootstrap import ProjectBootstrapAgent
from agent_spec_clarification import SpecClarificationAgent
from agents.agent_planning_app_target import PlanningAgent_AppTarget

# Import the new agent from the 'agents' subfolder
from agents.agent_project_scoping import ProjectScopingAgent

# --- Page Configuration ---
st.set_page_config(
    page_title="ASDF",
    page_icon="🤖",
    layout="wide"
)

# --- Application State Management ---
db_dir = Path("data")
db_dir.mkdir(exist_ok=True)
db_path = db_dir / "asdf.db"

# Initialize session state variables
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = MasterOrchestrator(db_path=str(db_path))
    with st.session_state.orchestrator.db_manager as db:
        api_key = db.get_config_value("LLM_API_KEY")
        if not api_key:
            st.warning("LLM API Key not found. Please go to the Settings page to configure it.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = ""


# --- Sidebar ---
with st.sidebar:
    st.markdown("## 🤖 Autonomous Software Development Factory")
    st.markdown("---")
    page = st.radio("Navigation", ["Project", "Reports", "Settings"], label_visibility="collapsed")
    st.markdown("---")

    st.markdown("### Project Information")
    status_info = st.session_state.orchestrator.get_status()
    labels = {"project_id": "Project ID", "project_name": "Project Name", "current_phase": "Current Phase"}
    for key, label in labels.items():
        value = status_info.get(key)
        display_value = value if value is not None else "N/A"
        st.markdown(f"**{label}:** {display_value}")

    st.markdown("---")
    st.markdown("### Project Lifecycle")

    if st.button("📂 Load Archived Project", use_container_width=True):
        st.session_state.orchestrator.set_phase("VIEWING_PROJECT_HISTORY")
        st.rerun()

    if st.session_state.orchestrator.project_id:
        if st.button("⏹️ Stop & Export Active Project", use_container_width=True):
            st.session_state.show_export_confirmation = True

        if st.session_state.get("show_export_confirmation"):
            with st.form("export_form"):
                st.warning(
                    "**Archive Project Confirmation**\n\n"
                    "This will save all project data to an external archive file and clear the active session. "
                    "This action is for permanently archiving your work, unlike the temporary 'Pause' function."
                )
                archive_name_input = st.text_input(
                    "Enter a name for the archive file:",
                    value=f"{st.session_state.orchestrator.project_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
                )
                with st.session_state.orchestrator.db_manager as db:
                    archive_path = db.get_config_value("DEFAULT_ARCHIVE_PATH") or "data/archives"

                submitted = st.form_submit_button("Confirm and Export")
                if submitted:
                    if archive_name_input:
                        archive_file_path = st.session_state.orchestrator.stop_and_export_project(archive_path, archive_name_input)
                        if archive_file_path:
                            st.session_state.last_action_success_message = f"Project archived to: `{archive_file_path}`"
                        else:
                            st.error("Failed to export project.")
                        st.session_state.show_export_confirmation = False
                        st.rerun()
                    else:
                        st.error("Archive name cannot be empty.")


# --- Main Application UI ---

if page == "Project":
    if "last_action_success_message" in st.session_state:
        st.success(st.session_state.last_action_success_message)
        del st.session_state.last_action_success_message

    if not st.session_state.orchestrator.project_id:
        st.subheader("Start a New Project")
        project_name_input = st.text_input("Enter a name for your new project:")
        if st.button("Start New Project"):
            if project_name_input:
                st.session_state.orchestrator.start_new_project(project_name_input)
                st.rerun()
            else:
                st.error("Please enter a project name.")
    else:
        status_info = st.session_state.orchestrator.get_status()
        current_phase_name = status_info.get("current_phase")

        if current_phase_name == "ENV_SETUP_TARGET_APP":
            setup_agent = EnvironmentSetupAgent_AppTarget()
            setup_agent.run_setup_flow()
            if st.session_state.get('git_initialized'):
                st.divider()
                if st.button("Complete Environment Setup & Proceed", use_container_width=True):
                    apex_file = st.session_state.get("apex_file_name_input", "").strip()
                    if not apex_file:
                        st.error("Please provide a main Executable File Name.")
                    else:
                        with st.session_state.orchestrator.db_manager as db:
                            db.update_project_technology(st.session_state.orchestrator.project_id, st.session_state.language)
                            db.update_project_apex_file(st.session_state.orchestrator.project_id, apex_file)
                        st.session_state.orchestrator.set_phase("SPEC_ELABORATION")
                        keys_to_clear = ['project_root_path', 'path_confirmed', 'git_initialized', 'language', 'language_select', 'frameworks', 'apex_file_name_input']
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

        elif current_phase_name == "SPEC_ELABORATION":
            st.header("Phase 1: Project Initialization & Specification Elaboration")

            # Initialize session state keys for this phase
            if 'specification_text' not in st.session_state:
                st.session_state.specification_text = None
            if 'complexity_analysis' not in st.session_state:
                st.session_state.complexity_analysis = None
            if 'proceed_with_complexity' not in st.session_state:
                st.session_state.proceed_with_complexity = False

            # --- UI for providing the specification ---
            if st.session_state.specification_text is None:
                st.markdown("Please provide the initial specification for your target application.")
                tab1, tab2 = st.tabs(["Upload Specification Documents", "Enter Brief Description"])
                with tab1:
                    uploaded_files = st.file_uploader("Upload Docs", type=["txt", "md", "docx"], accept_multiple_files=True, label_visibility="collapsed")
                    if st.button("Process Uploaded Documents"):
                        if uploaded_files:
                            bootstrap_agent = ProjectBootstrapAgent()
                            # MODIFIED: Handle new return signature from bootstrap agent
                            extracted_text, messages, size_error = bootstrap_agent.extract_text_from_files(uploaded_files)
                            for msg in messages:
                                st.warning(msg)

                            # (CR-ASDF-004) Stage 1: Handle Size Guardrail Error
                            if size_error:
                                st.error(size_error) # Display the specific error message
                            elif extracted_text:
                                st.session_state.specification_text = extracted_text
                                st.rerun()
                        else:
                            st.warning("Please upload at least one document.")

                with tab2:
                    brief_desc_input = st.text_area("Brief Description", height=150, key="brief_desc")
                    if st.button("Process Brief Description"):
                        if brief_desc_input:
                            with st.spinner("AI is expanding the description..."):
                                try:
                                    with st.session_state.orchestrator.db_manager as db:
                                        api_key = db.get_config_value("LLM_API_KEY")
                                    if not api_key:
                                        st.error("LLM API Key is not set in Settings.")
                                    else:
                                        clarification_agent = SpecClarificationAgent(api_key=api_key, db_manager=st.session_state.orchestrator.db_manager)
                                        expanded_text = clarification_agent.expand_brief_description(brief_desc_input)
                                        st.session_state.specification_text = expanded_text
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Spec Expansion Error: {e}")

            # --- Main workflow after getting specification text ---
            if st.session_state.specification_text is not None:
                st.subheader("Processed Specification Draft")
                st.text_area("", value=st.session_state.specification_text, height=250, disabled=True)
                st.divider()

                # (CR-ASDF-004) Stage 2: Perform Complexity Analysis
                if st.session_state.complexity_analysis is None:
                    with st.spinner("Performing high-level complexity analysis..."):
                        try:
                            with st.session_state.orchestrator.db_manager as db:
                                api_key = db.get_config_value("LLM_API_KEY")
                            if not api_key:
                                st.error("Cannot perform complexity analysis. LLM API Key is not set.")
                            else:
                                scoping_agent = ProjectScopingAgent(api_key=api_key)
                                result = scoping_agent.analyze_complexity(st.session_state.specification_text)
                                st.session_state.complexity_analysis = result
                                st.rerun()
                        except Exception as e:
                            st.error(f"Complexity Analysis Failed: {e}")

                # (CR-ASDF-004) Stage 2: Display Complexity Warning if needed
                elif not st.session_state.proceed_with_complexity:
                    rating = st.session_state.complexity_analysis.get("rating")
                    justification = st.session_state.complexity_analysis.get("justification")
                    st.subheader("Complexity Analysis Result")
                    st.write(f"**Rating:** {rating}")
                    st.write(f"**Justification:** *{justification}*")

                    if rating in ["High", "Very Large"]:
                        st.warning(
                            "**Warning: The scope of this project is very large, which may impact performance. "
                            "It is recommended to divide it into smaller projects. Do you wish to proceed?**"
                        ) #
                        if st.button("Yes, I wish to proceed"):
                            st.session_state.proceed_with_complexity = True
                            st.rerun()
                    else: # Low or Medium complexity
                        st.session_state.proceed_with_complexity = True
                        st.rerun()

                # --- Clarification Loop (only runs after complexity gate is passed) ---
                else:
                    if 'clarification_issues' not in st.session_state:
                        st.session_state.clarification_issues = None
                    if 'clarification_chat' not in st.session_state:
                        st.session_state.clarification_chat = []

                    if st.session_state.clarification_issues:
                        st.subheader("Clarification Required")
                        if st.button("✅ Approve Specification and Proceed", use_container_width=True, type="primary"):
                            with st.spinner("Finalizing specification..."):
                                with st.session_state.orchestrator.db_manager as db:
                                    db.save_final_specification(st.session_state.orchestrator.project_id, st.session_state.specification_text)
                                st.session_state.orchestrator.set_phase("TECHNICAL_SPECIFICATION")
                                for key in ['specification_text', 'complexity_analysis', 'proceed_with_complexity', 'clarification_issues', 'clarification_chat', 'brief_desc']:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.rerun()

                        st.divider()
                        for message in st.session_state.clarification_chat:
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])

                        if prompt := st.chat_input("Provide clarifications..."):
                            st.session_state.clarification_chat.append({"role": "user", "content": prompt})
                            with st.spinner("AI is refining the specification..."):
                                agent = SpecClarificationAgent(api_key=api_key, db_manager=st.session_state.orchestrator.db_manager)
                                revised_spec = agent.refine_specification(st.session_state.specification_text, st.session_state.clarification_issues, prompt)
                                st.session_state.specification_text = revised_spec
                                st.session_state.clarification_issues = None
                                st.session_state.clarification_chat = []
                                st.rerun()

                    else: # If clarification issues are not yet identified
                        if st.button("Analyze Specification & Begin Clarification", use_container_width=True):
                            with st.spinner("AI is analyzing the specification for issues..."):
                                agent = SpecClarificationAgent(api_key=api_key, db_manager=st.session_state.orchestrator.db_manager)
                                issues = agent.identify_potential_issues(st.session_state.specification_text)
                                st.session_state.clarification_issues = issues
                                st.session_state.clarification_chat.append({"role": "assistant", "content": issues})
                                st.rerun()

        elif current_phase_name == "TECHNICAL_SPECIFICATION":
            st.header("Phase 1.5: Technical Specification & Architecture")
            st.markdown("Now we will establish the technical foundation for the project. You can either define the technology stack and architecture directly, or have the ASDF analyze the functional specification and propose one for your review.")

            # Initialize session state for this phase
            if 'tech_spec_choice' not in st.session_state:
                st.session_state.tech_spec_choice = None
            if 'tech_spec_draft' not in st.session_state:
                st.session_state.tech_spec_draft = ""

            # Get the finalized functional spec from the database for context
            with st.session_state.orchestrator.db_manager as db:
                project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                final_spec_text = project_details['final_spec_text']

            # Let the user choose the method
            st.session_state.tech_spec_choice = st.radio(
                "Choose your method:",
                ["Let ASDF propose a technology stack", "I will define the technology stack directly"],
                key="tech_spec_radio"
            )

            # --- Handle AI Proposal Path ---
            if st.session_state.tech_spec_choice == "Let ASDF propose a technology stack":
                if st.button("Generate Proposal"):
                    with st.spinner("AI is analyzing the specification and generating a proposal..."):
                        try:
                            with st.session_state.orchestrator.db_manager as db:
                                api_key = db.get_config_value("LLM_API_KEY")
                            if not api_key:
                                st.error("Cannot generate proposal. LLM API Key is not set.")
                            else:
                                from agents.agent_tech_stack_proposal import TechStackProposalAgent
                                agent = TechStackProposalAgent(api_key=api_key)
                                proposal = agent.propose_stack(final_spec_text)
                                st.session_state.tech_spec_draft = proposal
                        except Exception as e:
                            st.error(f"Failed to generate proposal: {e}")

            # --- Text area for final review, editing, or direct input ---
            st.session_state.tech_spec_draft = st.text_area(
                "Technical Specification Document",
                value=st.session_state.tech_spec_draft,
                height=400,
                help="You can edit the AI-generated proposal here, or write/paste your own technical specification if you chose the direct input method."
            )

            st.divider()

            # --- Approval Step ---
            if st.session_state.tech_spec_draft:
                if st.button("Approve Technical Specification and Proceed to Planning", type="primary"):
                    with st.spinner("Saving technical specification..."):
                        with st.session_state.orchestrator.db_manager as db:
                            db.save_tech_specification(
                                st.session_state.orchestrator.project_id,
                                st.session_state.tech_spec_draft
                            )

                        # Transition to the next phase
                        st.session_state.orchestrator.set_phase("PLANNING")

                        # Clean up session state for this phase
                        for key in ['tech_spec_choice', 'tech_spec_draft']:
                             if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

        # Other phases remain unchanged for now
        elif current_phase_name == "INTEGRATION_AND_VERIFICATION":
            st.header("Phase 3.5: Automated Integration & Verification")
            st.info("The factory is now integrating all newly developed components, performing a full system build, and running verification tests.")

            with st.spinner("Running automated integration... This may take a moment."):
                # This backend method runs the entire phase 3.5 logic
                st.session_state.orchestrator._run_integration_and_verification_phase()

            st.success("Integration and verification process complete.")
            time.sleep(2) # Pause for 2 seconds to allow the user to read the message
            st.rerun()

        elif current_phase_name == "PLANNING":
            st.header("Phase 2: Strategic Development Planning")

            # Initialize session state for this phase
            if 'development_plan' not in st.session_state:
                st.session_state.development_plan = None

            # If a plan has been generated, display it for review
            if st.session_state.development_plan:
                st.subheader("Generated Development Plan")
                st.markdown("Please review the generated plan. If it is acceptable, approve it to begin the development phase. To generate a new version, click the 'Generate' button again.")

                # Display the plan as a JSON object for clear structure
                st.json(st.session_state.development_plan)

                st.divider()
                col1, _, col3 = st.columns([1, 2, 1.5])

                with col1:
                    # The button to approve the plan and proceed
                    if st.button("✅ Approve Plan & Proceed to Development", type="primary"):
                        # Load the plan into the orchestrator
                        st.session_state.orchestrator.load_development_plan(st.session_state.development_plan)
                        # Transition to the Genesis phase
                        st.session_state.orchestrator.set_phase("GENESIS")
                        # Clean up session state
                        del st.session_state.development_plan
                        st.toast("Plan approved! Starting development...")
                        st.rerun()
                with col3:
                    # The button to re-generate the plan
                    if st.button("🔄 Re-generate Development Plan"):
                         st.session_state.development_plan = None
                         st.rerun()


            # If no plan exists yet, show the button to generate one
            else:
                st.info("Click the button below to generate a detailed, sequential development plan based on the finalized specifications.")
                if st.button("Generate Development Plan", type="primary"):
                    with st.spinner("AI is generating the development plan... This may take a few moments."):
                        try:
                            with st.session_state.orchestrator.db_manager as db:
                                api_key = db.get_config_value("LLM_API_KEY")
                                project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                                final_spec = project_details.get('final_spec_text')
                                tech_spec = project_details.get('tech_spec_text')

                            if not all([api_key, final_spec, tech_spec]):
                                st.error("Could not generate plan: Missing API Key, Final Specification, or Technical Specification.")
                            else:
                                agent = PlanningAgent_AppTarget(api_key=api_key)
                                plan_json = agent.generate_development_plan(final_spec, tech_spec)

                                # Check if the agent returned an error
                                if '"error":' in plan_json:
                                    st.error(f"Failed to generate plan: {plan_json}")
                                else:
                                    st.session_state.development_plan = plan_json
                                    st.rerun()
                        except Exception as e:
                            st.error(f"An unexpected error occurred: {e}")

        elif current_phase_name == "GENESIS":
            st.header("Phase 3: Iterative Component Development")

            # First, check if a plan is loaded. If not, guide the user back to planning.
            if not st.session_state.orchestrator.active_plan:
                st.warning("No active development plan is loaded.")
                st.info("Please go to the 'Planning' phase to generate a development plan.")
                if st.button("⬅️ Go to Planning Phase"):
                    st.session_state.orchestrator.set_phase("PLANNING")
                    st.rerun()
            else:
                # If a plan is active, display the PM Checkpoint.
                st.subheader("PM Checkpoint")

                # Get dynamic details of the current task from the orchestrator
                task = st.session_state.orchestrator.get_current_task_details()
                total_tasks = len(st.session_state.orchestrator.active_plan)
                cursor = st.session_state.orchestrator.active_plan_cursor

                if task:
                    st.progress((cursor) / total_tasks, text=f"Executing Task {cursor + 1} of {total_tasks}")
                    st.info(f"""
                    Next component in the plan is: **'{task.get('component_name')}'** (based on micro-spec `{task.get('micro_spec_id')}`).

                    How would you like to proceed?
                    """)
                else:
                    # This state is reached if the plan was just completed
                    st.progress(1.0, text=f"All {total_tasks} tasks complete!")
                    st.success("Development plan execution is complete. The next step is Integration & Verification.")
                    if st.button("▶️ Proceed to Integration & Verification"):
                         st.session_state.orchestrator.set_phase("INTEGRATION_AND_VERIFICATION")
                         st.rerun()
                    return # Stop rendering the buttons below

                # Create columns for the buttons for a clean layout.
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    if st.button("▶️ Proceed", use_container_width=True, type="primary"):
                        with st.spinner(f"Executing task for '{task.get('component_name')}'... This may take a moment."):
                            st.session_state.orchestrator.handle_proceed_action()
                        st.rerun()

                with col2:
                    if st.button("✍️ Raise CR", use_container_width=True):
                        st.session_state.orchestrator.handle_raise_cr_action()
                        st.rerun()

                with col3:
                    if st.button("🔁 Implement CR", use_container_width=True):
                        st.session_state.orchestrator.handle_view_cr_register_action()
                        st.rerun()

                with col4:
                    if st.button("⏸️ Pause", use_container_width=True):
                        st.toast("Pausing factory operations...")
                        st.session_state.orchestrator.pause_project()
                        # UI will just stay here until resumed

                with col5:
                    if st.button("⏹️ Stop & Export", use_container_width=True):
                        st.session_state.show_export_confirmation = True
                        st.rerun()

        # (CR-ASDF-003) UI for the new PM Checkpoint on declarative changes
        elif current_phase_name == "AWAITING_PM_DECLARATIVE_CHECKPOINT":
            st.header("PM Checkpoint: High-Risk Change Detected")
            st.warning("The development plan requires a modification to a declarative file (e.g., build script, database schema, config file). Please review the proposed change below.")

            task = st.session_state.orchestrator.task_awaiting_approval

            if task:
                st.markdown(f"**File to Modify:** `{task.get('component_file_path')}`")
                st.markdown(f"**Component:** `{task.get('component_name')}`")

                st.subheader("Proposed Change Snippet")
                # The 'task_description' for these types holds the change snippet
                st.code(task.get('task_description'), language='diff')

                st.divider()
                st.markdown("How would you like to proceed with this change?")

                col1, col2, _ = st.columns([1, 1, 3])

                with col1:
                    if st.button("✅ Execute Automatically", use_container_width=True, type="primary"):
                        st.session_state.orchestrator.handle_declarative_checkpoint_decision("EXECUTE_AUTOMATICALLY")
                        st.toast(f"Executing change for {task.get('component_name')}...")
                        st.rerun()

                with col2:
                    if st.button("✍️ I will Execute Manually", use_container_width=True):
                        st.session_state.orchestrator.handle_declarative_checkpoint_decision("WILL_EXECUTE_MANUALLY")
                        st.toast("Acknowledged. Please apply the change manually.")
                        st.rerun()
            else:
                st.error("Could not retrieve the task awaiting approval. Returning to Genesis phase.")
                st.session_state.orchestrator.set_phase("GENESIS")
                if st.button("Go Back"):
                    st.rerun()

        elif current_phase_name == "VIEWING_PROJECT_HISTORY":
            st.header("Load an Archived Project")

            project_history = st.session_state.orchestrator.get_project_history()

            if not project_history:
                st.warning("There are no archived projects in the history.")
            else:
                history_data = [
                    {
                        "ID": row['history_id'],
                        "Project Name": row['project_name'],
                        "Project ID": row['project_id'],
                        "Archived On": row['last_stop_timestamp'],
                        "Archive Path": row['archive_file_path']
                    }
                    for row in project_history
                ]
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True, hide_index=True, column_config={"ID": "Select"})

                history_ids = [row['history_id'] for row in project_history]
                selected_id = st.selectbox("Select a Project ID to load:", options=[""] + history_ids)

                if st.button("Load Selected Project", disabled=(not selected_id)):
                    with st.spinner("Loading project data and running pre-flight checks..."):
                        # This method now triggers the pre-flight checks and sets the next phase
                        st.session_state.orchestrator.load_archived_project(selected_id)
                        st.rerun()

            st.divider()
            if st.button("⬅️ Back to Main Page"):
                st.session_state.orchestrator.project_id = None # Clear any potential partial state
                st.session_state.orchestrator.set_phase("IDLE")
                st.rerun()

        # (CR-ASDF-006) UI for Pre-flight Check Resolution
        elif current_phase_name == "AWAITING_PREFLIGHT_RESOLUTION":
            st.header("Pre-flight Check Resolution")

            result = st.session_state.orchestrator.preflight_check_result
            if not result:
                st.error("Error: Pre-flight check result not found.")
                if st.button("Go Back"):
                    st.session_state.orchestrator.set_phase("IDLE")
                    st.rerun()

            else:
                status = result.get("status")
                message = result.get("message")

                # Outcome A: All Checks Pass ("Fast Path")
                if status == "ALL_PASS":
                    st.success(message)
                    st.info("The project environment is valid and clean. You can proceed directly to the main workflow, bypassing the setup phase.")
                    if st.button("▶️ Proceed to Specification Elaboration"):
                        st.session_state.orchestrator.set_phase("SPEC_ELABORATION")
                        st.rerun()

                # Outcome B & C: Fatal or Partial Failure
                elif status in ["PATH_NOT_FOUND", "GIT_MISSING", "ERROR"]:
                    st.error(message)
                    st.warning("The factory cannot proceed until this environmental issue is resolved.")
                    if st.button("Go to Environment Setup to Resolve"):
                        st.session_state.orchestrator.set_phase("ENV_SETUP_TARGET_APP")
                        st.rerun()

                # Outcome D: State Drift Detected
                elif status == "STATE_DRIFT":
                    st.warning(message)

                    col1, col2, _ = st.columns([1.5, 1.5, 3])
                    with col1:
                        if st.button("I will resolve this manually", help="Use your own tools (e.g., git commit, git stash) to clean the repository, then load the project again from the main menu."):
                            st.session_state.orchestrator.project_id = None
                            st.session_state.orchestrator.set_phase("IDLE")
                            st.rerun()

                    with col2:
                        # Using a popover for the confirmation dialog
                        with st.popover("Expert Option: Discard"):
                            st.markdown("⚠️ **This will permanently delete all uncommitted changes in your local repository. This cannot be undone.**")
                            if st.button("Confirm & Discard All Changes", type="primary"):
                                with st.spinner("Resetting repository and re-checking..."):
                                    # We need a project_id to reset. The orchestrator has it from the failed load attempt.
                                    project_id_to_reset = st.session_state.orchestrator.project_id
                                    st.session_state.orchestrator.handle_discard_changes(project_id_to_reset)
                                st.rerun()

        else: # Fallback for any other phase
            st.header(f"Current Phase: {current_phase_name}")
            st.info("The UI for this phase is under construction.")

elif page == "Settings":
    # Settings page code remains the same as before
    st.markdown("<h2>Factory Settings</h2>", unsafe_allow_html=True)
    st.subheader("LLM API Key Management")
    def save_api_key():
        if st.session_state.api_key_input:
            with st.session_state.orchestrator.db_manager as db:
                db.set_config_value("LLM_API_KEY", st.session_state.api_key_input)
            st.success("API Key saved!")
    def clear_api_key():
        with st.session_state.orchestrator.db_manager as db:
            db.set_config_value("LLM_API_KEY", "")
        st.session_state.api_key_input = ""
        st.success("API Key cleared.")
    with st.session_state.orchestrator.db_manager as db:
        key_status = "Set" if db.get_config_value("LLM_API_KEY") else "Not Set"
    st.markdown(f"**Status:** `{key_status}`")
    st.text_input("Enter/Update LLM API Key", type="password", key="api_key_input")
    c1, c2, c3 = st.columns([1,1,5])
    c1.button("Save Key", on_click=save_api_key, use_container_width=True)
    c2.button("Clear Key", on_click=clear_api_key, use_container_width=True, disabled=(key_status == "Not Set"))
    st.markdown("---")
    # Add other settings fields here if needed in future steps

elif page == "Reports":
    # Reports page code remains the same as before
    st.markdown("<h2>Project Reports</h2>", unsafe_allow_html=True)
    if not st.session_state.orchestrator.project_id:
        st.warning("Start a project to view reports.")
    else:
        st.info("Report generation is under construction.")