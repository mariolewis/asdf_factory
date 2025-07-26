# agents/agent_planning_app_target.py

"""
This module contains the PlanningAgent_AppTarget class.
(ASDF PRD v0.4, F-Phase 2)
"""

import logging
import textwrap
import google.generativeai as genai
import json

class PlanningAgent_AppTarget:
    """
    Agent responsible for generating a detailed, sequential development plan
    based on the finalized application and technical specifications.
    """

    def __init__(self, api_key: str):
        """
        Initializes the PlanningAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for LLM interactions.
        """
        if not api_key:
            raise ValueError("API key is required for the PlanningAgent_AppTarget.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        logging.info("PlanningAgent_AppTarget initialized.")

    def generate_development_plan(self, final_spec_text: str, tech_spec_text: str) -> str:
        """
        Analyzes specifications and generates a development plan as a JSON string.
        This now uses an adaptive strategy: for smaller specs, it uses the full
        text for consistency; for larger specs, it summarizes to prevent errors.
        """
        logging.info("PlanningAgent_AppTarget: Generating development plan using adaptive strategy...")

        # A threshold to decide when to summarize vs. use full text.
        # This can be adjusted, but 15000 chars is a safe starting point.
        PLANNING_SUMMARY_THRESHOLD = 15000
        total_spec_length = len(final_spec_text) + len(tech_spec_text)

        combined_context = ""

        try:
            # If the total spec length is over the threshold, summarize first.
            if total_spec_length > PLANNING_SUMMARY_THRESHOLD:
                logging.info(f"Specifications length ({total_spec_length}) exceeds threshold. Using 'divide and conquer' summary strategy.")
                summary_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')

                # Step 1: Summarize the Functional Specification
                func_summary_prompt = "Summarize the key features, user stories, and data entities from the following application specification into a concise bulleted list."
                func_summary_response = summary_model.generate_content(f"{func_summary_prompt}\n\n{final_spec_text}")
                func_summary = func_summary_response.text

                # Step 2: Summarize the Technical Specification
                tech_summary_prompt = "Summarize the key architectural patterns, technology choices, frameworks, and database schema details from the following technical specification into a concise bulleted list."
                tech_summary_response = summary_model.generate_content(f"{tech_summary_prompt}\n\n{tech_spec_text}")
                tech_summary = tech_summary_response.text

                combined_context = f"Functional Requirements Summary:\n{func_summary}\n\nTechnical Choices Summary:\n{tech_summary}"
            else:
                # If specs are small enough, use the full text for better consistency.
                logging.info(f"Specifications length ({total_spec_length}) is within threshold. Using direct planning strategy.")
                combined_context = f"Full Application Specification:\n{final_spec_text}\n\nFull Technical Specification:\n{tech_spec_text}"

            # Step 3: Generate the final JSON plan from the prepared context.
            logging.info("Generating JSON plan from prepared context...")
            plan_prompt = textwrap.dedent(f"""
                You are an expert Lead Solutions Architect. Your task is to create a detailed, sequential development plan in JSON format based on the provided project specifications or summaries.

                **MANDATORY INSTRUCTIONS:**
                1.  **Determine Main Executable:** Based on the context, determine a logical name for the main executable file with an extension appropriate for the implementation technology (e.g., `main.py`, `app.kt`).
                2.  **Deconstruct the Project:** Break down the entire application into a logical sequence of the smallest possible, independent, fine-grained components. Prioritize granularity.
                3.  **JSON Object Output:** Your entire response MUST be a single, valid JSON object `{{}}`.
                4.  **JSON Schema:** The JSON object MUST have two top-level keys:
                    - `"main_executable_file"`: A string containing the name of the main executable file.
                    - `"development_plan"`: A JSON array `[]` where each element is a micro-specification task.
                5.  **Micro-specification Schema:** Each task object MUST have the keys: `micro_spec_id`, `task_description`, `component_name`, `component_type`, `component_file_path`, `test_file_path`.
                6.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON object itself.

                **--- Project Context ---**
                {combined_context}

                **--- Detailed Development Plan (JSON Output) ---**
            """)

            response = self.model.generate_content(plan_prompt)
            cleaned_response = response.text.strip().removeprefix("```json").removesuffix("```").strip()

            try:
                parsed_json = json.loads(cleaned_response)
                if "main_executable_file" in parsed_json and "development_plan" in parsed_json:
                    return cleaned_response
                else:
                    raise ValueError("JSON object is missing required 'main_executable_file' or 'development_plan' keys.")
            except json.JSONDecodeError as e:
                logging.error(f"The AI response was not in a valid JSON format. Response was: {cleaned_response}")
                raise ValueError("The AI response was not in a valid JSON format.")

        except Exception as e:
            logging.error(f"PlanningAgent_AppTarget logic failed: {e}")
            return json.dumps({"error": f"An unexpected error occurred in the planning agent: {e}"})