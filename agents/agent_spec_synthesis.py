# agents/agent_spec_synthesis.py

import logging
import textwrap
from pathlib import Path
from llm_service import LLMService
from asdf_db_manager import ASDFDBManager
from agents.agent_report_generator import ReportGeneratorAgent
from master_orchestrator import MasterOrchestrator

class SpecSynthesisAgent:
    """
    Agent responsible for synthesizing a collection of code summaries into
    high-level project specification documents.
    """

    def __init__(self, orchestrator: MasterOrchestrator):
        if not orchestrator or not orchestrator.llm_service or not orchestrator.db_manager:
            raise ValueError("A fully initialized orchestrator is required for the SpecSynthesisAgent.")
        self.orchestrator = orchestrator
        self.llm_service = orchestrator.llm_service
        self.db_manager = orchestrator.db_manager
        self.report_generator = ReportGeneratorAgent()
        logging.info("SpecSynthesisAgent initialized.")

    def synthesize_all_specs(self, project_id: str):
        """
        Orchestrates the generation of all relevant specification documents.
        """
        logging.info(f"Starting specification synthesis for project {project_id}.")

        project_details = self.db_manager.get_project_by_id(project_id)
        if not project_details:
            raise Exception("Project details not found.")

        project_name = project_details['project_name']
        project_root = Path(project_details['project_root_folder'])
        docs_dir = project_root / "docs"
        docs_dir.mkdir(exist_ok=True)

        all_artifacts = self.db_manager.get_all_artifacts_for_project(project_id)
        if not all_artifacts:
            logging.warning("No artifacts found to synthesize specs from.")
            return

        # Consolidate all summaries into a single context block
        summaries_context = "\n\n---\n\n".join(
            f"File: {art['file_path']}\nSummary:\n{art['code_summary']}"
            for art in all_artifacts if art['code_summary']
        )

        # Generate, save, and update DB for each spec type
        app_spec = self._generate_spec(summaries_context, "Application", project_name)
        self._save_and_update_spec(project_id, app_spec, "Application Specification", "application_spec", "final_spec_text", docs_dir, project_name)

        tech_spec = self._generate_spec(summaries_context, "Technical", project_name)
        self._save_and_update_spec(project_id, tech_spec, "Technical Specification", "technical_spec", "tech_spec_text", docs_dir, project_name)

        # Conditionally generate UX/UI spec
        if self._detect_ui_presence(all_artifacts):
            ux_spec = self._generate_spec(summaries_context, "UX/UI", project_name)
            self._save_and_update_spec(project_id, ux_spec, "UX/UI Specification", "ux_ui_spec", "ux_spec_text", docs_dir, project_name)

        logging.info("Specification synthesis complete.")
        return True

    def _generate_spec(self, summaries_context: str, spec_type: str, project_name: str) -> str:
        """Generic method to generate a specific type of specification."""
        logging.info(f"Generating draft {spec_type} Specification...")

        prompt_details = {
            "Application": "Focus on user-facing features, functionality, and user stories.",
            "Technical": "Focus on architecture, technology stack, data models, and component interactions.",
            "UX/UI": "Focus on user personas, user journeys, screen layouts, and a high-level style guide."
        }

        prompt = textwrap.dedent(f"""
            You are an expert technical writer. Your task is to synthesize a collection of code summaries into a coherent, high-level **{spec_type} Specification** document.

            **MANDATORY INSTRUCTIONS:**
            1. **Analyze Summaries:** Read all the provided file summaries to build a holistic understanding of the codebase.
            2. **Synthesize Document:** Write a structured specification document in Markdown format. {prompt_details.get(spec_type, "")}
            3. **Raw Markdown Output:** Your entire response MUST be only the raw content of the Markdown document. Do not include a header, preamble, or any other conversational text.

            **--- Project Name ---**
            {project_name}

            **--- Collection of Code Summaries ---**
            {summaries_context}

            **--- Draft {spec_type} Specification (Markdown) ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Failed to generate {spec_type} Spec: {e}")
            return f"### Error\nAn error occurred during {spec_type} Specification generation: {e}"

    def _detect_ui_presence(self, artifacts: list) -> bool:
        """Heuristic to detect if a project has a significant UI component."""
        ui_extensions = ['.js', '.ts', '.html', '.css', '.scss', '.xaml', '.ui']
        for art in artifacts:
            if Path(art['file_path']).suffix.lower() in ui_extensions:
                return True
        return False

    def _save_and_update_spec(self, project_id, content, doc_type_name, file_base_name, db_field, docs_dir, project_name):
        """Helper to prepend header, save files, and update the database for a spec."""
        # Prepend the generic header
        full_content_with_header = self.orchestrator.prepend_standard_header(content, doc_type_name)

        # Add the user-requested preamble
        preamble = "Note: This document was automatically generated by the system's codebase analysis. It provides a high-level, synthesized overview for human review and verification. For detailed, component-level implementation, the system's downstream processes will refer to a more granular, machine-readable model of the codebase."
        final_content_for_files = f"*{preamble}*\n\n---\n\n" + full_content_with_header

        # Save .md file
        md_path = docs_dir / f"{file_base_name}.md"
        md_path.write_text(final_content_for_files, encoding='utf-8')
        logging.info(f"Saved {doc_type_name} to {md_path}")

        # Save .docx file
        docx_bytes = self.report_generator.generate_text_document_docx(
            title=f"{doc_type_name} - {project_name}",
            content=final_content_for_files
        )
        docx_path = docs_dir / f"{file_base_name}.docx"
        with open(docx_path, 'wb') as f:
            f.write(docx_bytes.getbuffer())
        logging.info(f"Saved {doc_type_name} to {docx_path}")

        # Update the database with the raw content (without the preamble for AI use)
        self.db_manager.update_project_field(project_id, db_field, full_content_with_header)