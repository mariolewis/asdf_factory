# agents/agent_spec_clarification.py

"""
This module contains the SpecClarificationAgent class.
"""

import logging
import textwrap
import re
from typing import List
from asdf_db_manager import ASDFDBManager
from llm_service import LLMService


class SpecClarificationAgent:
    """
    Analyzes specifications, identifies ambiguities, and interacts with the PM
    to produce a complete and clear specification document.
    """

    def __init__(self, llm_service: LLMService, db_manager: ASDFDBManager):
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

        Args:
            project_brief (str): The original project brief for non-GUI requirements.
            ux_spec_markdown (str): The UX/UI spec for contextual information like personas.
            ui_blueprint_json (str): The definitive JSON blueprint for UI structure.

        Returns:
            A string containing the consolidated requirements document.
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

    def expand_brief_description(self, brief_description: str, is_gui_project: bool = False, template_content: str | None = None) -> str:
        """
        Expands a brief user description into a detailed draft specification.
        """
        fallback_instruction = ""
        if is_gui_project:
            fallback_instruction = textwrap.dedent("""
            4.  **UI/UX Fallback Section:** Because this is a GUI application, you MUST include a section titled "UI Layout & Style Guide". In this section, provide a basic, high-level guide for a consistent look and feel, including suggestions for a color palette, typography, and general layout principles.
            """)

        template_instruction = ""
        if template_content:
            template_instruction = textwrap.dedent(f"""
            **CRITICAL TEMPLATE INSTRUCTION:**
            Your entire output MUST strictly and exactly follow the structure, headings, and formatting of the provided template.
            Populate the sections of the template with content derived from the user's brief.
            DO NOT invent new sections. DO NOT change the names of the headings from the template.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        prompt = textwrap.dedent(f"""
            You are an expert Business Analyst. Your task is to expand the following brief description into a detailed, structured Application Specification.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the specification document. Do not include any preamble, introduction, or conversational text.

            {template_instruction}

            **MANDATORY INSTRUCTIONS:**
            1.  **STRICT MARKDOWN FORMATTING:** You MUST use Markdown for all formatting. Use '##' for main headings and '###' for sub-headings. For lists, each item MUST start on a new line with an asterisk and a space (e.g., "* List item text."). Paragraphs MUST be separated by a full blank line. This is mandatory.
            2.  **Technology Agnostic:** Your response MUST be purely functional and non-functional. You MUST NOT include any recommendations for specific programming languages, frameworks, databases, or technology stacks.
            3.  **User-Specified Tech:** The only exception is if the user's brief explicitly commands the use of a specific technology. In that case, you must include it.
            4.  **Logical Data Schema:** If the description implies data storage, include a 'Data Schema' section. Describe the tables and columns using logical data types (e.g., Text, Number, Date), not physical SQL types (e.g., VARCHAR, INT).
            {fallback_instruction}
            The user's brief description is:
            ---
            {brief_description}
            ---
        """)

        try:
            logging.info("Calling LLM service to expand brief description...")
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            if not response_text:
                raise ValueError("The LLM service returned an empty response.")

            logging.info("Successfully received expanded specification from LLM service.")
            return response_text
        except Exception as e:
            logging.error(f"LLM service call failed during spec expansion: {e}")
            raise

    def identify_potential_issues(self, spec_text: str, iteration_count: int) -> str:
        """
        Analyzes a specification draft to identify ambiguities, narrowing focus on later iterations.
        """
        kb_prefix = ""
        logging.info(f"SpecClarificationAgent: Identifying issues for iteration {iteration_count}.")

        # Knowledge base query remains the same
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
            convergence_directive = textwrap.dedent("""
            **IMPORTANT - CONVERGENCE DIRECTIVE:**
            This is refinement iteration {iteration_count}. You MUST focus ONLY on high or medium-severity issues such as logical contradictions, missing critical functionality, or significant ambiguities. IGNORE low-severity stylistic points or trivial suggestions.
            """)

        prompt = textwrap.dedent(f"""
            You are an expert requirements analyst. Your task is to review the following software specification draft.
            Your goal is to identify ambiguities and guide the Product Manager to a clear, actionable resolution.

            {convergence_directive}

            **MANDATORY INSTRUCTIONS:**
            1.  **STRICT MARKDOWN FORMATTING:** Your entire response must be in raw Markdown. Use '##' for main headings and '###' for sub-headings. For lists, each item MUST start on a new line with a '*' character. Paragraphs MUST be separated by a full blank line. This is mandatory.
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

    def refine_specification(self, current_draft_text: str, issues_found: str, pm_clarification: str, is_gui_project: bool = False) -> str:
        """
        Refines the specification draft based on PM feedback.
        """
        fallback_instruction = ""
        if is_gui_project:
            fallback_instruction = textwrap.dedent("""
            **IMPORTANT:** This is a GUI application. Ensure your revised output includes a complete section titled "UI Layout & Style Guide" based on all available information.
            """)

        prompt = textwrap.dedent(f"""
            You are an expert software architect revising a document. Your task is to take the body of a software specification and refine it based on a list of identified issues and specific feedback from a Product Manager.

            **MANDATORY INSTRUCTIONS:**
            1.  **Refine Body Only**: The text you receive is only the body of a document. Your task is to incorporate the PM's clarifications to resolve the identified issues.
            2.  **RAW MARKDOWN ONLY:** Your entire response MUST be only the raw, refined text of the document's body. Do not add a header, preamble, introduction, or any conversational text.
            3.  **STRICT MARKDOWN FORMATTING:** You MUST use Markdown for all formatting (e.g., '##' for headings).

            **--- INPUT 1: Current Draft Body ---**
            ```markdown
            {current_draft_text}
            ```

            **--- INPUT 2: Issues Previously Identified ---**
            ```
            {issues_found}
            ```

            **--- INPUT 3: Product Manager's Clarifications to Implement ---**
            ```
            {pm_clarification}
            ```

            **--- Refined Document Body (Raw Markdown Output) ---**
        """)

        try:
            logging.info("Calling LLM service to refine the specification...")
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            if not response_text:
                raise ValueError("The LLM service returned an empty response during refinement.")
            logging.info("Successfully received refined specification from LLM service.")
            return response_text
        except Exception as e:
            logging.error(f"LLM service call failed during spec refinement: {e}")
            raise