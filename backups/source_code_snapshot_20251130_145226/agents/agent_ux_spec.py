import config
# agents/agent_ux_spec.py

"""
This module contains the UX_Spec_Agent class, responsible for the iterative
generation of the UX/UI Specification document.
"""

import logging
import textwrap
import json
import re
import subprocess
from pathlib import Path
from llm_service import LLMService, parse_llm_json
import vault

class UX_Spec_Agent:
    """
    An agent that collaborates with the PM to iteratively build the
    UX/UI Specification document.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the UX_Spec_Agent.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the UX_Spec_Agent.")
        self.llm_service = llm_service
        logging.info("UX_Spec_Agent initialized.")

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
                fix_prompt_template = vault.get_prompt("agent_ux_spec__fix_prompt_template_59")

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

    def generate_enriched_ux_draft(self, project_brief: str, personas: list[str], template_content: str | None = None) -> str:
        """
        Generates a single, consolidated UX/UI Specification draft in Markdown.
        """
        logging.info("UX_Spec_Agent: Generating consolidated UX/UI specification draft...")

        personas_str = "- " + "\n- ".join(personas) if personas else "No specific personas were confirmed."

        template_instruction = ""
        if template_content:
            template_instruction = vault.get_prompt("agent_ux_spec__template_instruction_97").format(template_content=template_content)

        # Use standard string to avoid brace collisions
        prompt_template = vault.get_prompt("agent_ux_spec__prompt_template_108")

        # Manually inject variables
        prompt = prompt_template.replace("<<TEMPLATE_INSTRUCTION>>", template_instruction)
        prompt = prompt.replace("<<PROJECT_BRIEF>>", project_brief)
        prompt = prompt.replace("<<PERSONAS_STR>>", personas_str)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            draft = response_text.strip()

            # VALIDATION LOOP
            validated_draft = self._validate_and_fix_dot_diagrams(draft)

            return validated_draft

        except Exception as e:
            logging.error(f"UX_Spec_Agent failed to generate enriched UX draft: {e}")
            return f"### Error\nCould not generate the UX/UI Specification Draft. Details: {e}"

    def refine_ux_spec(self, current_draft: str, pm_feedback: str, template_content: str | None = None) -> str:
        """
        Refines an existing UX/UI specification draft based on PM feedback.
        """
        logging.info("UX_Spec_Agent: Refining UX/UI specification draft...")

        template_instruction = ""
        if template_content:
            template_instruction = vault.get_prompt("agent_ux_spec__template_instruction_189").format(template_content=template_content)

        # Use standard string
        prompt_template = vault.get_prompt("agent_ux_spec__prompt_template_198")

        prompt = prompt_template.replace("<<TEMPLATE_INSTRUCTION>>", template_instruction)
        prompt = prompt.replace("<<CURRENT_DRAFT>>", current_draft)
        prompt = prompt.replace("<<PM_FEEDBACK>>", pm_feedback)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            draft = response_text.strip()

            # VALIDATION LOOP
            validated_draft = self._validate_and_fix_dot_diagrams(draft)

            return validated_draft

        except Exception as e:
            logging.error(f"UX_Spec_Agent failed to refine UX draft: {e}")
            raise e

    def parse_final_spec_and_generate_blueprint(self, final_spec_markdown: str) -> str:
        # ... (Keep existing logic)
        logging.info("UX_Spec_Agent: Parsing final spec to generate JSON blueprint...")
        prompt_template = vault.get_prompt("agent_ux_spec__prompt_template_250")
        prompt = prompt_template.replace("<<FINAL_SPEC_MARKDOWN>>", final_spec_markdown)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()
            parse_llm_json(cleaned_response)
            return cleaned_response
        except Exception as e:
            logging.error(f"UX_Spec_Agent failed to parse spec: {e}")
            return json.dumps({"error": f"Details: {e}"}, indent=2)

    def generate_user_journeys(self, project_brief: str, personas: list[str]) -> str:
        # ... (Keep existing logic)
        logging.info("UX_Spec_Agent: Generating user journeys...")
        personas_str = "- " + "\n- ".join(personas)
        prompt = vault.get_prompt("agent_ux_spec__prompt_275").format(project_brief=project_brief, personas_str=personas_str)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            return f"Error: {e}"

    def identify_screens_from_journeys(self, user_journeys: str) -> str:
        # ... (Keep existing logic)
        logging.info("UX_Spec_Agent: Identifying screens from user journeys...")
        prompt = vault.get_prompt("agent_ux_spec__prompt_296").format(user_journeys=user_journeys)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            return f"Error: {e}"

    def generate_screen_blueprint(self, screen_name: str, pm_description: str) -> str:
        # ... (Keep existing logic)
        logging.info(f"UX_Spec_Agent: Generating blueprint for screen: {screen_name}")
        prompt_template = vault.get_prompt("agent_ux_spec__prompt_template_315")
        prompt = prompt_template.replace("<<SCREEN_NAME>>", screen_name).replace("<<PM_DESCRIPTION>>", pm_description)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()
            parse_llm_json(cleaned_response)
            return cleaned_response
        except Exception as e:
            return json.dumps({"error": f"Details: {e}"}, indent=2)

    def generate_style_guide(self, pm_description: str) -> str:
        # ... (Keep existing logic)
        logging.info("UX_Spec_Agent: Generating Theming & Style Guide...")
        prompt = vault.get_prompt("agent_ux_spec__prompt_338").format(pm_description=pm_description)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            return f"### Error\nDetails: {e}"