# agents/agent_spec_clarification.py

"""
This module contains the SpecClarificationAgent class.
"""

import logging
import textwrap
import re
import subprocess
from typing import List
from klyve_db_manager import KlyveDBManager
from llm_service import LLMService


class SpecClarificationAgent:
    """
    Analyzes specifications, identifies ambiguities, and interacts with the PM
    to produce a complete and clear specification document.
    """

    def __init__(self, llm_service: LLMService, db_manager: KlyveDBManager):
        """
        Initializes the SpecClarificationAgent.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the SpecClarificationAgent.")
        if not db_manager:
            raise ValueError("Database manager is required for the SpecClarificationAgent.")

        self.llm_service = llm_service
        self.db_manager = db_manager

    def consolidate_requirements(self, project_brief: str, ux_spec_markdown: str, ui_blueprint_json: str) -> str:
        """
        Consolidates three sources of requirements into a single document using an LLM.
        """
        logging.info("SpecClarificationAgent: Consolidating multiple requirement sources...")

        prompt = textwrap.dedent(f"""
            You are an expert Business Analyst and Technical Writer. Your task is to consolidate three sources of project requirements (a project brief, a UX/UI specification, and a UI blueprint JSON) into a single, coherent, and comprehensive 'Consolidated Requirements Document'.

            **MANDATORY INSTRUCTIONS:**
            1.  **Prioritize Inputs:** You MUST use the inputs according to this hierarchy:
                -   **Highest Priority:** The UI Blueprint JSON is the definitive source of truth for all UI screens, components, and their structure. It overrides any conflicting UI descriptions in the other documents.
                -   **Medium Priority:** The UX/UI Specification Markdown should be used for contextual information like User Personas, User Journeys, and Theming, but NOT for UI structure if it conflicts with the JSON.
                -   **Lowest Priority:** The Original Project Brief is the source of truth for all **non-GUI requirements** (e.g., backend logic, services, data handling, performance requirements). You MUST preserve these.
            2.  **Check for Discrepancies:** You MUST compare the screens listed in the UI Blueprint JSON against those described in the UX/UI Spec Markdown. If you detect that screens have been added or removed, you MUST insert a section at the top of your output titled "## Note to the Product Manager" and use a bulleted list to flag these discrepancies for review.
            3.  **Output Format:** Your entire response MUST be the raw, consolidated Markdown document. Do not include any conversational text, preamble, or explanations.

            ---
            **INPUT 1: UI Blueprint (JSON - Highest Priority for UI)**
            ```json
            {ui_blueprint_json}
            ```
            ---
            **INPUT 2: UX/UI Specification (Markdown - For UX Context)**
            ```markdown
            {ux_spec_markdown}
            ```
            ---
            **INPUT 3: Original Project Brief (For all Non-GUI Requirements)**
            ```
            {project_brief}
            ```
            ---
            **OUTPUT: Consolidated Requirements Document (Raw Markdown)**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            if not response_text or response_text.startswith("Error:"):
                raise ValueError(f"LLM returned an error or empty response: {response_text}")
            return response_text
        except Exception as e:
            logging.error(f"Failed during requirements consolidation: {e}")
            return f"### Error\nAn unexpected error occurred during requirements consolidation: {e}"

    def _extract_tags_from_spec(self, spec_text: str) -> list[str]:
        """A simple helper to extract potential search tags from spec text."""
        keywords = re.findall(r'\b[A-Z][a-zA-Z]{3,}\b', spec_text)
        tags = set(kw.lower() for kw in keywords)
        return list(tags)

    def _validate_and_fix_dot_diagrams(self, markdown_text: str) -> str:
        """
        Scans the markdown for DOT blocks, attempts to render them locally to check for syntax errors,
        and uses the LLM to fix them if they fail.
        """
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

    def expand_brief_description(self, brief_description: str, is_gui_project: bool = False, template_content: str | None = None) -> str:
        """
        Expands a brief user description into a detailed draft specification using Professional Graphviz style.
        """
        fallback_instruction = ""
        if is_gui_project:
            fallback_instruction = textwrap.dedent("""
            4.  **UI/UX Fallback Section:** Include a section titled "UI Layout & Style Guide" with high-level look and feel suggestions.
            """)

        template_instruction = ""
        if template_content:
            template_instruction = textwrap.dedent(f"""
            **CRITICAL TEMPLATE INSTRUCTION:**
            Your entire output MUST strictly and exactly follow the structure, headings, and formatting of the provided template.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        # Use standard string (no 'f' prefix)
        prompt_template = textwrap.dedent("""
            You are an expert Business Analyst. Your task is to expand the following brief description into a detailed, structured Application Specification.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the specification document. Do not include any preamble.

            <<TEMPLATE_INSTRUCTION>>

            **MANDATORY INSTRUCTIONS:**
            1.  **STRICT MARKDOWN FORMATTING:** Use '##' for main headings and '###' for sub-headings. Paragraphs MUST be separated by a full blank line.
            2.  **Technology Agnostic:** Requirements must be purely functional. Do NOT recommend specific stacks unless explicitly requested.

            **SECTION REQUIREMENTS:**
            If no template is provided, you MUST generate a document containing the following sections in this exact order:

            `## 1. Executive Summary`
            High-level project overview.

            `## 2. User Personas`
            Detailed profiles of key users.

            `## 3. Functional Requirements (Epics & Features)`
            **CRITICAL:** Start this section by generating a **"High-Level Use Case Diagram"**.

            **DIAGRAMMING RULE (Professional Graphviz):**
            - Use the **DOT language** inside a ```dot ... ``` code block.
            - **CRITICAL:** You MUST use `digraph G {` (directed graph). Do NOT use `graph {`.
            - **Layout & Style:** Use these exact settings for a professional look:
                `graph [fontname="Arial", fontsize=12, rankdir=LR, splines=ortho, nodesep=0.8, ranksep=1.0, bgcolor="white"];`
                `node [fontname="Arial", fontsize=12, shape=note, style="filled,rounded", fillcolor="#FFF9C4", color="#FBC02D", penwidth=1.5, margin="0.2,0.1"];`
                `edge [fontname="Arial", fontsize=10, color="#555555", penwidth=1.5, arrowsize=0.8];`
            - **Content:** Diagram the interactions between the Actors (from Section 2) and the Core Epics.

            `## 4. Non-Functional Requirements`
            Performance, Security, Reliability.

            `## 5. Data Requirements`
            High-level entities (not a full schema).

            <<FALLBACK_INSTRUCTION>>

            The user's brief description is:
            ---
            <<BRIEF_DESCRIPTION>>
            ---
        """)

        # Manually inject variables
        prompt = prompt_template.replace("<<TEMPLATE_INSTRUCTION>>", template_instruction)
        prompt = prompt.replace("<<FALLBACK_INSTRUCTION>>", fallback_instruction)
        prompt = prompt.replace("<<BRIEF_DESCRIPTION>>", brief_description)

        try:
            logging.info("Calling LLM service to expand brief description...")
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            # Apply Self-Correction Loop
            validated_text = self._validate_and_fix_dot_diagrams(response_text)

            logging.info("Successfully received and validated expanded specification.")
            return validated_text
        except Exception as e:
            logging.error(f"LLM service call failed during spec expansion: {e}")
            raise

    def identify_potential_issues(self, spec_text: str, iteration_count: int) -> str:
        """
        Analyzes a specification draft to identify ambiguities, narrowing focus on later iterations.
        """
        kb_prefix = ""
        logging.info(f"SpecClarificationAgent: Identifying issues for iteration {iteration_count}.")

        tags = self._extract_tags_from_spec(spec_text)
        if tags:
            try:
                kb_results = self.db_manager.query_kb_by_tags(tags)
                if kb_results:
                    solution = kb_results[0]['solution']
                    logging.info(f"SpecClarificationAgent: Found relevant clarification in Knowledge Base (ID: {kb_results[0]['entry_id']}).")
                    kb_prefix = f"**Suggestion from Knowledge Base:**\nA similar issue was previously resolved with the following clarification: *'{solution}'*\\n\\n---\n\n"
            except Exception as e:
                logging.warning(f"SpecClarificationAgent: Failed to query Knowledge Base. Error: {e}")

        convergence_directive = ""
        if iteration_count > 1:
            convergence_directive = textwrap.dedent(f"""
            **IMPORTANT - CONVERGENCE DIRECTIVE:**
            This is refinement iteration {iteration_count}. You MUST focus ONLY on high or medium-severity issues such as logical contradictions, missing critical functionality, or significant ambiguities. IGNORE low-severity stylistic points or trivial suggestions.
            """)

        prompt = textwrap.dedent(f"""
            You are an expert requirements analyst. Your task is to review the following software specification draft.
            Your goal is to identify ambiguities and guide the Product Manager to a clear, actionable resolution.

            {convergence_directive}

            **MANDATORY INSTRUCTIONS:**

            1.  **STRICT MARKDOWN FORMATTING:** Use '##' for main headings.
            2.  Identify any ambiguities, contradictions, underspecified features, or missing information.
            3.  For each issue you identify, you MUST propose 1-2 concrete potential solutions or clarifying options for the Product Manager to consider.
            4.  Structure your response as a numbered list. For each item, clearly state the "Issue" and then provide the "Proposed Solutions".
            5.  If you find no issues, your entire response MUST be the single phrase: "No significant issues found."

            **The specification draft is:**
            ---
            {spec_text}
            ---
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            if not response_text:
                raise ValueError("The LLM service returned an empty response when identifying issues.")

            logging.info("Successfully received issue analysis from LLM service.")
            return kb_prefix + response_text

        except Exception as e:
            logging.error(f"LLM service call failed during issue identification: {e}")
            raise

    def refine_specification(self, current_draft_text: str, issues_found: str, pm_clarification: str, is_gui_project: bool = False, template_content: str | None = None) -> str:
        """
        Refines the specification draft based on PM feedback.
        """
        fallback_instruction = ""
        if is_gui_project:
            fallback_instruction = textwrap.dedent("""
            **IMPORTANT:** This is a GUI application. Ensure your revised output includes a complete section titled "UI Layout & Style Guide" based on all available information.
            """)

        template_instruction = ""
        if template_content:
            template_instruction = textwrap.dedent(f"""
            **CRITICAL TEMPLATE INSTRUCTION:**
            The original draft was based on a template. Your refined output MUST also strictly and exactly follow the structure, headings, and formatting of that same template.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        # Use standard string to avoid brace collisions
        prompt_template = textwrap.dedent("""
            You are an expert software architect revising a document. Your task is to take the body of a software specification and refine it based on a list of identified issues and specific feedback from a Product Manager.

            **MANDATORY INSTRUCTIONS:**
            1.  **Refine Body Only**: The text you receive is only the body of a document. Your task is to incorporate the PM's clarifications to resolve the identified issues.
            2.  **RAW MARKDOWN ONLY**: Your entire response MUST be only the raw, refined text of the document's body. Do not add a header, preamble, introduction, or any conversational text.
            3.  **STRICT MARKDOWN FORMATTING:** You MUST use Markdown for all formatting (e.g., '##' for headings).

            **DIAGRAMMING RULE (Professional Graphviz):**
            - If you update or regenerate the diagram, you MUST use the **DOT language** inside a ```dot ... ``` code block.
            - **SCOPE:** Maintain a **"High-Level Use Case Diagram"**. Map **Actors** to **Core Epics/Features**. Do NOT attempt to diagram every granular User Story. Keep it readable.
            - **CRITICAL:** You MUST use `digraph G {` (directed graph). Do NOT use `graph {`.
            - **Layout & Style:** Use these exact settings:
                `graph [fontname="Arial", fontsize=12, rankdir=LR, splines=ortho, nodesep=0.8, ranksep=1.0, bgcolor="white"];`
                `node [fontname="Arial", fontsize=12, shape=note, style="filled,rounded", fillcolor="#FFF9C4", color="#FBC02D", penwidth=1.5, margin="0.2,0.1"];`
                `edge [fontname="Arial", fontsize=10, color="#555555", penwidth=1.5, arrowsize=0.8];`

            <<FALLBACK_INSTRUCTION>>
            <<TEMPLATE_INSTRUCTION>>

            **--- INPUT 1: Current Draft Body ---**
            ```markdown
            <<CURRENT_DRAFT>>
            ```

            **--- INPUT 2: Issues Previously Identified ---**
            ```
            <<ISSUES_FOUND>>
            ```

            **--- INPUT 3: Product Manager's Clarifications to Implement ---**
            ```
            <<PM_CLARIFICATION>>
            ```

            **--- Refined Document Body (Raw Markdown Output) ---**
        """)

        prompt = prompt_template.replace("<<FALLBACK_INSTRUCTION>>", fallback_instruction)
        prompt = prompt.replace("<<TEMPLATE_INSTRUCTION>>", template_instruction)
        prompt = prompt.replace("<<CURRENT_DRAFT>>", current_draft_text)
        prompt = prompt.replace("<<ISSUES_FOUND>>", issues_found)
        prompt = prompt.replace("<<PM_CLARIFICATION>>", pm_clarification)

        try:
            logging.info("Calling LLM service to refine the specification...")
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            if not response_text:
                raise ValueError("The LLM service returned an empty response during refinement.")

            # Apply Self-Correction Loop
            validated_text = self._validate_and_fix_dot_diagrams(response_text)

            logging.info("Successfully received refined specification from LLM service.")
            return validated_text
        except Exception as e:
            logging.error(f"LLM service call failed during spec refinement: {e}")
            raise