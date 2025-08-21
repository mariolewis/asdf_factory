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
            **CRITICAL TEMPLATE INSTRUCTION:** You MUST use the following template to structure your entire response. Adhere to its headings, formatting, and style. Populate the template with content derived from the user's brief.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        prompt = textwrap.dedent(f"""
            You are an expert Business Analyst. Your task is to expand the following brief description into a detailed, structured Application Specification.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the specification document. Do not include any preamble, introduction, or conversational text.

            {template_instruction}

            **MANDATORY INSTRUCTIONS:**
            1.  **Technology Agnostic:** Your response MUST be purely functional and non-functional. You MUST NOT include any recommendations for specific programming languages, frameworks, databases, or technology stacks.
            2.  **User-Specified Tech:** The only exception is if the user's brief explicitly commands the use of a specific technology. In that case, you must include it.
            3.  **Logical Data Schema:** If the description implies data storage, include a 'Data Schema' section. Describe the tables and columns using logical data types (e.g., Text, Number, Date), not physical SQL types (e.g., VARCHAR, INT).
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
            1.  Identify any ambiguities, contradictions, underspecified features, or missing information.
            2.  For each issue you identify, you MUST propose 1-2 concrete potential solutions or clarifying options for the Product Manager to consider.
            3.  Structure your response as a numbered list. For each item, clearly state the "Issue" and then provide the "Proposed Solutions".
            4.  If you find no issues, your entire response MUST be the single phrase: "No significant issues found."

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
            As an expert software architect, your task is to revise a software specification draft.
            You have the current draft, a list of issues previously identified with it, and a set of clarifications from the Product Manager (PM).

            Your goal is to integrate the PM's clarifications to resolve the identified issues and produce a new, more complete, and unambiguous version of the specification.

            **MANDATORY INSTRUCTIONS:**
            1.  **Preserve Header**: The document has a standard header (Project Number, Type, Date, Version). You MUST preserve this header and its structure exactly as it is.
            2.  **Modify Body Only**: Your changes should only be in the body of the document based on the PM's clarifications.
            3.  **Complete Document**: Ensure the new version is a complete, standalone document including the preserved header.
            {fallback_instruction}
            **Current Specification Draft:**
            ---
            {current_draft_text}
            ---

            **Issues You Identified:**
            ---
            {issues_found}
            ---

            **Product Manager's Clarifications:**
            ---
            {pm_clarification}
            ---

            Please provide the complete, revised specification draft below.
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