import streamlit as st
from pathlib import Path
import time
import pandas as pd
from datetime import datetime
import logging
import docx
import json

# Imports from the project's root directory
from master_orchestrator import MasterOrchestrator
from agent_environment_setup_app_target import EnvironmentSetupAgent_AppTarget
from agent_project_bootstrap import ProjectBootstrapAgent
from agent_spec_clarification import SpecClarificationAgent
from agents.agent_planning_app_target import PlanningAgent_AppTarget
from agents.agent_report_generator import ReportGeneratorAgent
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
    page = st.radio("Navigation", ["Project", "Documents", "Reports", "Settings"], label_visibility="collapsed")
    st.markdown("---")

    st.markdown("### Project Information")
    status_info = st.session_state.orchestrator.get_status()
    st.markdown(f"**Project ID:** {status_info.get('project_id', 'N/A')}")
    st.markdown(f"**Project Name:** {status_info.get('project_name', 'N/A')}")

    current_phase_enum = st.session_state.orchestrator.current_phase
    display_phase_name = st.session_state.orchestrator.PHASE_DISPLAY_NAMES.get(current_phase_enum, current_phase_enum.name)
    st.markdown(f"**Current Phase:** {display_phase_name}")

    st.markdown("---")
    st.markdown("### Actions")

    # Only show these buttons if a project is active
    if st.session_state.orchestrator.project_id:
        if st.button("✍️ Raise CR", use_container_width=True):
            st.session_state.orchestrator.handle_raise_cr_action()
            st.rerun()

        if st.button("🐞 Report Bug", use_container_width=True):
            st.session_state.orchestrator.handle_report_bug_action()
            st.rerun()

        # Disable the Implement button if Genesis is not complete
        genesis_complete = st.session_state.orchestrator.is_genesis_complete
        if st.button("🔁 Implement CR/Bug", use_container_width=True, disabled=not genesis_complete, help="Enabled after initial development is complete."):
            st.session_state.orchestrator.handle_view_cr_register_action()
            st.rerun()

    st.markdown("---")
    st.markdown("### Project Lifecycle")

    # --- CORRECTED & SIMPLIFIED RESUME LOGIC ---
    # The orchestrator now knows its own state on initialization. We just ask it.
    if st.session_state.orchestrator.resumable_state:
        if st.button("▶️ Resume Paused Project", use_container_width=True, type="primary"):
            if st.session_state.orchestrator.resume_project():
                st.rerun()
            else:
                st.error("Failed to resume project. Check logs for details.")

    # Show Stop button ONLY if a project is active and NOT in a resumable state.
    if st.session_state.orchestrator.project_id and not st.session_state.orchestrator.resumable_state:
        if st.button("⏹️ Stop & Export Active Project", use_container_width=True):
            st.session_state.show_export_confirmation = True

    if st.button("📂 Load Archived Project", use_container_width=True):
        st.session_state.orchestrator.set_phase("VIEWING_PROJECT_HISTORY")
        st.rerun()

    # The 'show_export_confirmation' logic remains the same as before
    if st.session_state.get("show_export_confirmation"):
        with st.form("export_form"):
            st.warning(
                "**Archive Project Confirmation**\n\n"
                "This will save all project data to an external archive file and clear the active session."
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
                        # --- CORRECTED: Perform a hard reset of the orchestrator state ---
                        st.session_state.last_action_success_message = f"Project archived to: `{archive_file_path}`"
                        # Re-initialize the orchestrator to ensure a clean state.
                        st.session_state.orchestrator = MasterOrchestrator(db_path=str(db_path))
                        st.session_state.show_export_confirmation = False
                        st.rerun()
                    else:
                        st.error("Failed to export project.")
                else:
                    st.error("Archive name cannot be empty.")

# --- Main Application UI ---
st.markdown("""
    <script>
        const streamlitDoc = window.parent.document;
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length) {
                    streamlitDoc.querySelector('.main').scrollTo(0, 0);
                }
            });
        });
        observer.observe(streamlitDoc.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)

if page == "Project":
    if "last_action_success_message" in st.session_state:
        st.success(st.session_state.last_action_success_message)
        del st.session_state.last_action_success_message

    # Get the current phase name once at the top
    status_info = st.session_state.orchestrator.get_status()
    current_phase_name = status_info.get("current_phase")

    # --- CORRECTED LOGIC: Check for specific phases before checking for an active project ---
    if current_phase_name == "VIEWING_PROJECT_HISTORY":
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
            selected_id_str = st.selectbox("Select a Project ID to action:", options=[""] + [str(i) for i in history_ids])

            if selected_id_str:
                selected_id = int(selected_id_str)
                selected_project_record = next((p for p in project_history if p['history_id'] == selected_id), None)

                is_active_project = (st.session_state.orchestrator.project_id == selected_project_record['project_id'])

                col1, col2, _ = st.columns([1, 1, 4])
                with col1:
                    if st.button("📂 Load Selected Project", use_container_width=True, type="primary"):
                        with st.spinner("Loading project data and running pre-flight checks..."):
                            # Save the selected ID to session state so it's available on the next screen
                            st.session_state.selected_history_id_for_action = selected_id
                            st.session_state.orchestrator.load_archived_project(selected_id)
                            st.rerun()
                with col2:
                    delete_button = st.button("🗑️ Delete Selected Project", use_container_width=True, disabled=is_active_project, help="You cannot delete the currently active project.")

                if delete_button:
                    with st.popover("Confirm Deletion", use_container_width=True):
                        st.warning(f"**Are you sure you want to permanently delete project '{selected_project_record['project_name']}' (ID: {selected_id})?**")
                        st.error("This action cannot be undone and will delete the project history record and its associated archive files from the disk.")
                        if st.button("Yes, permanently delete this project", type="primary", use_container_width=True):
                            success, message = st.session_state.orchestrator.delete_archived_project(selected_id)
                            if success:
                                st.toast(f"✅ {message}")
                            else:
                                st.error(message)
                            time.sleep(2)
                            st.rerun()

        st.divider()
        if st.button("⬅️ Back to Main Page"):
            # Perform a hard reset to ensure a clean return to the idle state
            st.session_state.orchestrator = MasterOrchestrator(db_path=str(db_path))
            st.rerun()

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
            if status == "ALL_PASS":
                st.success(message)
                st.info("The project environment is valid and clean. You can proceed directly to the main workflow, bypassing the setup phase.")
                if st.button("▶️ Proceed to Specification Elaboration"):
                    st.session_state.orchestrator.set_phase("SPEC_ELABORATION")
                    st.rerun()
            elif status in ["PATH_NOT_FOUND", "GIT_MISSING", "ERROR"]:
                st.error(message)
                st.warning("The factory cannot proceed until this environmental issue is resolved.")
                if st.button("Go to Environment Setup to Resolve"):
                    # This is a fatal error, so we create a new project with the same name.
                    # This will cleanly guide the user through the setup flow again.
                    project_name = selected_project_record['project_name'] if selected_project_record else "New Project"
                    st.session_state.orchestrator.start_new_project(project_name)
                    st.rerun()
            elif status == "STATE_DRIFT":
                st.warning(message)
                col1, col2, _ = st.columns([1.5, 1.5, 3])
                with col1:
                    if st.button("I will resolve this manually", help="Use your own tools (e.g., git commit, git stash) to clean the repository, then load the project again from the main menu."):
                        st.session_state.orchestrator.project_id = None
                        st.session_state.orchestrator.set_phase("IDLE")
                        st.rerun()
                with col2:
                    with st.popover("Expert Option: Discard"):
                        st.markdown("⚠️ **This will permanently delete all uncommitted changes in your local repository. This cannot be undone.**")
                        if st.button("Confirm & Discard All Changes", type="primary"):
                            with st.spinner("Resetting repository and re-checking..."):
                                project_id_to_reset = st.session_state.orchestrator.project_id
                                st.session_state.orchestrator.handle_discard_changes(history_id=st.session_state.selected_history_id_for_action)
                            st.rerun()

    elif not st.session_state.orchestrator.project_id:
        st.subheader("Start a New Project")
        st.info(
            "**Note:** If another project is currently active in the factory, "
            "it will be automatically saved and archived before the new project begins."
        )
        project_name_input = st.text_input("Enter a name for your new project:")
        if st.button("Start New Project"):
            if project_name_input:
                st.session_state.orchestrator.start_new_project(project_name_input)
                st.rerun()
            else:
                st.error("Please enter a project name.")
    else:
        # This 'else' block now correctly handles all other phases for an active project.
        if current_phase_name == "ENV_SETUP_TARGET_APP":
            st.header(st.session_state.orchestrator.PHASE_DISPLAY_NAMES.get(st.session_state.orchestrator.current_phase))
            st.divider()
            agent = EnvironmentSetupAgent_AppTarget()
            agent.render()

        elif current_phase_name == "SPEC_ELABORATION":
            st.header("Phase 1: Application Specification")
            if 'spec_draft' not in st.session_state:
                st.session_state.spec_draft = None
            if 'spec_step' not in st.session_state:
                st.session_state.spec_step = 'initial_input'
            if 'ai_issues' not in st.session_state:
                st.session_state.ai_issues = None
            if st.session_state.spec_draft is None:
                st.markdown("Please provide the initial specification for your target application.")
                tab1, tab2 = st.tabs(["Upload Specification Documents", "Enter Brief Description"])
                with tab1:
                    uploaded_files = st.file_uploader("Upload Docs", type=["txt", "md", "docx"], accept_multiple_files=True, label_visibility="collapsed")
                    if st.button("Process Uploaded Documents"):
                        if uploaded_files:
                            bootstrap_agent = ProjectBootstrapAgent()
                            extracted_text, messages, size_error = bootstrap_agent.extract_text_from_files(uploaded_files)
                            for msg in messages:
                                st.warning(msg)
                            if size_error:
                                st.error(size_error)
                            elif extracted_text:
                                st.session_state.spec_draft = extracted_text
                                st.session_state.spec_step = 'pm_feedback'
                                st.rerun()
                with tab2:
                    brief_desc_input = st.text_area("Brief Description", height=150, key="brief_desc")
                    if st.button("Process Brief Description"):
                        if brief_desc_input:
                            with st.spinner("AI is expanding the description into a draft specification..."):
                                with st.session_state.orchestrator.db_manager as db:
                                    api_key = db.get_config_value("LLM_API_KEY")
                                agent = SpecClarificationAgent(api_key=api_key, db_manager=st.session_state.orchestrator.db_manager)
                                expanded_text = agent.expand_brief_description(brief_desc_input)
                                st.session_state.spec_draft = expanded_text
                                st.session_state.spec_step = 'pm_feedback'
                                st.rerun()
            elif st.session_state.spec_step == 'pm_feedback':
                st.subheader("Draft Specification - Your Review")
                st.markdown("Please review the initial draft. Provide any corrections, additions, or feedback in the text area below.")
                st.text_area("Current Draft:", value=st.session_state.spec_draft, height=300, key="spec_draft_display", disabled=True)
                pm_feedback_text = st.text_area("Your Feedback and Corrections:", height=200)
                col1, col2, _ = st.columns([1.5, 2.5, 3])
                with col1:
                    if st.button("Submit Feedback & Refine Draft", use_container_width=True):
                        if pm_feedback_text.strip():
                            with st.spinner("AI is refining the draft with your feedback..."):
                                with st.session_state.orchestrator.db_manager as db:
                                    api_key = db.get_config_value("LLM_API_KEY")
                                agent = SpecClarificationAgent(api_key=api_key, db_manager=st.session_state.orchestrator.db_manager)
                                refined_draft = agent.refine_specification(st.session_state.spec_draft, "PM initial review feedback.", pm_feedback_text)
                                st.session_state.spec_draft = refined_draft
                                st.session_state.spec_step = 'pm_review_refined'
                                st.rerun()
                        else:
                            st.warning("Please provide feedback to refine the draft.")
                with col2:
                    if st.button("✅ Approve & Proceed to AI Analysis", use_container_width=True, type="primary"):
                        with st.spinner("AI is checking the draft for ambiguities..."):
                            with st.session_state.orchestrator.db_manager as db:
                                api_key = db.get_config_value("LLM_API_KEY")
                            agent = SpecClarificationAgent(api_key=api_key, db_manager=st.session_state.orchestrator.db_manager)
                            issues = agent.identify_potential_issues(st.session_state.spec_draft)
                            st.session_state.ai_issues = issues
                            st.session_state.spec_step = 'ai_clarification'
                            st.rerun()
            elif st.session_state.spec_step == 'pm_review_refined':
                st.subheader("Refined Draft - Your Review")
                st.markdown("The draft has been updated with your feedback. Please review the changes below.")
                st.text_area("Refined Draft:", value=st.session_state.spec_draft, height=300, key="spec_draft_display_refined", disabled=True)
                st.info("You can now either run the AI's ambiguity analysis on this version or provide another round of feedback.")
                col1, col2, _ = st.columns([1.5, 1.5, 3])
                with col1:
                    if st.button("✅ Approve & Proceed to your Review", type="primary", use_container_width=True):
                        with st.spinner("AI is checking the refined draft for ambiguities..."):
                            with st.session_state.orchestrator.db_manager as db:
                                api_key = db.get_config_value("LLM_API_KEY")
                            agent = SpecClarificationAgent(api_key=api_key, db_manager=st.session_state.orchestrator.db_manager)
                            issues = agent.identify_potential_issues(st.session_state.spec_draft)
                            st.session_state.ai_issues = issues
                            st.session_state.spec_step = 'ai_clarification'
                            st.rerun()
                with col2:
                    if st.button("✍️ I Have More Feedback", use_container_width=True):
                        st.session_state.spec_step = 'pm_feedback'
                        st.rerun()
            elif st.session_state.spec_step == 'ai_clarification':
                st.subheader("Specification Refinement - AI Analysis")
                st.text_area("Current Draft:", value=st.session_state.spec_draft, height=300, key="spec_draft_display_2", disabled=True)
                st.divider()
                st.markdown("**AI Analysis Results:**")
                st.info(st.session_state.ai_issues)
                st.markdown("You can now provide clarifications to the AI's points below, or approve the specification if you are satisfied.")
                clarification_text = st.text_area("Your Clarifications:", height=150, key="pm_clarification_text")
                col1, col2, _ = st.columns([1.5, 2, 3])
                with col1:
                    if st.button("Submit Clarifications", use_container_width=True):
                        if clarification_text.strip():
                            with st.spinner("AI is refining the draft and re-analyzing..."):
                                with st.session_state.orchestrator.db_manager as db:
                                    api_key = db.get_config_value("LLM_API_KEY")
                                agent = SpecClarificationAgent(api_key=api_key, db_manager=st.session_state.orchestrator.db_manager)
                                st.session_state.orchestrator.capture_spec_clarification_learning(
                                    problem_context=st.session_state.ai_issues,
                                    solution_text=clarification_text,
                                    spec_text=st.session_state.spec_draft
                                )
                                refined_draft = agent.refine_specification(st.session_state.spec_draft, st.session_state.ai_issues, clarification_text)
                                st.session_state.spec_draft = refined_draft
                                issues = agent.identify_potential_issues(st.session_state.spec_draft)
                                st.session_state.ai_issues = issues
                                st.rerun()
                        else:
                            st.warning("Please enter your clarifications before submitting.")
                with col2:
                    if st.button("✅ Approve Specification and Proceed", type="primary", use_container_width=True):
                        with st.spinner("Finalizing and saving specification..."):
                            with st.session_state.orchestrator.db_manager as db:
                                db.save_final_specification(st.session_state.orchestrator.project_id, st.session_state.spec_draft)
                            st.session_state.orchestrator.set_phase("TECHNICAL_SPECIFICATION")
                            keys_to_clear = ['spec_draft', 'spec_step', 'ai_issues', 'brief_desc', 'pm_clarification_text']
                            for key in keys_to_clear:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()

        elif current_phase_name == "TECHNICAL_SPECIFICATION":
            st.header(st.session_state.orchestrator.PHASE_DISPLAY_NAMES.get(st.session_state.orchestrator.current_phase))
            if 'tech_spec_step' not in st.session_state:
                st.session_state.tech_spec_step = 'initial_choice'
            if 'tech_spec_draft' not in st.session_state:
                st.session_state.tech_spec_draft = ""
            if 'target_os' not in st.session_state:
                st.session_state.target_os = "Linux"
            if st.session_state.tech_spec_step == 'initial_choice':
                st.markdown("First, select the target Operating System for the application.")
                st.session_state.target_os = st.selectbox(
                    "Select Target Operating System:",
                    ["Linux", "Windows", "macOS"],
                    index=["Linux", "Windows", "macOS"].index(st.session_state.target_os)
                )
                st.divider()
                st.markdown("Next, choose how you would like to create the Technical Specification document.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🤖 Let ASDF Propose a Tech Stack", use_container_width=True, type="primary"):
                        with st.spinner("AI is analyzing the specification and generating a proposal..."):
                            try:
                                with st.session_state.orchestrator.db_manager as db:
                                    api_key = db.get_config_value("LLM_API_KEY")
                                    project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                                    final_spec_text = project_details['final_spec_text']
                                if not api_key: st.error("Cannot generate proposal. LLM API Key is not set.")
                                else:
                                    from agents.agent_tech_stack_proposal import TechStackProposalAgent
                                    agent = TechStackProposalAgent(api_key=api_key)
                                    proposal = agent.propose_stack(final_spec_text, st.session_state.target_os)
                                    st.session_state.tech_spec_draft = proposal
                                    st.session_state.tech_spec_step = 'pm_review'
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Failed to generate proposal: {e}")
                with col2:
                    if st.button("✍️ Set Technology Choices/Guidelines", use_container_width=True):
                        st.session_state.tech_spec_step = 'pm_define'
                        st.rerun()

            elif st.session_state.tech_spec_step == 'pm_define':
                st.subheader("Define Technical Specification")
                st.markdown("Please provide your key technology choices or guidelines below (e.g., 'Use Python with a Flask backend and a SQLite database'). The ASDF will use your input to generate the full technical specification document.")
                st.session_state.tech_spec_draft = st.text_area(
                    "Your Technology Guidelines:",
                    value=st.session_state.tech_spec_draft,
                    height=200
                )
                if st.button("Generate Full Specification from My Input", type="primary"):
                    if st.session_state.tech_spec_draft.strip():
                        with st.spinner("AI is expanding your input into a full technical specification..."):
                            try:
                                with st.session_state.orchestrator.db_manager as db:
                                    api_key = db.get_config_value("LLM_API_KEY")
                                    project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                                    context = (
                                        f"{project_details['final_spec_text']}\n\n"
                                        f"--- PM Directive for Technology Stack ---\n{st.session_state.tech_spec_draft}"
                                    )
                                if not api_key:
                                    st.error("Cannot generate proposal. LLM API Key is not set.")
                                else:
                                    from agents.agent_tech_stack_proposal import TechStackProposalAgent
                                    agent = TechStackProposalAgent(api_key=api_key)
                                    proposal = agent.propose_stack(context, st.session_state.target_os)
                                    st.session_state.tech_spec_draft = proposal
                                    st.session_state.tech_spec_step = 'pm_review'
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Failed to generate specification from your input: {e}")
                    else:
                        st.warning("Please provide your technology guidelines before generating the specification.")

            elif st.session_state.tech_spec_step == 'pm_review':
                st.subheader("Review Technical Specification")
                st.markdown("Please review the draft below. You can either approve it or provide feedback for refinement.")
                st.text_area(
                    "Technical Specification Draft",
                    value=st.session_state.tech_spec_draft,
                    height=400,
                    key="tech_spec_draft_display",
                    disabled=False
                )
                feedback_text = st.text_area("Your Feedback and Refinements:", height=150)
                col1, col2, _ = st.columns([1.5, 2, 3])
                with col1:
                    if st.button("Submit Feedback & Refine", use_container_width=True):
                        if feedback_text.strip():
                            with st.spinner("AI is refining the proposal based on your feedback..."):
                                try:
                                    with st.session_state.orchestrator.db_manager as db:
                                        api_key = db.get_config_value("LLM_API_KEY")
                                        project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                                        context = (
                                            f"{project_details['final_spec_text']}\n\n"
                                            f"--- Current Draft to Refine ---\n{st.session_state.tech_spec_draft}\n\n"
                                            f"--- PM Feedback for Refinement ---\n{feedback_text}"
                                        )
                                    if not api_key: st.error("Cannot generate proposal. LLM API Key is not set.")
                                    else:
                                        from agents.agent_tech_stack_proposal import TechStackProposalAgent
                                        agent = TechStackProposalAgent(api_key=api_key)
                                        proposal = agent.propose_stack(context, st.session_state.target_os)
                                        st.session_state.tech_spec_draft = proposal
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to generate proposal: {e}")
                        else:
                            st.warning("Please enter feedback before submitting for refinement.")
                with col2:
                    is_disabled = not st.session_state.tech_spec_draft.strip()
                    if st.button("✅ Approve Specification", use_container_width=True, type="primary", disabled=is_disabled):
                        with st.spinner("Saving technical specification and extracting primary technology..."):
                            with st.session_state.orchestrator.db_manager as db:
                                db.update_project_os(st.session_state.orchestrator.project_id, st.session_state.target_os)
                                db.save_tech_specification(st.session_state.orchestrator.project_id, st.session_state.tech_spec_draft)
                            st.session_state.orchestrator._extract_and_save_primary_technology(st.session_state.tech_spec_draft)
                        st.session_state.orchestrator.set_phase("BUILD_SCRIPT_SETUP")
                        keys_to_clear = ['tech_spec_draft', 'target_os', 'tech_spec_step']
                        for key in keys_to_clear:
                                if key in st.session_state:
                                    del st.session_state[key]
                        st.rerun()

        elif current_phase_name == "BUILD_SCRIPT_SETUP":
            st.header(st.session_state.orchestrator.PHASE_DISPLAY_NAMES.get(st.session_state.orchestrator.current_phase))
            st.markdown("The technical specification is complete. Now, let's establish the build script for the project.")
            st.info("This script (e.g., `requirements.txt`, `pom.xml`) manages project dependencies and how the application is built.")
            with st.session_state.orchestrator.db_manager as db:
                api_key = db.get_config_value("LLM_API_KEY")
                project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                tech_spec_text = project_details['tech_spec_text']
                target_os = project_details['target_os']
            if not target_os:
                st.error("Cannot proceed: Target OS has not been set in the previous step.")
            else:
                st.write(f"Generating options for Target OS: **{target_os}**")
                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🤖 Auto-Generate Build Script", use_container_width=True, type="primary"):
                        with st.spinner(f"Generating standard build script for the specified tech stack..."):
                            try:
                                if not api_key:
                                    st.error("Cannot generate script: LLM API Key is not set.")
                                else:
                                    from agents.agent_build_script_generator import BuildScriptGeneratorAgent
                                    agent = BuildScriptGeneratorAgent(api_key=api_key)
                                    script_info = agent.generate_script(tech_spec_text, target_os)
                                    if script_info:
                                        filename, content = script_info
                                        project_root = Path(project_details['project_root_folder'])
                                        (project_root / filename).write_text(content, encoding='utf-8')
                                        with st.session_state.orchestrator.db_manager as db:
                                            db.update_project_build_automation_status(st.session_state.orchestrator.project_id, True)
                                        st.success(f"Generated and saved `{filename}` to the project root.")
                                        time.sleep(2)
                                        st.session_state.orchestrator.set_phase("TEST_ENVIRONMENT_SETUP")
                                        st.rerun()
                                    else:
                                        st.error(f"The AI was unable to generate a build script. Please proceed manually.")
                            except Exception as e:
                                st.error(f"An error occurred during build script generation: {e}")
                with col2:
                    if st.button("✍️ I Will Create it Manually", use_container_width=True):
                        with st.session_state.orchestrator.db_manager as db:
                            db.update_project_build_automation_status(st.session_state.orchestrator.project_id, False)
                        st.info("Acknowledged. You will be responsible for the project's build script.")
                        time.sleep(2)
                        st.session_state.orchestrator.set_phase("TEST_ENVIRONMENT_SETUP")
                        st.rerun()

        elif current_phase_name == "TEST_ENVIRONMENT_SETUP":
            st.header(st.session_state.orchestrator.PHASE_DISPLAY_NAMES.get(st.session_state.orchestrator.current_phase))
            st.markdown("Please follow the steps below to set up the necessary testing frameworks for your project's technology stack.")
            if 'setup_tasks' not in st.session_state:
                with st.spinner("Analyzing technical spec to generate setup steps..."):
                    st.session_state.setup_tasks = st.session_state.orchestrator.start_test_environment_setup()
                    st.session_state.current_setup_step = 0
                    st.session_state.setup_help_text = None
            tasks = st.session_state.setup_tasks
            if tasks is None:
                st.error("Could not generate setup tasks. Please check the logs and ensure the technical specification is complete.")
            elif st.session_state.current_setup_step >= len(tasks):
                st.success("All setup steps have been actioned.")
                st.markdown("Please confirm the final command that should be used to run all automated tests for this project.")
                with st.session_state.orchestrator.db_manager as db:
                     project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                     tech_spec_text = project_details['tech_spec_text']
                if 'suggested_test_command' not in st.session_state:
                    from agents.agent_verification_app_target import VerificationAgent_AppTarget # Local import
                    with st.session_state.orchestrator.db_manager as db:
                        api_key = db.get_config_value("LLM_API_KEY")
                    if api_key and tech_spec_text:
                        agent = VerificationAgent_AppTarget(api_key)
                        details = agent._get_test_execution_details(tech_spec_text)
                        st.session_state.suggested_test_command = details.get("command") if details else "pytest"
                    else:
                        st.session_state.suggested_test_command = "pytest"
                confirmed_command = st.text_input(
                    "Test Execution Command:",
                    value=st.session_state.suggested_test_command
                )
                if st.button("Finalize Test Environment Setup", type="primary"):
                    if confirmed_command.strip():
                        if st.session_state.orchestrator.finalize_test_environment_setup(confirmed_command):
                            keys_to_clear = ['setup_tasks', 'current_setup_step', 'setup_help_text', 'suggested_test_command']
                            for key in keys_to_clear:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()
                        else:
                            st.error("Failed to finalize setup. Please check the logs.")
                    else:
                        st.warning("The test execution command cannot be empty.")
            else:
                current_step_index = st.session_state.current_setup_step
                task = tasks[current_step_index]
                st.subheader(f"Step {current_step_index + 1} of {len(tasks)}: {task.get('tool_name', 'Unnamed Step')}")
                st.markdown(task.get('instructions', 'No instructions provided.'))
                if st.session_state.setup_help_text:
                    with st.chat_message("assistant", avatar="❓"):
                        st.info(st.session_state.setup_help_text)
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Done, Next Step", use_container_width=True, type="primary"):
                        st.session_state.current_setup_step += 1
                        st.session_state.setup_help_text = None # Clear help text when moving on
                        st.rerun()
                with col2:
                    if st.button("❓ I Need Help", use_container_width=True):
                        with st.spinner("Getting more details..."):
                            st.session_state.setup_help_text = st.session_state.orchestrator.get_help_for_setup_task(task.get('instructions', ''))
                        st.rerun()
                with col3:
                    if st.button("⚠️ Ignore & Continue", use_container_width=True):
                        task = st.session_state.setup_tasks[st.session_state.current_setup_step]
                        st.session_state.orchestrator.handle_ignore_setup_task(task)
                        st.session_state.current_setup_step += 1
                        st.session_state.setup_help_text = None
                        st.rerun()

        elif current_phase_name == "CODING_STANDARD_GENERATION":
            st.header("Phase 2.A: Coding Standard Generation")
            if 'coding_standard_step' not in st.session_state:
                st.session_state.coding_standard_step = 'initial'
            if 'coding_standard_draft' not in st.session_state:
                st.session_state.coding_standard_draft = ""
            if st.session_state.coding_standard_step == 'initial':
                st.markdown("Generate a project-specific coding standard based on the technical specification. This standard will be enforced by all code-generating agents.")
                if st.button("Generate Coding Standard Draft", type="primary"):
                    with st.spinner("AI is generating the coding standard..."):
                        try:
                            with st.session_state.orchestrator.db_manager as db:
                                api_key = db.get_config_value("LLM_API_KEY")
                                project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                                tech_spec = project_details['tech_spec_text']
                            if not api_key or not tech_spec:
                                st.error("Cannot generate standard: Missing API Key or Technical Specification.")
                            else:
                                from agents.agent_coding_standard_app_target import CodingStandardAgent_AppTarget
                                agent = CodingStandardAgent_AppTarget(api_key=api_key)
                                standard = agent.generate_standard(tech_spec)
                                st.session_state.coding_standard_draft = standard
                                st.session_state.coding_standard_step = 'pm_review' # Move to review step
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to generate coding standard: {e}")
            elif st.session_state.coding_standard_step == 'pm_review':
                st.subheader("Review Coding Standard")
                st.markdown("Please review the draft below. You can either approve it or provide feedback for refinement.")
                st.text_area(
                    "Coding Standard Draft",
                    value=st.session_state.coding_standard_draft,
                    height=400,
                    key="coding_standard_display",
                    disabled=True
                )
                feedback_text = st.text_area("Your Feedback and Refinements:", height=150)
                col1, col2, _ = st.columns([1.5, 2, 3])
                with col1:
                    if st.button("Submit Feedback & Refine", use_container_width=True):
                        if feedback_text.strip():
                            st.warning("Feedback refinement for the Coding Standard is not yet implemented.")
                        else:
                            st.warning("Please enter feedback before submitting for refinement.")
                with col2:
                    is_disabled = not st.session_state.coding_standard_draft.strip()
                    if st.button("✅ Approve Coding Standard", use_container_width=True, type="primary", disabled=is_disabled):
                        with st.spinner("Saving coding standard..."):
                            with st.session_state.orchestrator.db_manager as db:
                                db.save_coding_standard(
                                    st.session_state.orchestrator.project_id,
                                    st.session_state.coding_standard_draft
                                )
                            st.session_state.orchestrator.set_phase("PLANNING")
                            keys_to_clear = ['coding_standard_draft', 'coding_standard_step']
                            for key in keys_to_clear:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()

        elif current_phase_name == "PLANNING":
            st.header("Phase 2: Strategic Development Planning")
            if 'development_plan' not in st.session_state:
                st.session_state.development_plan = None
            if st.session_state.development_plan:
                st.subheader("Generated Development Plan")
                st.markdown("Please review the generated plan. To proceed, approve it below. To generate a new version, click the 'Re-generate' button.")
                st.json(st.session_state.development_plan)
                st.divider()
                col1, col2, col3 = st.columns([1.5, 1, 1.5])
                with col1:
                    if st.button("✅ Approve Plan & Proceed to Development", type="primary"):
                        with st.spinner("Saving plan and transitioning to development phase..."):
                            full_plan_object_str = st.session_state.development_plan
                            with st.session_state.orchestrator.db_manager as db:
                                db.save_development_plan(st.session_state.orchestrator.project_id, full_plan_object_str)
                            try:
                                with st.session_state.orchestrator.db_manager as db:
                                    project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                                    if not project_details or not project_details['technology_stack']:
                                        st.error("Validation Failed: A target technology stack has not been set for this project. Please reload the project and complete the Technical Specification phase.")
                                        st.stop() # Halt execution
                                full_plan_data = json.loads(full_plan_object_str)
                                dev_plan_list = full_plan_data.get("development_plan")
                                if dev_plan_list is not None:
                                    st.session_state.orchestrator.load_development_plan(json.dumps(dev_plan_list))
                                    st.session_state.orchestrator.set_phase("GENESIS")
                                    keys_to_clear = ['development_plan']
                                    for key in keys_to_clear:
                                        if key in st.session_state:
                                            del st.session_state[key]
                                    st.toast("Plan approved! Starting development...")
                                    st.rerun()
                                else:
                                    st.error("The generated plan is missing the 'development_plan' key.")
                            except json.JSONDecodeError:
                                st.error("Failed to parse the development plan. The format is invalid.")
                with col2:
                    report_generator = ReportGeneratorAgent()
                    dev_plan_docx_bytes = report_generator.generate_text_document_docx(
                        title=f"Sequential Development Plan - {st.session_state.orchestrator.project_name}",
                        content=st.session_state.development_plan,
                        is_code=True
                    )
                    st.download_button(
                        label="📄 Print to .docx",
                        data=dev_plan_docx_bytes,
                        file_name=f"Development_Plan_{st.session_state.orchestrator.project_id}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                with col3:
                    if st.button("🔄 Re-generate Development Plan"):
                         st.session_state.development_plan = None
                         st.rerun()
            else:
                st.info("Click the button below to generate a detailed, sequential development plan based on the finalized specifications.")
                if st.button("Generate Development Plan", type="primary"):
                    with st.spinner("AI is generating the development plan... This may take a few moments."):
                        try:
                            with st.session_state.orchestrator.db_manager as db:
                                api_key = db.get_config_value("LLM_API_KEY")
                                project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                                final_spec = project_details['final_spec_text']
                                tech_spec = project_details['tech_spec_text']
                            if not all([api_key, final_spec, tech_spec]):
                                st.error("Could not generate plan: Missing API Key, Final Specification, or Technical Specification.")
                            else:
                                agent = PlanningAgent_AppTarget(api_key=api_key)
                                response_json_str = agent.generate_development_plan(final_spec, tech_spec)
                                response_data = json.loads(response_json_str)
                                if "error" in response_data:
                                    st.error(f"Failed to generate plan: {response_data['error']}")
                                else:
                                    plan_data = response_data.get("development_plan")
                                    main_executable = response_data.get("main_executable_file")
                                    if not plan_data or not main_executable:
                                        st.error("Failed to generate a valid plan and executable name from the AI.")
                                    else:
                                        with st.session_state.orchestrator.db_manager as db:
                                            db.update_project_apex_file(st.session_state.orchestrator.project_id, main_executable)
                                        st.session_state.development_plan = json.dumps(response_data, indent=4)
                                        st.rerun()
                        except Exception as e:
                            st.error(f"An unexpected error occurred: {e}")

        elif current_phase_name == "GENESIS":
            st.header("Phase 3: Iterative Component Development")
            if not st.session_state.orchestrator.active_plan:
                st.warning("No active development plan is loaded.")
                st.info("Please go to the 'Planning' phase to generate a development plan.")
                if st.button("⬅️ Go to Planning Phase"):
                    st.session_state.orchestrator.set_phase("PLANNING")
                    st.rerun()
            else:
                st.subheader("PM Checkpoint")
                task = st.session_state.orchestrator.get_current_task_details()
                total_tasks = len(st.session_state.orchestrator.active_plan)
                cursor = st.session_state.orchestrator.active_plan_cursor
                if task:
                    st.progress(cursor / total_tasks, text=f"Executing Task {cursor + 1} of {total_tasks}")
                    st.info(f"""
                    Next component in the plan is: **'{task.get('component_name')}'** (based on micro-spec `{task.get('micro_spec_id')}`).
                    How would you like to proceed?
                    """)
                else:
                    st.success(f"All {total_tasks} development tasks are complete.")
                    st.info("Click 'Proceed' to finalize development and begin the Integration & Validation phase.")
                col1, col2, _ = st.columns([1.5, 1.5, 3])
                with col1:
                    if st.button("▶️ Proceed", use_container_width=True, type="primary"):
                        with st.status("Executing next development step...", expanded=True) as status:
                            st.session_state.orchestrator.handle_proceed_action(status_ui_object=status)
                            status.update(label="Step completed successfully!", state="complete", expanded=False)
                        st.rerun()
                with col2:
                    if st.button("⏹️ Stop & Export", use_container_width=True):
                        st.session_state.show_export_confirmation = True
                        st.rerun()

        elif current_phase_name == "AWAITING_INTEGRATION_CONFIRMATION":
            st.header("Integration Warning")
            st.warning(
                "**The development phase is complete, but one or more components have known issues or failed their unit tests.**"
            )
            st.markdown(
                "Proceeding with integration may result in an unstable or non-functional build. It is recommended to fix these issues before continuing."
            )
            issues = st.session_state.orchestrator.task_awaiting_approval.get("known_issues", [])
            if issues:
                st.subheader("Components with Known Issues:")
                for issue in issues:
                    st.error(f"- **{issue.get('artifact_name')}** (Status: {issue.get('status')})")
            st.divider()
            st.markdown("Do you want to proceed with integration anyway?")
            col1, col2, _ = st.columns([1.5, 2, 3])
            with col1:
                if st.button("✅ Yes, Proceed to Integration", type="primary"):
                    st.session_state.orchestrator.task_awaiting_approval = None
                    st.session_state.orchestrator._run_integration_and_ui_testing_phase()
                    st.rerun()
            with col2:
                if st.button("❌ No, Return to Development"):
                    st.session_state.orchestrator.task_awaiting_approval = None
                    st.session_state.orchestrator.set_phase("GENESIS")
                    st.rerun()

        elif current_phase_name == "MANUAL_UI_TESTING":
            st.header("Phase 4: Manual UI Testing")
            st.info(
                "The automated integration and build were successful. "
                "The UI Test Plan has been generated based on the project specification."
            )
            st.markdown(
                "**Your action is required:**\n\n"
                "1.  Navigate to the **Documents** page from the sidebar.\n"
                "2.  Download the **UI Test Plan** document.\n"
                "3.  Execute the tests as described and fill in the results.\n"
                "4.  Upload the completed document below to trigger the evaluation."
            )
            st.divider()
            uploaded_file = st.file_uploader(
                "Upload Completed UI Test Plan Results",
                type=['txt', 'md', 'docx']
            )
            if uploaded_file is not None:
                if st.button("Process Test Results", type="primary"):
                    with st.spinner("Reading and evaluating test results..."):
                        content = ""
                        try:
                            if uploaded_file.name.endswith('.docx'):
                                import docx
                                doc = docx.Document(uploaded_file)
                                content = "\n".join([p.text for p in doc.paragraphs])
                            else: # For .txt and .md files
                                content = uploaded_file.getvalue().decode("utf-8")
                            st.session_state.orchestrator.handle_ui_test_result_upload(content)
                            st.success("Test results submitted for evaluation. The system will now process any failures.")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to process file: {e}")
            st.divider()
            st.markdown("If all tests have passed and been fixed, you can proceed.")
            if st.button("Complete Project and Return to Idle"):
                st.session_state.orchestrator.set_phase("IDLE")
                st.toast("Project phase complete!")
                st.rerun()

        elif current_phase_name == "AWAITING_INTEGRATION_RESOLUTION":
            st.header("Phase 5: Integration & Verification Failed")
            st.error("The automated integration and verification process could not be completed due to a system-level or environment error.")
            if st.session_state.orchestrator.task_awaiting_approval:
                failure_reason = st.session_state.orchestrator.task_awaiting_approval.get("failure_reason", "No specific reason was provided.")
                st.markdown("**Failure Details:**")
                st.code(failure_reason, language='text')
            st.warning("This is often caused by a missing testing framework (like 'pytest') in your environment or a configuration issue. You cannot re-run the automated test, but you can acknowledge the failure and proceed to manual UI testing.")
            if st.button("Acknowledge Failure & Proceed to Manual UI Testing", type="primary", use_container_width=True):
                st.session_state.orchestrator.handle_acknowledge_integration_failure()
                st.rerun()

        elif current_phase_name == "AWAITING_PM_TRIAGE_INPUT":
            st.header("Phase 5: Interactive Debugging Triage")
            st.warning(
                "**Action Required:** The automated triage system could not determine the "
                "root cause of the last failure from the available logs."
            )
            st.markdown(
                "Please describe the failure in as much detail as possible below. "
                "This description will be used to generate a fix."
            )
            st.divider()
            if 'pm_triage_input' not in st.session_state:
                st.session_state.pm_triage_input = ""
            pm_error_description = st.text_area(
                "Manual Error Description:",
                height=200,
                key="pm_triage_input"
            )
            col1, col2, _ = st.columns([1.5, 2, 3])
            with col1:
                if st.button("Submit Description for Analysis", type="primary"):
                    if pm_error_description.strip():
                        with st.spinner("Submitting your description for analysis..."):
                            st.session_state.orchestrator.handle_pm_triage_input(pm_error_description)
                        st.toast("Description submitted. The factory will now attempt to plan a fix.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Please provide a description of the error before submitting.")
            with col2:
                if st.button("Cancel and Return to Checkpoint"):
                    st.session_state.orchestrator.set_phase("GENESIS")
                    st.toast("Returning to the main development checkpoint.")
                    st.rerun()

        elif current_phase_name == "DEBUG_PM_ESCALATION":
            st.header("Phase 5: Debug Escalation")
            st.error(
                "**Action Required:** The factory has been unable to automatically fix a persistent bug after multiple attempts."
            )
            if st.session_state.orchestrator.task_awaiting_approval:
                failure_context = st.session_state.orchestrator.task_awaiting_approval.get("failure_log", "No specific failure log was captured.")
                with st.expander("Click to view failure details"):
                    st.code(failure_context, language='text')
            st.markdown(
                "Please choose how you would like to proceed. Your selection will determine the next steps for the factory."
            )
            st.divider()
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Retry Automated Fix", use_container_width=True, help="This will reset the counter and run the entire triage and fix pipeline again from a clean state."):
                    st.session_state.orchestrator.handle_pm_debug_choice("RETRY")
                    st.rerun()
            with col2:
                if st.button("⏸️ Pause for Manual Fix", use_container_width=True, help="This will pause the factory, allowing you to manually investigate and fix the code in your own editor."):
                    st.session_state.orchestrator.handle_pm_debug_choice("MANUAL_PAUSE")
                    st.success("Project paused. You can now manually edit the code. The factory will remain idle.")
                    st.rerun()
            with col3:
                if st.button("🚫 Ignore Bug & Proceed", use_container_width=True, help="Acknowledge the bug but proceed with the next task in the development plan. The bug will be noted but not fixed now."):
                    st.session_state.orchestrator.handle_pm_debug_choice("IGNORE")
                    st.toast("Bug ignored. Proceeding with the next development task.")
                    st.rerun()

        elif current_phase_name == "INTEGRATION_AND_VERIFICATION":
            st.header("Phase 3.5: Automated Integration & Verification")
            st.info("The factory is now integrating all newly developed components, performing a full system build, and running verification tests.")
            with st.spinner("Running automated integration... This may take a moment."):
                st.session_state.orchestrator._run_integration_and_verification_phase()
            st.success("Integration and verification process complete.")
            time.sleep(2) # Pause for 2 seconds to allow the user to read the message
            st.rerun()

        elif current_phase_name == "AWAITING_PM_DECLARATIVE_CHECKPOINT":
            st.header("PM Checkpoint: High-Risk Change Detected")
            st.warning("The development plan requires a modification to a declarative file (e.g., build script, database schema, config file). Please review the proposed change below.")
            task = st.session_state.orchestrator.task_awaiting_approval
            if task:
                st.markdown(f"**File to Modify:** `{task.get('component_file_path')}`")
                st.markdown(f"**Component:** `{task.get('component_name')}`")
                st.subheader("Proposed Change Snippet")
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

        elif current_phase_name == "RAISING_CHANGE_REQUEST":
            st.header("Phase 6: Raise New Change Request")
            st.info("First, select the type of change you are requesting.")
            if 'cr_type' not in st.session_state:
                st.session_state.cr_type = "Functional Enhancement"
            if 'cr_description' not in st.session_state:
                st.session_state.cr_description = ""
            if 'spec_correction_text' not in st.session_state:
                st.session_state.spec_correction_text = ""
            st.session_state.cr_type = st.radio(
                "Select Change Request Type:",
                ["Functional Enhancement", "Specification Correction"],
                horizontal=True,
                key="cr_type_radio"
            )
            st.divider()
            if st.session_state.cr_type == "Functional Enhancement":
                st.markdown("Please provide a detailed description of the new feature or change in functionality.")
                st.session_state.cr_description = st.text_area(
                    "Change Request Description:",
                    value=st.session_state.cr_description,
                    height=250
                )
                if st.button("Save Change Request", type="primary"):
                    if st.session_state.cr_description.strip():
                        st.session_state.orchestrator.save_new_change_request(st.session_state.cr_description, "CHANGE_REQUEST")
                        st.rerun()
                    else:
                        st.warning("The description cannot be empty.")
            elif st.session_state.cr_type == "Specification Correction":
                st.markdown("Paste the **full, corrected text** of the specification below. The system will analyze the differences to create a linked implementation plan.")
                if not st.session_state.spec_correction_text:
                     with st.session_state.orchestrator.db_manager as db:
                        project_docs = db.get_project_by_id(st.session_state.orchestrator.project_id)
                        st.session_state.spec_correction_text = project_docs['final_spec_text'] if project_docs else ""
                st.session_state.spec_correction_text = st.text_area(
                    "Full Corrected Specification Text:",
                    value=st.session_state.spec_correction_text,
                    height=400
                )
                if st.button("Save Specification Change", type="primary"):
                    if st.session_state.spec_correction_text.strip():
                        st.session_state.orchestrator.save_spec_correction_cr(st.session_state.spec_correction_text)
                        st.rerun()
                    else:
                        st.warning("The specification text cannot be empty.")
            st.divider()
            if st.button("Cancel"):
                st.session_state.orchestrator.set_phase("GENESIS")
                st.rerun()

        elif current_phase_name == "AWAITING_INITIAL_IMPACT_ANALYSIS":
            st.header("Phase 6: New Change Request Logged")
            st.success("The new Change Request has been saved to the register.")
            st.markdown("Would you like to perform a high-level impact analysis on this new CR now?")
            try:
                latest_cr_id = st.session_state.orchestrator.get_all_change_requests()[0]['cr_id']
            except (IndexError, TypeError):
                st.error("Could not retrieve the newly created Change Request. Returning to checkpoint.")
                if st.button("Back to Checkpoint"):
                    st.session_state.orchestrator.set_phase("GENESIS")
                    st.rerun()
                st.stop()
            col1, col2, _ = st.columns([1, 1, 5])
            with col1:
                if st.button("Yes, Run Analysis", type="primary", use_container_width=True):
                    with st.spinner(f"Running impact analysis for CR-{latest_cr_id}..."):
                        st.session_state.orchestrator.handle_run_impact_analysis_action(latest_cr_id)
                    st.toast(f"Impact analysis complete for CR-{latest_cr_id}.")
                    st.session_state.orchestrator.set_phase("GENESIS")
                    st.rerun()
            with col2:
                if st.button("No, Later", use_container_width=True):
                    st.toast("Acknowledged. You can run the analysis later from the CR Register.")
                    st.session_state.orchestrator.set_phase("GENESIS")
                    st.rerun()

        elif current_phase_name == "IMPLEMENTING_CHANGE_REQUEST":
            st.header("Phase 6: Implement Requested Change")
            st.markdown("Select a Change Request from the register below to view available actions.")
            change_requests = st.session_state.orchestrator.get_all_change_requests()
            if not change_requests:
                st.warning("There are no change requests in the register for this project.")
            else:
                cr_data_for_df = []
                for cr in change_requests:
                    cr_data_for_df.append({
                        "ID": cr['cr_id'],
                        "Type": cr['request_type'].replace('_', ' ').title(),
                        "Status": cr['status'],
                        "Severity/Impact": cr['impact_rating'],
                        "Description": cr['description'],
                        "Analysis Summary": cr['impact_analysis_details']
                    })
                df = pd.DataFrame(cr_data_for_df)
                column_order = ["ID", "Type", "Status", "Severity/Impact", "Description", "Analysis Summary"]
                st.dataframe(df[column_order], use_container_width=True, hide_index=True)
                cr_ids = [cr['cr_id'] for cr in change_requests]
                selected_cr_id_str = st.selectbox("Select a Change Request ID to action:", options=[""] + [str(i) for i in cr_ids])
                if selected_cr_id_str:
                    selected_cr_id = int(selected_cr_id_str)
                    selected_cr = next((cr for cr in change_requests if cr['cr_id'] == selected_cr_id), None)
                    st.subheader(f"Actions for CR-{selected_cr_id}")
                    is_raised_status = selected_cr['status'] == 'RAISED'
                    is_impact_analyzed = selected_cr['status'] == 'IMPACT_ANALYZED'
                    genesis_is_complete = st.session_state.orchestrator.is_genesis_complete
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("✏️ Edit CR", use_container_width=True, disabled=not is_raised_status, help="You can only edit a CR before its impact has been analyzed."):
                            st.session_state.orchestrator.handle_edit_cr_action(selected_cr_id)
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Delete CR", use_container_width=True, disabled=not is_raised_status, help="You can only delete a CR before its impact has been analyzed."):
                            with st.popover("Confirm Deletion"):
                                st.write(f"Are you sure you want to permanently delete CR-{selected_cr_id}?")
                                if st.button("Yes, Confirm Delete", type="primary"):
                                    st.session_state.orchestrator.handle_delete_cr_action(selected_cr_id)
                                    st.toast(f"Change Request {selected_cr_id} deleted.")
                                    st.rerun()
                    with col3:
                        if st.button("🔬 Run Impact Analysis", use_container_width=True, disabled=not is_raised_status, help="Run analysis to determine the scope and impact of the change."):
                            with st.spinner(f"Running impact analysis for CR-{selected_cr_id}..."):
                                st.session_state.orchestrator.handle_run_impact_analysis_action(selected_cr_id)
                            st.toast(f"Impact analysis complete for CR-{selected_cr_id}.")
                            st.rerun()
                    with col4:
                        if st.button("▶️ Implement CR", use_container_width=True, type="primary", disabled=not (is_impact_analyzed and genesis_is_complete), help="Implementation is enabled only after impact analysis is run and main development is complete."):
                            with st.spinner(f"Generating refactoring plan for CR-{selected_cr_id}..."):
                                st.session_state.orchestrator.handle_implement_cr_action(selected_cr_id)
                            st.rerun()
                if not st.session_state.orchestrator.is_genesis_complete:
                    st.info("Note: CR implementation is enabled after the main development plan from Phase 2 is fully completed.")
            st.divider()
            if st.button("⬅️ Back to Main Checkpoint"):
                st.session_state.orchestrator.set_phase("GENESIS")
                st.rerun()

        elif current_phase_name == "EDITING_CHANGE_REQUEST":
            st.header("Phase 6: Edit Change Request")
            cr_details = st.session_state.orchestrator.get_active_cr_details_for_edit()
            if not cr_details:
                st.error("Error: Could not load Change Request details for editing.")
                if st.button("⬅️ Back to Register"):
                    st.session_state.orchestrator.cancel_cr_edit()
                    st.rerun()
            else:
                if 'cr_edit_description' not in st.session_state:
                    st.session_state.cr_edit_description = cr_details.get('description', '')
                st.markdown(f"You are editing **CR-{cr_details['cr_id']}**.")
                st.session_state.cr_edit_description = st.text_area(
                    "Change Request Description:",
                    value=st.session_state.cr_edit_description,
                    height=250
                )
                st.divider()
                col1, col2, _ = st.columns([1, 1, 5])
                with col1:
                    if st.button("Save Changes", use_container_width=True, type="primary"):
                        if st.session_state.orchestrator.save_edited_change_request(st.session_state.cr_edit_description):
                            st.toast("✅ Change Request updated!")
                            del st.session_state.cr_edit_description # Clean up
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to save changes.")
                with col2:
                    if st.button("Cancel Edit", use_container_width=True):
                        st.session_state.orchestrator.cancel_cr_edit()
                        del st.session_state.cr_edit_description # Clean up
                        st.rerun()

        elif current_phase_name == "REPORTING_OPERATIONAL_BUG":
            st.header("Report Operational Bug")
            st.info("Use this form to report a bug found during normal operation. Provide a detailed description and assign a severity rating.")
            if 'bug_description' not in st.session_state:
                st.session_state.bug_description = ""
            if 'bug_severity' not in st.session_state:
                st.session_state.bug_severity = "Medium" # Default value
            st.session_state.bug_description = st.text_area(
                "Bug Description:",
                value=st.session_state.bug_description,
                height=250,
                help="Provide a detailed description of the bug, including steps to reproduce if possible."
            )
            st.session_state.bug_severity = st.selectbox(
                "Severity:",
                options=["Minor", "Medium", "Major"],
                index=1, # Default to 'Medium'
                help="Major: An entire function doesn't work or the system crashes.\n\nMedium: A function is partly working or produces incorrect results.\n\nMinor: A small inconvenience or cosmetic issue; nothing is broken."
            )
            st.divider()
            col1, col2, _ = st.columns([1, 1, 5])
            with col1:
                if st.button("Save Bug Report", use_container_width=True, type="primary"):
                    if st.session_state.bug_description.strip():
                        if st.session_state.orchestrator.save_bug_report(st.session_state.bug_description, st.session_state.bug_severity):
                            st.toast("✅ Bug Report saved!")
                            del st.session_state.bug_description
                            del st.session_state.bug_severity
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to save the Bug Report.")
                    else:
                        st.warning("The bug description cannot be empty.")
            with col2:
                if st.button("Cancel", use_container_width=True):
                    if 'bug_description' in st.session_state:
                        del st.session_state.bug_description
                    if 'bug_severity' in st.session_state:
                        del st.session_state.bug_severity
                    st.session_state.orchestrator.set_phase("GENESIS")
                    st.rerun()

        elif current_phase_name == "AWAITING_LINKED_DELETE_CONFIRMATION":
            st.header("Confirm Linked Deletion")
            st.error("WARNING: This is a linked item. Deleting it will also delete its corresponding dependent item and may involve rolling back a specification change. This action cannot be undone.")
            linked_pair = st.session_state.orchestrator.task_awaiting_approval
            if linked_pair:
                primary_id = linked_pair.get('primary_cr_id')
                linked_id = linked_pair.get('linked_cr_id')
                st.markdown(f"You are attempting to delete **CR-{primary_id}**, which is linked to **CR-{linked_id}**.")
                st.divider()
                col1, col2, _ = st.columns([1.5, 1, 3])
                with col1:
                    if st.button("Yes, Delete Both Items", type="primary", use_container_width=True):
                        with st.spinner("Processing linked deletion..."):
                            st.session_state.orchestrator.handle_linked_delete_confirmation(primary_id, linked_id)
                        st.toast("Linked items have been deleted.")
                        st.rerun()
                with col2:
                    if st.button("No, Cancel", use_container_width=True):
                        st.session_state.orchestrator.task_awaiting_approval = None
                        st.session_state.orchestrator.set_phase("IMPLEMENTING_CHANGE_REQUEST")
                        st.rerun()
            else:
                st.error("Could not retrieve linked item details. Returning to the register.")
                if st.button("Back to Register"):
                    st.session_state.orchestrator.set_phase("IMPLEMENTING_CHANGE_REQUEST")
                    st.rerun()

        else: # Fallback for any other phase
            st.header(f"Current Phase: {current_phase_name}")
            st.info("The UI for this phase is under construction.")

elif page == "Documents":
    st.header("Project Documents")
    st.markdown("Select a project to view and download its core documents.")

    # --- Project Selection Logic ---
    doc_project_id = st.session_state.orchestrator.project_id
    doc_project_name = st.session_state.orchestrator.project_name

    project_history = st.session_state.orchestrator.get_project_history()

    if project_history:
        # Create a dictionary to map display names to project IDs
        history_options = {f"{row['project_name']} (ID: {row['project_id']})": row['project_id'] for row in project_history}

        # If a project is active, find its corresponding display name to set the default
        default_index = 0
        if doc_project_id:
            try:
                active_project_display_name = next(name for name, pid in history_options.items() if pid == doc_project_id)
                default_index = list(history_options.keys()).index(active_project_display_name) + 1
            except StopIteration:
                pass # Active project might not be in history yet

        selected_option = st.selectbox(
            "Select a Project:",
            options=[""] + list(history_options.keys()),
            index=default_index,
            help="Select any active or archived project to view its documents."
        )

        if selected_option:
            doc_project_id = history_options[selected_option]
            doc_project_name = selected_option.split(' (ID:')[0]
        else:
            # Clear the ID if the user selects the blank option
            doc_project_id = None

    elif doc_project_id:
        st.info(f"Displaying documents for the only active project: **{doc_project_name}**")
    else:
        st.warning("Please start a new project to generate documents.")
        st.stop()

    # --- Document Display and Download ---
    if doc_project_id:
        st.subheader(f"Documents for: {doc_project_name}")

        with st.session_state.orchestrator.db_manager as db:
            project_docs = db.get_project_by_id(doc_project_id)

        if project_docs:
            report_generator = ReportGeneratorAgent()

            # Application Specification
            with st.expander("Application Specification", expanded=False):
                # CORRECTED: Use dictionary-style key access for sqlite3.Row
                spec_text = project_docs['final_spec_text'] if project_docs else None
                if spec_text:
                    st.text_area("Spec Content", spec_text, height=300, disabled=True, key=f"spec_{doc_project_id}")
                    spec_docx_bytes = report_generator.generate_text_document_docx(f"Application Specification - {doc_project_name}", spec_text)
                    st.download_button("📄 Print to .docx", spec_docx_bytes, f"AppSpec_{doc_project_id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"download_spec_{doc_project_id}")
                else:
                    st.info("This document has not been generated for this project yet.")

            # Technical Specification
            with st.expander("Technical Specification", expanded=False):
                # CORRECTED: Use dictionary-style key access
                tech_spec_text = project_docs['tech_spec_text'] if project_docs else None
                if tech_spec_text:
                    st.text_area("Tech Spec Content", tech_spec_text, height=300, disabled=True, key=f"tech_spec_{doc_project_id}")
                    tech_spec_docx_bytes = report_generator.generate_text_document_docx(f"Technical Specification - {doc_project_name}", tech_spec_text)
                    st.download_button("📄 Print to .docx", tech_spec_docx_bytes, f"TechSpec_{doc_project_id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"download_tech_spec_{doc_project_id}")
                else:
                    st.info("This document has not been generated for this project yet.")

            # Coding Standard
            with st.expander("Coding Standard", expanded=False):
                coding_standard_text = project_docs['coding_standard_text'] if project_docs else None
                if coding_standard_text:
                    st.text_area("Coding Standard Content", coding_standard_text, height=300, disabled=True, key=f"cs_{doc_project_id}")
                    cs_docx_bytes = report_generator.generate_text_document_docx(f"Coding Standard - {doc_project_name}", coding_standard_text)
                    st.download_button("📄 Print to .docx", cs_docx_bytes, f"CodingStandard_{doc_project_id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"download_cs_{doc_project_id}")
                else:
                    st.info("This document has not been generated for this project yet.")

            # Development Plan
            with st.expander("Development Plan", expanded=False):
                # CORRECTED: Use dictionary-style key access
                dev_plan_text = project_docs['development_plan_text'] if project_docs else None
                if dev_plan_text:
                    st.json(dev_plan_text)
                    dev_plan_docx_bytes = report_generator.generate_text_document_docx(f"Development Plan - {doc_project_name}", dev_plan_text, is_code=True)
                    st.download_button("📄 Print to .docx", dev_plan_docx_bytes, f"DevPlan_{doc_project_id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"download_dev_plan_{doc_project_id}")
                else:
                    st.info("This document has not been generated for this project yet.")

            # Integration Plan
            with st.expander("Integration Plan", expanded=False):
                # CORRECTED: Use dictionary-style key access
                integration_plan_text = project_docs['integration_plan_text'] if project_docs else None
                if integration_plan_text:
                    st.json(integration_plan_text)
                    integration_plan_docx_bytes = report_generator.generate_text_document_docx(f"Integration Plan - {doc_project_name}", integration_plan_text, is_code=True)
                    st.download_button("📄 Print to .docx", integration_plan_docx_bytes, f"IntegrationPlan_{doc_project_id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"download_integration_plan_{doc_project_id}")
                else:
                    st.info("This document has not been generated for this project yet.")

            # UI Test Plan
            with st.expander("UI Test Plan", expanded=False):
                ui_test_plan_text = project_docs['ui_test_plan_text']
                if ui_test_plan_text:
                    st.markdown(ui_test_plan_text)
                    ui_test_plan_docx_bytes = report_generator.generate_text_document_docx(f"UI Test Plan - {doc_project_name}", ui_test_plan_text)
                    st.download_button("📄 Print to .docx", ui_test_plan_docx_bytes, f"UITestPlan_{doc_project_id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key="download_ui_test_plan")
                else:
                    st.info("This document has not been generated for this project yet.")

        else:
            st.error(f"Could not retrieve document data for project ID: {doc_project_id}")

elif page == "Reports":
    st.header("Project Reports")

    # --- Project Selection Logic ---
    report_project_id = st.session_state.orchestrator.project_id
    project_history = st.session_state.orchestrator.get_project_history()

    # If no project is active, prompt the user to select one from history
    if not report_project_id and project_history:
        st.info("No project is currently active. Please select a project from the history to view its reports.")

        history_options = {f"{row['project_name']} (ID: {row['project_id']})": row['project_id'] for row in project_history}
        selected_option = st.selectbox("Select a Project:", options=[""] + list(history_options.keys()))

        if selected_option:
            report_project_id = history_options[selected_option]

    elif not report_project_id and not project_history:
        st.warning("Please start a new project or load an archived project to view reports.")
        st.stop()

    if not report_project_id:
        st.stop() # Stop if no project is active and none is selected

    st.subheader(f"Displaying Reports for Project ID: {report_project_id}")

    # --- Instantiate the report generator agent ---
    # We create it here to ensure it's available for both reports
    try:
        from agents.agent_report_generator import ReportGeneratorAgent
        report_generator = ReportGeneratorAgent()
    except ImportError:
        st.error("ReportGeneratorAgent could not be loaded. Please check the 'agents' directory.")
        st.stop()


    # --- Report 1: Development Progress Summary ---
    st.divider()
    st.markdown("#### Development Progress Summary")
    with st.session_state.orchestrator.db_manager as db:
        all_artifacts = db.get_all_artifacts_for_project(report_project_id)
        status_counts = db.get_component_counts_by_status(report_project_id)

    if not all_artifacts:
        st.info("No components have been defined for this project yet.")
    else:
        total_components = len(all_artifacts)
        st.metric(label="Total Components Defined", value=total_components)

        # Display status counts in columns for a cleaner look
        cols = st.columns(len(status_counts) or 1)
        for i, (status, count) in enumerate(status_counts.items()):
            cols[i].metric(label=status.replace("_", " ").title(), value=count)

        # Download button for this report
        summary_docx_bytes = report_generator.generate_progress_summary_docx(total_components, status_counts)
        st.download_button(
            label="📄 Print to .docx",
            data=summary_docx_bytes,
            file_name=f"ASDF_Progress_Summary_{report_project_id}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    # --- Report 2: Change Requests & Bug Fixes ---
    st.divider()
    st.markdown("#### Change Requests & Bug Fixes")

    filter_option = st.selectbox("Filter by:", options=["Pending", "Closed", "All"])

    report_data = st.session_state.orchestrator.get_cr_and_bug_report_data(report_project_id, filter_option)

    if not report_data:
        st.info(f"No items found for the '{filter_option}' filter.")
    else:
        df = pd.DataFrame(report_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Download button for this report
        cr_bug_docx_bytes = report_generator.generate_cr_bug_report_docx(report_data, filter_option)
        st.download_button(
            label="📄 Print to .docx",
            data=cr_bug_docx_bytes,
            file_name=f"ASDF_CR_Bug_Report_{report_project_id}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="cr_bug_download"
        )

elif page == "Settings":
    st.header("Factory Settings")
    st.markdown("Configure the operational parameters of the ASDF.")
    st.divider()

    # --- LLM API Key Management ---
    st.subheader("LLM API Key Management")
    def save_api_key():
        if st.session_state.api_key_input:
            with st.session_state.orchestrator.db_manager as db:
                db.set_config_value("LLM_API_KEY", st.session_state.api_key_input)
            st.success("✅ LLM API Key saved!")
        else:
            st.warning("API Key field cannot be empty.")

    def clear_api_key():
        with st.session_state.orchestrator.db_manager as db:
            db.set_config_value("LLM_API_KEY", "")
        st.session_state.api_key_input = ""
        st.success("✅ LLM API Key cleared.")

    with st.session_state.orchestrator.db_manager as db:
        current_key_value = db.get_config_value("LLM_API_KEY")
        key_status = "Set" if current_key_value else "Not Set"

    st.markdown(f"**Current Status:** `{key_status}`")
    st.text_input("Enter or Update LLM API Key", type="password", key="api_key_input")
    col1, col2, _ = st.columns([1, 1, 5])
    with col1:
        col1.button("Save Key", on_click=save_api_key, use_container_width=True)
    with col2:
        col2.button("Clear Key", on_click=clear_api_key, use_container_width=True, disabled=(key_status == "Not Set"))

    st.divider()

    # --- Additional Settings ---
    st.subheader("Additional Settings")

    # Load all settings from DB to populate widgets
    with st.session_state.orchestrator.db_manager as db:
        all_config = db.get_all_config_values()

    # Create widgets for each configurable parameter
    st.number_input(
        "Maximum Automated Debug Attempts",
        min_value=1,
        key="max_debug_attempts",
        value=int(all_config.get("MAX_DEBUG_ATTEMPTS", 2)),
        help="Defines the number of automated fix attempts the Debug Pipeline will perform before escalating to the PM."
    )

    st.number_input(
        "Context Window Character Limit",
        min_value=10000,
        step=5000,
        key="context_window_limit",
        value=int(all_config.get("CONTEXT_WINDOW_CHAR_LIMIT", 200000)),
        help="Defines the maximum number of characters to send to the LLM for complex analysis. A larger value may provide more context but increase processing time."
    )

    pm_checkpoint_options = {"ALWAYS_ASK": "Always ask before proceeding", "AUTO_PROCEED": "Automatically proceed if successful"}
    current_pm_behavior = all_config.get("PM_CHECKPOINT_BEHAVIOR", "ALWAYS_ASK")
    pm_checkpoint_index = list(pm_checkpoint_options.keys()).index(current_pm_behavior)
    st.selectbox(
        "PM Checkpoint Behavior (Genesis Phase)",
        options=pm_checkpoint_options.values(),
        index=pm_checkpoint_index,
        key="pm_checkpoint_behavior",
        help="Controls the factory's behavior after successfully developing a component."
    )

    logging_options = ["Standard", "Detailed", "Debug"]
    current_logging_level = all_config.get("LOGGING_LEVEL", "Standard")
    # Handle case where saved value might not be in the list
    try:
        logging_index = logging_options.index(current_logging_level)
    except ValueError:
        logging_index = 0 # Default to Standard
    st.selectbox(
        "ASDF Operational Logging Level",
        options=logging_options,
        index=logging_index,
        key="logging_level",
        help="Controls the verbosity of ASDF's internal logs, useful for troubleshooting the factory application itself."
    )

    st.text_input("Default Base Path for New Target Projects", key="default_project_path", value=all_config.get("DEFAULT_PROJECT_PATH", ""), help="Optional. Set a default parent directory (e.g., 'C:\\Users\\YourName\\Projects'). When you start a new project, ASDF will suggest a path inside this directory, which you can still edit for each project.")
    st.text_input("Default Project Archive Path", key="default_archive_path", value=all_config.get("DEFAULT_ARCHIVE_PATH", ""), help="Optional. Set a default folder for saving project archives when you use the 'Stop & Export' feature. This provides a consistent location to find your exported project data.")

    def save_additional_settings():
        """Callback function to save all settings to the database."""
        settings_to_save = {
            "MAX_DEBUG_ATTEMPTS": st.session_state.max_debug_attempts,
            "CONTEXT_WINDOW_CHAR_LIMIT": st.session_state.context_window_limit,
            "LOGGING_LEVEL": st.session_state.logging_level,
            "DEFAULT_PROJECT_PATH": st.session_state.default_project_path,
            "DEFAULT_ARCHIVE_PATH": st.session_state.default_archive_path
        }
        # Convert selected UI text back to the key for storage
        selected_pm_behavior_value = st.session_state.pm_checkpoint_behavior
        for key, value in pm_checkpoint_options.items():
            if value == selected_pm_behavior_value:
                settings_to_save["PM_CHECKPOINT_BEHAVIOR"] = key
                break

        with st.session_state.orchestrator.db_manager as db:
            for key, value in settings_to_save.items():
                db.set_config_value(key, str(value))
        st.success("✅ Additional settings saved!")

    st.button("Save All Additional Settings", on_click=save_additional_settings, type="primary", use_container_width=True)
