import google.generativeai as genai
import logging
import json

class IntegrationPlannerAgent:
    """
    Agent responsible for creating a plan to integrate new components.

    This agent analyzes newly created artifacts and the existing codebase
    to produce a detailed plan of modifications required to "wire in"
    the new components.
    """

    def __init__(self, api_key: str):
        """
        Initializes the IntegrationPlannerAgent.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')


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
            prompt = f"""
            You are a senior software engineer specializing in system integration.
            Your task is to create a detailed plan to integrate newly created software components into an existing codebase.

            **CRITICAL INSTRUCTION:** Your entire response MUST be only the raw content of the JSON object. Do not include any preamble, introduction, comments, or markdown formatting like ```json. The first character of your response must be the opening brace `{{`.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your response MUST be a single, valid JSON object. This object will map file paths to the modifications needed for that file.
            2.  **JSON Schema:** The JSON object should have the following structure:
                `{{
                    "file_path_to_modify.py": [
                        {{
                            "action": "ADD_IMPORT",
                            "line_content": "from new_module import new_function"
                        }},
                        {{
                            "action": "REPLACE_LINE",
                            "line_number": 42,
                            "new_content": "result = new_function(data)"
                        }},
                        {{
                            "action": "INSERT_AFTER",
                            "line_number": 55,
                            "content_to_insert": "    # Additional logic for new component\\n    process_new_component()"
                        }}
                    ],
                    "another_file.py": [ ... ]
                }}`
            3.  **Allowed Actions:** The "action" key must be one of: "ADD_IMPORT", "REPLACE_LINE", "INSERT_AFTER", "INSERT_BEFORE", "DELETE_LINE".
            4.  **Analysis:** Analyze the new artifacts and the existing code files to determine the necessary changes. Common changes include adding import statements at the top of files and calling the new functions/classes where appropriate in the application's logic.
            5.  **No Other Text:** Do not include any text, explanations, or markdown formatting like ```json outside of the raw JSON object itself.

            **--- INPUTS ---**

            **1. New Artifacts to Integrate (JSON from RoWD):**
            ```json
            {new_artifacts_json}
            ```

            **2. Existing Code Files That May Need Modification:**
            {existing_files_context}

            **--- Detailed Integration Plan (JSON Output) ---**
            """

            response = self.model.generate_content(prompt)
            cleaned_response = response.text.strip()
            json.loads(cleaned_response) # Validate if the response is a valid JSON object
            return cleaned_response

        except json.JSONDecodeError as e:
            error_msg = f"Error: The AI did not return a valid JSON object. {e}\\nResponse was:\\n{response.text}"
            logging.error(error_msg)
            return f'{{{"error": "{error_msg}"}}}'
        except Exception as e:
            error_msg = f"An unexpected error occurred during integration planning: {e}"
            logging.error(error_msg)
            return f'{{{"error": "{error_msg}"}}}'