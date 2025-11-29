import os
from pathlib import Path
import re

def robust_patch_agents(project_root):
    agents_dir = project_root / "agents"

    print("Running Phase 1.5: Deep Robustness Patch on Agents...")

    for agent_file in agents_dir.glob("*.py"):
        # Read file
        try:
            content = agent_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Skipping {agent_file.name}: {e}")
            continue

        original_content = content
        modified = False

        # CHECK 1: Does this file use json.loads?
        if "json.loads(" in content:

            # CHECK 2: Is this an agent that interacts with LLMs?
            # (We look for llm_service import to avoid patching utility scripts unnecessarily,
            # though parse_llm_json is safe for valid JSON too).
            if "from llm_service import" in content:

                # 1. Ensure the robust parser is imported
                if "parse_llm_json" not in content:
                    # Replace the import line to include the function
                    content = re.sub(
                        r"from llm_service import (.*?)LLMService",
                        r"from llm_service import \1LLMService, parse_llm_json",
                        content
                    )
                    # If regex didn't match (e.g. whitespace diffs), try append style
                    if "parse_llm_json" not in content:
                        # Fallback: simple string replace
                        content = content.replace(
                            "from llm_service import LLMService",
                            "from llm_service import LLMService, parse_llm_json"
                        )

                # 2. Replace all instances of json.loads with parse_llm_json
                # We use a regex to capture the argument: json.loads(ARG) -> parse_llm_json(ARG)
                # This handles balanced parentheses reasonably well for simple cases.

                # Strategy: Simple string replacement is safer than complex regex for
                # 'json.loads(' -> 'parse_llm_json('.
                # The closing parenthesis is naturally handled by the existing code.

                if "json.loads(" in content:
                    content = content.replace("json.loads(", "parse_llm_json(")
                    modified = True
                    print(f"  -> Patched: {agent_file.name}")

        if modified:
            agent_file.write_text(content, encoding='utf-8')

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    robust_patch_agents(root)