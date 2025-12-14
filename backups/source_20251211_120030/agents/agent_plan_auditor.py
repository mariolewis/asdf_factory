# agents/agent_plan_auditor.py

import logging
import textwrap
import json
from llm_service import LLMService, parse_llm_json
import vault

class PlanAuditorAgent:
    """
    An agent that analyzes a sprint implementation plan for potential risks
    and adherence to project standards before the sprint begins.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the PlanAuditorAgent.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the PlanAuditorAgent.")
        self.llm_service = llm_service
        logging.info("PlanAuditorAgent initialized.")

    def run_audit(self, audit_type: str, plan_json: str, tech_spec: str) -> str:
        """
        Runs a specific type of audit on the implementation plan.

        Args:
            audit_type (str): The type of audit to run (e.g., "Security", "Scalability").
            plan_json (str): The JSON string of the implementation plan to be audited.
            tech_spec (str): The full text of the project's technical specification for context.

        Returns:
            A string containing the audit results, formatted in Markdown.
        """
        logging.info(f"Running '{audit_type}' audit on the implementation plan...")

        prompt = self._get_prompt_for_audit(audit_type, plan_json, tech_spec)

        try:
            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            # The prompt asks for Markdown, so we return the raw response.
            return response_text.strip()
        except Exception as e:
            logging.error(f"PlanAuditorAgent failed during '{audit_type}' audit: {e}")
            raise e # Re-raise the exception

    def _get_prompt_for_audit(self, audit_type: str, plan_json: str, tech_spec: str) -> str:
        """Selects and formats the correct prompt for the requested audit type."""

        audit_instructions = {
            "Security": """
                - **Primary Focus:** Identify potential security vulnerabilities introduced by the plan.
                - **Check Against Spec:** First, look for a 'Security Requirements' section in the Technical Specification.
                - **Audit Logic:** If a security spec exists, verify that every task in the plan that handles user input, file access, or authentication includes explicit steps to adhere to that spec (e.g., input sanitization, permission checks). If the spec is missing, state that no policy was found and then check the plan for common vulnerabilities (e.g., potential for SQL injection, missing authentication steps) based on general best practices.
            """,
            "Scalability": """
                - **Primary Focus:** Identify potential scalability bottlenecks or non-performant approaches in the plan.
                - **Check Against Spec:** First, look for a 'Scalability' or 'Performance Requirements' section in the Technical Specification.
                - **Audit Logic:** If a performance spec exists, check if the plan's tasks (e.g., database queries, loops, API calls) are likely to meet those requirements. If the spec is missing, state that and then analyze the plan for common scalability issues like inefficient database access patterns (N+1 queries), processing large datasets in memory, or synchronous operations that could block the main thread.
            """,
            "Readability": """
                - **Primary Focus:** Assess the clarity and unambiguity of the `task_description` for each step in the plan.
                - **Check Against Spec:** The Coding Standard is the primary reference for this.
                - **Audit Logic:** Review each `task_description`. Is it clear and detailed enough for a developer (or another AI) to implement without making major assumptions? Flag any steps that are too vague, use ambiguous language, or lack necessary detail (e.g., "process the data" instead of specifying the exact operation).
            """,
            "Best Practices": """
                - **Primary Focus:** Check if the plan adheres to general software engineering best practices and the project's architectural principles.
                - **Check Against Spec:** Analyze the overall Technical Specification for architectural patterns (e.g., MVC, Layered Architecture).
                - **Audit Logic:** Review the plan to see if it promotes modular, maintainable code. Flag tasks that might violate the Single Responsibility Principle (e.g., a single task that handles UI, business logic, and data access), suggest the use of configuration files over hardcoded values, or recommend more robust error handling strategies where they seem to be missing.
            """
        }

        specific_instructions = audit_instructions.get(audit_type, "Error: Unknown audit type.")

        prompt = vault.get_prompt("agent_plan_auditor__prompt_78").format(audit_type=audit_type, audit_type_lower=audit_type.lower(), specific_instructions=specific_instructions, tech_spec=tech_spec, plan_json=plan_json)
        return prompt