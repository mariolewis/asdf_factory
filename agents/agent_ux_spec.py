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
from llm_service import LLMService

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

        dot_executable = "dot"

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

    def generate_enriched_ux_draft(self, project_brief: str, personas: list[str], template_content: str | None = None) -> str:
        """
        Generates a single, consolidated UX/UI Specification draft in Markdown.
        """
        logging.info("UX_Spec_Agent: Generating consolidated UX/UI specification draft...")

        personas_str = "- " + "\n- ".join(personas) if personas else "No specific personas were confirmed."

        template_instruction = ""
        if template_content:
            template_instruction = textwrap.dedent(f"""
            **CRITICAL TEMPLATE INSTRUCTION:**
            Your entire output MUST strictly and exactly follow the structure, headings, and formatting of the provided template.
            Populate the sections of the template with content derived from the inputs.
            DO NOT invent new sections. DO NOT change the names of the headings from the template.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        # Use standard string to avoid brace collisions
        prompt_template = textwrap.dedent("""
            You are a senior UX Designer and Business Analyst. Your task is to create a single, comprehensive, and consolidated UX/UI Specification document in Markdown format.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the Markdown document. Do not include any preamble, introduction, or conversational text.

            <<TEMPLATE_INSTRUCTION>>

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Holistically:** Analyze the provided Project Brief and User Personas to understand the application's goals and target audience.
            2.  **STRICT MARKDOWN FORMATTING:** You MUST use Markdown for all formatting. Use '##' for main headings and '###' for sub-headings. Paragraphs MUST be separated by a full blank line.

            **SECTION REQUIREMENTS:**
            If no template is provided, you MUST generate a document containing the following sections in this exact order:

            `## 1. User Personas`
            `## 2. Epics`
            `## 3. Features (grouped by Epic)`
            `## 4. User Stories (grouped by Feature)`

            `## 5. Inferred Screens & Components`
            **CRITICAL:** In this section, you MUST first generate a **"Core Journey Diagram"**. **IMMEDIATELY AFTER** the **"Core Journey Diagram"**, you MUST generate a list of screens.

            **DIAGRAMMING RULE (Professional Graphviz):**
            - Use the **DOT language** inside a ```dot ... ``` code block.
            - **SCOPE:** Diagram ONLY the main **"Happy Path"** (Critical User Flow) of the Core Journey. Max 10-12 nodes.
            - **CRITICAL:** Use `digraph G {` (directed graph).
            - **Layout:** Use `rankdir=TB` (Top-to-Bottom). This ensures the diagram fits vertically on the page.
            - **Style:** `graph [fontname="Arial", fontsize=12, rankdir=TB, splines=ortho, nodesep=0.8, ranksep=1.0, bgcolor="white"]; node [fontname="Arial", fontsize=12, shape=box, style="filled,rounded", fillcolor="#E8F4FA", color="#007ACC", penwidth=1.5, margin="0.2,0.1"]; edge [fontname="Arial", fontsize=10, color="#555555", penwidth=1.5, arrowsize=0.8];`

            `## 6. Prescriptive Style Guide (for Code Agent)`
            **CRITICAL:** Generate specific, tech-agnostic rules using this exact format:
                ### A. Color Palette
                * `accent_color`: `"#007ACC"`
                * `primary_text_color`: `"#F0F0F0"`
                * `secondary_text_color`: `"#A9B7C6"`
                * `primary_background_color`: `"#202021"`
                * `secondary_background_color`: `"#2A2A2B"`
                * `error_color`: `"#CC7832"`
                ### B. Typography
                * `font_family`: `"Inter, Segoe UI, sans-serif"`
                ### C. Component Rules
                * **Primary Button:** `background: accent_color; color: primary_text_color; min-height: 35px;`
                * **Text Input:** `background: primary_background_color; border: 1px solid secondary_background_color; padding: 8px;`

            ---
            **INPUT 1: Project Brief**
            <<PROJECT_BRIEF>>

            **INPUT 2: Confirmed User Personas**
            <<PERSONAS_STR>>
            ---

            **Consolidated UX/UI Specification (Markdown):**
        """)

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
            template_instruction = textwrap.dedent(f"""
            **CRITICAL TEMPLATE INSTRUCTION:**
            The original draft was based on a template. Your refined output MUST also strictly and exactly follow the structure, headings, and formatting of that same template.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        # Use standard string
        prompt_template = textwrap.dedent("""
            You are a senior UX Designer revising a document. Your task is to refine an existing draft of a UX/UI Specification based on specific feedback from a Product Manager.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the refined document. Do not include any preamble.

            <<TEMPLATE_INSTRUCTION>>

            **MANDATORY INSTRUCTIONS:**
            1.  **Preserve Header**: The document has a standard header. Preserve it.
            2.  **Modify Body Only**: Incorporate the PM's feedback.
            3.  **RAW MARKDOWN ONLY**: Return only the raw content.

            **DIAGRAMMING RULE (Professional Graphviz):**
            - Use the **DOT language** inside a ```dot ... ``` code block.
            - **SCOPE:** Maintain the scope of the **"Core Journey Diagram"**.
            - **CRITICAL:** Use `digraph G {` (directed graph).
            - **Layout:** Use `rankdir=TB` (Top-to-Bottom). This ensures the diagram fits vertically on the page.
            - **Style:** `graph [fontname="Arial", fontsize=12, rankdir=TB, splines=ortho, nodesep=0.8, ranksep=1.0, bgcolor="white"]; node [fontname="Arial", fontsize=12, shape=box, style="filled,rounded", fillcolor="#E8F4FA", color="#007ACC", penwidth=1.5, margin="0.2,0.1"]; edge [fontname="Arial", fontsize=10, color="#555555", penwidth=1.5, arrowsize=0.8];`

            **--- INPUT 1: Current Draft ---**
            ```markdown
            <<CURRENT_DRAFT>>
            ```

            **--- INPUT 2: PM Feedback to Address ---**
            ```
            <<PM_FEEDBACK>>
            ```

            **--- Refined UX/UI Specification Document (Markdown) ---**
        """)

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
        prompt_template = textwrap.dedent("""
            You are a meticulous data extraction system. Your task is to analyze a final UX/UI Specification...
            **MANDATORY INSTRUCTIONS:**
            1. **JSON Output:** Your response MUST be a single, valid JSON object.
            ...
            ---
            **INPUT: Final UX/UI Specification (Markdown)**
            <<FINAL_SPEC_MARKDOWN>>
            ---
            **OUTPUT: Structural UI Blueprint (JSON Object):**
        """)
        prompt = prompt_template.replace("<<FINAL_SPEC_MARKDOWN>>", final_spec_markdown)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()
            json.loads(cleaned_response)
            return cleaned_response
        except Exception as e:
            logging.error(f"UX_Spec_Agent failed to parse spec: {e}")
            return json.dumps({"error": f"Details: {e}"}, indent=2)

    def generate_user_journeys(self, project_brief: str, personas: list[str]) -> str:
        # ... (Keep existing logic)
        logging.info("UX_Spec_Agent: Generating user journeys...")
        personas_str = "- " + "\n- ".join(personas)
        prompt = textwrap.dedent(f"""
            You are a senior UX Designer...
            **MANDATORY INSTRUCTIONS:**
            1. **Identify Journeys:**...
            ---
            **Project Brief:**
            {project_brief}
            **User Personas:**
            {personas_str}
            ---
            **Core User Journeys (Numbered List):**
        """)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            return f"Error: {e}"

    def identify_screens_from_journeys(self, user_journeys: str) -> str:
        # ... (Keep existing logic)
        logging.info("UX_Spec_Agent: Identifying screens from user journeys...")
        prompt = textwrap.dedent(f"""
            You are a senior UI/UX Architect...
            **MANDATORY INSTRUCTIONS:**
            1. **Analyze:** Read the user journeys...
            ---
            **Core User Journeys:**
            {user_journeys}
            ---
            **Required Screens/Views (Numbered List):**
        """)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            return f"Error: {e}"

    def generate_screen_blueprint(self, screen_name: str, pm_description: str) -> str:
        # ... (Keep existing logic)
        logging.info(f"UX_Spec_Agent: Generating blueprint for screen: {screen_name}")
        prompt_template = textwrap.dedent("""
            You are a meticulous UI/UX Architect...
            ...
            ---
            **Screen to Design:**
            <<SCREEN_NAME>>
            **Product Manager's Description:**
            <<PM_DESCRIPTION>>
            ---
            **Generated Screen Blueprint (JSON Object):**
        """)
        prompt = prompt_template.replace("<<SCREEN_NAME>>", screen_name).replace("<<PM_DESCRIPTION>>", pm_description)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()
            json.loads(cleaned_response)
            return cleaned_response
        except Exception as e:
            return json.dumps({"error": f"Details: {e}"}, indent=2)

    def generate_style_guide(self, pm_description: str) -> str:
        # ... (Keep existing logic)
        logging.info("UX_Spec_Agent: Generating Theming & Style Guide...")
        prompt = textwrap.dedent(f"""
            You are a senior UI/UX Designer...
            ...
            ---
            **Product Manager's Description:**
            {pm_description}
            ---
            **Theming & Style Guide (Markdown):**
        """)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            return f"### Error\nDetails: {e}"