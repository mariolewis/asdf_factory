# agents/agent_project_intake_advisor.py

import logging
import textwrap
import re
import json
from llm_service import LLMService

class ProjectIntakeAdvisorAgent:
    """
    Performs a holistic analysis of a user's initial project documents
    to propose a tailored, proportional workflow plan.
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
        Analyzes the initial brief for triviality and completeness, and
        segregates content to propose a tailored workflow.

        Args:
            brief_text (str): The combined text from the user's initial input.

        Returns:
            A JSON string containing the full workflow proposal.
        """
        prompt = textwrap.dedent(f"""
            You are an expert Solutions Architect responsible for project intake. Your task is to perform a multi-stage analysis of a user's initial project brief and return a single, structured JSON object proposing a tailored workflow.

            **Stage 1: Triviality Assessment**
            First, determine if the request is for a trivial, "Hello World" style application. A trivial project is defined as a simple, single-file application with no complex logic or dependencies.
            - If the project is trivial, your entire output MUST be a simple JSON object:
              `{{ "is_trivial": true, "justification": "A brief explanation of why it's trivial." }}`
            - If it is not trivial, proceed to Stage 2.

            **Stage 2: Granular Completeness Assessment (for non-trivial projects)**
            Independently assess the provided text for the completeness of the following five artifacts. For each, determine a proposed action from the allowed list:
            - **UX/UI Specification**: `ELABORATE` (missing), `REFINE` (high-level ideas present), `SKIP` (comprehensive details found).
            - **Application Specification**: `ELABORATE`, `REFINE`, `SKIP`.
            - **Technical Specification**: `ELABORATE`, `REFINE`, `SKIP`.
            - **Coding Standard**: `ELABORATE` (not found), `ADOPT` (a complete standard is present).
            - **Project Backlog**: `ELABORATE` (not found), `ADOPT` (a well-defined backlog of epics/features/stories is present).

            **Stage 3: Content Segregation**
            For any artifact where the proposed action is `SKIP`, `REFINE`, or `ADOPT`, you MUST extract the clean, relevant block of text for that artifact from the user's brief.

            **Final Output: MANDATORY JSON STRUCTURE**
            Your entire response MUST be a single, valid JSON object and nothing else.
            - For a trivial project, use the simple structure from Stage 1.
            - For a non-trivial project, you MUST use the following comprehensive structure:
            ```json
            {{
              "is_trivial": false,
              "assessment_summary": "A concise, one-sentence summary of your findings for the PM.",
              "proposed_plan": [
                {{ "phase": "UX/UI Design", "action": "...", "justification": "..." }},
                {{ "phase": "Application Specification", "action": "...", "justification": "..." }},
                {{ "phase": "Technical Specification", "action": "...", "justification": "..." }},
                {{ "phase": "Coding Standard", "action": "...", "justification": "..." }},
                {{ "phase": "Backlog Generation", "action": "...", "justification": "..." }}
              ],
              "segregated_content": {{
                "ux_spec_text": "...",
                "final_spec_text": "...",
                "tech_spec_text": "...",
                "coding_standard_text": "...",
                "project_backlog_text": "..."
              }}
            }}
            ```
            - Note: For `segregated_content`, only include keys for content that was actually found and extracted.

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
            logging.error(f"ProjectIntakeAdvisorAgent failed to get or parse LLM response: {e}")
            error_payload = {
                "error": "Failed to analyze the project brief.",
                "details": str(e)
            }
            return json.dumps(error_payload)