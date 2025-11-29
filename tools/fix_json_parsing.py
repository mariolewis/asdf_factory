import sys
from pathlib import Path

def fix_agent_json(project_root):
    target_file = project_root / "agents" / "agent_sprint_integration_test.py"

    if not target_file.exists():
        print(f"Error: Could not find {target_file}")
        return

    print(f"Patching {target_file.name} for robust JSON parsing...")
    content = target_file.read_text(encoding='utf-8')

    # 1. Inject 'import ast' if missing
    if "import ast" not in content:
        content = content.replace("import json", "import json\nimport ast")

    # 2. Replace the strict json.loads with a robust fallback
    # We look for the specific line known to cause the issue
    old_line = "            result = json.loads(json_match.group(0))"

    # Replacement block handles both JSON and Python-dict syntax
    new_block = """            try:
                result = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                # Fallback: parse as Python dictionary (handles single quotes)
                result = ast.literal_eval(json_match.group(0))"""

    if old_line in content:
        content = content.replace(old_line, new_block)
        target_file.write_text(content, encoding='utf-8')
        print("SUCCESS: Patch applied.")
    else:
        print("WARNING: Target line not found. The file might already be patched or formatted differently.")

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    fix_agent_json(root)