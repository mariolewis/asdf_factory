import streamlit as st
from pathlib import Path
import time
import pandas as pd
from master_orchestrator import MasterOrchestrator
from agent_environment_setup_app_target import EnvironmentSetupAgent_AppTarget
from agent_project_bootstrap import ProjectBootstrapAgent

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
    col1, col2 = st.columns([0.15, 0.85], gap="small")
    with col1:
        st.markdown("## 🤖")
    with col2:
        st.markdown("## Autonomous Software Development Factory")

    st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
    page = st.radio("Navigation", ["Project", "Reports", "Settings"], label_visibility="collapsed")
    st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)

    st.markdown("<h3 style='color: #FFC300;'>Project Information</h3>", unsafe_allow_html=True)
    status_info = st.session_state.orchestrator.get_status()
    labels = {"project_id": "Project ID", "project_name": "Project Name", "current_phase": "Current Phase"}
    for key, label in labels.items():
        value = status_info.get(key)
        display_value = value if value is not None else "N/A"
        st.markdown(f"**{label}:** {display_value}")


# --- Main Application UI ---

if page == "Project":
    # --- Logic for starting a new project (if none is active) ---
    if not st.session_state.orchestrator.project_id:
        st.subheader("Start a New Project")
        project_name_input = st.text_input("Enter a name for your new project:")
        if st.button("Start New Project"):
            if project_name_input:
                st.session_state.orchestrator.start_new_project(project_name_input)
                st.rerun()
            else:
                st.error("Please enter a project name.")

    # --- Logic for an active project, displayed based on its current phase ---
    else:
        status_info = st.session_state.orchestrator.get_status()
        current_phase_name = status_info.get("current_phase")

        # --- Phase: Environment Setup ---
        if current_phase_name == "ENV_SETUP_TARGET_APP":
            setup_agent = EnvironmentSetupAgent_AppTarget()
            setup_agent.run_setup_flow()

            # Display a button to advance to the next phase when setup is complete
            if st.session_state.get('git_initialized'):
                st.divider()
                if st.button("Complete Environment Setup & Proceed to Phase 1", use_container_width=True):
                    with st.session_state.orchestrator.db_manager as db:
                        db.update_project_technology(
                            st.session_state.orchestrator.project_id,
                            st.session_state.language
                        )
                    st.session_state.orchestrator.set_phase("SPEC_ELABORATION")
                    # Clean up session state keys used by the setup agent
                    for key in ['project_root_path', 'path_confirmed', 'git_initialized', 'language', 'language_select', 'frameworks']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

        # --- Phase: Specification Elaboration ---
        elif current_phase_name == "SPEC_ELABORATION":
            st.header("Phase 1: Project Initialization & Specification Elaboration")
            st.markdown("Please provide the initial specification for your target application using one of the methods below.")

            if 'specification_text' not in st.session_state:
                st.session_state.specification_text = None

            # Create two tabs for the two input modes as per PRD F-Phase 1.
            tab1, tab2 = st.tabs(["Upload Specification Documents", "Enter Brief Description"])

            with tab1:
                st.markdown("Upload one or more documents containing your application's specifications. Supported formats are `.txt`, `.md`, and `.docx`.")
                uploaded_files = st.file_uploader(
                    "Upload Specification Documents",
                    type=["txt", "md", "docx"],
                    accept_multiple_files=True,
                    label_visibility="collapsed"
                )
                if st.button("Process Uploaded Documents"):
                    if uploaded_files:
                        bootstrap_agent = ProjectBootstrapAgent()
                        extracted_text, messages = bootstrap_agent.extract_text_from_files(uploaded_files)
                        for msg in messages:
                            st.warning(msg)
                        if extracted_text:
                            st.session_state.specification_text = extracted_text
                            st.rerun()
                    else:
                        st.warning("Please upload at least one document.")

            with tab2:
                st.markdown("Enter a brief, one or two paragraph description of your target application. The AI will expand this into a draft specification.")
                brief_desc_input = st.text_area("Brief Description", height=150, key="brief_desc")
                if st.button("Process Brief Description"):
                    if brief_desc_input:
                        with st.spinner("AI is expanding the description into a draft specification..."):
                            try:
                                with st.session_state.orchestrator.db_manager as db:
                                    api_key = db.get_config_value("LLM_API_KEY")
                                if not api_key:
                                    st.error("Cannot proceed. LLM API Key is not set in Settings.")
                                else:
                                    clarification_agent = SpecClarificationAgent(api_key=api_key)
                                    expanded_text = clarification_agent.expand_brief_description(brief_desc_input)
                                    st.session_state.specification_text = expanded_text
                                    st.rerun()
                            except Exception as e:
                                st.error(f"An error occurred while communicating with the AI: {e}")
                    else:
                        st.warning("Please enter a description.")

            st.divider()

            # This section appears below the tabs, once specification_text is populated.
            if st.session_state.specification_text:
                st.subheader("Processed Specification Draft")
                st.text_area("", value=st.session_state.specification_text, height=300, disabled=True, key="spec_draft_display")
                st.divider()

                # Initialize session state keys for the clarification loop
                if 'clarification_issues' not in st.session_state:
                    st.session_state.clarification_issues = None
                if 'clarification_chat' not in st.session_state:
                    st.session_state.clarification_chat = []

                # --- Main Clarification Loop UI ---
                if st.session_state.clarification_issues:
                    st.subheader("Clarification Required")

                    st.markdown("Once all issues are resolved and the draft below is final, approve it to proceed.")
                    if st.button("✅ Approve Specification and Proceed to Planning", use_container_width=True, type="primary"):
                        with st.spinner("Finalizing specification and moving to next phase..."):
                            try:
                                # Save the final spec to the DB
                                with st.session_state.orchestrator.db_manager as db:
                                    db.save_final_specification(
                                        st.session_state.orchestrator.project_id,
                                        st.session_state.specification_text
                                    )
                                # Set the new phase
                                st.session_state.orchestrator.set_phase("PLANNING")

                                # Cleanup session state for this phase
                                for key in ['specification_text', 'clarification_issues', 'clarification_chat', 'spec_draft_display', 'brief_desc']:
                                    if key in st.session_state:
                                        del st.session_state[key]

                                st.success("Specification Approved!")
                                time.sleep(2)
                                st.rerun()

                            except Exception as e:
                                st.error(f"An error occurred during finalization: {e}")
                    st.divider()

                    # Display chat history for the clarification
                    for message in st.session_state.clarification_chat:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                    # Get PM's input
                    if prompt := st.chat_input("Provide clarifications to address the points above..."):
                        # Add PM's message to chat history for context
                        st.session_state.clarification_chat.append({"role": "user", "content": prompt})

                        with st.spinner("AI is refining the specification based on your feedback..."):
                            try:
                                with st.session_state.orchestrator.db_manager as db:
                                    api_key = db.get_config_value("LLM_API_KEY")
                                if not api_key:
                                    st.error("Cannot proceed. LLM API Key is not set in Settings.")
                                else:
                                    agent = SpecClarificationAgent(api_key=api_key)
                                    revised_spec = agent.refine_specification(
                                        original_spec_text=st.session_state.specification_text,
                                        issues_found=st.session_state.clarification_issues,
                                        pm_clarification=prompt
                                    )
                                    # This is the core of the loop: the spec is updated with the new version.
                                    st.session_state.specification_text = revised_spec

                                    # Clear the issues and chat to reset the loop for re-analysis.
                                    st.session_state.clarification_issues = None
                                    st.session_state.clarification_chat = []

                                    st.success("✅ Specification draft updated.")
                                    time.sleep(2) # Give user time to read the success message.
                                    st.rerun()

                            except Exception as e:
                                st.error(f"An error occurred during refinement: {e}")

                # --- Button to start the loop ---
                else:
                    if st.button("Analyze Specification & Begin Clarification", use_container_width=True):
                        with st.spinner("AI is analyzing the specification for issues..."):
                            try:
                                with st.session_state.orchestrator.db_manager as db:
                                    api_key = db.get_config_value("LLM_API_KEY")
                                if not api_key:
                                    st.error("Cannot proceed. LLM API Key is not set in Settings.")
                                else:
                                    agent = SpecClarificationAgent(api_key=api_key)
                                    issues = agent.identify_potential_issues(st.session_state.specification_text)
                                    st.session_state.clarification_issues = issues
                                    # Add the AI's findings as the first message in the clarification chat
                                    st.session_state.clarification_chat.append({"role": "assistant", "content": issues})
                                    st.rerun()
                            except Exception as e:
                                st.error(f"An error occurred during analysis: {e}")

        # --- Phase: Planning ---
        elif current_phase_name == "PLANNING":
            st.header("Phase 2: Strategic Development Planning")
            st.info("This is a placeholder for the Development Planning UI.")
            st.markdown("In a future step, the `PlanningAgent` will generate the development plan here for your approval.")

            st.divider()

            # This button allows us to manually advance to the next phase for now.
            if st.button("Approve Plan & Proceed to Development", use_container_width=True, type="primary"):
                st.session_state.orchestrator.set_phase("GENESIS")
                st.rerun()

        # --- Phase: Genesis (Iterative Development) ---
        elif current_phase_name == "GENESIS":
            st.header("Phase 3: Iterative Component Development")

            # PM Checkpoint UI (as per PRD F-Phase 3)
            st.subheader("PM Checkpoint")

            # NOTE: In a real implementation, these values would be dynamically
            # populated by the MasterOrchestrator from the development plan.
            previous_component = "User Login UI"
            current_component = "User Profile Data Class"
            micro_spec_id = "MS-0042"

            st.markdown(f"""
            Development of **'{previous_component}'** was successful.

            Next component in the plan is: **'{current_component}'** (based on micro-spec `{micro_spec_id}`).

            How would you like to proceed?
            """)

            # Create columns for the buttons for a clean layout.
            col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 3])

            with col1:
                if st.button("▶️ Proceed", use_container_width=True, type="primary"):
                    st.toast("Proceeding with component development...")
                    # TODO: Add call to orchestrator to handle 'proceed' logic.

            with col2:
                if st.button("⏸️ Pause", use_container_width=True):
                    st.toast("Pausing factory operations...")
                    st.session_state.orchestrator.pause_project()
                    st.rerun()


            with col3:
                if st.button("🔁 Request Change", use_container_width=True):
                    st.toast("Initiating change management workflow...")
                    # TODO: Add call to orchestrator to handle 'change' logic.

            with col4:
                if st.button("⏹️ Discontinue", use_container_width=True):
                    st.toast("Discontinuing project...")
                    st.session_state.orchestrator.discontinue_project()
                    st.rerun()

        # --- Default View for other phases ---
        else:
            st.subheader(f"Project View (Phase: {current_phase_name})")
            st.info("The UI for this phase has not been implemented yet.")

elif page == "Settings":
    # (Settings page code remains the same)
    st.markdown("<h2 style='color: #64C8FF;'>Factory Settings</h2>", unsafe_allow_html=True)
    st.markdown("---")

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
    _, col2, col3 = st.columns([0.6, 0.2, 0.2])
    with col2:
        st.button("Save Key", on_click=save_api_key, use_container_width=True)
    with col3:
        is_disabled = (key_status == "Not Set")
        st.button("Clear Key", on_click=clear_api_key, use_container_width=True, disabled=is_disabled)

    st.markdown("---")

    st.subheader("Additional Settings")
    with st.session_state.orchestrator.db_manager as db:
        all_config = db.get_all_config_values()

    st.number_input("Maximum Automated Debug Attempts", min_value=1, key="max_debug_attempts", value=int(all_config.get("MAX_DEBUG_ATTEMPTS", 5)))
    pm_checkpoint_options = {"ALWAYS_ASK": "Always ask before proceeding", "AUTO_PROCEED": "Automatically proceed if successful"}
    current_pm_behavior = all_config.get("PM_CHECKPOINT_BEHAVIOR", "ALWAYS_ASK")
    pm_checkpoint_index = list(pm_checkpoint_options.keys()).index(current_pm_behavior)
    st.selectbox("PM Checkpoint Behavior", options=pm_checkpoint_options.values(), index=pm_checkpoint_index, key="pm_checkpoint_behavior", help="Controls the factory's behavior after successfully developing a component. 'Always ask' requires your confirmation to proceed to the next component.")
    logging_options = ["Standard", "Detailed", "Debug"]
    current_logging_level = all_config.get("LOGGING_LEVEL", "Standard")
    logging_index = logging_options.index(current_logging_level)
    st.selectbox("ASDF Operational Logging Level", options=logging_options, index=logging_index, key="logging_level", help="Controls the verbosity of ASDF's internal logs, which is useful for troubleshooting the factory application itself.")
    st.text_input("Default Base Path for New Target Projects", key="default_project_path", value=all_config.get("DEFAULT_PROJECT_PATH", ""))
    st.text_input("Default Project Archive Path", key="default_archive_path", value=all_config.get("DEFAULT_ARCHIVE_PATH", ""))
    def save_additional_settings():
        settings_to_save = {"MAX_DEBUG_ATTEMPTS": st.session_state.max_debug_attempts, "LOGGING_LEVEL": st.session_state.logging_level, "DEFAULT_PROJECT_PATH": st.session_state.default_project_path, "DEFAULT_ARCHIVE_PATH": st.session_state.default_archive_path}
        selected_pm_behavior_value = st.session_state.pm_checkpoint_behavior
        for key, value in pm_checkpoint_options.items():
            if value == selected_pm_behavior_value:
                settings_to_save["PM_CHECKPOINT_BEHAVIOR"] = key
                break
        with st.session_state.orchestrator.db_manager as db:
            for key, value in settings_to_save.items():
                db.set_config_value(key, str(value))
        st.success("✅ Additional settings saved!")
    st.button("Save All Settings", on_click=save_additional_settings)

elif page == "Reports":
    st.markdown("<h2 style='color: #64C8FF;'>Project Reports</h2>", unsafe_allow_html=True)

    project_id = st.session_state.orchestrator.project_id
    if not project_id:
        st.warning("Please start a new project from the 'Project' page to view reports.")
    else:
        # --- Development Progress Summary Report ---
        st.subheader("Development Progress Summary")
        with st.session_state.orchestrator.db_manager as db:
            all_artifacts = db.get_all_artifacts_for_project(project_id)
            status_counts = db.get_component_counts_by_status(project_id)

        if not all_artifacts:
            st.info("No components have been defined for this project yet.")
        else:
            st.metric(label="Total Components Defined", value=len(all_artifacts))
            st.markdown("**Components by Status:**")
            st.json(status_counts)
            st.markdown("**Component Details:**")
            df_data = [{"Name": art['artifact_name'], "Type": art['artifact_type'], "Status": art['status']} for art in all_artifacts]
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)

        st.markdown("---")

        # --- Pending Changes & Bug Fix Status Report ---
        st.subheader("Pending Changes & Bug Fix Status")

        # [cite_start]As per the PRD, this report filters for specific statuses. [cite: 356, 357, 358]
        pending_statuses = [
            "UNIT_TESTS_FAILING", "AWAITING_PM_REVIEW", "AWAITING_UI_TEST_RESULTS",
            "DEBUG_IN_PROGRESS", "PM_INTERVENTION_REQUIRED_DEBUG", "PM_REVIEW_PENDING_CHANGE"
        ]

        with st.session_state.orchestrator.db_manager as db:
            pending_artifacts = db.get_artifacts_by_statuses(project_id, pending_statuses)

        if not pending_artifacts:
            st.info("There are no components currently awaiting changes or bug fixes.")
        else:
            st.markdown(f"**Found {len(pending_artifacts)} component(s) requiring attention.**")
            df_pending_data = [{"Name": art['artifact_name'], "Type": art['artifact_type'], "Status": art['status']} for art in pending_artifacts]
            df_pending = pd.DataFrame(df_pending_data)
            st.dataframe(df_pending, use_container_width=True)