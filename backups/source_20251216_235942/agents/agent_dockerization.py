# agents/agent_dockerization.py
import logging
import textwrap

from llm_service import LLMService
import vault


class DockerizationAgent:
    """
    Agent responsible for generating a Dockerfile for the target application.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the DockerizationAgent.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the DockerizationAgent.")
        self.llm_service = llm_service
        logging.info("DockerizationAgent initialized.")

    def generate_dockerfile(self, tech_spec_text: str) -> str | None:
        """
        Generates a standard Dockerfile based on the technical specification.
        """
        logging.info("Generating Dockerfile from technical specification...")
        prompt = vault.get_prompt("agent_dockerization__prompt_27").format(tech_spec_text=tech_spec_text)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            if not response_text or response_text.strip().startswith("Error:"):
                raise ValueError(f"LLM returned an error or empty response: {response_text}")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Failed to generate Dockerfile: {e}", exc_info=True)
            return None