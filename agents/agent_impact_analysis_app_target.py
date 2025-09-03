import logging
import json
from llm_service import LLMService

# ... (module docstring)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ImpactAnalysisAgent_AppTarget:
    """
    Agent responsible for analyzing the impact of a proposed change request.

    It assesses a change request against the existing project documentation
    and Record-of-Work-Done (RoWD) to determine its scope and potential impact.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the ImpactAnalysisAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("LLMService is required for the ImpactAnalysisAgent_AppTarget.")
        self.llm_service = llm_service

    def analyze_impact(self, change_request_desc: str, final_spec_text: str, rowd_json: str) -> tuple[str | None, str | None, list[str] | None]:
        """
        Performs a high-level impact analysis, assigning a rating and identifying
        the specific artifacts that are impacted.

        Returns:
            A tuple containing (impact_rating, impact_summary, impacted_artifact_ids).
            Returns (None, None, None) on failure.
        """
        try:
            prompt = f"""
            You are a seasoned Software Architect. Your task is to perform a high-level impact analysis of a proposed change request. Your role is to determine WHAT needs to change, not to critique the validity of the request.

            **MANDATORY INSTRUCTIONS:**
            1.  **Objective Analysis:** Analyze the inputs to determine the technical scope of the change. DO NOT provide opinions on whether the change request is good or bad. Your summary must focus on the implementation scope.
            2.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            3.  **JSON Schema:** The JSON object MUST have three keys:
                - `impact_rating`: Your assessment of the change's scope ("Minor", "Medium", or "Major").
                - `impact_summary`: A brief, one-paragraph TECHNICAL summary describing the required changes (e.g., "This will require modifying the User class to add a new property, updating the database schema with a new column, and adding a new field to the user profile UI.").
                - `impacted_artifact_ids`: A JSON array of strings, where each string is the `artifact_id` from the RoWD for a component you believe will be directly created or modified by this change.
            4.  **No Other Text:** Do not include any text or markdown formatting outside of the raw JSON object itself.

            **--- INPUTS ---**
            **1. Change Request Description:** `{change_request_desc}`
            **2. Finalized Application Specification:** `{final_spec_text}`
            **3. Record-of-Work-Done (RoWD) - Existing Artifacts (JSON):** `{rowd_json}`

            **--- Impact Analysis (JSON Output) ---**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            analysis_result = json.loads(cleaned_response)

            rating = analysis_result.get("impact_rating")
            summary = analysis_result.get("impact_summary")
            impacted_ids = analysis_result.get("impacted_artifact_ids", [])

            if rating not in ["Minor", "Medium", "Major"] or not isinstance(impacted_ids, list):
                raise ValueError("Invalid format received from AI.")

            return rating, summary, impacted_ids

        except Exception as e:
            error_msg = f"An unexpected error occurred during impact analysis: {e}"
            logging.error(error_msg)
            return None, error_msg, None

    def generate_technical_preview(self, change_request_desc: str, final_spec_text: str, rowd_json: str) -> str:
        """
        Analyzes a change request and provides a human-readable technical summary
        of the anticipated changes to the codebase.

        Returns:
            A string containing the summary, or an error message on failure.
        """
        import textwrap
        try:
            prompt = textwrap.dedent(f"""
                You are a senior solutions architect. Your task is to analyze a change request and the current state of a project to provide a concise, high-level technical preview of the required work.

                **MANDATORY INSTRUCTIONS:**
                1.  **Raw Markdown Only:** Your entire response MUST be only the raw content of a Markdown bulleted list. Do not include any preamble, conversational text, HTML tags, or markdown fences. The first character of your response must be a `-` or `*`.
                2.  **Analyze Holistically:** Review the change request, the application specification, and the list of existing code artifacts (RoWD).
                3.  **Identify Key Changes:** Determine which existing files will likely need modification and identify any new files that will need to be created.
                4.  **Focus on "What", Not "How":** The summary should state *what* will change (e.g., "Modify the `UserService` class," "Create a new `api/endpoint.py` file"), not the specific lines of code.

                **--- INPUTS ---**
                **1. Change Request Description:** {change_request_desc}
                **2. Finalized Application Specification:** {final_spec_text}
                **3. Record-of-Work-Done (RoWD) - Existing Artifacts (JSON):** {rowd_json}

                **--- Technical Preview Summary (Raw Markdown Bulleted List) ---**
            """)

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            if not response_text or response_text.startswith("Error:"):
                raise ValueError(f"LLM returned an error or empty response: {response_text}")

            return response_text.strip()

        except Exception as e:
            error_msg = f"An unexpected error occurred during technical preview generation: {e}"
            logging.error(error_msg, exc_info=True)
            return f"Error: Could not generate technical preview. Details: {e}"