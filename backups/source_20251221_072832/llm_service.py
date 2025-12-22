# llm_service.py

import logging
import json
import ast
import re
from abc import ABC, abstractmethod

class LLMService(ABC):
    """
    Abstract base class for all LLM providers.
    """
    @abstractmethod
    def generate_text(self, prompt: str, task_complexity: str) -> str:
        """
        Generates text based on the provider's specific API requirements.
        """
        pass

class GeminiAdapter(LLMService):
    """
    Adapter for Google's Gemini models via the google-genai SDK (v1.0+).
    VALIDATED: Fixes 'tool_config' placement and adds 'thinking_config' support for Gemini 2.0.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str, generation_config: dict = None):
        from google import genai
        from google.genai import types

        if not api_key:
            raise ValueError("API key is required for the GeminiAdapter.")

        # Initialize Client
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=600000)
        )

        self.reasoning_model_name = reasoning_model_name
        self.fast_model_name = fast_model_name

        # Base config preparation
        self.base_config = generation_config.copy() if generation_config else {"temperature": 0.0}

        # FIX: Wrap tool_config inside the base config dictionary to disable function calling
        self.base_config['tool_config'] = types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode='NONE')
        )

        logging.info(f"GeminiAdapter initialized. Models: {reasoning_model_name}, {fast_model_name}")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        from google.genai import types
        try:
            model_to_use = self.reasoning_model_name if task_complexity == "complex" else self.fast_model_name

            # Create a call-specific config to handle thinking parameters safely
            call_config = self.base_config.copy()

            # Handle 'thinking_budget' for Gemini 2.0 Flash/Pro (Thinking Mode)
            # If the user provided a 'thinking_budget' in settings, move it to the correct structure
            if 'thinking_budget' in call_config:
                budget = call_config.pop('thinking_budget')
                # Only apply thinking config if the model supports it (Gemini 2.0+)
                if "gemini-2" in model_to_use or "gemini-3" in model_to_use:
                    call_config['thinking_config'] = types.ThinkingConfig(include_thoughts=False, thinking_budget=int(budget))

            response = self.client.models.generate_content(
                model=model_to_use,
                contents=prompt,
                config=call_config # Correctly passed as a single config object
            )

            if not response.text:
                finish_reason = "Unknown"
                if response.candidates and len(response.candidates) > 0:
                    finish_reason = response.candidates[0].finish_reason

                log_msg = f"Gemini empty response. Reason: {finish_reason}. Usage: {response.usage_metadata}"
                logging.warning(log_msg)
                return f"Error: The AI model returned an empty response. Reason: {finish_reason}"

            return response.text.strip()
        except Exception as e:
            logging.error(f"Gemini API call failed: {e}", exc_info=True)
            raise e

class OpenAIAdapter(LLMService):
    """
    Adapter for OpenAI models.
    VALIDATED: Handles 'max_completion_tokens', 'reasoning_effort', and strips 'temperature' for o1/o3 models.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str, generation_config: dict = None):
        import openai

        if not api_key:
            raise ValueError("API key is required for the OpenAIAdapter.")

        self.client = openai.OpenAI(api_key=api_key)
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        self.generation_config = (
            generation_config.copy() if generation_config else {"temperature": 0.0}
        )

        logging.info("OpenAIAdapter initialized. Models: %s (reasoning), %s (fast)", reasoning_model_name, fast_model_name)

    def _is_reasoning_model(self, model_name: str) -> bool:
        model_name = (model_name or "").lower()
        return model_name.startswith(("o1", "o3", "gpt-5", "gpt-5.", "o4", "o"))

    def _normalize_call_params(self, model_name: str, call_params: dict) -> dict:
        params = call_params.copy()

        if "max_tokens" in params and "max_completion_tokens" not in params:
            params["max_completion_tokens"] = params.pop("max_tokens")
            logging.debug("Renamed max_tokens -> max_completion_tokens")

        if "reasoning_effort" in params:
            params["reasoning.effort"] = params.pop("reasoning_effort")

        if self._is_reasoning_model(model_name):
            for key in ("temperature", "top_p", "presence_penalty", "frequency_penalty", "stream", "n", "best_of"):
                params.pop(key, None)

        return params

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            call_params = self._normalize_call_params(model_to_use, self.generation_config)

            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                timeout=300,
                **call_params,
            )

            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The OpenAI model returned an empty response.")

            return response_text.strip()

        except Exception as exc:
            logging.error("OpenAI API call failed: %s", exc, exc_info=True)
            raise

class AnthropicAdapter(LLMService):
    """
    Adapter for Anthropic Claude models.
    VALIDATED: Handles system prompts as top-level params and extended thinking budgets.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str, generation_config: dict = None):
        import anthropic

        if not api_key:
            raise ValueError("API key is required for the AnthropicAdapter.")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name

        self.generation_config = generation_config if generation_config else {}
        if "max_tokens" not in self.generation_config:
            self.generation_config["max_tokens"] = 8192
        if "temperature" not in self.generation_config:
            self.generation_config["temperature"] = 0.0

        logging.info(f"AnthropicAdapter initialized. Models: {reasoning_model_name}, {fast_model_name}")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            call_params = self.generation_config.copy()

            system_prompt = call_params.pop("system", None)
            thinking_config = call_params.pop("thinking", None)

            kwargs = {
                "model": model_to_use,
                "messages": [{"role": "user", "content": prompt}],
                "timeout": 300,
                **call_params
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            # Enable extended thinking only for complex tasks if configured
            if thinking_config and task_complexity == "complex":
                kwargs["thinking"] = thinking_config

            message = self.client.messages.create(**kwargs)
            response_text = message.content[0].text

            if not response_text:
                raise ValueError("The Anthropic model returned an empty response.")

            return response_text.strip()

        except Exception as e:
            logging.error(f"Anthropic API call failed: {e}", exc_info=True)
            raise e

class GrokAdapter(LLMService):
    """
    Adapter for xAI Grok models.
    Validated as correct for standard OpenAI-compatible endpoints.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str, generation_config: dict = None):
        import openai
        if not api_key:
            raise ValueError("API key is required for the GrokAdapter.")
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        self.generation_config = generation_config if generation_config else {"temperature": 0.0}
        logging.info(f"GrokAdapter initialized. Models: {reasoning_model_name}, {fast_model_name}")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                timeout=300,
                **self.generation_config
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The Grok model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Grok API call failed: {e}")
            raise e

class DeepseekAdapter(LLMService):
    """
    Adapter for Deepseek models.
    VALIDATED: Handles 'reasoner' parameter exclusions.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str, generation_config: dict = None):
        import openai
        if not api_key:
            raise ValueError("API key is required for the DeepseekAdapter.")

        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=300
        )
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        self.generation_config = generation_config if generation_config else {"temperature": 0.0}

        logging.info(f"DeepseekAdapter initialized. Models: {reasoning_model_name}, {fast_model_name}")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            call_params = self.generation_config.copy()

            if "reasoner" in model_to_use.lower():
                call_params.pop("temperature", None)
                call_params.pop("top_p", None)
                call_params.pop("frequency_penalty", None)
                call_params.pop("presence_penalty", None)
                if "reasoning_effort" not in call_params:
                    call_params["reasoning_effort"] = "medium"

            if task_complexity == "complex":
                call_params["timeout"] = 600

            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                **call_params
            )

            if not completion.choices or len(completion.choices) == 0:
                raise ValueError("No choices returned from Deepseek API")

            message = completion.choices[0].message
            if not message or not message.content:
                raise ValueError("The Deepseek model returned an empty response.")

            return message.content.strip()

        except Exception as e:
            logging.error(f"Deepseek API call failed: {e}", exc_info=True)
            raise e

class LlamaAdapter(LLMService):
    """
    Adapter for Llama models hosted on Replicate.
    VALIDATED: Uses raw prompt formatting and max_new_tokens.
    """
    def __init__(self, api_key: str, reasoning_model_name: str, fast_model_name: str, generation_config: dict = None):
        import replicate
        if not api_key:
            raise ValueError("API key is required for the LlamaAdapter (Replicate).")
        self.client = replicate.Client(api_token=api_key)
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name

        # Replicate defaults are often too restrictive.
        defaults = {
            "temperature": 0.01,
            "max_new_tokens": 4096
            # Note: presence_penalty and frequency_penalty can be added here if needed
        }
        if generation_config:
            defaults.update(generation_config)
        self.generation_config = defaults

        logging.info(f"LlamaAdapter initialized. Models: {reasoning_model_name}, {fast_model_name}")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model

            # Manually format prompt for Replicate Llama 3 models which expect raw strings
            formatted_prompt = (
                f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
                f"{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
            )

            input_params = {
                "prompt": formatted_prompt,
                **self.generation_config
            }

            output_iterator = self.client.run(
                model_to_use,
                input=input_params
            )

            # Replicate returns a generator of tokens
            response_parts = [str(part) for part in output_iterator]
            response_text = "".join(response_parts)

            if not response_text:
                raise ValueError("The Llama (Replicate) model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Llama (Replicate) API call failed: {e}")
            raise e

class OllamaAdapter(LLMService):
    """
    Adapter for local models via Ollama.
    """
    def __init__(self, reasoning_model_name: str, fast_model_name: str, base_url: str = "http://localhost:11434/v1", generation_config: dict = None):
        import openai
        self.client = openai.OpenAI(base_url=base_url, api_key="ollama")
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        self.generation_config = generation_config if generation_config else {"temperature": 0.0}
        logging.info(f"OllamaAdapter initialized. Models: {reasoning_model_name}, {fast_model_name}")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        import openai
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model

            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                timeout=300,
                **self.generation_config
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError(f"The local Ollama model ({model_to_use}) returned an empty response.")
            return response_text.strip()
        except openai.APIConnectionError as e:
            logging.error(f"Ollama Connection Error: {e}")
            raise ConnectionError(f"Could not connect to Ollama at {self.client.base_url}. Is Ollama running?")
        except Exception as e:
            logging.error(f"Ollama API call failed: {e}")
            raise e

class CustomEndpointAdapter(LLMService):
    """
    Adapter for generic OpenAI-compatible endpoints.
    """
    def __init__(self, base_url: str, api_key: str, reasoning_model_name: str, fast_model_name: str, generation_config: dict = None):
        import openai
        if not all([base_url, api_key, reasoning_model_name, fast_model_name]):
            raise ValueError("All parameters are required for the CustomEndpointAdapter.")
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.reasoning_model = reasoning_model_name
        self.fast_model = fast_model_name
        self.generation_config = generation_config if generation_config else {"temperature": 0.0}
        logging.info(f"CustomEndpointAdapter initialized for endpoint at {base_url}.")

    def generate_text(self, prompt: str, task_complexity: str) -> str:
        try:
            model_to_use = self.reasoning_model if task_complexity == "complex" else self.fast_model
            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": prompt}],
                timeout=300,
                **self.generation_config
            )
            response_text = completion.choices[0].message.content
            if not response_text:
                raise ValueError("The custom endpoint model returned an empty response.")
            return response_text.strip()
        except Exception as e:
            logging.error(f"Custom Endpoint API call failed: {e}")
            raise e

def parse_llm_json(llm_output: str):
    """
    Robustly extracts and parses JSON from LLM output.
    Can handle markdown blocks, chatty intros, and trailing commas.
    """
    clean_text = llm_output.strip()

    # 1. Try extracting from Markdown blocks first
    if "```" in clean_text:
        match = re.search(r"```(?:json)?(.*?)```", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()

    # 2. Try parsing explicitly
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    # 3. Fallback: Search for the first '[' or '{' and valid end char
    # This helps when LLMs say "Here is the JSON: [ ... ]" without backticks.
    try:
        # Regex to find the largest bracketed group
        match = re.search(r"(\{.*\}|\[.*\])", clean_text, re.DOTALL)
        if match:
            potential_json = match.group(0)
            return json.loads(potential_json)
    except Exception:
        pass

    # 4. AST Literal Eval (last resort for single-quote JSONs)
    try:
        if clean_text.startswith("{") or clean_text.startswith("["):
            return ast.literal_eval(clean_text)
    except (ValueError, SyntaxError):
        pass

    # 5. Aggressive cleanup for trailing commas
    try:
        clean_text = re.sub(r",\s*([\]}])", r"\1", clean_text)
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Could not parse valid JSON/Dict from response: {llm_output[:50]}...")