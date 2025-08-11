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