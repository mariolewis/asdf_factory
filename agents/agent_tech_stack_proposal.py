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
            You are an expert Solutions Architect. Your task is to create a formal Technical Specification, including a high-level architecture and a complete technology stack, for a **{target_os}** environment.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the Technical Specification document. Do not include any preamble or conversational text.

            {template_instruction}

            **MANDATORY INSTRUCTIONS:**
            1.  **Adhere to PM Guidelines:** If PM Guidelines are provided, they are a mandatory constraint and take precedence over your own suggestions. You must build the architecture around the specified technologies.
            2.  **Propose if No Guidelines:** If no PM guidelines are provided, propose the most appropriate technology stack from scratch, providing a brief justification for each choice.
            3.  **Include Setup Guide:** You MUST include a dedicated section titled **"Development Environment Setup Guide"**.
            4.  **OS-Specific:** All recommendations must be well-suited for a **"{target_os}"** environment.
            5.  **Strict Markdown:** Your response MUST use clean Markdown formatting ('##' for headings, etc.).

            {pm_guidelines_section}

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