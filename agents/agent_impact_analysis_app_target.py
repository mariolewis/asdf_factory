import logging
import json
from llm_service import LLMService
import vault

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
            prompt = vault.get_prompt("agent_impact_analysis_app_target__prompt_31").format(change_request_desc=change_request_desc, final_spec_text=final_spec_text, rowd_json=rowd_json)

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