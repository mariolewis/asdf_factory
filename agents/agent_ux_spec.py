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