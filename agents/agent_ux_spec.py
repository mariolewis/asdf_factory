# agents/agent_ux_spec.py

"""
This module contains the UX_Spec_Agent class, responsible for the iterative
generation of the UX/UI Specification document.
"""

import logging
import textwrap
import json
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

        prompt = textwrap.dedent(f"""
            You are a senior UX Designer and Business Analyst. Your task is to create a single, comprehensive, and consolidated UX/UI Specification document in Markdown format.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the Markdown document. Do not include any preamble, introduction, or conversational text.

            {template_instruction}

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Holistically:** Analyze the provided Project Brief and User Personas to understand the application's goals and target audience.
            2.  **Markdown Format:** The entire output must be a well-structured Markdown document.
            3.  **Required Sections (if no template is provided):** If no template is given, you MUST generate a document containing the following sections, using the exact heading names provided:
                - `## 1. User Personas`
                - `## 2. Core User Journeys`
                - `## 3. Features & User Stories`
                - `## 4. Inferred Screens & Components`
                - `## 5. Draft Theming & Style Guide`
            4.  **Content Generation:** For each section, generate detailed and logical content based on the inputs. For the Style Guide, propose a clean, modern, and professional theme suitable for the application type.

            ---
            **INPUT 1: Project Brief**
            {project_brief}

            **INPUT 2: Confirmed User Personas**
            {personas_str}
            ---

            **Consolidated UX/UI Specification (Markdown):**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
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

        prompt = textwrap.dedent(f"""
            You are a senior UX Designer revising a document. Your task is to refine an existing draft of a UX/UI Specification based on specific feedback from a Product Manager.

            {template_instruction}

            **MANDATORY INSTRUCTIONS:**
            1.  **Preserve Header**: The document has a standard header (Project Number, Type, Date, Version). You MUST preserve this header and its structure exactly as it is.
            2.  **Modify Body Only**: Your changes should only be in the body of the document to incorporate the PM's feedback. Do not regenerate the entire document from scratch.
            3.  **RAW MARKDOWN ONLY:** Your entire response MUST be only the raw content of the refined document, including the preserved header.

            **--- INPUT 1: Current Draft ---**
            ```markdown
            {current_draft}
            ```

            **--- INPUT 2: PM Feedback to Address ---**
            ```
            {pm_feedback}
            ```

            **--- Refined UX/UI Specification Document (Markdown) ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            logging.error(f"UX_Spec_Agent failed to refine UX draft: {e}")
            return f"### Error\nCould not refine the UX/UI Specification Draft. Details: {e}"

    def parse_final_spec_and_generate_blueprint(self, final_spec_markdown: str) -> str:
        """
        Parses the final, human-readable UX/UI spec in Markdown and generates
        a structured, machine-readable JSON blueprint of the screens and components.
        """
        logging.info("UX_Spec_Agent: Parsing final spec to generate JSON blueprint...")

        prompt = textwrap.dedent(f"""
            You are a meticulous data extraction system. Your task is to analyze a final UX/UI Specification written in Markdown and convert all screen and component descriptions into a single, structured JSON object.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the JSON object. Do not include any preamble, introduction, comments, or markdown formatting like ```json. The first character of your response must be the opening brace `{{`.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your response MUST be a single, valid JSON object.
            2.  **Top-Level Key:** The top-level key of the JSON object MUST be "screens". Its value should be an array of screen objects.
            3.  **Screen Object Schema:** Each object in the "screens" array MUST adhere to the following schema:
                {{
                  "screen_name": "...",
                  "layout_description": "...",
                  "components": [
                    {{
                      "component_type": "...",
                      "label": "...",
                      "details": "...",
                      "action": "..."
                    }}
                  ]
                }}
            4.  **Extraction:** Carefully read the 'Inferred Screens & Components' section of the Markdown input and populate the JSON structure accordingly. Infer the layout, component types, labels, details, and actions from the text.

            ---
            **INPUT: Final UX/UI Specification (Markdown)**
            {final_spec_markdown}
            ---

            **OUTPUT: Structural UI Blueprint (JSON Object):**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            # Clean the response to remove potential markdown fences
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()
            # Final validation check
            json.loads(cleaned_response)
            return cleaned_response
        except Exception as e:
            logging.error(f"UX_Spec_Agent failed to parse spec and generate blueprint: {e}")
            error_json = {{"error": f"Could not generate blueprint from spec. Details: {e}"}}
            return json.dumps(error_json, indent=2)

    def generate_user_journeys(self, project_brief: str, personas: list[str]) -> str:
        """
        Generates a list of core user journeys based on the project brief and personas.
        """
        logging.info("UX_Spec_Agent: Generating user journeys...")

        personas_str = "- " + "\n- ".join(personas)

        prompt = textwrap.dedent(f"""
            You are a senior UX Designer. Your task is to outline the most critical user journeys for an application based on its description and the target user personas.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the numbered list. Do not include any preamble, introduction, or conversational text. The first character of your response must be the first character of the list (e.g., "1.").

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze:** Consider the project brief and the user personas.
            2.  **Identify Journeys:** Identify a list of high-level, end-to-end user journeys. A journey describes a complete task a user would perform (e.g., "Booking a flight," "Viewing a monthly sales report," "Configuring user settings").
            3.  **Numbered List:** Your response MUST be only a numbered list of these journeys.

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
            logging.error(f"UX_Spec_Agent failed to generate user journeys: {e}")
            return f"Error: Could not generate user journeys. Details: {e}"

    def identify_screens_from_journeys(self, user_journeys: str) -> str:
        """
        Analyzes a list of user journeys and identifies the necessary UI screens/views.
        """
        logging.info("UX_Spec_Agent: Identifying screens from user journeys...")

        prompt = textwrap.dedent(f"""
            You are a senior UI/UX Architect. Your task is to analyze a list of user journeys and identify all the unique screens, views, or major UI components required to fulfill them.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the numbered list. Do not include any preamble, introduction, or conversational text. The first character of your response must be the first character of the list (e.g., "1.").

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze:** Read the user journeys and list every distinct screen or view that is explicitly mentioned or strongly implied.
            2.  **Consolidate:** Consolidate duplicate screens. For example, if one journey mentions a "Login Page" and another mentions a "Sign-in screen," list it once as "Login Screen."
            3.  **Numbered List:** Your response MUST be only a numbered list of these screen/view names.

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
            logging.error(f"UX_Spec_Agent failed to identify screens: {e}")
            return f"Error: Could not identify screens from journeys. Details: {e}"

    def generate_screen_blueprint(self, screen_name: str, pm_description: str) -> str:
        """
        Takes a PM's description of a screen and generates a structured
        JSON blueprint for its layout and components.
        """
        logging.info(f"UX_Spec_Agent: Generating blueprint for screen: {screen_name}")

        prompt = textwrap.dedent(f"""
            You are a meticulous UI/UX Architect creating a machine-readable specification. Your task is to convert a natural language description of a single application screen into a structured JSON object.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the JSON object. Do not include any preamble, introduction, comments, or markdown formatting like ```json. The first character of your response must be the opening brace `{{`.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your response MUST be a single, valid JSON object.
            2.  **JSON Schema:** The JSON object MUST adhere to the following schema:
                {{
                  "screen_name": "...",
                  "layout_description": "...",
                  "components": [
                    {{
                      "component_type": "...",
                      "label": "...",
                      "details": "...",
                      "action": "..."
                    }}
                  ]
                }}
            3.  **Schema Fields:**
                - `screen_name`: The name of the screen you are designing.
                - `layout_description`: A brief description of the screen's layout (e.g., "2-column layout with a fixed sidebar", "Main content area with a modal dialog").
                - `components`: An array of objects, where each object represents a single UI element.
                - `component_type`: The type of the element (e.g., "button", "data_table", "chart", "text_input", "kpi_card", "navigation_menu").
                - `label`: The visible text or title for the component.
                - `details`: A brief description of the component's purpose or the data it displays.
                - `action`: A description of what happens when the user interacts with the component (e.g., "navigate_to_details_screen", "submit_form", "opens_settings_modal").

            ---
            **Screen to Design:**
            {screen_name}

            **Product Manager's Description of Components:**
            {pm_description}
            ---

            **Generated Screen Blueprint (JSON Object):**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            # Clean the response to remove potential markdown fences
            cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()
            # Final validation check
            json.loads(cleaned_response)
            return cleaned_response
        except Exception as e:
            logging.error(f"UX_Spec_Agent failed to generate screen blueprint: {e}")
            error_json = {{"error": f"Could not generate blueprint. Details: {e}"}}
            return json.dumps(error_json, indent=2)

    def generate_style_guide(self, pm_description: str) -> str:
        """
        Takes a PM's description of a desired look and feel and generates
        a text-based Theming & Style Guide in Markdown.
        """
        logging.info("UX_Spec_Agent: Generating Theming & Style Guide...")

        prompt = textwrap.dedent(f"""
            You are a senior UI/UX Designer specializing in creating design systems. Your task is to take a high-level, natural language description of a desired "look and feel" and convert it into a structured, text-based Theming & Style Guide using Markdown.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the Markdown document. Do not include any preamble, introduction, or conversational text. The first character of your response must be the first character of the document's content (e.g., the `#` of a heading).

            **MANDATORY INSTRUCTIONS:**
            1.  **Markdown Output:** Your response MUST be a well-formatted Markdown document.
            2.  **Core Sections:** The document MUST include the following sections:
                - `## Color Palette`: Define primary, secondary, accent, success, and error colors. Provide hex codes.
                - `## Typography`: Define the primary font families for headings and body text.
                - `## Component Styling`: Provide general rules for the look of common elements (e.g., buttons, input fields, cards).
                - `## Iconography`: Suggest a suitable, widely-used icon library (e.g., "Material Design Icons", "Font Awesome").
            3.  **Interpret Vague Terms:** Interpret subjective terms from the user's description (e.g., "modern," "professional," "clean") into concrete design choices.

            ---
            **Product Manager's Description of Desired Look and Feel:**
            {pm_description}
            ---

            **Theming & Style Guide (Markdown):**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            return response_text.strip()
        except Exception as e:
            logging.error(f"UX_Spec_Agent failed to generate style guide: {e}")
            return f"### Error\nCould not generate style guide. Details: {e}"