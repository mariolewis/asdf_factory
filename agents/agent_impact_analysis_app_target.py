import google.generativeai as genai
import logging
import json

"""
This module contains the ImpactAnalysisAgent_AppTarget class.
"""

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ImpactAnalysisAgent_AppTarget:
    """
    Agent responsible for analyzing the impact of a proposed change request.

    It assesses a change request against the existing project documentation
    and Record-of-Work-Done (RoWD) to determine its scope and potential impact.
    """

    def __init__(self, api_key: str):
        """
        Initializes the ImpactAnalysisAgent_AppTarget.

        Args:
            api_key (str): The Gemini API key for authentication.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        genai.configure(api_key=self.api_key)

    def analyze_impact(self, change_request_desc: str, final_spec_text: str, rowd_json: str) -> tuple[str | None, str | None]:
        """
        Performs a high-level impact analysis and assigns a rating.

        Args:
            change_request_desc (str): The description of the change request.
            final_spec_text (str): The full text of the finalized application specification.
            rowd_json (str): A JSON string representing the list of artifacts in the
                             Record-of-Work-Done (RoWD).

        Returns:
            tuple[str | None, str | None]: A tuple containing:
                                           - The impact rating ("Minor", "Medium", "Major").
                                           - A summary of the analysis.
                                           Returns (None, "Error message") on failure.
        """
        try:
            model = genai.GenerativeModel('gemini-pro')

            prompt = f"""
            You are a seasoned Software Architect. Your task is to perform a high-level impact analysis
            of a proposed change request based on the project's specification and its current state
            as documented in the Record-of-Work-Done (RoWD).

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze the Change:** Carefully read the Change Request Description to understand what is being asked.
            2.  **Compare with Specification:** Compare the change request against the original Finalized Specification to identify deviations or new requirements.
            3.  **Analyze RoWD:** Examine the provided RoWD (a JSON list of all software artifacts like classes, functions, files) to identify which existing components are likely to be affected (created, modified, or deleted).
            4.  **Determine Impact Rating:** Based on your analysis, determine the impact rating.
                -   **Minor:** The change affects a single component, is cosmetic, or requires a very small, isolated code change.
                -   **Medium:** The change affects a few interacting components or requires moderate logic changes.
                -   **Major:** The change is architectural, affects many components, impacts the database schema, or alters a core feature of the application.
            5.  **Write Summary:** Write a brief, one or two-paragraph summary explaining your reasoning for the rating. Mention the key artifacts from the RoWD that are likely to be impacted.
            6.  **JSON Output:** Your entire response MUST be a single, valid JSON object with two keys: "impact_rating" and "impact_summary". The value for "impact_rating" must be one of "Minor", "Medium", or "Major".

            **--- INPUTS ---**

            **1. Change Request Description:**
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

            **--- Impact Analysis (JSON Output) ---**
            """

            response = model.generate_content(prompt)

            # Clean the response to ensure it's valid JSON
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")

            analysis_result = json.loads(cleaned_response)

            rating = analysis_result.get("impact_rating")
            summary = analysis_result.get("impact_summary")

            if rating not in ["Minor", "Medium", "Major"]:
                raise ValueError("Invalid impact rating received from AI.")

            return rating, summary

        except json.JSONDecodeError as e:
            error_msg = f"Error decoding AI response as JSON: {e}\nResponse was: {response.text}"
            logging.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred during impact analysis: {e}"
            logging.error(error_msg)
            return None, error_msg