# agent_spec_clarification.py

"""
This module contains the SpecClarificationAgent class.

This agent is responsible for managing the interactive clarification loop with the
PM to resolve ambiguities in a specification draft, including database details.
(ASDF Dev Plan v0.2, F-Dev 2.3)
"""

import logging
import textwrap
import google.generativeai as genai
from typing import List

class SpecClarificationAgent:
    """
    Analyzes specifications, identifies ambiguities, and interacts with the PM
    to produce a complete and clear specification document.
    """

    def __init__(self, api_key: str):
        """
        Initializes the SpecClarificationAgent.

        Args:
            api_key (str): The Gemini API key for LLM interactions.
        """
        if not api_key:
            raise ValueError("API key is required for the SpecClarificationAgent.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

        # As per the PRD, the clarification loop must handle DB table specs.
        # [cite_start]This was confirmed by the PM. [cite: 218, 228]

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
        or underspecified areas by calling the generative AI model.

        Args:
            spec_text: The full text of the specification draft.

        Returns:
            A string containing a list of potential issues identified by the AI.

        Raises:
            Exception: If the API call fails or returns an empty response.
        """
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
            logging.info("Calling Gemini API to identify potential spec issues...")
            response = self.model.generate_content(prompt)

            if not response.text:
                raise ValueError("The AI model returned an empty response when identifying issues.")

            logging.info("Successfully received issue analysis from API.")
            return response.text
        except Exception as e:
            logging.error(f"Gemini API call failed during issue identification: {e}")
            raise

    def run_clarification_loop(self, spec_text: str):
        """
        Manages the iterative loop of analyzing the spec, asking questions,
        and refining it with the PM.
        (Placeholder for the main agent logic)
        [cite_start](ASDF PRD v0.2, Phase 1) [cite: 215, 225]
        """
        # TODO: Implement the full clarification loop logic.
        # 1. Analyze spec_text for ambiguities, missing details, etc.
        # 2. Generate questions for the PM.
        # 3. Present questions and get feedback via the GUI.
        # 4. Refine spec_text based on feedback.
        # 5. Repeat until PM confirms completion.

        # Placeholder response:
        return f"// This is a placeholder for the first clarification question based on the provided spec."