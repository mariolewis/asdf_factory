# agent_spec_clarification.py

"""
This module contains the SpecClarificationAgent class.

This agent is responsible for managing the interactive clarification loop with the
PM to resolve ambiguities in a specification draft, including database details.
(ASDF Dev Plan v0.2, F-Dev 2.3)
"""

import logging
import textwrap
import re
import google.generativeai as genai
from typing import List
from asdf_db_manager import ASDFDBManager


class SpecClarificationAgent:
    """
    Analyzes specifications, identifies ambiguities, and interacts with the PM
    to produce a complete and clear specification document.
    """

    def __init__(self, api_key: str, db_manager: ASDFDBManager):
        """
        Initializes the SpecClarificationAgent.

        Args:
            api_key (str): The Gemini API key for LLM interactions.
            db_manager (ASDFDBManager): An instance of the database manager for KB access.
        """
        if not api_key:
            raise ValueError("API key is required for the SpecClarificationAgent.")
        if not db_manager:
            raise ValueError("Database manager is required for the SpecClarificationAgent.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.db_manager = db_manager

        # As per the PRD, the clarification loop must handle DB table specs.
        # [cite_start]This was confirmed by the PM. [cite: 218, 228]

    def _extract_tags_from_spec(self, spec_text: str) -> list[str]:
        """A simple helper to extract potential search tags from spec text."""
        # Find capitalized words that might be features or nouns
        keywords = re.findall(r'\b[A-Z][a-zA-Z]{3,}\b', spec_text)
        # Combine, lowercase, and get unique tags
        tags = set(kw.lower() for kw in keywords)
        return list(tags)

    def expand_brief_description(self, brief_description: str) -> str:
        """
        Expands a brief user description into a detailed draft specification
        by calling the generative AI model.
        (ASDF PRD v0.2, Phase 1, Option B)

        Args:
            brief_description: The user-provided brief description.

        Returns:
            The AI-generated detailed specification draft as a string.

        Raises:
            Exception: If the API call fails or returns an empty response.
        """
        # The prompt instructs the AI on its role and the required output format,
        # including the critical requirement for database table specs.
        prompt = textwrap.dedent(f"""
            As an expert software architect, expand the following brief application description into a detailed, structured draft specification.
            The draft should be comprehensive and well-organized, suitable for a development team to begin work.
            Crucially, if the description implies the need for data storage, include a dedicated 'Database Schema' section with detailed specifications for the necessary database tables, including column names, data types (e.g., TEXT, INTEGER, REAL, BLOB), and descriptions for each column.

            The user's brief description is:
            ---
            {brief_description}
            ---
        """)

        try:
            logging.info("Calling Gemini API to expand brief description...")
            response = self.model.generate_content(prompt)

            if not response.text:
                raise ValueError("The AI model returned an empty response.")

            logging.info("Successfully received expanded specification from API.")
            return response.text
        except Exception as e:
            logging.error(f"Gemini API call failed during spec expansion: {e}")
            # Re-raise the exception so the UI layer can catch it and display an error.
            raise

    def identify_potential_issues(self, spec_text: str) -> str:
        """
        Analyzes a specification draft to identify ambiguities, contradictions,
        or underspecified areas by calling the generative AI model. It first
        checks the knowledge base for existing solutions.

        Args:
            spec_text: The full text of the specification draft.

        Returns:
            A string containing a list of potential issues identified by the AI,
            potentially prefixed with insights from the knowledge base.

        Raises:
            Exception: If the API call fails or returns an empty response.
        """
        # --- Step 1: Query the Knowledge Base ---
        kb_prefix = ""
        logging.info("SpecClarificationAgent: Querying Knowledge Base for similar specs.")
        tags = self._extract_tags_from_spec(spec_text)
        if tags:
            try:
                with self.db_manager as db:
                    kb_results = db.query_kb_by_tags(tags)
                if kb_results:
                    solution = kb_results[0]['solution']
                    logging.info(f"SpecClarificationAgent: Found relevant clarification in Knowledge Base (ID: {kb_results[0]['entry_id']}).")
                    kb_prefix = f"**Suggestion from Knowledge Base:**\nA similar issue was previously resolved with the following clarification: *'{solution}'*\\n\\n---\n\n"
            except Exception as e:
                logging.warning(f"SpecClarificationAgent: Failed to query Knowledge Base. Error: {e}")

        # --- Step 2: Proceed with LLM analysis ---
        logging.info("SpecClarificationAgent: Calling Gemini API to identify potential spec issues...")
        prompt = textwrap.dedent(f"""
            As an expert requirements analyst, please review the following software specification draft.
            Your task is to identify and list any ambiguities, contradictions, underspecified features, or missing information that would prevent a developer from building the application without making assumptions.
            Pay close attention to:
            - Vague requirements (e.g., "fast", "user-friendly").
            - Undefined user flows.
            - Incomplete or conflicting business logic.
            - Missing details in the database schema (e.g., missing columns, unclear relationships, unspecified data types).
            - Unclear error handling conditions.

            Present your findings as a numbered list of issues. For each issue, briefly explain the problem. If you find no issues, please state that the specification appears to be clear and complete.

            The specification draft is:
            ---
            {spec_text}
            ---
        """)

        try:
            response = self.model.generate_content(prompt)

            if not response.text:
                raise ValueError("The AI model returned an empty response when identifying issues.")

            logging.info("Successfully received issue analysis from API.")
            # Prepend the knowledge base finding (if any) to the fresh analysis
            return kb_prefix + response.text

        except Exception as e:
            logging.error(f"Gemini API call failed during issue identification: {e}")
            raise

    def refine_specification(self, original_spec_text: str, issues_found: str, pm_clarification: str) -> str:
        """
        Refines the specification draft based on PM feedback.

        This method takes the original spec, the issues identified by the AI,
        and the PM's clarification, and generates a new version of the spec.

        Args:
            original_spec_text: The current version of the specification.
            issues_found: The list of issues the AI previously identified.
            pm_clarification: The PM's response to address the issues.

        Returns:
            The revised specification text.

        Raises:
            Exception: If the API call fails or returns an empty response.
        """
        prompt = textwrap.dedent(f"""
            As an expert software architect, your task is to revise a software specification draft.
            You have the original draft, a list of issues previously identified with it, and a set of clarifications from the Product Manager (PM).

            Your goal is to integrate the PM's clarifications to resolve the identified issues and produce a new, more complete, and unambiguous version of the specification. Do not omit any parts of the original specification that were not discussed; only modify the parts that are affected by the clarifications. Ensure the new version is a complete, standalone document.

            **Original Specification Draft:**
            ---
            {original_spec_text}
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
            logging.info("Calling Gemini API to refine the specification...")
            response = self.model.generate_content(prompt)
            if not response.text:
                raise ValueError("The AI model returned an empty response during refinement.")
            logging.info("Successfully received refined specification from API.")
            return response.text
        except Exception as e:
            logging.error(f"Gemini API call failed during spec refinement: {e}")
            raise