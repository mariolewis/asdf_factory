import config
# agents/agent_spec_clarification.py

"""
This module contains the SpecClarificationAgent class.
"""

import logging
import textwrap
import re
import subprocess
import sys
from typing import List
from klyve_db_manager import KlyveDBManager
from llm_service import LLMService
import vault


class SpecClarificationAgent:
    """
    Analyzes specifications, identifies ambiguities, and interacts with the PM
    to produce a complete and clear specification document.
    """

    def __init__(self, llm_service: LLMService, db_manager: KlyveDBManager):
        """
        Initializes the SpecClarificationAgent.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the SpecClarificationAgent.")
        if not db_manager:
            raise ValueError("Database manager is required for the SpecClarificationAgent.")

        self.llm_service = llm_service
        self.db_manager = db_manager

    def consolidate_requirements(self, project_brief: str, ux_spec_markdown: str, ui_blueprint_json: str) -> str:
        """
        Consolidates three sources of requirements into a single document using an LLM.
        """
        logging.info("SpecClarificationAgent: Consolidating multiple requirement sources...")

        prompt = vault.get_prompt("agent_spec_clarification__prompt_40").format(ui_blueprint_json=ui_blueprint_json, ux_spec_markdown=ux_spec_markdown, project_brief=project_brief)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            if not response_text or response_text.startswith("Error:"):
                raise ValueError(f"LLM returned an error or empty response: {response_text}")
            return response_text
        except Exception as e:
            logging.error(f"Failed during requirements consolidation: {e}")
            return f"### Error\nAn unexpected error occurred during requirements consolidation: {e}"

    def _validate_and_fix_dot_diagrams(self, markdown_text: str) -> str:
        """
        Scans the markdown for DOT blocks, attempts to render them locally to check for syntax errors,
        and uses the LLM to fix them if they fail.
        """
        dot_blocks = list(re.finditer(r"```dot\s*(.*?)```", markdown_text, re.DOTALL))
        if not dot_blocks:
            return markdown_text

        dot_executable = config.get_graphviz_binary()

        # Prepare suppression flags for Windows
        run_kwargs = {}
        if sys.platform == "win32":
            # subprocess.CREATE_NO_WINDOW = 0x08000000
            run_kwargs['creationflags'] = 0x08000000

        for match in reversed(dot_blocks):
            original_code = match.group(1)
            try:
                # Dry run using graphviz 'dot'
                subprocess.run(
                    [dot_executable, "-Tpng"],
                    input=original_code.encode('utf-8'),
                    capture_output=True,
                    check=True,
                    **run_kwargs
                )
                continue
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                error_msg = e.stderr.decode('utf-8') if isinstance(e, subprocess.CalledProcessError) else str(e)
                logging.warning(f"DOT Validation Failed. Attempting AI Fix. Error: {error_msg}")

                # Use standard string to avoid brace collision
                fix_prompt_template = vault.get_prompt("agent_spec_clarification__fix_prompt_template_106")

                fix_prompt = fix_prompt_template.replace("<<ERROR_MSG>>", error_msg)
                fix_prompt = fix_prompt.replace("<<ORIGINAL_CODE>>", original_code)

                try:
                    fixed_response = self.llm_service.generate_text(fix_prompt, task_complexity="simple")
                    code_match = re.search(r"```dot\s*(.*?)```", fixed_response, re.DOTALL)
                    if code_match:
                        fixed_code = code_match.group(1)
                        subprocess.run(
                            [dot_executable, "-Tpng"],
                            input=fixed_code.encode('utf-8'),
                            capture_output=True,
                            check=True,
                            **run_kwargs
                        )
                        start, end = match.span(1)
                        markdown_text = markdown_text[:start] + fixed_code + markdown_text[end:]
                        logging.info("DOT Diagram successfully fixed by AI.")
                except Exception as fix_error:
                    logging.error(f"Failed to apply AI fix to DOT diagram: {fix_error}")

        return markdown_text

    def expand_brief_description(self, brief_description: str, is_gui_project: bool = False, template_content: str | None = None) -> str:
        """
        Expands a brief user description into a detailed draft specification using Professional Graphviz style.
        """
        fallback_instruction = ""
        if is_gui_project:
            fallback_instruction = textwrap.dedent("""
            4.  **UI/UX Fallback Section:** Include a section titled "UI Layout & Style Guide" with high-level look and feel suggestions.
            """)

        template_instruction = ""
        if template_content:
            template_instruction = vault.get_prompt("agent_spec_clarification__template_instruction_146").format(template_content=template_content)

        # Use standard string (no 'f' prefix)
        prompt_template = vault.get_prompt("agent_spec_clarification__prompt_template_155")

        # Manually inject variables
        prompt = prompt_template.replace("<<TEMPLATE_INSTRUCTION>>", template_instruction)
        prompt = prompt.replace("<<FALLBACK_INSTRUCTION>>", fallback_instruction)
        prompt = prompt.replace("<<BRIEF_DESCRIPTION>>", brief_description)

        try:
            logging.info("Calling LLM service to expand brief description...")
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")

            # Apply Self-Correction Loop
            validated_text = self._validate_and_fix_dot_diagrams(response_text)

            logging.info("Successfully received and validated expanded specification.")
            return validated_text
        except Exception as e:
            logging.error(f"LLM service call failed during spec expansion: {e}")
            raise

    def identify_potential_issues(self, spec_text: str, iteration_count: int) -> str:
        """
        Analyzes a specification draft to identify ambiguities, narrowing focus on later iterations.
        """
        logging.info(f"SpecClarificationAgent: Identifying issues for iteration {iteration_count}.")

        convergence_directive = ""
        if iteration_count > 1:
            convergence_directive = textwrap.dedent(f"""
            **IMPORTANT - CONVERGENCE DIRECTIVE:**
            This is refinement iteration {iteration_count}. You MUST focus ONLY on high or medium-severity issues such as logical contradictions, missing critical functionality, or significant ambiguities. IGNORE low-severity stylistic points or trivial suggestions.
            """)

        prompt = vault.get_prompt("agent_spec_clarification__prompt_233").format(convergence_directive=convergence_directive, spec_text=spec_text)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            if not response_text:
                raise ValueError("The LLM service returned an empty response when identifying issues.")

            logging.info("Successfully received issue analysis from LLM service.")
            return response_text

        except Exception as e:
            logging.error(f"LLM service call failed during issue identification: {e}")
            raise

    def refine_specification(self, current_draft_text: str, issues_found: str, pm_clarification: str, is_gui_project: bool = False, template_content: str | None = None) -> str:
        """
        Refines the specification draft based on PM feedback.
        """
        fallback_instruction = ""
        if is_gui_project:
            fallback_instruction = textwrap.dedent("""
            **IMPORTANT:** This is a GUI application. Ensure your revised output includes a complete section titled "UI Layout & Style Guide" based on all available information.
            """)

        template_instruction = ""
        if template_content:
            template_instruction = vault.get_prompt("agent_spec_clarification__template_instruction_277").format(template_content=template_content)

        # Use standard string
        prompt_template = vault.get_prompt("agent_spec_clarification__prompt_template_286")

        prompt = prompt_template.replace("<<FALLBACK_INSTRUCTION>>", fallback_instruction)
        prompt = prompt.replace("<<TEMPLATE_INSTRUCTION>>", template_instruction)
        prompt = prompt.replace("<<CURRENT_DRAFT>>", current_draft_text)
        prompt = prompt.replace("<<ISSUES_FOUND>>", issues_found)
        prompt = prompt.replace("<<PM_CLARIFICATION>>", pm_clarification)

        try:
            logging.info("Calling LLM service to refine the specification...")
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            if not response_text:
                raise ValueError("The LLM service returned an empty response during refinement.")

            # Apply Self-Correction Loop
            validated_text = self._validate_and_fix_dot_diagrams(response_text)

            logging.info("Successfully received refined specification from LLM service.")
            return validated_text
        except Exception as e:
            logging.error(f"LLM service call failed during spec refinement: {e}")
            raise