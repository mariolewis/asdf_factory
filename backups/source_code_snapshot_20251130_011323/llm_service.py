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
            response = model_to_use.generate_content(prompt, request_options={'timeout': 60})

            # Robust check for valid response content
            if not response.candidates or not response.candidates[0].content.parts:
                finish_reason = response.candidates[0].finish_reason if response.candidates else 'N/A'
                safety_ratings = response.prompt_feedback.safety_ratings if response.prompt_feedback else 'N/A'
                log_msg = (f"Gemini model returned an empty response. "
                        f"Finish Reason: {finish_reason}, Safety Ratings: {safety_ratings}")
                logging.warning(log_msg)
                return f"Error: The AI model returned an empty response. This could be due to a safety filter or hitting a token limit."

            return response.text.strip()
        except Exception as e:
            logging.error(f"Gemini API call failed: {e}", exc_info=True)
            # Re-raise the exception to be caught by the worker
            raise e

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
                timeout=300
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The OpenAI model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"OpenAI API call failed: {e}")
            # Re-raise the exception to be caught by the worker
            raise e

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
                timeout=300
            )
            response_text = message.content[0].text
            if not response_text:
                raise ValueError("The Anthropic model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Anthropic API call failed: {e}")
            # Re-raise the exception to be caught by the worker
            raise e

class GrokAdapter(LLMService):
    """
    Concrete implementation of the LLMService for Grok models via the Groq API.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str):
        import openai
        if not api_key:
            raise ValueError("API key is required for the GrokAdapter.")
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        logging.info(f"GrokAdapter initialized with models: {reasoning_model_name} (Complex) and {fast_model_name} (Simple).")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                timeout=300
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The Grok model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Grok API call failed: {e}")
            # Re-raise the exception to be caught by the worker
            raise e

class DeepseekAdapter(LLMService):
    """
    Concrete implementation of the LLMService for Deepseek models.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str):
        import openai
        if not api_key:
            raise ValueError("API key is required for the DeepseekAdapter.")
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
        )
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        logging.info(f"DeepseekAdapter initialized with models: {reasoning_model_name} (Complex) and {fast_model_name} (Simple).")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                timeout=300
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The Deepseek model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Deepseek API call failed: {e}")
            # Re-raise the exception to be caught by the worker
            raise e

class LlamaAdapter(LLMService):
    """
    Concrete implementation of the LLMService for Meta's Llama models via Replicate.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str):
        import replicate
        if not api_key:
            raise ValueError("API key is required for the LlamaAdapter (Replicate).")
        self.client = replicate.Client(api_token=api_key)
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        logging.info(f"LlamaAdapter initialized with models: {reasoning_model_name} (Complex) and {fast_model_name} (Simple).")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model

            output_iterator = self.client.run(
                model_to_use,
                input={"prompt": prompt}
            )

            response_parts = [str(part) for part in output_iterator]
            response_text = "".join(response_parts)

            if not response_text:
                raise ValueError("The Llama (Replicate) model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Llama (Replicate) API call failed: {e}")
            # Re-raise the exception to be caught by the worker
            raise e

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
                timeout=300
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The local Phi-3 model returned an empty response.")
            return response_text.strip()
        except openai.APIConnectionError as e:
            logging.error(f"Local Phi-3 (Ollama) API call failed: {e}")
            # Re-raise the exception to be caught by the worker
            raise ConnectionError(f"Could not connect to the local Ollama server. Details: {e}")
        except Exception as e:
            logging.error(f"Local Phi-3 (Ollama) API call failed: {e}")
            # Re-raise the exception to be caught by the worker
            raise e

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
                timeout=300
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The custom endpoint model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Custom Endpoint API call failed: {e}")
            # Re-raise the exception to be caught by the worker
            raise e

import json
import ast
import re

def parse_llm_json(llm_output: str):
    """
    Robustly extracts and parses JSON from LLM output.
    Handles markdown fences, single quotes (lazy JSON), and trailing commas.
    """
    # 1. Strip Markdown Fences
    clean_text = llm_output.strip()
    if "```" in clean_text:
        # Regex to find content inside ```json ... ``` or just ``` ... ```
        match = re.search(r"```(?:json)?(.*?)```", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()

    # 2. Attempt Strict Parsing
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # 3. Attempt Python Literal Evaluation (Handles single quotes)
    try:
        # Safety check: ensure it looks like a dict/list before eval
        if clean_text.startswith("{") or clean_text.startswith("["):
            return ast.literal_eval(clean_text)
    except (ValueError, SyntaxError):
        pass

    # 4. Last Resort: Regex cleanup for common JSON errors (e.g., trailing commas)
    # This is risky, so we only do it if the above fail.
    try:
        # Remove trailing commas before closing braces/brackets
        clean_text = re.sub(r",\s*([\]}])", r"\1", clean_text)
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Could not parse valid JSON/Dict from response: {llm_output[:50]}...")
