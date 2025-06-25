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
            You are an expert Solutions Architect. Your task is to analyze the following functional software specification and propose the most appropriate high-level architecture and a complete technology stack for its implementation, specifically tailored for the target **Operating System: {target_os}**.

            **MANDATORY INSTRUCTIONS:**
            1.  **OS-Specific Recommendations:** All of your recommendations for programming languages, frameworks, databases, and key libraries MUST be compatible and well-suited for a "{target_os}" environment.
            2.  **Justifications:** For each technology choice, you MUST provide a brief justification explaining WHY it is a good fit for this specific project on the specified OS.
            3.  **Format:** Structure your response clearly using Markdown. Use a top-level heading for the Architecture Pattern and then sub-headings for each component of the stack.

            **--- Functional Specification ---**
            {functional_spec_text}
            **--- End of Specification ---**

            Based on the specification provided, here is my recommended architecture and technology stack for a **{target_os}** deployment:
        """)

        try:
            response = self.model.generate_content(prompt)
            logging.info("Successfully received OS-aware technology stack proposal from API.")
            return response.text
        except Exception as e:
            logging.error(f"TechStackProposalAgent API call failed: {e}")
            return f"Error: An unexpected error occurred while generating the tech stack proposal: {e}"