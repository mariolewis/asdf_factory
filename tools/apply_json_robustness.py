import os
from pathlib import Path
import re

def add_robust_parser_to_llm_service(project_root):
    """Adds a robust JSON extraction/parsing method to the LLMService base class."""
    target_file = project_root / "llm_service.py"
    content = target_file.read_text(encoding='utf-8')

    # Check if already applied
    if "def parse_llm_json" in content:
        print("llm_service.py already contains robust parser.")
        return

    # We inject a static helper method into the LLMService class
    # or just as a standalone utility in the file.
    # Let's add it as a standalone function at the end of the file
    # so it can be imported easily, or add it to the module scope.

    robust_parser_code = '''
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
        clean_text = re.sub(r",\s*([\]}])", r"\\1", clean_text)
        return json.loads(clean_text)
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Could not parse valid JSON/Dict from response: {llm_output[:50]}...")
'''

    # Append to file
    with open(target_file, 'a', encoding='utf-8') as f:
        f.write("\n" + robust_parser_code)

    print("SUCCESS: Added parse_llm_json to llm_service.py")

def refactor_agents(project_root):
    """Scans agents and replaces json.loads logic with parse_llm_json."""
    agents_dir = project_root / "agents"

    for agent_file in agents_dir.glob("*.py"):
        content = agent_file.read_text(encoding='utf-8')
        original_content = content

        # Skip if it doesn't use json parsing on LLM output
        # We look for typical patterns like: json.loads(response_text) or json.loads(cleaned_response)

        # Pattern 1: Standard json import injection
        if "import json" in content and "from llm_service import" in content:
            if "parse_llm_json" not in content:
                # Add import
                content = content.replace("from llm_service import LLMService", "from llm_service import LLMService, parse_llm_json")

        # Pattern 2: Replace the cleaning logic blocks
        # Many agents have a block like:
        # cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
        # result = json.loads(cleaned_response)

        # We replace that entire flow with:
        # result = parse_llm_json(response_text)

        # Regex to find the cleaning pattern
        # It matches the cleaning line and the loading line
        pattern = r'(?:cleaned_response|json_str)\s*=\s*response_text.*?\.replace.*?\(.*?\)\s*\n\s*.*?\s*=\s*json\.loads\((?:cleaned_response|json_str)\)'

        # This is hard to regex perfectly due to variable naming variations.
        # Instead, we will target specific known variations found in your codebase analysis.

        # Specific targeting for the most common pattern found in your files:
        # cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
        # result = json.loads(cleaned_response)

        old_block_1 = """cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            result = json.loads(cleaned_response)"""

        new_block_1 = """result = parse_llm_json(response_text)"""

        if old_block_1 in content:
            content = content.replace(old_block_1, new_block_1)
            print(f"  -> Patched Pattern 1 in {agent_file.name}")

        # Handle variations (like 'result_json' instead of 'result')
        old_block_2 = """cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
            result_json = json.loads(cleaned_response)"""
        new_block_2 = """result_json = parse_llm_json(response_text)"""

        if old_block_2 in content:
            content = content.replace(old_block_2, new_block_2)
            print(f"  -> Patched Pattern 2 in {agent_file.name}")

        # Handle the 'cleaned_json' variation (Intake Advisor)
        old_block_3 = """cleaned_json = json_match.group(0)
            # Validate that it's proper JSON
            json.loads(cleaned_json)
            return cleaned_json"""
        new_block_3 = """cleaned_json = json_match.group(0)
            # Validate using robust parser
            parse_llm_json(cleaned_json)
            return cleaned_json"""

        if old_block_3 in content:
            content = content.replace(old_block_3, new_block_3)
            print(f"  -> Patched Pattern 3 in {agent_file.name}")

        if content != original_content:
            agent_file.write_text(content, encoding='utf-8')

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    add_robust_parser_to_llm_service(root)
    refactor_agents(root)