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
                    st.session_state.orchestrator.set_phase("SPEC_ELABORATION")
                    # Clean up session state keys used by the setup agent
                    for key in ['project_root_path', 'path_confirmed', 'git_initialized', 'language', 'language_select', 'frameworks']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

        # --- Phase: Specification Elaboration ---
        elif current_phase_name == "SPEC_ELABORATION":
            st.header("Phase 1: Specification Elaboration")
            st.markdown(
                "Please upload the specification documents for your target application. "
                [cite_start]"Supported formats are `.txt`, `.md`, and `.docx`. [cite: 341, 686, 1031, 1376]"
            )

            uploaded_files = st.file_uploader(
                "Upload Specification Documents",
                type=["txt", "md", "docx"],
                accept_multiple_files=True
            )

            if 'specification_text' not in st.session_state:
                st.session_state.specification_text = None

            if uploaded_files:
                bootstrap_agent = ProjectBootstrapAgent()
                extracted_text, messages = bootstrap_agent.extract_text_from_files(uploaded_files)

                for msg in messages:
                    st.warning(msg)

                if extracted_text:
                    st.session_state.specification_text = extracted_text
                    st.success("✅ Files processed successfully!")
                    with st.expander("View Extracted Specification Text"):
                        st.text_area("", value=extracted_text, height=300, disabled=True)

            if st.session_state.specification_text:
                st.divider()
                if st.button("Proceed to Specification Clarification", use_container_width=True):
                    # This will trigger the next agent in a future step
                    st.info("This concludes the bootstrap process. The next step will be the clarification loop.")
                    # st.session_state.orchestrator.set_phase("PLANNING")
                    # st.rerun()

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