# agents/agent_project_intake_advisor.py

import logging
import textwrap
import re
import json
from llm_service import LLMService

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
        prompt = textwrap.dedent(f"""
            You are an expert Solutions Architect. Your task is to analyze a user's initial project brief and produce a structured JSON summary.

            **Your Analysis & Summary Task:**
            1.  Read the entire project brief provided by the user.
            2.  Synthesize your understanding into a concise, two-part summary formatted in markdown. The summary should be no more than 8-9 lines in total.
                - Use a "#### Functional Description" heading for the first part.
                - Use a "#### Technical Description" heading for the second part.
            3.  Based on your analysis, provide a brief, advisory assessment on the completeness of the documents.
                - If you identify potential gaps (e.g., in error handling, user interface details, data validation, technology gaps, conflicting specifications), your assessment should be a soft, advisory statement like: "Gaps or inconsistencies were identified in the detailing of [area], for which the system may be able to offer solution options during the specification phases."
                - If the brief appears very detailed and complete, your assessment should be: "The provided brief appears to be sufficiently detailed to proceed for development."

            **Final Output: MANDATORY JSON STRUCTURE**
            Your entire response MUST be a single, valid JSON object and nothing else. Use the following structure:
            ```json
            {{
              "project_summary_markdown": "#### Functional Description\\n...\\n\\n#### Technical Description\\n...",
              "completeness_assessment": "..."
            }}
            ```

            **--- USER'S PROJECT BRIEF ---**
            {brief_text}
            **--- END OF BRIEF ---**

            **JSON OUTPUT:**
        """)

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