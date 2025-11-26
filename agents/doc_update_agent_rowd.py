"""
This module contains the DocUpdateAgentRoWD class.
"""
import logging
import json
import textwrap
import re
import subprocess
from pathlib import Path
from llm_service import LLMService

class DocUpdateAgentRoWD:
    """
    Agent responsible for updating the Record-of-Work-Done (RoWD) database
    for the target application.
    """

    def __init__(self, db_manager, llm_service: LLMService):
        if not db_manager:
            raise ValueError("Database manager cannot be None.")
        if not llm_service:
            raise ValueError("LLMService is required for the DocUpdateAgentRoWD.")
        self.db_manager = db_manager
        self.llm_service = llm_service

    def _validate_and_fix_dot_diagrams(self, markdown_text: str) -> str:
        """
        Scans the markdown for DOT blocks, attempts to render them locally to check for syntax errors,
        and uses the LLM to fix them if they fail.
        """
        dot_blocks = list(re.finditer(r"```dot\s*(.*?)```", markdown_text, re.DOTALL))
        if not dot_blocks:
            return markdown_text

        dot_executable = "dot"

        for match in reversed(dot_blocks):
            original_code = match.group(1)
            try:
                subprocess.run(
                    [dot_executable, "-Tpng"],
                    input=original_code.encode('utf-8'),
                    capture_output=True,
                    check=True
                )
                continue
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                error_msg = e.stderr.decode('utf-8') if isinstance(e, subprocess.CalledProcessError) else str(e)
                logging.warning(f"DOT Validation Failed in DocUpdate. Attempting AI Fix. Error: {error_msg}")

                # Use standard string to avoid brace collision
                fix_prompt_template = textwrap.dedent("""
                You are a Graphviz DOT expert. The following DOT code caused a syntax error.
                **Error:** <<ERROR_MSG>>
                **Invalid Code:**
                ```dot
                <<ORIGINAL_CODE>>
                ```
                **Task:** Fix the syntax error so it compiles.
                **CRITICAL RULE:** Ensure the graph type is `digraph` (directed graph) if using `->` arrows. Do not use `graph` with `->`.
                **Output:** Return ONLY the fixed DOT code inside a ```dot ... ``` block.
                """)

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

    def update_specification_text(self, original_spec: str, implementation_plan: str, current_date: str) -> str:
        """
        Updates a specification document based on a completed implementation plan.
        """
        logging.info("Invoking LLM to update specification document post-implementation.")
        try:
            # Use standard string to avoid f-string brace collision
            prompt_template = textwrap.dedent("""
            You are an expert technical writer responsible for keeping documentation in sync with source code.
            An existing specification document needs to be updated to reflect a series of code changes that were just implemented.

            **Your Task:**
            Review the original specification and the development plan. Return a new, complete version of the specification that incorporates the changes and new features described in the plan, along with an updated date and version.

            **MANDATORY INSTRUCTIONS:**
            1.  **Incorporate Changes:** Integrate the changes from the development plan into the original document.
            2.  **Increment Version:** Find a version number in the document's header and increment it.
            3.  **Update Date:** Replace the 'Date:' line with: <<CURRENT_DATE>>.
            4.  **Clean Output:** Your output MUST be only the raw text of the new specification.

            **DIAGRAMMING RULE (Professional Graphviz):**
            - If the specification contains a diagram (DOT code block), you MUST preserve it and update it to reflect the new architecture/flows.
            - **SCOPE:** Keep the diagram High-Level. Do not diagram every single new file. Focus on Modules and Core Components.
            - **CRITICAL:** You MUST use `digraph G {` (directed graph).
            - **DISCLAIMER:** Immediately BEFORE the diagram, ensure this line is present in italics: *"Note: The scope of this graphic has been limited to include only key components and interactions for the sake of clarity."*
            - **Layout & Style:** Use these exact settings:
                `graph [fontname="Arial", fontsize=12, rankdir=TB, splines=ortho, nodesep=0.8, ranksep=1.0, bgcolor="white"];`
                `node [fontname="Arial", fontsize=12, shape=box, style="filled,rounded", fillcolor="#E8F4FA", color="#007ACC", penwidth=1.5, margin="0.2,0.1"];`
                `edge [fontname="Arial", fontsize=10, color="#555555", penwidth=1.5, arrowsize=0.8];`

            **--- INPUT 1: Original Specification Document ---**
            ```
            <<ORIGINAL_SPEC>>
            ```

            **--- INPUT 2: The Executed Development Plan (JSON) ---**
            ```json
            <<IMPLEMENTATION_PLAN>>
            ```

            **--- OUTPUT: New, Updated Specification Document ---**
            """)

            prompt = prompt_template.replace("<<CURRENT_DATE>>", current_date)
            prompt = prompt.replace("<<ORIGINAL_SPEC>>", original_spec)
            prompt = prompt.replace("<<IMPLEMENTATION_PLAN>>", implementation_plan)

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            if not response_text or response_text.startswith("Error:"):
                raise ValueError(f"LLM returned an error or empty response for spec update: {response_text}")

            # Apply Self-Correction Loop
            validated_text = self._validate_and_fix_dot_diagrams(response_text)
            return validated_text

        except Exception as e:
            logging.error(f"Failed to update specification document via LLM: {e}")
            return original_spec

    def update_artifact_record(self, artifact_data: dict) -> bool:
        """Creates or updates a record for a single software artifact in the RoWD."""
        try:
            artifact_data.pop('status', None)
            artifact_data.setdefault('version', 1)
            artifact_data.setdefault('commit_hash', None)
            artifact_data.setdefault('dependencies', None)
            artifact_data.setdefault('unit_test_status', 'PENDING_GENERATION')
            self.db_manager.add_or_update_artifact(artifact_data)
            return True
        except Exception as e:
            logging.error(f"Error updating RoWD for artifact: {artifact_data.get('artifact_id')}. Error: {e}")
            return False
