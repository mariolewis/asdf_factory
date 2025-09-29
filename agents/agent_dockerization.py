# agents/agent_dockerization.py
import logging
import textwrap

from llm_service import LLMService


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
        prompt = textwrap.dedent(f"""
            You are an expert DevOps engineer specializing in containerization. Your task is to generate a complete, production-ready Dockerfile based on the provided technical specification.

            **MANDATORY INSTRUCTIONS:**
            1.  **Analyze Tech Stack:** Carefully analyze the technical specification to determine the base image, dependencies, build steps, and runtime commands.
            2.  **Best Practices:** The generated Dockerfile MUST follow best practices, including using multi-stage builds, minimizing layer sizes, and running as a non-root user.
            3.  **RAW DOCKERFILE ONLY:** Your entire response MUST be only the raw, valid content of the Dockerfile.
            Do not include any conversational text, explanations, or markdown fences like ```dockerfile.

            **--- Technical Specification ---**
            {tech_spec_text}
            **--- End Specification ---**

            **--- Generated Dockerfile ---**
        """)
        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            if not response_text or response_text.strip().startswith("Error:"):
                raise ValueError(f"LLM returned an error or empty response: {response_text}")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Failed to generate Dockerfile: {e}", exc_info=True)
            return None