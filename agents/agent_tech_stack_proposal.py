# agents/agent_tech_stack_proposal.py

"""
This module contains the TechStackProposalAgent class.
(ASDF Change Request CR-ASDF-001)
"""

import logging
import textwrap
import google.generativeai as genai

class TechStackProposalAgent:
    """
    Analyzes functional specifications to propose a suitable technology stack.
    This is a core component of the Formal Technical Specification Phase.
    (ASDF Change Request CR-ASDF-001)
    """

    def __init__(self, api_key: str):
        """
        Initializes the TechStackProposalAgent.

        Args:
            api_key (str): The Gemini API key for LLM interactions.
        """
        if not api_key:
            raise ValueError("API key is required for the TechStackProposalAgent.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        logging.info("TechStackProposalAgent initialized.")

    def propose_stack(self, functional_spec_text: str, target_os: str) -> str:
        """
        Analyzes a functional specification and proposes a tech stack tailored
        for a specific operating system.

        Args:
            functional_spec_text: The full text of the finalized application spec.
            target_os (str): The target OS (e.g., "Windows", "Linux", "macOS").

        Returns:
            A string containing the proposed tech stack with justifications.
        """
        logging.info(f"TechStackProposalAgent: Proposing technology stack for OS: {target_os}...")

        prompt = textwrap.dedent(f"""
            You are an expert Solutions Architect. Your task is to create a formal Technical Specification, including a high-level architecture and a complete technology stack, based on the provided functional specification for a **{target_os}** environment.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze for Existing Tech:** First, review the specification to see if a technology stack is already mentioned.
            2.  **If Tech IS Specified:** Your primary task is to accept and expand upon the user's choice. Validate that it fits the requirements and then detail the architecture and any missing libraries or components needed to complete the stack.
            3.  **If Tech IS NOT Specified:** Your task is to propose the most appropriate technology stack from scratch, providing a brief justification for each choice.
            4.  **OS-Specific:** All recommendations must be well-suited for a **"{target_os}"** environment.
            5.  **Format:** Structure your response clearly using Markdown.

            **--- Functional Specification ---**
            {functional_spec_text}
            **--- End of Specification ---**

            Based on the specification provided, here is the recommended Technical Specification for a **{target_os}** deployment:
        """)

        try:
            response = self.model.generate_content(prompt)
            logging.info("Successfully received OS-aware technology stack proposal from API.")
            return response.text
        except Exception as e:
            logging.error(f"TechStackProposalAgent API call failed: {e}")
            return f"Error: An unexpected error occurred while generating the tech stack proposal: {e}"