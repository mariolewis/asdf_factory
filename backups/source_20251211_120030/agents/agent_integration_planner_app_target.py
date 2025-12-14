import logging
import json
from llm_service import LLMService, parse_llm_json
import vault

class IntegrationPlannerAgent:
    """
    Agent responsible for creating a plan to integrate new components.

    This agent analyzes newly created artifacts and the existing codebase
    to produce a detailed plan of modifications required to "wire in"
    the new components.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the IntegrationPlannerAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the IntegrationPlannerAgent.")
        self.llm_service = llm_service


    def create_integration_plan(self, new_artifacts_json: str, existing_code_files: dict[str, str]) -> str:
        """
        Generates a JSON-based plan for integrating new components.
        """
        try:
            # Prepare the context of existing files for the prompt
            existing_files_context = ""
            for path, content in existing_code_files.items():
                existing_files_context += f"--- File: {path} ---\\n```\\n{content}\\n```\\n\\n"

            # CORRECTED: Escaped all literal curly braces in the JSON schema example.
            prompt = vault.get_prompt("agent_integration_planner_app_target__prompt_37").format(new_artifacts_json=new_artifacts_json, existing_files_context=existing_files_context)

            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            cleaned_response = response_text.strip()
            parse_llm_json(cleaned_response) # Validate if the response is a valid JSON object
            return cleaned_response

        except json.JSONDecodeError as e:
            error_msg = f"Error: The AI did not return a valid JSON object. {e}\\nResponse was:\\n{response_text}"
            logging.error(error_msg)
            return f'{{"error": "{error_msg}"}}'
        except Exception as e:
            error_msg = f"An unexpected error occurred during integration planning: {e}"
            logging.error(error_msg)
            return f'{{"error": "{error_msg}"}}'