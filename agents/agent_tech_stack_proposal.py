# agents/agent_tech_stack_proposal.py

"""
This module contains the TechStackProposalAgent class.
"""

import logging
import textwrap
from llm_service import LLMService

class TechStackProposalAgent:
    """
    Analyzes functional specifications to propose a suitable technology stack.
    This is a core component of the Formal Technical Specification Phase.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the TechStackProposalAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the TechStackProposalAgent.")
        self.llm_service = llm_service
        logging.info("TechStackProposalAgent initialized.")

    def propose_stack(self, functional_spec_text: str, target_os: str) -> str:
        """
        Analyzes a functional specification and proposes a tech stack tailored
        for a specific operating system, including a development setup guide.

        Args:
            functional_spec_text: The full text of the finalized application spec.
            target_os (str): The target OS (e.g., "Windows", "Linux", "macOS").

        Returns:
            A string containing the proposed tech stack with justifications.
        """
        logging.info(f"TechStackProposalAgent: Proposing technology stack for OS: {target_os}...")

        prompt = textwrap.dedent(f"""
            You are an expert Solutions Architect. Your task is to create a formal Technical Specification, including a high-level architecture and a complete technology stack, based on the provided functional specification for a **{target_os}** environment.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the Technical Specification document. Do not include any preamble, introduction, or conversational text. The first character of your response must be the first character of the document's content.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze for Existing Tech:** First, review the specification to see if a technology stack is already mentioned.
            2.  **If Tech IS Specified:** Your primary task is to accept and expand upon the user's choice. Validate that it fits the requirements and then detail the architecture and any missing libraries or components needed to complete the stack.
            3.  **If Tech IS NOT Specified:** Your task is to propose the most appropriate technology stack from scratch, providing a brief justification for each choice.
            4.  **Include Setup Guide:** You MUST include a dedicated section in your response titled **"Development Environment Setup Guide"**. This section must contain a clear, human-readable list of all necessary languages, frameworks, libraries, and tools that need to be installed to build and run the application.
            5.  **OS-Specific:** All recommendations must be well-suited for a **"{target_os}"** environment.
            6.  **Format:** Structure your response clearly using Markdown.

            ---
            **Functional Specification:**
            {functional_spec_text}
            ---
            **End of Specification** ---

            Based on the specification provided, here is the recommended Technical Specification for a **{target_os}** deployment:
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            logging.info("Successfully received OS-aware technology stack proposal from API.")
            return response_text
        except Exception as e:
            logging.error(f"TechStackProposalAgent API call failed: {e}")
            return f"Error: An unexpected error occurred while generating the tech stack proposal: {e}"