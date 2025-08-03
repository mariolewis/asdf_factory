# agents/agent_planning_app_target.py

"""
This module contains the PlanningAgent_AppTarget class.
(ASDF PRD v0.4, F-Phase 2)
"""

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
        """
        Initializes the PlanningAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
            db_manager (ASDFDBManager): An instance of the database manager for config access.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the PlanningAgent_AppTarget.")
        if not db_manager:
            raise ValueError("db_manager is required for the PlanningAgent_AppTarget.")
        self.llm_service = llm_service
        self.db_manager = db_manager
        logging.info("PlanningAgent_AppTarget initialized.")

    def generate_development_plan(self, final_spec_text: str, tech_spec_text: str) -> str:
        """
        Analyzes specifications and generates a development plan as a JSON string.
        """
        logging.info("PlanningAgent_AppTarget: Generating development plan using adaptive strategy...")

        try:
            with self.db_manager as db:
                limit_str = db.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "2000000"
            planning_summary_threshold = int(int(limit_str) * 0.8)
        except Exception as e:
            logging.error(f"Could not read CONTEXT_WINDOW_CHAR_LIMIT from DB, using fallback. Error: {e}")
            planning_summary_threshold = 128000

        total_spec_length = len(final_spec_text) + len(tech_spec_text)
        combined_context = ""

        if total_spec_length > planning_summary_threshold:
            logging.info(f"Specifications length ({total_spec_length}) exceeds threshold. Using 'divide and conquer' summary strategy.")
            func_summary_prompt = f"Summarize the key features and user stories from the following application specification into a concise bulleted list.\n\n{final_spec_text}"
            func_summary = self.llm_service.generate_text(func_summary_prompt, task_complexity="simple")
            tech_summary_prompt = f"Summarize the key architectural patterns and technology choices from the following technical specification into a concise bulleted list.\n\n{tech_spec_text}"
            tech_summary = self.llm_service.generate_text(tech_summary_prompt, task_complexity="simple")
            combined_context = f"Functional Requirements Summary:\n{func_summary}\n\nTechnical Choices Summary:\n{tech_summary}"
        else:
            logging.info(f"Specifications length ({total_spec_length}) is within threshold. Using direct planning strategy.")
            combined_context = f"Full Application Specification:\n{final_spec_text}\n\nFull Technical Specification:\n{tech_spec_text}"

        plan_prompt = textwrap.dedent(f"""
            You are an expert Lead Solutions Architect. Your task is to create a sequential development plan in JSON format.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the JSON object. Do not include any preamble, introduction, comments, or markdown formatting. The first character of your response must be the opening brace `{{`.

            **MANDATORY INSTRUCTIONS:**
            1.  **Trivial Project Check:** Before all other steps, you MUST assess if the project is a "trivial" or "Hello World" style application (e.g., reads one input, does one simple action, prints one output, has no complex logic). **If it is trivial, you MUST generate a plan with only ONE OR TWO steps** that build the entire application in a single source file. This rule overrides all other instructions about granularity.
            2.  **Proportional Granularity:** If the project is not trivial, the level of detail and the number of steps in your plan MUST be proportionate to the scope and complexity of the application. For small projects, produce a concise plan (e.g., 2-5 steps). For large or complex projects, provide a more detailed breakdown.
            3.  **JSON Object Output:** Your entire response MUST be a single, valid JSON object.
            4.  **JSON Schema:** The JSON object MUST have two top-level keys: `"main_executable_file"` and `"development_plan"`.
            5.  **Micro-specification Schema:** Each task in the `"development_plan"` array MUST have the keys: `micro_spec_id`, `task_description`, `component_name`, `component_type`, `component_file_path`, `test_file_path`.

            **--- Project Context ---**
            {combined_context}

            **--- Detailed Development Plan (JSON Output) ---**
        """)

        response_text = self.llm_service.generate_text(plan_prompt, task_complexity="complex")
        cleaned_response = response_text.strip().removeprefix("```json").removesuffix("```").strip()

        try:
            parsed_json = json.loads(cleaned_response)
            if "main_executable_file" in parsed_json and "development_plan" in parsed_json:
                return cleaned_response
            else:
                raise ValueError("JSON object is missing required 'main_executable_file' or 'development_plan' keys.")
        except json.JSONDecodeError:
            raise ValueError(f"The AI response was not in a valid JSON format. Response was: {cleaned_response}")