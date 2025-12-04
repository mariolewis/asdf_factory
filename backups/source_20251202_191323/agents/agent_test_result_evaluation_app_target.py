import logging
from llm_service import LLMService
import vault

# ... (module docstring & logging config)

class TestResultEvaluationAgent_AppTarget:
    """
    Agent responsible for evaluating the results of manually executed UI tests.
    It parses a structured text input (e.g., a Markdown table) containing
    test results and identifies which tests failed, providing a summary that
    can be used to initiate the debugging pipeline.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initializes the TestResultEvaluationAgent_AppTarget.

        Args:
            llm_service (LLMService): An instance of a class that adheres to the LLMService interface.
        """
        if not llm_service:
            raise ValueError("llm_service is required for the TestResultEvaluationAgent_AppTarget.")
        self.llm_service = llm_service

    def evaluate_ui_test_results(self, test_results_text: str) -> str:
        """
        Parses UI test results and provides a summary of failures.
        This method prompts the LLM API to analyze a block of text containing
        test results and extract the details of any failed tests into a
        structured, easy-to-read summary.
        """
        try:
            prompt = vault.get_prompt("agent_test_result_evaluation_app_target__prompt_33").format(test_results_text=test_results_text)

            response_text = self.llm_service.generate_text(prompt, task_complexity="simple")
            return response_text.strip()

        except Exception as e:
            error_message = f"An error occurred during UI test result evaluation: {e}"
            logging.error(error_message)
            raise e # Re-raise the exception