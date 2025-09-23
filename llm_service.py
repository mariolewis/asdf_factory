# llm_service.py

import logging
from abc import ABC, abstractmethod

class LLMService(ABC):
    """
    An abstract base class that defines the standard interface for an LLM service.
    """
    @abstractmethod
    def generate_text(self, prompt: str, task_complexity: str) -> str:
        """
        Generates text using the configured LLM.
        """
        pass

class GeminiAdapter(LLMService):
    """
    Concrete implementation of the LLMService for Google's Gemini models.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str):
        import google.generativeai as genai
        if not api_key:
            raise ValueError("API key is required for the GeminiAdapter.")
        genai.configure(api_key=api_key)
        self.reasoning_model = genai.GenerativeModel(reasoning_model_name)
        self.fast_model = genai.GenerativeModel(fast_model_name)
        logging.info(f"GeminiAdapter initialized with models: {reasoning_model_name} (Complex) and {fast_model_name} (Simple).")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        """
        Generates text using the appropriate Gemini model based on task complexity.
        """
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            response = model_to_use.generate_content(prompt, request_options={'timeout': 180})
            if not hasattr(response, 'text') or not response.text:
                logging.warning(f"Gemini model returned an empty or malformed response.")
                return "Error: The Gemini model returned an empty response."
            return response.text.strip()
        except Exception as e:
            logging.error(f"Gemini API call failed: {e}", exc_info=True)
            return f"Error: The call to the Gemini API failed. Details: {e}"

class OpenAIAdapter(LLMService):
    """
    Concrete implementation of the LLMService for OpenAI's models (e.g., GPT-4).
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str):
        import openai
        if not api_key:
            raise ValueError("API key is required for the OpenAIAdapter.")
        self.client = openai.OpenAI(api_key=api_key)
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        logging.info(f"OpenAIAdapter initialized with models: {reasoning_model_name} (Complex) and {fast_model_name} (Simple).")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        import openai
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                timeout=180
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The OpenAI model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"OpenAI API call failed: {e}")
            return f"Error: The call to the OpenAI API failed. Details: {e}"

class AnthropicAdapter(LLMService):
    """
    Concrete implementation of the LLMService for Anthropic's Claude models.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str):
        import anthropic
        if not api_key:
            raise ValueError("API key is required for the AnthropicAdapter.")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        logging.info(f"AnthropicAdapter initialized with models: {reasoning_model_name} (Complex) and {fast_model_name} (Simple).")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            message = self.client.messages.create(
                model=model_to_use,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
                timeout=180
            )
            response_text = message.content[0].text
            if not response_text:
                raise ValueError("The Anthropic model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Anthropic API call failed: {e}")
            return f"Error: The call to the Anthropic API failed. Details: {e}"

class LocalPhi3Adapter(LLMService):
    """
    Concrete implementation of the LLMService for a local Phi-3 model via Ollama.
    """
    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        import openai
        self.client = openai.OpenAI(base_url=base_url, api_key="ollama")
        self.model = "phi3"
        logging.info(f"LocalPhi3Adapter initialized for model '{self.model}' at {base_url}.")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        import openai
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=180
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The local Phi-3 model returned an empty response.")
            return response_text.strip()
        except openai.APIConnectionError as e:
            logging.error(f"Local Phi-3 (Ollama) API call failed: {e}")
            return f"Error: Could not connect to the local Ollama server. Details: {e}"
        except Exception as e:
            logging.error(f"Local Phi-3 (Ollama) API call failed: {e}")
            return f"Error: The call to the local Phi-3 (Ollama) API failed. Details: {e}"

class CustomEndpointAdapter(LLMService):
    """
    Concrete implementation for a generic, OpenAI-compatible custom endpoint.
    """
    def __init__(self, base_url: str, api_key: str, reasoning_model_name: str, fast_model_name: str):
        import openai
        if not all([base_url, api_key, reasoning_model_name, fast_model_name]):
            raise ValueError("All parameters are required for the CustomEndpointAdapter.")
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        logging.info(f"CustomEndpointAdapter initialized for endpoint at {base_url}.")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                timeout=180
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The custom endpoint model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Custom Endpoint API call failed: {e}")
            return f"Error: The call to the Custom Endpoint API failed. Details: {e}"