import logging
import json
from llm_service import LLMService

# ... (module docstring)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ImpactAnalysisAgent_AppTarget:
    """
    Agent responsible for analyzing the impact of a proposed change request.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the ImpactAnalysisAgent_AppTarget.
        """
        if not llm_service:
            raise ValueError("LLMService is required for the ImpactAnalysisAgent_AppTarget.")
        self.llm_service = llm_service

    def run_full_analysis(self, change_request_desc: str, final_spec_text: str, rowd_json: str) -> dict | None:
        """
        Performs a full, combined impact and technical preview analysis in a single call
        using a robust, function-call-emulation prompt.
        """
        import textwrap
        logging.info(f"Running robust full analysis for: {change_request_desc[:80]}...")
        try:
            prompt = textwrap.dedent(f"""
                You are a system architect analyzing a change request. Your task is to determine the parameters to call a function `record_analysis(rating, summary, ids, preview)`.

                **MANDATORY INSTRUCTIONS:**
                1.  **Prioritize the Change Request:** Your analysis MUST focus primarily on the 'Change Request Description'. The 'Final Application Specification' is for context only. If the CR is small, your analysis MUST be small.
                2.  **Content Separation:** The `summary` parameter MUST be a prose paragraph. The `preview` parameter MUST be a Markdown bulleted list of specific files/components.
                3.  **JSON Output:** Your entire response MUST be a single, valid JSON object representing the arguments for the function call. Do not include any other text.

                **--- Function and Parameters ---**
                `record_analysis(impact_rating, impact_summary, impacted_artifact_ids, technical_preview)`
                - `impact_rating`: (String) "Minor", "Medium", or "Major".
                - `impact_summary`: (String) A prose paragraph describing the scope.
                - `impacted_artifact_ids`: (Array of Strings) IDs from the RoWD of components to be changed. Can be empty.
                - `technical_preview`: (String) A Markdown bulleted list of files/components to be created or modified.

                **--- INPUTS ---**
                1. Change Request Description: {change_request_desc}
                2. Finalized Application Specification (for context): {final_spec_text}
                3. Record-of-Work-Done (RoWD) - Existing Artifacts: {rowd_json}

                **--- JSON Arguments for `record_analysis` function ---**
            """)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            analysis_result = json.loads(cleaned_response)

            if all(k in analysis_result for k in ["impact_rating", "impact_summary", "impacted_artifact_ids", "technical_preview"]):
                return analysis_result
            else:
                raise ValueError("LLM output was missing one or more required keys.")

        except Exception as e:
            error_msg = f"An unexpected error occurred during full analysis: {e}"
            logging.error(error_msg, exc_info=True)
            return None