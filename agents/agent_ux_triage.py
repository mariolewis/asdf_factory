# agents/agent_ux_triage.py

"""
This module contains the UX_Triage_Agent class.
"""

import logging
import textwrap
import json
import google.generativeai as genai

class UX_Triage_Agent:
    """
    Agent responsible for the initial analysis of a project brief to infer
    if a GUI is required and to recommend the necessity of a dedicated
    UX/UI Design phase.
    """

    def __init__(self, api_key: str):
        """
        Initializes the UX_Triage_Agent.
        """
        if not api_key:
            raise ValueError("API key is required for the UX_Triage_Agent.")
        genai.configure(api_key=api_key)
        # Use a capable model for this nuanced analysis
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        logging.info("UX_Triage_Agent initialized.")

    def analyze_brief(self, project_brief: str) -> dict:
        """
        Analyzes a project brief and returns a structured assessment.
        """
        logging.info("UX_Triage_Agent: Analyzing project brief...")

        prompt = textwrap.dedent(f"""
            You are an expert Solutions Architect. Your task is to perform an initial analysis of a project brief to guide the development workflow.

            **MANDATORY INSTRUCTIONS:**
            1.  **JSON Output:** Your entire response MUST be a single, valid JSON object.
            2.  **Analysis:** Based on the brief, you must determine:
                a. If the application requires a Graphical User Interface (GUI).
                b. The necessity of a dedicated UX/UI design phase.
                c. A brief justification for your necessity rating.
                d. A list of 1-3 inferred, high-level user personas/roles if it is a GUI application.
            3.  **JSON Schema:** The JSON object MUST strictly adhere to this schema:
                {{
                  "requires_gui": boolean,
                  "ux_phase_necessity": "Recommended" | "Optional" | "Not Recommended",
                  "justification": "...",
                  "inferred_personas": ["...", "..."]
                }}
            4.  **Necessity Criteria:**
                - "Recommended": For complex apps with high data density, specialized workflows, or multiple user roles (e.g., financial trading platform, industrial control system).
                - "Optional": For standard business/consumer apps where a dedicated design phase would improve polish and differentiation (e.g., sales reporting tool, simple inventory system).
                - "Not Recommended": For non-GUI applications (APIs, CLIs) or simple, single-purpose utilities (e.g., a calculator).
            5.  **No Other Text:** Do not include any text, comments, or markdown formatting outside of the raw JSON object.

            ---
            PROJECT BRIEF:
            {project_brief}
            ---

            JSON OUTPUT:
        """)

        try:
            response = self.model.generate_content(prompt)
            cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "")
            result = json.loads(cleaned_response_text)
            logging.info("Successfully received initial UX triage analysis.")
            return result
        except Exception as e:
            logging.error(f"UX_Triage_Agent failed to get or parse LLM response: {e}")
            return {{
                "error": "Failed to get a valid analysis from the AI model.",
                "details": str(e)
            }}