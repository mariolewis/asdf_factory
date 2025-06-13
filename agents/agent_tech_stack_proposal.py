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
        self.model = genai.GenerativeModel('gemini-pro')
        logging.info("TechStackProposalAgent initialized.")

    def propose_stack(self, functional_spec_text: str) -> str:
        """
        Analyzes a functional specification and proposes a tech stack.

        Args:
            functional_spec_text: The full text of the finalized application spec.

        Returns:
            A string containing the proposed tech stack with justifications,
            formatted in Markdown for readability. Returns an error message on failure.
        """
        logging.info("TechStackProposalAgent: Proposing technology stack...")

        prompt = textwrap.dedent(f"""
            You are an expert Solutions Architect. Your task is to analyze the following functional software specification and propose the most appropriate high-level architecture and a complete technology stack for its implementation.

            **MANDATORY INSTRUCTIONS:**
            1.  **Determine Architecture First:** Your first step MUST be to determine and state the optimal **Architecture Pattern** based on the specification (e.g., "Monolithic Desktop Application", "3-Tier Web Application", "Native Mobile App", "Microservices Backend with Web Frontend").
            2.  **Recommend a Full Stack:** Based on your chosen architecture, your proposal must then include a technology stack covering all major areas:
                -   **Programming Language(s):** The primary language(s) to be used.
                -   **Key Frameworks/SDKs:** The main frameworks or Software Development Kits needed (e.g., for UI, backend logic, mobile development).
                -   **Data Storage:** The recommended database or storage solution (e.g., PostgreSQL, SQLite, Filesystem).
                -   **External Integrations:** Identify any necessary third-party API integrations (e.g., payment gateways, mapping services, social media logins).
                -   **Communication Protocols:** Define the primary protocols for communication if different parts of the system need to talk to each other (e.g., REST API for client-server, gRPC for inter-service, WebSockets for real-time updates).
                -   **Key Libraries:** Suggest any other essential standard libraries for tasks like data handling, authentication, etc.
            3.  **Provide Justifications:** For the architecture and EACH technology choice, you MUST provide a brief, clear justification explaining WHY it is a good fit for this specific project.
            4.  **Format:** Structure your response clearly using Markdown. Use a top-level heading for the Architecture Pattern and then sub-headings for each component of the stack.

            **--- Functional Specification ---**
            {functional_spec_text}
            **--- End of Specification ---**

            Based on the specification provided, here is my recommended architecture and technology stack:
        """)

        try:
            response = self.model.generate_content(prompt)
            logging.info("Successfully received technology stack proposal from API.")
            return response.text
        except Exception as e:
            logging.error(f"TechStackProposalAgent API call failed: {e}")
            return f"Error: An unexpected error occurred while generating the tech stack proposal: {e}"