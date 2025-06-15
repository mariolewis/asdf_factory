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
from agents.agent_report_generator import ReportGeneratorAgent

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
    page = st.radio("Navigation", ["Project", "Documents", "Reports", "Settings"], label_visibility="collapsed")
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

        if st.button("Complete Environment Setup & Proceed", use_container_width=True):
                apex_file = st.session_state.get("apex_file_name_input", "").strip()
                if not apex_file:
                    st.error("Please provide a main Executable File Name.")
                # Also ensure the build script choice has been made
                elif 'build_script_choice_made' not in st.session_state or not st.session_state.build_script_choice_made:
                    st.error("Please confirm your Build Script choice before proceeding.")
                else:
                    with st.session_state.orchestrator.db_manager as db:
                        db.update_project_technology(st.session_state.orchestrator.project_id, st.session_state.language)
                        db.update_project_apex_file(st.session_state.orchestrator.project_id, apex_file)
                        # Add this call to the new DAO method
                        db.update_project_build_automation_status(
                            st.session_state.orchestrator.project_id,
                            st.session_state.get('is_build_automated', True) # Defaults to True
                        )

                    st.session_state.orchestrator.set_phase("SPEC_ELABORATION")
                    # Add the new session state keys to the cleanup list
                    keys_to_clear = [
                        'project_root_path', 'path_confirmed', 'git_initialized',
                        'language', 'language_select', 'frameworks', 'apex_file_name_input',
                        'build_script_choice_made', 'is_build_automated'
                    ]
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

                #
                # --- ADD THIS ENTIRE NEW BLOCK OF CODE ---
                #

                # --- UI for Acknowledging the Finalized Specification ---
                elif st.session_state.get('spec_approved_but_not_acknowledged'):
                    st.subheader("Final Specification Approved")

                    # Display the message to the PM as per PRD requirement.
                    st.success(
                        "The final specification is now agreed upon and displayed below. "
                        "Please copy this text into a local document for your own records and future reference."
                    )

                    # Display the finalized specification text in a disabled text area.
                    st.text_area(
                        "Finalized Specification:",
                        value=st.session_state.specification_text,
                        height=300,
                        disabled=True
                    )

                    st.divider()

                    # The new button to acknowledge and move to the next phase.
                    if st.button("Acknowledge and Proceed to Technical Specification", type="primary"):
                        # This button now performs the actions the old 'Approve' button did.
                        st.session_state.orchestrator.set_phase("TECHNICAL_SPECIFICATION")

                        # Clean up all session state keys related to the spec elaboration phase.
                        keys_to_clear = [
                            'specification_text', 'complexity_analysis',
                            'proceed_with_complexity', 'clarification_issues',
                            'clarification_chat', 'brief_desc',
                            'spec_approved_but_not_acknowledged'
                        ]
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]

                        st.rerun()

                # --- Clarification Loop (only runs after complexity gate is passed) ---
                else:
                    if 'clarification_issues' not in st.session_state:
                        st.session_state.clarification_issues = None
                    if 'clarification_chat' not in st.session_state:
                        st.session_state.clarification_chat = []

                    if st.session_state.clarification_issues:
                        st.subheader("Clarification Required")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Approve Specification and Proceed", use_container_width=True, type="primary"):
                                with st.spinner("Finalizing specification..."):
                                    # Save the finalized specification to the database.
                                    with st.session_state.orchestrator.db_manager as db:
                                        db.save_final_specification(
                                            st.session_state.orchestrator.project_id,
                                            st.session_state.specification_text
                                        )
                                    # Set a new session state flag to indicate approval.
                                    st.session_state.spec_approved_but_not_acknowledged = True
                                    st.rerun()
                        with col2:
                            # The download button remains for convenience.
                            report_generator = ReportGeneratorAgent()
                            spec_docx_bytes = report_generator.generate_text_document_docx(
                                title=f"Application Specification - {st.session_state.orchestrator.project_name}",
                                content=st.session_state.specification_text
                            )
                            st.download_button(
                                label="📄 Print to .docx",
                                data=spec_docx_bytes,
                                file_name=f"Application_Specification_{st.session_state.orchestrator.project_id}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )

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
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve Technical Specification", use_container_width=True, type="primary"):
                        with st.spinner("Saving technical specification..."):
                            with st.session_state.orchestrator.db_manager as db:
                                db.save_tech_specification(
                                    st.session_state.orchestrator.project_id,
                                    st.session_state.tech_spec_draft
                                )
                            st.session_state.orchestrator.set_phase("CODING_STANDARD_GENERATION")
                            # ... (rest of the button logic is the same)
                with col2:
                    # Add the download button
                    report_generator = ReportGeneratorAgent()
                    tech_spec_docx_bytes = report_generator.generate_text_document_docx(
                        title=f"Technical Specification - {st.session_state.orchestrator.project_name}",
                        content=st.session_state.tech_spec_draft
                    )
                    st.download_button(
                        label="📄 Print to .docx",
                        data=tech_spec_docx_bytes,
                        file_name=f"Technical_Specification_{st.session_state.orchestrator.project_id}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                    with st.spinner("Saving technical specification..."):
                        with st.session_state.orchestrator.db_manager as db:
                            db.save_tech_specification(
                                st.session_state.orchestrator.project_id,
                                st.session_state.tech_spec_draft
                            )

                        # Transition to the next phase
                        st.session_state.orchestrator.set_phase("CODING_STANDARD_GENERATION")

                        # Clean up session state for this phase
                        for key in ['tech_spec_choice', 'tech_spec_draft']:
                             if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

        elif current_phase_name == "CODING_STANDARD_GENERATION":
            st.header("Phase 2.A: Coding Standard Generation")
            st.markdown("Here you can generate a project-specific coding standard based on the technical specification. This standard will be enforced by all code-generating agents.")

            # Initialize session state
            if 'coding_standard_draft' not in st.session_state:
                st.session_state.coding_standard_draft = ""

            # Button to trigger the agent
            if st.button("Generate Coding Standard Draft"):
                with st.spinner("AI is generating the coding standard..."):
                    try:
                        with st.session_state.orchestrator.db_manager as db:
                            api_key = db.get_config_value("LLM_API_KEY")
                            project_details = db.get_project_by_id(st.session_state.orchestrator.project_id)
                            tech_spec = project_details.get('tech_spec_text')

                        if not api_key or not tech_spec:
                            st.error("Cannot generate standard: Missing API Key or Technical Specification.")
                        else:
                            from agents.agent_coding_standard_app_target import CodingStandardAgent_AppTarget
                            agent = CodingStandardAgent_AppTarget(api_key=api_key)
                            standard = agent.generate_standard(tech_spec)
                            st.session_state.coding_standard_draft = standard
                    except Exception as e:
                        st.error(f"Failed to generate coding standard: {e}")

            # Text area for review and editing
            st.session_state.coding_standard_draft = st.text_area(
                "Coding Standard Document",
                value=st.session_state.coding_standard_draft,
                height=400,
                help="You can edit the AI-generated coding standard here before approving."
            )

            st.divider()

            # Approval Step
            if st.session_state.coding_standard_draft:
                if st.button("Approve Coding Standard and Proceed to Planning", type="primary"):
                    with st.spinner("Saving coding standard..."):
                        with st.session_state.orchestrator.db_manager as db:
                            db.save_coding_standard(
                                st.session_state.orchestrator.project_id,
                                st.session_state.coding_standard_draft
                            )

                        # Transition to the next phase
                        st.session_state.orchestrator.set_phase("PLANNING")

                        # Clean up session state for this phase
                        if 'coding_standard_draft' in st.session_state:
                            del st.session_state['coding_standard_draft']
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
                col1, col2, col3 = st.columns([1.5, 1, 1.5])
                with col1:
                    # The button to approve the plan and proceed

                    if st.button("✅ Approve Plan & Proceed to Development", type="primary"):
                        with st.spinner("Saving and loading development plan..."):
                            plan_json = st.session_state.development_plan
                            # Save the plan to the database
                            with st.session_state.orchestrator.db_manager as db:
                                db.save_development_plan(st.session_state.orchestrator.project_id, plan_json)

                            # Load the plan into the orchestrator's active state
                            st.session_state.orchestrator.load_development_plan(plan_json)

                            # Set the new session state flag to trigger the acknowledgment UI
                            st.session_state.plan_approved_but_not_acknowledged = True
                            st.toast("Plan approved! Awaiting acknowledgment.")
                            st.rerun()
                with col2:
                    # Add the download button
                    report_generator = ReportGeneratorAgent()
                    dev_plan_docx_bytes = report_generator.generate_text_document_docx(
                        title=f"Sequential Development Plan - {st.session_state.orchestrator.project_name}",
                        content=st.session_state.development_plan,
                        is_code=True # Format this content as code
                    )
                    st.download_button(
                        label="📄 Print to .docx",
                        data=dev_plan_docx_bytes,
                        file_name=f"Development_Plan_{st.session_state.orchestrator.project_id}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                with col3:
                    # The button to re-generate the plan
                    if st.button("🔄 Re-generate Development Plan"):
                         st.session_state.development_plan = None
                         st.rerun()

            # --- UI for Acknowledging the Approved Development Plan ---
            elif st.session_state.get('plan_approved_but_not_acknowledged'):
                st.subheader("Development Plan Approved")

                # Display the message to the PM as per PRD F-Phase 2 requirement.
                st.success(
                    "The Development Plan has been approved and is displayed below. "
                    "Please copy this text into a local document for your records."
                )

                # Display the finalized plan using st.json for readability.
                st.json(st.session_state.development_plan)

                st.divider()

                # The new button to acknowledge and move to the development phase.
                if st.button("Acknowledge and Proceed to Development", type="primary"):
                    # This button now performs the final actions.
                    st.session_state.orchestrator.set_phase("GENESIS")

                    # Clean up all session state keys related to the planning phase.
                    keys_to_clear = [
                        'development_plan',
                        'plan_approved_but_not_acknowledged'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]

                    st.toast("Plan acknowledged! Starting development...")
                    time.sleep(1)
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
                    st.stop() # Stop rendering the buttons below

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


        elif current_phase_name == "INTEGRATION_AND_VERIFICATION":
            st.header("Phase 3.5: Automated Integration & Verification")
            st.info("The factory is now integrating all newly developed components, performing a full system build, and running verification tests.")

            with st.spinner("Running automated integration... This may take a moment."):
                # This backend method runs the entire phase 3.5 logic
                st.session_state.orchestrator._run_integration_and_verification_phase()

            st.success("Integration and verification process complete.")
            time.sleep(2) # Pause for 2 seconds to allow the user to read the message
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

        elif current_phase_name == "RAISING_CHANGE_REQUEST":
            st.header("Phase 6: Raise New Change Request")
            st.markdown("Please provide a detailed description of the change you are requesting below. This will be logged in the Change Request Register.")

            # Use session state to hold the text area's value to prevent loss on reruns
            if 'cr_description' not in st.session_state:
                st.session_state.cr_description = ""

            # The widget's key is separate from the session state variable
            st.session_state.cr_description = st.text_area(
                "Change Request Description:",
                value=st.session_state.cr_description,
                height=250
            )

            st.divider()
            col1, col2, _ = st.columns([1, 1, 5])

            with col1:
                if st.button("Save Change Request", use_container_width=True, type="primary"):
                    if st.session_state.cr_description.strip():
                        if st.session_state.orchestrator.save_new_change_request(st.session_state.cr_description):
                            st.toast("✅ Change Request saved!")
                            # Clean up the session state variable and rerun to go back to the Genesis phase
                            del st.session_state.cr_description
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to save the Change Request.")
                    else:
                        st.warning("The change request description cannot be empty.")

            with col2:
                if st.button("Cancel", use_container_width=True):
                    # Clean up the session state variable and return to the Genesis phase
                    if 'cr_description' in st.session_state:
                        del st.session_state.cr_description
                    st.session_state.orchestrator.set_phase("GENESIS")
                    st.rerun()

        elif current_phase_name == "IMPLEMENTING_CHANGE_REQUEST":
            st.header("Phase 6: Implement Requested Change")
            st.markdown("Select a Change Request from the register below to view available actions.")

            change_requests = st.session_state.orchestrator.get_all_change_requests()

            if not change_requests:
                st.warning("There are no change requests in the register for this project.")
            else:
                # Prepare data for display in a pandas DataFrame
                cr_data_for_df = []
                for cr in change_requests:
                    cr_data_for_df.append({
                        "ID": cr['cr_id'],
                        "Status": cr['status'],
                        "Impact": cr['impact_rating'],
                        "Description": cr['description'],
                        "Analysis Summary": cr['impact_analysis_details']
                    })

                df = pd.DataFrame(cr_data_for_df)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Allow PM to select a CR by ID
                cr_ids = [cr['cr_id'] for cr in change_requests]
                selected_cr_id_str = st.selectbox("Select a Change Request ID to action:", options=[""] + [str(i) for i in cr_ids])

                if selected_cr_id_str:
                    selected_cr_id = int(selected_cr_id_str)
                    selected_cr = next((cr for cr in change_requests if cr['cr_id'] == selected_cr_id), None)

                    st.subheader(f"Actions for CR-{selected_cr_id}")

                    # Business Logic for enabling/disabling buttons based on CR status
                    is_raised_status = selected_cr['status'] == 'RAISED'
                    is_impact_analyzed = selected_cr['status'] == 'IMPACT_ANALYZED'

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if st.button("✏️ Edit CR", use_container_width=True, disabled=not is_raised_status, help="You can only edit a CR before its impact has been analyzed."):
                            st.session_state.orchestrator.handle_edit_cr_action(selected_cr_id)
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Delete CR", use_container_width=True, disabled=not is_raised_status, help="You can only delete a CR before its impact has been analyzed."):
                            # Use a popover for a confirmation dialog to prevent accidental deletion
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
                        if st.button("▶️ Implement CR", use_container_width=True, type="primary", disabled=not is_impact_analyzed, help="Generate a development plan and begin implementation."):
                            with st.spinner(f"Generating refactoring plan for CR-{selected_cr_id}..."):
                                st.session_state.orchestrator.handle_implement_cr_action(selected_cr_id)
                            st.rerun()

            st.divider()
            if st.button("⬅️ Back to Main Checkpoint"):
                st.session_state.orchestrator.set_phase("GENESIS")
                st.rerun()

        elif current_phase_name == "EDITING_CHANGE_REQUEST":
            st.header("Phase 6: Edit Change Request")

            # Get the details of the CR to be edited from the orchestrator
            cr_details = st.session_state.orchestrator.get_active_cr_details_for_edit()

            if not cr_details:
                st.error("Error: Could not load Change Request details for editing.")
                if st.button("⬅️ Back to Register"):
                    st.session_state.orchestrator.cancel_cr_edit()
                    st.rerun()
            else:
                # Use session state to hold the text area's value.
                # Initialize it with the existing description only once.
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
                selected_id_str = st.selectbox("Select a Project ID to action:", options=[""] + [str(i) for i in history_ids])

                if selected_id_str:
                    selected_id = int(selected_id_str)
                    selected_project_record = next((p for p in project_history if p['history_id'] == selected_id), None)

                    # --- Button Logic ---
                    is_active_project = (st.session_state.orchestrator.project_id == selected_project_record['project_id'])

                    col1, col2, _ = st.columns([1, 1, 4])
                    with col1:
                        if st.button("📂 Load Selected Project", use_container_width=True, type="primary"):
                            with st.spinner("Loading project data and running pre-flight checks..."):
                                st.session_state.orchestrator.load_archived_project(selected_id)
                                st.rerun()
                    with col2:
                        # Add the delete button with its popover confirmation
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
                st.session_state.orchestrator.project_id = None
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
                spec_text = project_docs.get('final_spec_text')
                if spec_text:
                    st.text_area("Spec Content", spec_text, height=300, disabled=True, key=f"spec_{doc_project_id}")
                    spec_docx_bytes = report_generator.generate_text_document_docx(f"Application Specification - {doc_project_name}", spec_text)
                    st.download_button("📄 Print to .docx", spec_docx_bytes, f"AppSpec_{doc_project_id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                else:
                    st.info("This document has not been generated for this project yet.")

            # Technical Specification
            with st.expander("Technical Specification", expanded=False):
                tech_spec_text = project_docs.get('tech_spec_text')
                if tech_spec_text:
                    st.text_area("Tech Spec Content", tech_spec_text, height=300, disabled=True, key=f"tech_spec_{doc_project_id}")
                    tech_spec_docx_bytes = report_generator.generate_text_document_docx(f"Technical Specification - {doc_project_name}", tech_spec_text)
                    st.download_button("📄 Print to .docx", tech_spec_docx_bytes, f"TechSpec_{doc_project_id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                else:
                    st.info("This document has not been generated for this project yet.")

            # Development Plan
            with st.expander("Development Plan", expanded=False):
                dev_plan_text = project_docs.get('development_plan_text')
                if dev_plan_text:
                    st.json(dev_plan_text)
                    dev_plan_docx_bytes = report_generator.generate_text_document_docx(f"Development Plan - {doc_project_name}", dev_plan_text, is_code=True)
                    st.download_button("📄 Print to .docx", dev_plan_docx_bytes, f"DevPlan_{doc_project_id}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                else:
                    st.info("This document has not been generated for this project yet.")
        else:
            st.error(f"Could not retrieve document data for project ID: {doc_project_id}")

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