# agents/agent_spec_synthesis.py

import logging
import textwrap
import json
import os
import subprocess
import re
from gui.utils import render_markdown_to_html
from pathlib import Path
from PySide6.QtGui import QTextDocument
from llm_service import LLMService
from klyve_db_manager import KlyveDBManager
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
        self.report_generator = ReportGeneratorAgent(self.db_manager)
        logging.info("SpecSynthesisAgent initialized.")

    def _detect_database_usage(self, project_root: Path) -> tuple[str | None, dict]:
        """
        Detects database usage in a project using a three-stage funnel.

        Args:
            project_root (Path): The root path of the project to scan.

        Returns:
            A tuple containing the stage of detection ('SCHEMA_FILE', 'KEYWORD')
            or None, and a dictionary mapping file paths to their content.
        """
        logging.info("Starting 3-stage database usage detection...")

        # Stage 1: High-Certainty File Analysis [cite: 196]
        logging.info("DB Detection Stage 1: Searching for high-certainty schema files...")
        schema_files = []
        for ext in ['*.sql']:
            schema_files.extend(project_root.rglob(ext))

        if schema_files:
            logging.info(f"DB Detection Stage 1: Found {len(schema_files)} dedicated schema file(s).")
            file_content = {str(p.relative_to(project_root)): p.read_text(encoding='utf-8', errors='ignore') for p in schema_files}
            return "SCHEMA_FILE", file_content

        # Stage 2: Keyword Heuristic Analysis [cite: 199]
        logging.info("DB Detection Stage 2: Searching for database keywords in source files...")
        db_keywords = [
            'sqlalchemy', 'sqlite3', 'psycopg2', 'mysql.connector',
            'mongoose', 'sequelize', 'knex', 'typeorm', 'prisma',
            'system.data.sqlclient', 'entityframeworkcore', 'dapper',
            'create table', 'select from', 'insert into', 'update set',
            'database', 'dbconnection', 'sqlconnection', 'jdbctemplate'
        ]
        source_extensions = ['.py', '.js', '.ts', '.cs', '.java', '.go', '.rs', '.php', '.rb', '.cpp', '.c', '.swift', '.kt', '.m', '.scala']
        candidate_files = {}

        for dirpath, _, filenames in os.walk(project_root):
            for filename in filenames:
                file_path = Path(dirpath) / filename
                if file_path.suffix.lower() in source_extensions:
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if any(keyword in content.lower() for keyword in db_keywords):
                            candidate_files[str(file_path.relative_to(project_root))] = content
                    except Exception as e:
                        logging.warning(f"Could not read file {file_path} during DB keyword scan: {e}")

        if candidate_files:
            logging.info(f"DB Detection Stage 2: Found {len(candidate_files)} candidate file(s) with keywords.")
            # Stage 3 (synthesis) is handled by the caller, which will use the content of these files. [cite: 204, 205]
            return "KEYWORD", candidate_files

        logging.info("DB Detection Complete: No database usage detected in any stage.")
        return None, {}

    def _validate_and_fix_dot_diagrams(self, markdown_text: str) -> str:
        """
        Scans the markdown for DOT blocks, attempts to render them locally to check for syntax errors,
        and uses the LLM to fix them if they fail.
        """
        # Find all DOT blocks
        dot_blocks = list(re.finditer(r"```dot\s*(.*?)```", markdown_text, re.DOTALL))
        if not dot_blocks:
            return markdown_text

        dot_executable = "dot"

        for match in reversed(dot_blocks):
            original_code = match.group(1)
            try:
                # Dry run using graphviz 'dot'
                subprocess.run(
                    [dot_executable, "-Tpng"],
                    input=original_code.encode('utf-8'),
                    capture_output=True,
                    check=True
                )
                continue
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                error_msg = e.stderr.decode('utf-8') if isinstance(e, subprocess.CalledProcessError) else str(e)
                logging.warning(f"DOT Validation Failed. Attempting AI Fix. Error: {error_msg}")

                # Use standard string to avoid brace collision
                fix_prompt_template = textwrap.dedent("""
                You are a Graphviz DOT expert. The following DOT code caused a syntax error.
                **Error:** <<ERROR_MSG>>
                **Invalid Code:**
                ```dot
                <<ORIGINAL_CODE>>
                ```
                **Task:** Fix the syntax error so it compiles.
                **CRITICAL RULE:** Ensure the graph type is `digraph` (directed graph) if using `->` arrows. Do not use `graph` with `->`.
                **Output:** Return ONLY the fixed DOT code inside a ```dot ... ``` block.
                """)

                fix_prompt = fix_prompt_template.replace("<<ERROR_MSG>>", error_msg)
                fix_prompt = fix_prompt.replace("<<ORIGINAL_CODE>>", original_code)

                try:
                    fixed_response = self.llm_service.generate_text(fix_prompt, task_complexity="simple")
                    code_match = re.search(r"```dot\s*(.*?)```", fixed_response, re.DOTALL)
                    if code_match:
                        fixed_code = code_match.group(1)
                        start, end = match.span(1)
                        markdown_text = markdown_text[:start] + fixed_code + markdown_text[end:]
                        logging.info("DOT Diagram successfully fixed by AI.")
                except Exception as fix_error:
                    logging.error(f"Failed to apply AI fix to DOT diagram: {fix_error}")

        return markdown_text

    def _generate_db_schema_spec(self, detection_stage: str, files_content: dict, project_name: str) -> str:
        """
        Generates the Database Schema Specification document using an LLM.
        """
        logging.info(f"Generating Database Schema Specification from {detection_stage} context...")

        context_str = ""
        for path, content in files_content.items():
            context_str += f"--- File: {path} ---\n{content}\n\n"

        prompt_focus = ""
        if detection_stage == 'SCHEMA_FILE':
            prompt_focus = "The provided context contains .sql files. Parse these files and reverse-engineer the schema."
        else: # KEYWORD
            prompt_focus = "The provided context contains source code with database keywords. Infer the schema from ORM models or SQL strings."

        # FIXED: Use standard string (no 'f' prefix) to avoid brace collision
        prompt_template = textwrap.dedent("""
            You are an expert database administrator. Analyze the provided file contents and generate a clear, professional "Database Schema Specification" document in Markdown format.

            **MANDATORY INSTRUCTIONS:**
            1. **Analyze Content:** <<PROMPT_FOCUS>>
            2. **STRICT MARKDOWN FORMATTING:** Use '##' for main headings and '###' for sub-headings.
            3. **Raw Output:** Your entire response MUST be only the raw Markdown content.

            **DIAGRAMMING RULE (Professional Graphviz ERD):**
            - You MUST generate an **Entity-Relationship Diagram (ERD)**.
            - Use the **DOT language** inside a ```dot ... ``` code block.
            - **Layout & Style:** Use these exact settings:
                `graph [fontname="Arial", fontsize=12, rankdir=LR, splines=ortho, nodesep=0.8, ranksep=1.0, bgcolor="white"];`
                `node [fontname="Arial", fontsize=11, shape=record, style="filled,rounded", fillcolor="#F0F4C3", color="#827717", penwidth=1.5, margin="0.2,0.1"];`
                `edge [fontname="Arial", fontsize=10, color="#555555", penwidth=1.5, arrowsize=0.8];`
            - **Syntax:** Use "record" shapes for tables. Example:
                `Users [label="{{Users|+ ID (PK)\l+ Email\l+ PasswordHash\l}}"];`

            **--- Project Name ---**
            <<PROJECT_NAME>>

            **--- Relevant File Contents ---**
            <<CONTEXT_STR>>

            **--- Draft Database Schema Specification (Markdown) ---**
        """)

        # Safe injection
        prompt = prompt_template.replace("<<PROMPT_FOCUS>>", prompt_focus)
        prompt = prompt.replace("<<PROJECT_NAME>>", project_name)
        prompt = prompt.replace("<<CONTEXT_STR>>", context_str)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            # Apply Self-Correction Loop
            validated_text = self._validate_and_fix_dot_diagrams(response_text)

            return validated_text.strip()
        except Exception as e:
            logging.error(f"Failed to generate Database Schema Spec: {e}")
            raise e

    def synthesize_all_specs(self, project_id: str):
        """
        Orchestrates the generation of all relevant specification documents,
        now with conditional logic for UX/UI and Database Schema specs, and template support.
        """
        logging.info(f"Starting specification synthesis for project {project_id}.")

        try:

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

            summaries_context = "\n\n---\n\n".join(
                f"File: {art['file_path']}\nSummary:\n{art['code_summary']}"
                for art in all_artifacts if art['code_summary']
            )

            # Helper function to load a template
            def get_template(template_name):
                try:
                    template_record = self.db_manager.get_template_by_name(template_name)
                    if template_record:
                        template_path = Path(template_record['file_path'])
                        if template_path.exists():
                            logging.info(f"Found and loaded '{template_name}' template for brownfield generation.")
                            return template_path.read_text(encoding='utf-8')
                except Exception as e:
                    logging.warning(f"Could not load template '{template_name}': {e}")
                return None

            # Generate App Spec with template
            app_spec_template = get_template("Default Application Specification")
            app_spec = self._generate_spec(summaries_context, "Application", project_name, template_content=app_spec_template)
            self._save_and_update_spec(project_id, app_spec, "Application Specification", "application_spec", "final_spec_text", docs_dir, project_name)

            # Generate Tech Spec with template
            tech_spec_template = get_template("Default Technical Specification")
            tech_spec = self._generate_spec(summaries_context, "Technical", project_name, template_content=tech_spec_template)
            self._save_and_update_spec(project_id, tech_spec, "Technical Specification", "technical_spec", "tech_spec_text", docs_dir, project_name)

            # Now that tech spec exists, detect and save all technologies
            try:
                technologies = self.orchestrator.detect_technologies_in_spec(tech_spec)
                if technologies:
                    self.db_manager.update_project_field(project_id, "detected_technologies", json.dumps(technologies))
                    logging.info(f"Detected and saved technologies for brownfield project: {technologies}")
            except Exception as e:
                logging.error(f"Failed to detect technologies during brownfield synthesis: {e}")

            # Conditionally generate UX/UI spec with template
            has_ui = self._detect_ui_presence(all_artifacts, project_root)
            self.db_manager.update_project_field(project_id, "is_gui_project", 1 if has_ui else 0)
            if has_ui:
                ux_spec_template = get_template("Default UX/UI Specification")
                ux_spec = self._generate_spec(summaries_context, "UX/UI", project_name, template_content=ux_spec_template)
                self._save_and_update_spec(project_id, ux_spec, "UX/UI Specification", "ux_ui_spec", "ux_spec_text", docs_dir, project_name)
            else:
                logging.info("Skipping UX/UI Specification generation as no UI components were detected.")

            # Conditionally generate Database Schema spec (no template for this one)
            detection_stage, db_files_content = self._detect_database_usage(project_root)
            if db_files_content:
                db_schema_spec = self._generate_db_schema_spec(detection_stage, db_files_content, project_name)
                self._save_and_update_spec(project_id, db_schema_spec, "Database Schema Specification", "db_schema_spec", "db_schema_spec_text", docs_dir, project_name)
            else:
                logging.info("Skipping Database Schema Specification generation as no database usage was detected.")

            logging.info("Specification synthesis complete.")
            return True

        except Exception as e:
            logging.error(f"Fatal error during spec synthesis: {e}", exc_info=True)
            raise e # Re-raise to be caught by the worker

    def _generate_spec(self, summaries_context: str, spec_type: str, project_name: str, template_content: str | None = None) -> str:
        """Generic method to generate a specific type of specification with Professional Graphviz diagrams."""
        logging.info(f"Generating draft {spec_type} Specification...")

        template_instruction = ""
        if template_content:
            template_instruction = textwrap.dedent(f"""
            **CRITICAL TEMPLATE INSTRUCTION:**
            Strictly follow the structure of the provided template.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        prompt_details = {
            "Application": "Focus on user-facing features and user stories.",
            "Technical": "Focus on architecture, technology stack, and data models.",
            "UX/UI": "Focus on user personas, journeys, and screen layouts."
        }

        # Define specific placement rules for each document type
        placement_map = {
            "Application": "inside the 'System Overview' or 'Functional Architecture' section, immediately after the header.",
            "Technical": "inside the 'High-Level Architecture' section, immediately after the header.",
            "UX/UI": "inside the 'Navigation Structure' or 'Site Map' section, immediately after the header."
        }
        placement_rule = placement_map.get(spec_type, "at the beginning of the detailed architecture section.")

        # Use standard string (no 'f' prefix) to avoid brace collision
        prompt_template = textwrap.dedent("""
            You are an expert technical writer. Synthesize the code summaries into a high-level **<<SPEC_TYPE>> Specification**.

            **MANDATORY INSTRUCTIONS:**
            1. **Synthesize Document:** Write a structured specification in Markdown. <<PROMPT_DETAIL>>
            2. **Raw Output:** Return only the Markdown content.

            **DIAGRAMMING RULE (Professional Graphviz):**
            - Generate 1 key diagram relevant to the spec type.
            - Use the **DOT language** inside a ```dot ... ``` code block.
            - **SCOPE:** Create a **"High-Level Module View"**. Group classes/files into logical modules/namespaces. Do NOT create a node for every single file.
            - **CRITICAL:** You MUST use `digraph G {` (directed graph). Do NOT use `graph {`.
            - **PLACEMENT:** You MUST place this diagram <<PLACEMENT_INSTRUCTION>>
            - **Layout & Style:** Use these exact settings:
                `graph [fontname="Arial", fontsize=12, rankdir=TB, splines=ortho, nodesep=0.8, ranksep=1.0, bgcolor="white"];`
                `node [fontname="Arial", fontsize=12, shape=box, style="filled,rounded", fillcolor="#F3E5F5", color="#7B1FA2", penwidth=1.5, margin="0.2,0.1"];`
                `edge [fontname="Arial", fontsize=10, color="#555555", penwidth=1.5, arrowsize=0.8];`

            <<TEMPLATE_INSTRUCTION>>

            **--- Project Name ---**
            <<PROJECT_NAME>>

            **--- Code Summaries ---**
            <<SUMMARIES_CONTEXT>>

            **--- Draft <<SPEC_TYPE>> Specification (Markdown) ---**
        """)

        # Safe injection
        prompt = prompt_template.replace("<<SPEC_TYPE>>", spec_type)
        prompt = prompt.replace("<<PROMPT_DETAIL>>", prompt_details.get(spec_type, ""))
        prompt = prompt.replace("<<PLACEMENT_INSTRUCTION>>", placement_rule)
        prompt = prompt.replace("<<TEMPLATE_INSTRUCTION>>", template_instruction)
        prompt = prompt.replace("<<PROJECT_NAME>>", project_name)
        prompt = prompt.replace("<<SUMMARIES_CONTEXT>>", summaries_context)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            # Apply Self-Correction Loop
            validated_text = self._validate_and_fix_dot_diagrams(response_text)

            return validated_text.strip()
        except Exception as e:
            logging.error(f"Failed to generate {spec_type} Spec: {e}")
            raise e

    def _detect_ui_presence(self, all_artifacts: list, project_root: Path) -> bool:
        """
        Heuristic to detect if a project has a significant UI component by
        checking file extensions and file content for UI-related keywords.
        """
        logging.info("Starting 2-level UI presence detection...")

        # Level 1: File Type Analysis [cite: 2241]
        ui_extensions = ['.js', '.ts', '.html', '.css', '.scss', '.xaml', '.ui']
        for art in all_artifacts:
            if Path(art['file_path']).suffix.lower() in ui_extensions:
                logging.info(f"UI Detection Level 1: Found UI file extension in '{art['file_path']}'.")
                return True

        # Level 2: Content Heuristic Analysis [cite: 2242]
        logging.info("UI Detection Level 2: Searching for UI keywords in source files...")
        ui_keywords = [
            # Python
            'pyside6', 'pyqt5', 'tkinter', 'kivy', 'wxpython',
            # JS/TS Frameworks
            'react', 'angular', 'vue', 'svelte',
            # .NET
            'wpf', 'winforms', 'avalonia', 'maui',
            # Java
            'javafx', 'swing',
            # General
            'user interface', 'gui'
        ]

        for art in all_artifacts:
            try:
                # We need the full path to read the file content
                file_path = project_root / art['file_path']
                if file_path.exists() and file_path.is_file():
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if any(keyword in content.lower() for keyword in ui_keywords):
                        logging.info(f"UI Detection Level 2: Found UI keyword in '{art['file_path']}'.")
                        return True
            except Exception as e:
                logging.warning(f"Could not read file {art['file_path']} during UI keyword scan: {e}")

        logging.info("UI Detection Complete: No UI components detected.")
        return False

    def _save_and_update_spec(self, project_id, content, doc_type_name, file_base_name, db_field, docs_dir, project_name):
        """Helper to prepend header, save files, and update the database for a spec."""
        # Prepend the generic header
        full_content_with_header = self.orchestrator.prepend_standard_header(content, doc_type_name)

        # Add the user-requested preamble
        preamble = "Note: This document was automatically generated by the system's codebase analysis. It provides a high-level, synthesized overview for human review and verification. For detailed, component-level implementation, the system's downstream processes will refer to a more granular, machine-readable model of the codebase."
        final_content_for_files = f"*{preamble}*\n\n---\n\n" + full_content_with_header

        # We render the *full* content (including header) for the .docx file
        # html_for_docx = render_markdown_to_html(final_content_for_files)

        # Save .md file (This should save the raw, headed markdown as it's a .md file)
        md_path = docs_dir / f"{file_base_name}.md"
        md_path.write_text(final_content_for_files, encoding='utf-8')
        logging.info(f"Saved {doc_type_name} to {md_path}")

        # Save .docx file
        docx_bytes = self.report_generator.generate_text_document_docx(
            title=f"{doc_type_name} - {project_name}",
            content=final_content_for_files,
            is_html=False
        )
        docx_path = docs_dir / f"{file_base_name}.docx"
        with open(docx_path, 'wb') as f:
            f.write(docx_bytes.getbuffer())
        logging.info(f"Saved {doc_type_name} to {docx_path}")

        # Update the database with the raw content (without the preamble for AI use)
        # We must convert the markdown to plain text for downstream agents
        doc = QTextDocument()
        doc.setMarkdown(full_content_with_header)
        plain_text_content = doc.toPlainText()

        self.db_manager.update_project_field(project_id, db_field, plain_text_content)