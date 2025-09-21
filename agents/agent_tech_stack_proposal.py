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

    def propose_stack(self, functional_spec_text: str, target_os: str, template_content: str | None = None, pm_guidelines: str | None = None) -> str:
        """
        Analyzes a functional specification and proposes a tech stack tailored
        for a specific operating system, including a development setup guide.
        """
        logging.info(f"TechStackProposalAgent: Proposing technology stack for OS: {target_os}...")

        template_instruction = ""
        if template_content:
            template_instruction = textwrap.dedent(f"""
            **CRITICAL TEMPLATE INSTRUCTION:**
            Your entire output MUST strictly and exactly follow the structure, headings, and formatting of the provided template.
            DO NOT invent new sections. DO NOT change the names of the headings from the template.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        pm_guidelines_section = ""
        if pm_guidelines:
            pm_guidelines_section = textwrap.dedent(f"""
            **--- PM Directive for Technology Stack (This is a mandatory constraint) ---**
            {pm_guidelines}
            """)

        prompt = textwrap.dedent(f"""
            You are an expert Solutions Architect. Your task is to create a formal and appropriately detailed Technical Specification for a **{target_os}** environment, based on the provided Functional Specification.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the Technical Specification document. Do not include any preamble, introduction, or conversational text.

            {template_instruction}

            **--- Mandatory Analysis and Scoping Instructions ---**
            You MUST analyze the provided Functional Specification to determine the application's type and complexity. Your primary goal is to produce a document that is appropriately detailed for the project's scope.

            A comprehensive Technical Specification often includes the following sections. You MUST evaluate which of these are relevant and include them in your response. For a simple utility, only a few sections may be needed. For a complex enterprise system, most will be required.

            **1. High-Level Architecture:**
               - Provide a brief overview of the chosen architectural pattern (e.g., Monolith, Microservices, Client-Server, Event-Driven). Justify why this pattern is suitable.
            **2. Component Architecture Design:**
               - Break down the solution into its logical components (e.g., UI Frontend, Backend API, Database, Authentication Service, Data Processing Pipeline). Define the primary responsibility of each component.
            **3. Technology Stack Selection:**
               - List the chosen programming languages, frameworks, and key libraries. You MUST adhere to any specific technologies mentioned in the PM's Guidelines. Justify your choices based on the project's requirements.
            **4. Data & Integration Architecture:**
               - Describe the proposed data models or schema (logical, not physical SQL).
               - If applicable, describe how the system will integrate with external services via APIs or event streams.
            **5. Non-Functional Requirements (NFRs):**
               - Briefly detail the key NFRs considered, such as Performance, Scalability, Security, and Reliability.
            **6. Development Environment Setup Guide:**
               - You MUST include this section. Provide a clear, human-readable list of all necessary languages, frameworks, and tools that need to be installed to build and run the application.

            **--- PM Directive for Technology Stack (Mandatory Constraint, if provided) ---**
            {pm_guidelines if pm_guidelines else "None provided. You are to propose the most suitable stack."}

            **--- Functional Specification (The "What") ---**
            {functional_spec_text}
            ---

            **--- Generated Technical Specification (The "How") ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            logging.info("Successfully received OS-aware technology stack proposal from API.")
            return response_text
        except Exception as e:
            logging.error(f"TechStackProposalAgent API call failed: {e}")
            return f"Error: An unexpected error occurred while generating the tech stack proposal: {e}"

    def refine_stack(self, current_draft: str, pm_feedback: str, target_os: str) -> str:
        """
        Refines an existing technical specification draft based on PM feedback.

        Args:
            current_draft (str): The current version of the technical spec.
            pm_feedback (str): The feedback from the PM for refinement.
            target_os (str): The target operating system.

        Returns:
            A string containing the refined technical specification.
        """
        logging.info(f"TechStackProposalAgent: Refining tech spec for OS: {target_os}...")

        prompt = textwrap.dedent(f"""
            You are a senior Solutions Architect revising a document. Your task is to refine an existing draft of a Technical Specification based on specific feedback from a Product Manager, ensuring it remains appropriate for the target "{target_os}" environment.

            **MANDATORY INSTRUCTIONS:**
            1.  **Modify Body Only**: Your changes should only be in the body of the document based on the PM's feedback. Do not regenerate the entire document from scratch.
            2.  **RAW MARKDOWN ONLY:** Your entire response MUST be only the raw content of the refined document.
            3.  **STRICT MARKDOWN FORMATTING:** You MUST use Markdown for all formatting. Use '##' for main headings and '###' for sub-headings. For lists, each item MUST start on a new line with an asterisk and a space (e.g., "* List item text."). Paragraphs MUST be separated by a full blank line. This is mandatory.

            **--- INPUT 1: Current Draft ---**
            ```markdown
            {current_draft}
            ```

            **--- INPUT 2: PM Feedback to Address ---**
            ```
            {pm_feedback}
            ```

            **--- Refined Technical Specification for {target_os} (Markdown) ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            logging.info("Successfully refined technical specification from API.")
            return response_text
        except Exception as e:
            logging.error(f"TechStackProposalAgent refinement failed: {e}")
            return f"Error: An unexpected error occurred while refining the tech spec: {e}"