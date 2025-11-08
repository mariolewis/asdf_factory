# agents/agent_tech_stack_proposal.py

"""
This module contains the TechStackProposalAgent class.
"""

import logging
import textwrap
import json
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
            The following template provides both the required structure for the document AND **mandatory technical guidelines**.
            You MUST adhere to all rules, constraints, and technology choices already present in the template content.
            Your task is to **complete** this template by filling in the remaining details based on the application's specific requirements, while ensuring full compliance with the guidelines provided within the template itself.
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
            You are an expert Solutions Architect. Your task is to create the BODY of a formal and appropriately detailed Technical Specification for a **{target_os}** environment, based on the provided Functional Specification.

            **CRITICAL INSTRUCTIONS:** - Your entire response MUST be only the raw Markdown content of the document's BODY.
            - Do NOT add a header, preamble, introduction, or any conversational text.

            **STRICT MARKDOWN FORMATTING:** You MUST use Markdown for all formatting. Use '##' for main headings and '###' for sub-headings. For lists, each item MUST start on a new line with an asterisk and a space (e.g., "* List item text."). Paragraphs MUST be separated by a full blank line. This is mandatory.

            {template_instruction}

            **--- Mandatory Analysis and Scoping Instructions ---**
            1.  **Analyze Application Archetype:** First, you MUST analyze the provided Functional Specification to determine the application's core nature (e.g., simple CLI tool, complex data pipeline, real-time GUI, desktop CRUD app, web service).
            2.  **Tailor Document Structure:** Second, based on the archetype you identify, you MUST generate a Technical Specification BODY that includes only the relevant sections. For a simple CLI tool, you might only need 'Technology Stack' and 'Development Environment'. For a complex web service, you would also need 'High-Level Architecture', 'Data Architecture', and 'NFRs'. The level of detail must be appropriate for the project's scope.
            3.  **Adhere to Constraints:** You MUST treat any content in the provided Template and any guidelines from the PM Directive as mandatory constraints, building your technical proposal around them.

            A comprehensive Technical Specification often includes the following sections. You MUST evaluate which of these are relevant and include them in your response.
            - **High-Level Architecture**
            - **Component Architecture Design**
            - **Technology Stack Selection**
            - **Data & Integration Architecture**
            - **Non-Functional Requirements (NFRs)**
            - **Development Environment Setup Guide**

            **CRITICAL DIAGRAMMING RULE:**
            - **To maximize clarity, you SHOULD generate 2-3 key diagrams.**
            - **Your diagram choices MUST be relevant to the project's archetype.** For example, an `Architecture Diagram`, a `Data Flow Diagram`, or a `Data Model Diagram` (as appropriate).
            - You MUST generate diagrams using the **DOT language** inside a ```dot ... ``` code block.
            - The graph MUST be defined (e.g., `digraph G { ... }`).
            - **Layout:** For architectural layers or flows, you **MUST** prefer a vertical layout (Top-to-Bottom, e.g., `rankdir=TD`) to ensure the diagram fits a portrait document.
            - **Styling:**
                - You **MAY** use `fillcolor` to add *light pastel* colors to nodes (e.g., `fillcolor="#F0F8FF"`) to differentiate logical groups.
                - You **MUST NOT** specify any `fontname` or `fontsize`. The renderer will use a default.
                - You **MUST NOT** add attributes for `size`, `ratio`, or `dimensions`. Let the renderer auto-size.
            - **Syntax:**
                - **Nodes MUST use simple string labels.**
                - **FOR MULTI-LINE LABELS (like database tables):** You MUST use a simple string with newline characters (`\n`). **Example:** `MyTable [label="Products\n- ProductID (PK)\n- Name\n- Price"]`
                - **YOU MUST NOT** use complex, record-based, or HTML-like labels (e.g., `label=<...>`, `label="{{...|...}}"`, or `shape=record`).
                - **Ensure all nodes are defined only once.** Do not place a node in multiple subgraphs or ranksets.
                - **Use simple edge syntax:** `NodeA -> NodeB [label="edge label"]`. Do NOT use HTML-like labels or `<-` arrows.
            - Do NOT use ASCII art.

            - **DO NOT** write "helper" text like `[Diagram]`. This will break the system.
            - Your response for a diagram MUST be *ONLY* the code block, starting with ````dot` and ending with ````.

            **EXAMPLE of CORRECT (and ONLY) OUTPUT for a diagram:**
            ```dot
            digraph G {{
                A[Start] -> B[DoSomething];
                B -> C[End];
            }}
            ```

            {pm_guidelines_section}

            **--- Functional Specification (The "What") ---**
            {functional_spec_text}
            ---

            **--- Generated Technical Specification Body (Raw Markdown) ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            logging.info("Successfully received OS-aware technology stack proposal from API.")
            return response_text
        except Exception as e:
            logging.error(f"TechStackProposalAgent API call failed: {e}")
            return f"Error: An unexpected error occurred while generating the tech stack proposal: {e}"

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

        prompt = textwrap.dedent(f"""
            You are a senior Solutions Architect revising a document. Your task is to refine the body of a Technical Specification based on a list of identified issues and specific feedback from a Product Manager.

            **MANDATORY INSTRUCTIONS:**
            1.  **Refine Body Only**: The text you receive is the body of a document. Your task is to incorporate the PM's clarifications to resolve the identified issues.
            2.  **RAW MARKDOWN ONLY:** Your entire response MUST be only the raw, refined text of the document's body. Do NOT add a header, preamble, or any conversational text.
            3.  **STRICT MARKDOWN FORMATTING:** You MUST use Markdown for all formatting (e.g., '##' for main headings, '###' for sub-headings, and '*' for list items). Paragraphs MUST be separated by a full blank line.

            {template_instruction}

            **--- CONTEXT: Full Application Specification ---**
            {functional_spec_text}
            ---

            **--- INPUT 1: Current Draft Body ---**
            ```markdown
            {current_draft}
            ```

            **--- INPUT 2: AI-Generated Issues That the PM is Responding To ---**
            ```markdown
            {ai_issues_text}
            ```

            **--- INPUT 3: PM Feedback to Address ---**
            ```
            {pm_feedback}
            ```

            **--- Refined Document Body for {target_os} (Raw Markdown) ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            logging.info("Successfully refined technical specification from API.")
            return response_text
        except Exception as e:
            logging.error(f"TechStackProposalAgent refinement failed: {e}")
            return f"Error: An unexpected error occurred while refining the tech spec: {e}"

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

