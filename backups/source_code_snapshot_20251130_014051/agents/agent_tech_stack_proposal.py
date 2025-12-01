import config
# agents/agent_tech_stack_proposal.py

"""
This module contains the TechStackProposalAgent class.
"""

import logging
import textwrap
import json
from llm_service import LLMService, parse_llm_json
import subprocess
import re
from pathlib import Path
import vault

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

    def validate_guidelines(self, guidelines: str, app_spec_text: str) -> dict:
        """
        Validates PM-provided guidelines for internal consistency and
        compatibility with the application specification.
        """
        logging.info("Validating PM-provided technology guidelines...")
        prompt = vault.get_prompt("agent_tech_stack_proposal__prompt_39").format(app_spec_text=app_spec_text, guidelines=guidelines)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            result = parse_llm_json(response_text)
            if "compatible" in result and "recommendation" in result:
                return result
            raise ValueError("LLM response was missing required keys.")
        except Exception as e:
            logging.error(f"Failed to validate guidelines: {e}")
            return {"compatible": False, "recommendation": f"An unexpected error occurred during validation: {e}"}

    def _validate_and_fix_dot_diagrams(self, markdown_text: str) -> str:
        """
        Scans the markdown for DOT blocks, attempts to render them locally to check for syntax errors,
        and uses the LLM to fix them if they fail.
        """
        # Find all DOT blocks
        dot_blocks = list(re.finditer(r"```dot\s*(.*?)```", markdown_text, re.DOTALL))
        if not dot_blocks:
            return markdown_text

        dot_executable = config.get_graphviz_binary()

        for match in reversed(dot_blocks):
            original_code = match.group(1)
            try:
                # Dry run using graphviz 'dot'
                subprocess.run(
                    [dot_executable, "-Tpng"],
                    input=original_code.encode('utf-8'),
                    capture_output=True,
                    check=True
                )
                continue
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                error_msg = e.stderr.decode('utf-8') if isinstance(e, subprocess.CalledProcessError) else str(e)
                logging.warning(f"DOT Validation Failed. Attempting AI Fix. Error: {error_msg}")

                # Use standard string to avoid brace collision
                fix_prompt_template = vault.get_prompt("agent_tech_stack_proposal__fix_prompt_template_98")

                fix_prompt = fix_prompt_template.replace("<<ERROR_MSG>>", error_msg)
                fix_prompt = fix_prompt.replace("<<ORIGINAL_CODE>>", original_code)

                try:
                    fixed_response = self.llm_service.generate_text(fix_prompt, task_complexity="simple")
                    code_match = re.search(r"```dot\s*(.*?)```", fixed_response, re.DOTALL)
                    if code_match:
                        fixed_code = code_match.group(1)
                        start, end = match.span(1)
                        markdown_text = markdown_text[:start] + fixed_code + markdown_text[end:]
                        logging.info("DOT Diagram successfully fixed by AI.")
                except Exception as fix_error:
                    logging.error(f"Failed to apply AI fix to DOT diagram: {fix_error}")

        return markdown_text

    def propose_stack(self, functional_spec_text: str, target_os: str, template_content: str | None = None, pm_guidelines: str | None = None) -> str:
        """
        Proposes a tech stack and architecture using Professional Graphviz style.
        """
        logging.info(f"TechStackProposalAgent: Proposing technology stack for OS: {target_os}...")

        template_instruction = ""
        if template_content:
            template_instruction = vault.get_prompt("agent_tech_stack_proposal__template_instruction_134").format(template_content=template_content)

        pm_guidelines_section = ""
        if pm_guidelines:
            pm_guidelines_section = textwrap.dedent(f"""
            **--- PM Directive for Technology Stack (Mandatory Constraint) ---**
            {pm_guidelines}
            """)

        # Use standard string (no 'f' prefix) to avoid brace collision
        prompt_template = vault.get_prompt("agent_tech_stack_proposal__prompt_template_150")

        # Safe injection
        prompt = prompt_template.replace("<<TARGET_OS>>", target_os)
        prompt = prompt.replace("<<TEMPLATE_INSTRUCTION>>", template_instruction)
        prompt = prompt.replace("<<PM_GUIDELINES_SECTION>>", pm_guidelines_section)
        prompt = prompt.replace("<<FUNCTIONAL_SPEC_TEXT>>", functional_spec_text)

        try:
            # Note: Increased timeout is handled in llm_service.py
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            # Apply Self-Correction Loop
            validated_text = self._validate_and_fix_dot_diagrams(response_text)

            logging.info("Successfully received and validated technical specification.")
            return validated_text
        except Exception as e:
            logging.error(f"TechStackProposalAgent API call failed: {e}")
            raise e

    def refine_stack(self, current_draft: str, pm_feedback: str, target_os: str, functional_spec_text: str, ai_issues_text: str, template_content: str | None = None) -> str:
        """
        Refines an existing technical specification draft based on PM feedback.
        """
        logging.info(f"TechStackProposalAgent: Refining tech spec for OS: {target_os}...")

        template_instruction = ""
        if template_content:
            template_instruction = vault.get_prompt("agent_tech_stack_proposal__template_instruction_227").format(template_content=template_content)

        # Use standard string
        prompt_template = vault.get_prompt("agent_tech_stack_proposal__prompt_template_236")

        prompt = prompt_template.replace("<<TEMPLATE_INSTRUCTION>>", template_instruction)
        prompt = prompt.replace("<<FUNCTIONAL_SPEC>>", functional_spec_text)
        prompt = prompt.replace("<<CURRENT_DRAFT>>", current_draft)
        prompt = prompt.replace("<<AI_ISSUES>>", ai_issues_text)
        prompt = prompt.replace("<<PM_FEEDBACK>>", pm_feedback)
        prompt = prompt.replace("<<TARGET_OS>>", target_os)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            # Apply Self-Correction Loop
            validated_text = self._validate_and_fix_dot_diagrams(response_text)

            logging.info("Successfully refined technical specification from API.")
            return validated_text
        except Exception as e:
            logging.error(f"TechStackProposalAgent refinement failed: {e}")
            raise e

    def analyze_draft(self, tech_spec_draft: str, iteration_count: int, previous_analysis: str) -> str:
        """
        Analyzes a technical specification draft for issues, using previous analysis
        to drive convergence.
        """
        logging.info(f"Analyzing technical specification draft for issues (Iteration: {iteration_count})...")

        convergence_directive = ""
        if iteration_count > 1:
            convergence_directive = textwrap.dedent(f"""
            **IMPORTANT - CONVERGENCE DIRECTIVE:**
            You are analyzing refinement iteration {iteration_count}. The user's new draft is an attempt to fix the issues you raised previously.
            Your task is to VERIFY if the user's changes have successfully resolved the issues from the "Previous AI Analysis".
            - If the issues are resolved and no new CRITICAL issues have been introduced, your entire response MUST be the single phrase: "No significant issues found."
            - If some issues remain unresolved or the changes introduced a new CRITICAL issue, you MUST only report on those specific, unresolved items.
            - DO NOT report on new, low-severity stylistic or minor issues. Your focus is on convergence.

            **--- Previous AI Analysis ---**
            {previous_analysis}
            """)

        prompt = vault.get_prompt("agent_tech_stack_proposal__prompt_318").format(convergence_directive=convergence_directive, tech_spec_draft=tech_spec_draft)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Failed to analyze tech spec draft: {e}")
            return f"### Error\nAn unexpected error occurred during draft analysis: {e}"

