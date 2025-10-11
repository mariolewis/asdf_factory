import logging
from llm_service import LLMService

"""
This module contains the UITestPlannerAgent_AppTarget class.
"""

# Configure basic logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UITestPlannerAgent_AppTarget:
    """
    Agent responsible for generating UI test case content for a target application.

    Based on the application's specifications, this agent produces a structured,
    human-readable test plan for the Product Manager to execute manually.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the UITestPlannerAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the UITestPlannerAgent_AppTarget.")
        self.llm_service = llm_service

    def generate_ui_test_plan(self, functional_spec_text: str, technical_spec_text: str, ux_spec_text: str) -> str:
        """
        Generates a UI test plan based on functional, technical, and UX specs.

        Args:
            functional_spec_text (str): The complete functional specification.
            technical_spec_text (str): The complete technical specification.
            ux_spec_text (str): The complete UX/UI specification, including the JSON blueprint.

        Returns:
            str: A string containing the UI test plan in Markdown table format.
                Returns an error message string if an API call fails.
        """
        try:
            prompt = f"""
            You are a meticulous Software Quality Assurance (QA) Specialist.
            Your task is to create a detailed, human-readable UI test plan based on the provided project documentation.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the Markdown table for the test plan. Do not include any preamble, introduction, or conversational text. The first character of your response must be the first character of the table's header.

            **MANDATORY INSTRUCTIONS:**
            1.  **Primary Source:** You MUST use the **UX/UI Specification** as the primary source for creating test cases, as it contains the most detailed descriptions of screens, components, and user flows.
            2.  **Format:** Your entire response MUST be a single Markdown table.
            3.  **Table Columns:** The table MUST have the columns: "Test Case ID", "Feature", "Test Scenario", "Steps to Reproduce", "Expected Result", and a blank "Actual Result" column for the user to fill in.
            4.  **Comprehensive Coverage:** Your test cases must cover all user-facing features, screens, and components described in the UX/UI Specification. Use the other specifications for additional context on business logic and technical constraints.
            5.  **Clarity:** Provide clear, numbered steps that a non-technical user can follow.
            6.  **STRICT MARKDOWN FORMATTING:** For any content within the table cells that requires a list (like "Steps to Reproduce"), each item MUST start on a new line with a number and a space (e.g., "1. First step.").

            **--- INPUT 1: UX/UI Specification (Primary Source) ---**
            ```
            {ux_spec_text}
            ```

            **--- INPUT 2: Functional Specification (Context) ---**
            ```
            {functional_spec_text}
            ```

            **--- INPUT 3: Technical Specification (Context) ---**
            ```
            {technical_spec_text}
            ```

            **--- Generated UI Test Plan (Markdown Table) ---**
            """

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")

            if "|" in response_text and "---" in response_text:
                return response_text
            else:
                logging.warning("LLM response did not appear to be a Markdown table.")
                return "Error: The AI did not return a valid Markdown table. Please try again."

        except Exception as e:
            error_message = f"An error occurred during UI test plan generation: {e}"
            logging.error(error_message)
            return error_message