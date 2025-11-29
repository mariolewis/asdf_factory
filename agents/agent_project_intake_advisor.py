# agents/agent_project_intake_advisor.py

import logging
import textwrap
import re
import json
from llm_service import LLMService
import vault

class ProjectIntakeAdvisorAgent:
    """
    Analyzes the user's initial project brief to provide a summary and
    an advisory assessment on its completeness, guiding the PM's choice
    of a development lifecycle path.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the ProjectIntakeAdvisorAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the ProjectIntakeAdvisorAgent.")
        self.llm_service = llm_service
        logging.info("ProjectIntakeAdvisorAgent initialized.")

    def assess_brief_completeness(self, brief_text: str) -> str:
        """
        Analyzes the initial brief for completeness and generates a summary.

        Args:
            brief_text (str): The combined text from the user's initial input.

        Returns:
            A JSON string containing the project summary and completeness assessment.
        """
        prompt = vault.get_prompt("agent_project_intake_advisor__prompt_38").format(brief_text=brief_text)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="complex")
            # Clean the response to find the JSON block
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("LLM response did not contain a valid JSON object.")

            cleaned_json = json_match.group(0)
            # Validate that it's proper JSON
            json.loads(cleaned_json)
            return cleaned_json
        except Exception as e:
            logging.error(f"ProjectIntakeAdvisorAgent failed to get or parse LLM response: {{e}}")
            error_payload = {{
                "project_summary_markdown": "### Error\\nAn error occurred while analyzing the project brief.",
                "completeness_assessment": f"Details: {{str(e)}}"
            }}
            return json.dumps(error_payload)