import google.generativeai as genai
import logging
import json

"""
This module contains the RefactoringPlannerAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RefactoringPlannerAgent_AppTarget:
    """
    Agent responsible for creating a detailed development plan to implement
    a change request. It acts as the core of the Refactoring Pipeline.
    """

    def __init__(self, api_key: str):
        """
        Initializes the RefactoringPlannerAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        genai.configure(api_key=self.api_key)

    def create_refactoring_plan(self, change_request_desc: str, final_spec_text: str, rowd_json: str) -> str:
        """
        Generates a detailed, sequential plan of micro-specifications to implement a change.

        Args:
            change_request_desc (str): The description of the change request to be implemented.
            final_spec_text (str): The full text of the finalized application specification.
            rowd_json (str): A JSON string representing the list of artifacts in the
                             Record-of-Work-Done (RoWD).

        Returns:
            str: A detailed, step-by-step development plan.
                 Returns an error message string if an API call fails.
        """
        try:
            model = genai.GenerativeModel('gemini-pro')

            prompt = f"""
            You are an expert Solutions Architect. Your task is to create a detailed, sequential, and
            modular development plan to implement a given change request. This plan will be composed
            of "micro-specifications" that will be executed by other AI agents.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Context:** Analyze the change request in the context of the overall application specification and the already existing artifacts listed in the RoWD JSON.
            2.  **Deconstruct the Work:** Break down the work required to implement the change into the smallest logical and sequential steps. Each step will become a micro-specification.
            3.  **Plan Structure:** The output must be a clear, numbered list. Each item in the list represents one micro-specification and must describe a single, atomic task (e.g., "Create a new function", "Modify an existing class", "Add a column to a database table", "Delete a file").
            4.  **Detail is Crucial:** For each micro-specification, provide enough detail for a code-generating AI to understand what to do. For modifications, specify the file and artifact name. For new artifacts, describe their purpose, inputs, and outputs.
            5.  **Adhere to Principles:** The plan must adhere to the project's principle of sequential, modular development.

            **--- INPUTS ---**

            **1. Change Request to Implement:**
            ```
            {change_request_desc}
            ```

            **2. Finalized Application Specification:**
            ```
            {final_spec_text}
            ```

            **3. Record-of-Work-Done (RoWD) - Existing Artifacts (JSON):**
            ```json
            {rowd_json}
            ```

            **--- Detailed Refactoring Plan (List of Micro-Specifications) ---**
            """

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            error_message = f"An unexpected error occurred while creating the refactoring plan: {e}"
            logging.error(error_message)
            return error_message