# agents/agent_tech_stack_proposal.py

"""
This module contains the TechStackProposalAgent class.
"""

import logging
import textwrap
import json
from llm_service import LLMService
import subprocess
import re
from pathlib import Path

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
        prompt = textwrap.dedent(f"""
            You are a senior Solutions Architect. Your task is to validate a set of technology guidelines provided by a Product Manager against the project's application specification.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze for Conflicts:** Check for any direct contradictions between the guidelines and the functional requirements (e.g., specifying a web-only framework for a required desktop application).
            2.  **Analyze for Internal Consistency:** Check for poor or incompatible technology pairings within the guidelines themselves (e.g., pairing a Python backend with a .NET-exclusive UI framework).
            3.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            4.  **JSON Schema:** The JSON object MUST have two keys:
                - `compatible`: A boolean (`true` if no issues are found, `false` otherwise).
                - `recommendation`: A string. If incompatible, this must be a concise, helpful explanation of the issue and a suggested, compatible alternative. If compatible, it should be a simple confirmation message.
            5.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON object.

            **--- INPUT 1: Application Specification ---**
            {app_spec_text}

            **--- INPUT 2: PM's Technology Guidelines to Validate ---**
            {guidelines}

            **--- JSON Validation Result ---**
        """)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            result = json.loads(cleaned_response)
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

    def propose_stack(self, functional_spec_text: str, target_os: str, template_content: str | None = None, pm_guidelines: str | None = None) -> str:
        """
        Proposes a tech stack and architecture using Professional Graphviz style.
        """
        logging.info(f"TechStackProposalAgent: Proposing technology stack for OS: {target_os}...")

        template_instruction = ""
        if template_content:
            template_instruction = textwrap.dedent(f"""
            **CRITICAL TEMPLATE INSTRUCTION:**
            Adhere strictly to the structure of the provided template.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        pm_guidelines_section = ""
        if pm_guidelines:
            pm_guidelines_section = textwrap.dedent(f"""
            **--- PM Directive for Technology Stack (Mandatory Constraint) ---**
            {pm_guidelines}
            """)

        # Use standard string (no 'f' prefix) to avoid brace collision
        prompt_template = textwrap.dedent("""
            You are an expert Solutions Architect. Your task is to create the BODY of a formal Technical Specification for a **<<TARGET_OS>>** environment.

            **CRITICAL INSTRUCTIONS:** - Your entire response MUST be only the raw Markdown content.
            - Do NOT add a header or preamble.

            <<TEMPLATE_INSTRUCTION>>

            **MANDATORY SECTIONS & DIAGRAMS:**
            You MUST generate the document using the following sections. You MUST insert specific diagrams contextually as described below.

            `## 1. High-Level Architecture`
            - Describe the overall system design (e.g., MVC, Microservices).
            - **DIAGRAM 1 (Architecture):** Immediately after the description, generate a **"System Context Diagram"**.
                - **Scope:** Show ONLY the 5-7 highest-level components (e.g., Frontend, Backend API, Database, External Service).
                - **Syntax:** Use `digraph G {` inside a ```dot ... ``` block.
                - **DISCLAIMER:** Immediately BEFORE the diagram, add this line in italics: *"Note: The scope of this graphic has been limited to include only key components and interactions for the sake of clarity."*
                - **CRITICAL LAYOUT RULE:** You MUST use `rankdir=TB` (Top-to-Bottom) to ensure the diagram fits vertically.
                - **Style:** Use these settings: `graph [fontname="Arial", fontsize=12, rankdir=TB, splines=ortho, nodesep=0.8, ranksep=1.0, bgcolor="white", compound=true]; node [fontname="Arial", shape=component, style="filled,rounded", fillcolor="#E1F5FE", color="#0277BD", penwidth=1.5, margin="0.2,0.1"];`

            `## 2. Component Architecture Design`
            - Detailed breakdown of internal modules.

            `## 3. Technology Stack Selection`
            - Languages, Frameworks, Libraries.

            `## 4. Data & Integration Architecture`
            - Database choice, Schema design strategy.
            - **DIAGRAM 2 (Data Flow):** Immediately after the description, generate a **"High-Level Data Flow Diagram"**.
                - **Scope:** Show how data moves between the User, the App, and the Database. Max 5-8 nodes.
                - **Syntax:** Use `digraph G {` inside a ```dot ... ``` block.
                - **DISCLAIMER:** Immediately BEFORE the diagram, add this line in italics: *"Note: The scope of this graphic has been limited to include only key components and interactions for the sake of clarity."*
                - **CRITICAL LAYOUT RULE:** You MUST use `rankdir=TB` (Top-to-Bottom).
                - **Style:** Use these settings: `graph [fontname="Arial", rankdir=TB, splines=ortho, bgcolor="white"]; node [fontname="Arial", shape=cylinder, style="filled", fillcolor="#FFF3E0", color="#EF6C00"];`

            `## 5. Non-Functional Requirements (NFRs)`
            - Scalability, Security, Performance.

            `## 6. Development Environment Setup Guide`
            - Prerequisites and installation steps.

            <<PM_GUIDELINES_SECTION>>

            **--- Functional Specification ---**
            <<FUNCTIONAL_SPEC_TEXT>>
            ---

            **--- Generated Technical Specification Body (Raw Markdown) ---**
        """)

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
            template_instruction = textwrap.dedent(f"""
            **CRITICAL TEMPLATE INSTRUCTION:**
            The original draft was based on a template. Your refined output MUST also strictly and exactly follow the structure, headings, and formatting of that same template.
            --- TEMPLATE START ---
            {template_content}
            --- TEMPLATE END ---
            """)

        # Use standard string
        prompt_template = textwrap.dedent("""
            You are a senior Solutions Architect revising a document. Your task is to refine the body of a Technical Specification based on a list of identified issues and specific feedback from a Product Manager.

            **MANDATORY INSTRUCTIONS:**
            1.  **Refine Body Only**: The text you receive is the body of a document. Your task is to incorporate the PM's clarifications to resolve the identified issues.
            2.  **RAW MARKDOWN ONLY**: Your entire response MUST be only the raw, refined text of the document's body. Do NOT add a header, preamble, or any conversational text.
            3.  **STRICT MARKDOWN FORMATTING:** You MUST use Markdown for all formatting.

            **DIAGRAMMING RULE (Professional Graphviz):**
            - If the feedback requires updating a diagram, use the **DOT language** inside a ```dot ... ``` code block.
            - **SCOPE:** Keep diagrams high-level (Context/Architecture). Do not explode the node count.
            - **CRITICAL:** You MUST use `digraph G {` (directed graph).
            - **DISCLAIMER:** Immediately BEFORE the diagram, ensure this line is present in italics: *"Note: The scope of this graphic has been limited to include only key components and interactions for the sake of clarity."*
            - **Layout & Style:** Use these exact settings:
                `graph [fontname="Arial", fontsize=12, rankdir=TB, splines=ortho, nodesep=0.8, ranksep=1.0, bgcolor="white"];`
                `node [fontname="Arial", fontsize=12, shape=component, style="filled,rounded", fillcolor="#E1F5FE", color="#0277BD", penwidth=1.5, margin="0.2,0.1"];`
                `edge [fontname="Arial", fontsize=10, color="#555555", penwidth=1.5, arrowsize=0.8];`

            <<TEMPLATE_INSTRUCTION>>

            **--- CONTEXT: Full Application Specification ---**
            <<FUNCTIONAL_SPEC>>
            ---

            **--- INPUT 1: Current Draft Body ---**
            ```markdown
            <<CURRENT_DRAFT>>
            ```

            **--- INPUT 2: AI-Generated Issues That the PM is Responding To ---**
            ```markdown
            <<AI_ISSUES>>
            ```

            **--- INPUT 3: PM Feedback to Address ---**
            ```
            <<PM_FEEDBACK>>
            ```

            **--- Refined Document Body for <<TARGET_OS>> (Raw Markdown) ---**
        """)

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

        prompt = textwrap.dedent(f"""
            You are an expert requirements analyst. Your task is to review the following technical specification draft.
            Your goal is to identify ambiguities and guide the Product Manager to a clear, actionable resolution.

            {convergence_directive}

            **MANDATORY INSTRUCTIONS:**
            1.  **STRICT MARKDOWN FORMATTING:** Your entire response must be in raw Markdown.
            2.  If issues are found, structure your response as a numbered list. For each item, clearly state the "Issue" and then provide the "Proposed Solutions".

            **--- Technical Specification Draft to Analyze ---**
            {tech_spec_draft}
            ---
        """)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Failed to analyze tech spec draft: {e}")
            return f"### Error\nAn unexpected error occurred during draft analysis: {e}"

