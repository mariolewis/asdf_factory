# agents/agent_coding_standard_app_target.py

"""
This module contains the CodingStandardAgent_AppTarget class.
This agent implements F-Phase 2.A from the PRD.
"""

import logging
import textwrap
from llm_service import LLMService

class CodingStandardAgent_AppTarget:
    """
    Agent responsible for generating a detailed, technology-stack-specific
    coding standard for the target application.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the CodingStandardAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the CodingStandardAgent_AppTarget.")
        self.llm_service = llm_service
        logging.info("CodingStandardAgent_AppTarget initialized.")

    def generate_standard(self, tech_spec_text: str) -> str:
        """
        Analyzes a technical specification and generates a coding standard document.

        Args:
            tech_spec_text: The full text of the finalized technical specification.

        Returns:
            A string containing the generated coding standard, formatted in Markdown.
            Returns an error message on failure.
        """
        logging.info("CodingStandardAgent: Generating coding standard...")

        prompt = textwrap.dedent(f"""
            You are a lead software architect with extensive experience in establishing best practices.
            Your task is to generate a detailed, professional coding standard document based on the provided Technical Specification. The goal is to produce code that is highly readable, modular, and easily maintainable.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the coding standard document. Do not include any preamble, introduction, or conversational text. The first character of your response must be the first character of the document's content.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Tech Stack:** Analyze the Technical Specification to identify the primary programming language, frameworks, and key libraries.
            2.  **Generate Comprehensive Standard:** Your response MUST be a complete coding standard document formatted in Markdown. It must include, at a minimum, the following sections as specified in the PRD:
                -   **Formatting and Naming Conventions:** Rules for code layout, indentation, line length, and clear naming conventions for variables, functions, and classes.
                -   **Structural Principles:** A rule mandating the Single Responsibility Principle and guidelines on modular code organization.
                -   **Documentation Standards:** Requirements for documenting 'what' a component does (e.g., docstrings with parameters) and 'why' an implementation choice was made (inline comments for complex logic).
                -   **Data and Interface Contracts:** A rule requiring the use of explicit data structures (like classes or structs) for data exchange between components.
                -   **Security and Error Handling:** A mandatory requirement for using parameterized queries to prevent SQL injection and best practices for graceful error handling.
            3.  **Clarity and Detail:** Be specific and provide examples where appropriate.

            **--- INPUT: Technical Specification ---**
            {tech_spec_text}
            **--- End of Specification ---**

            **--- Generated Coding Standard Document ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            logging.info("Successfully generated coding standard from API.")
            return response_text
        except Exception as e:
            logging.error(f"CodingStandardAgent_AppTarget failed: {e}")
            return f"Error: An unexpected error occurred while generating the coding standard: {e}"