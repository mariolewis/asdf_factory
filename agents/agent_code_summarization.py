# agents/agent_code_summarization.py

import logging
import textwrap
from llm_service import LLMService

class CodeSummarizationAgent:
    """
    An agent that analyzes source code and creates a concise, structured
    summary of its public interface and key dependencies.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the CodeSummarizationAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the CodeSummarizationAgent.")
        self.llm_service = llm_service
        logging.info("CodeSummarizationAgent initialized.")

    def summarize_code(self, source_code: str) -> str:
        """
        Generates a structured summary of a given piece of source code.

        Args:
            source_code (str): The source code of the component to be summarized.

        Returns:
            A string containing a structured summary, or an error message on failure.
        """
        logging.info("CodeSummarizationAgent: Generating code summary...")

        prompt = textwrap.dedent(f"""
            You are an expert code analysis tool. Your task is to read the provided source code and generate a concise, structured summary in Markdown format.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze the Public Interface:** Identify all public classes, methods, and functions. For each, list its signature (name, parameters, return type if available).
            2.  **Describe Purpose:** For each major element (class or standalone function), provide a one-sentence description of its purpose.
            3.  **Identify Dependencies:** List the key modules or libraries that are imported and used.
            4.  **Markdown Format:** Your entire response MUST be formatted in clear, readable Markdown. Use headings for "Public Interface," "Purpose," and "Dependencies."
            5.  **Concise Output:** The summary should be brief and focus on the high-level structure. Do not describe the internal implementation details of methods.

            **--- SOURCE CODE TO SUMMARIZE ---**
            ```
            {source_code}
            ```
            **--- END SOURCE CODE ---**

            **--- STRUCTURED SUMMARY (Markdown) ---**
        """)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            return response_text.strip()
        except Exception as e:
            logging.error(f"CodeSummarizationAgent failed to generate summary: {e}")
            raise e # Re-raise the exception