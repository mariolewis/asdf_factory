# agents/agent_code_summarization.py

import logging
import textwrap
from llm_service import LLMService
import vault

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

        prompt = vault.get_prompt("agent_code_summarization__prompt_37").format(source_code=source_code)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            return response_text.strip()
        except Exception as e:
            logging.error(f"CodeSummarizationAgent failed to generate summary: {e}")
            raise e # Re-raise the exception