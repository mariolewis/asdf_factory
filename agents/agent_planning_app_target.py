# agents/agent_planning_app_target.py

import logging
import textwrap
import json
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