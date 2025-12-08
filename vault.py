# vault.py
import logging
from pathlib import Path
import config

def get_db_key() -> str:
    """
    Dev Mode Shim: Returns a dummy key.
    The DB Manager handles the actual dev/prod key logic, so this is rarely called in Dev,
    but provided here for interface compatibility.
    """
    return "DEV-KEY-UNENCRYPTED"

def get_prompt(prompt_name: str) -> str:
    """
    Dev Mode Shim: Reads the prompt text directly from the data/prompts directory.
    This ensures that changes to .txt files are reflected immediately without compilation.
    """
    try:
        # Locate the prompts directory relative to this script
        root_dir = Path(__file__).parent
        prompt_path = root_dir / "data" / "prompts" / f"{prompt_name}.txt"

        if prompt_path.exists():
            # Read and return the live content
            return prompt_path.read_text(encoding="utf-8")
        else:
            error_msg = f"VAULT ERROR: Could not find prompt file: {prompt_path}"
            logging.error(error_msg)
            return f"Error: Prompt {prompt_name} missing."

    except Exception as e:
        logging.error(f"VAULT ERROR: Failed to read prompt {prompt_name}: {e}")
        return f"Error loading prompt: {e}"