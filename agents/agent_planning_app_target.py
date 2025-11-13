# agents/agent_planning_app_target.py

import logging
import textwrap
import json
import re
from llm_service import LLMService
from asdf_db_manager import ASDFDBManager

class PlanningAgent_AppTarget:
    """
    Agent responsible for generating a detailed, sequential development plan
    based on the finalized application and technical specifications.
    """

    def __init__(self, llm_service: LLMService, db_manager: ASDFDBManager):
        if not llm_service:
            raise ValueError("llm_service is required for the PlanningAgent_AppTarget.")
        if not db_manager:
            raise ValueError("db_manager is required for the PlanningAgent_AppTarget.")
        self.llm_service = llm_service
        self.db_manager = db_manager
        logging.info("PlanningAgent_AppTarget initialized.")

    def generate_backlog_items(self, final_spec_text: str, tech_spec_text: str, ux_spec_text: str | None = None, db_schema_spec_text: str | None = None) -> str:
        """
        Analyzes specifications to deconstruct them into a structured list of
        backlog items, prioritizing UX specs when available.
        """
        logging.info("PlanningAgent: Generating initial backlog items from specifications...")

        ux_spec_context = ""
        if ux_spec_text:
            ux_spec_context = f"""
        **--- INPUT 1: UX/UI Specification (Primary Source for Features) ---**
        {ux_spec_text}
        --- End of UX/UI Specification ---
        """

        db_spec_context = ""
        if db_schema_spec_text:
            db_spec_context = f"""
        **--- INPUT 4: Database Schema Specification (for Context) ---**
        {db_schema_spec_text}
        --- End of Database Schema Specification ---
        """

        prompt = textwrap.dedent(f"""
            You are an expert Agile Business Analyst with deep technical knowledge. Your task is to create a valuable, customer-focused project backlog in a nested JSON format, based on the provided specifications.

            **MANDATORY INSTRUCTIONS:**
            1.  **Input Prioritization:** You MUST prioritize the provided specifications in this order:
                - **Primary Source:** If the "UX/UI Specification" is provided, it is the PRIMARY source for creating user-facing Epics, Features, and User Stories.
                - **Secondary Source:** Use the "Application Specification" for any non-GUI business logic, background processes, or API requirements not covered in the UX spec.
                - **Context Only:** Use the "Technical" and "Database Schema" specifications ONLY for contextual understanding to help you assess technical feasibility and complexity. Do NOT create backlog items directly from them.

            2.  **JSON Array Output:** Your entire response MUST be a single, valid JSON array `[]` where each root object represents an **Epic**.
            3.  **Focus on Customer Value:** The backlog MUST focus exclusively on features and functionalities that will be present in the final, deployed application for the end-user.
            4.  **STRICTLY FORBIDDEN ITEMS:** You MUST NOT create backlog items for development setup, environment configuration, CI/CD pipelines, or any other task related to the *process* of building the software.
            5.  **INVEST Criteria for User Stories:** Every "BACKLOG_ITEM" (User Story) object MUST adhere to the INVEST framework (Independent, Negotiable, Valuable, Estimable, Small, Testable).
            6.  **Nested JSON Schema:** You MUST adhere to the following nested structure:
                - Each **Epic object** must have keys: `"type": "EPIC"`, `"title"`, `"description"`, and `"features": []`.
                - Each **Feature object** must have keys: `"type": "FEATURE"`, `"title"`, `"description"`, and `"user_stories": []`.
                - Each **User Story object** (`BACKLOG_ITEM`) must have keys: `"type": "BACKLOG_ITEM"`, `"title"`, `"description"`, `"priority"` ("High", "Medium", or "Low"), and `"complexity"` ("Small", "Medium", or "Large").

            {ux_spec_context}

            **--- INPUT 2: Application Specification (The "What" for non-GUI logic) ---**
            {final_spec_text}
            --- End of Application Specification ---

            **--- INPUT 3: Technical Specification (The "How" for context) ---**
            {tech_spec_text}
            --- End of Technical Specification ---

            {db_spec_context}

            **--- Generated Backlog (JSON Array Output) ---**
        """)

        try:
            response_json_str = self.llm_service.generate_text(prompt, task_complexity="complex")
            json_match = re.search(r'\[.*\]', response_json_str, re.DOTALL)
            if not json_match:
                raise ValueError("LLM response did not contain a valid JSON array.")

            cleaned_response = json_match.group(0)
            parsed_json = json.loads(cleaned_response)
            logging.info(f"Successfully generated {len(parsed_json)} backlog items.")
            return cleaned_response
        except Exception as e:
            logging.error(f"Failed to generate backlog items: {e}")
            error_response = [{"error": "Failed to generate a valid backlog.", "details": str(e)}]
            return json.dumps(error_response)

    def generate_reference_backlog_from_specs(self, final_spec_text, tech_spec_text, ux_spec_text=None):
        """
        Parses specs to generate a two-level (Epic -> Feature) reference model
        of an existing codebase for the backlog.
        """
        logging.info("PlanningAgent: Generating two-level reference backlog from specs...")

        ux_spec_context = ""
        if ux_spec_text:
            ux_spec_context = f"""
            **--- UX/UI Specification (Primary Source) ---**
            {ux_spec_text}
            """

        prompt = textwrap.dedent(f"""
            You are an expert agile project manager. Your task is to analyze the following specifications of an EXISTING application and decompose them into a hierarchical reference model of Epics and Features.

            **MANDATORY INSTRUCTIONS:**
            1.  **Prioritize Inputs:** If the UX/UI Specification is provided, you MUST use it as the primary source for defining user-facing Epics and Features. Use the Application Specification for non-GUI logic and the Technical Specification only for context.
            2.  **Identify Epics & Features:** Identify high-level capabilities as **Epics** and their specific functionalities as **Features**.
            3.  **DO NOT** generate User Stories or Backlog Items. The goal is a high-level map of what exists.
            4.  **Provide Descriptions:** Provide a concise `title` and a one-sentence `description` for each Epic and Feature.
            5.  **JSON Output:** Your entire response **MUST** be a single, raw JSON array of objects. Do not include any other text, notes, or markdown formatting.

            **JSON Structure:**
            ```json
            [
              {{
                "title": "Epic Title",
                "description": "A high-level description of the epic.",
                "features": [
                  {{
                    "title": "Feature Title",
                    "description": "A description of a specific feature within the epic."
                  }}
                ]
              }}
            ]
            ```

            {ux_spec_context}

            **--- Application Specification (Secondary Source) ---**
            {final_spec_text}

            **--- Technical Specification (Context Only) ---**
            {tech_spec_text}

            **--- JSON Backlog Output ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            # Robustly find and extract the JSON array from the LLM's response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("LLM response did not contain a valid JSON array.")

            cleaned_response = json_match.group(0)
            # Final validation check
            json.loads(cleaned_response)
            return cleaned_response
        except Exception as e:
            logging.error(f"Failed to generate reference backlog: {e}", exc_info=True)
            # Re-raise the exception to be caught by the worker's error handler
            raise e

    def _summarize_text(self, text: str, document_type: str) -> str:
        """Helper to summarize long texts to fit context windows."""
        # This method is retained for future use as required by the PRD, but is not used by the direct prompt.
        logging.info(f"Summarizing {document_type}...")
        prompt = f"Summarize the key functional requirements from the following {document_type} into a concise bulleted list:\n\n{text}"
        try:
            summary = self.llm_service.generate_text(prompt, task_complexity="simple")
            return summary
        except Exception as e:
            logging.error(f"Failed to summarize {document_type}: {e}")
            return text

    def generate_development_plan(self, final_spec_text: str, tech_spec_text: str) -> str:
        """
        Analyzes specifications and generates a development plan as a JSON string.
        This version uses the original, verified, working prompt.
        """
        logging.info("PlanningAgent: Generating development plan directly from full specifications...")

        try:
            if not final_spec_text or not tech_spec_text:
                raise ValueError("Cannot generate plan: One or both of the specification documents are empty.")

            # This is the original, known-good prompt from the working file.
            prompt = textwrap.dedent(f"""
                You are an expert Lead Solutions Architect. Your task is to create a sequential development plan in JSON format.

                **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the JSON object. Do not include any preamble, introduction, comments, or markdown formatting. The first character of your response must be the opening brace `{{`.

                **MANDATORY INSTRUCTIONS:**
                1.  **Trivial Project Check:** Before all other steps, you MUST assess if the project is a "trivial" or "Hello World" style application (e.g., reads one input, does one simple action, prints one output, has no complex logic). **If it is trivial, you MUST generate a plan with only ONE OR TWO steps** that build the entire application in a single source file. This rule overrides all other instructions about granularity.
                2.  **Proportional Granularity:** If the project is not trivial, the level of detail and the number of steps in your plan MUST be proportionate to the scope and complexity of the application. For small projects, produce a concise plan (e.g., 2-5 steps). For large or complex projects, provide a more detailed breakdown.
                3.  **JSON Object Output:** Your entire response MUST be a single, valid JSON object.
                4.  **JSON Schema:** The JSON object MUST have two top-level keys: `"main_executable_file"` and `"development_plan"`.
                5.  **Micro-specification Schema:** Each task in the `"development_plan"` array MUST have the keys: `micro_spec_id`, `task_description`, `component_name`, `component_type`, `component_file_path`, `test_file_path`.

                **--- Project Context ---**
                Full Application Specification:
                {final_spec_text}

                Full Technical Specification:
                {tech_spec_text}

                **--- Detailed Development Plan (JSON Output) ---**
            """)

            response_json_str = self.llm_service.generate_text(prompt, task_complexity="complex")

            if not response_json_str or not response_json_str.strip():
                raise ValueError("LLM returned an empty response. This may be due to a transient error.")

            # A more robust cleaning and validation step
            cleaned_response = response_json_str.strip().removeprefix("```json").removesuffix("```").strip()
            parsed = json.loads(cleaned_response)

            if not isinstance(parsed, dict) or "development_plan" not in parsed:
                raise ValueError("LLM returned invalid JSON structure for development plan.")

            logging.info("Successfully generated development plan.")
            return cleaned_response

        except Exception as e:
            logging.error(f"Failed to generate development plan: {e}")
            error_response = {"error": "Failed to generate a valid development plan.", "details": str(e)}
            return json.dumps(error_response)

    def refine_plan(self, current_plan_json: str, pm_feedback: str, final_spec_text: str, tech_spec_text: str) -> str:
        """
        Refines an existing development plan based on PM feedback.
        """
        import re

        logging.info("PlanningAgent: Refining development plan based on PM feedback...")

        prompt = textwrap.dedent(f"""
            You are an expert Lead Solutions Architect revising a development plan. Your task is to refine an existing JSON development plan based on specific feedback from a Product Manager.

            **MANDATORY INSTRUCTIONS:**
            1.  **Modify, Don't Regenerate:** You MUST modify the "Current Plan Draft" to incorporate the "PM Feedback". Do not regenerate the entire plan from scratch. Preserve all tasks that are not affected by the feedback.
            2.  **JSON Object Output:** Your entire response MUST be a single, valid JSON object, identical in schema to the original plan.
            3.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON object.

            **--- CONTEXT: Project Specifications ---**
            Full Application Specification:
            {final_spec_text}

            Full Technical Specification:
            {tech_spec_text}

            **--- INPUT 1: Current Plan Draft (JSON) ---**
            ```json
            {current_plan_json}
            ```

            **--- INPUT 2: PM Feedback to Address ---**
            ```
            {pm_feedback}
            ```

            **--- Refined Development Plan (JSON Output) ---**
        """)

        try:
            response_json_str = self.llm_service.generate_text(prompt, task_complexity="complex")

            # --- CORRECTED CLEANING AND VALIDATION LOGIC ---
            # More robustly find and extract the JSON block using regex
            json_match = re.search(r"\{.*\}", response_json_str, re.DOTALL)

            if not json_match:
                logging.error(f"PlanningAgent could not find a JSON object in the LLM response during refinement. Response: '{response_json_str}'")
                raise ValueError("The AI model returned a response without a valid JSON object. Please try refining with different wording.")

            cleaned_response = json_match.group(0)
            # --- END OF CORRECTION ---

            # Final validation check
            json.loads(cleaned_response)
            logging.info("Successfully refined development plan from API.")
            return cleaned_response
        except Exception as e:
            logging.error(f"PlanningAgent_AppTarget refinement failed: {e}")
            error_response = {"error": "Failed to refine the development plan.", "details": str(e)}
            return json.dumps(error_response)