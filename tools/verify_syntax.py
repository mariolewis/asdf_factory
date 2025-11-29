import ast
import os
import sys
from pathlib import Path

def verify_syntax(project_root):
    print(f"Verifying Python syntax in: {project_root}")

    error_count = 0

    # Scan agents and root files
    files_to_scan = [project_root / "master_orchestrator.py", project_root / "klyve_db_manager.py"]
    files_to_scan.extend((project_root / "agents").glob("*.py"))

    for file_path in files_to_scan:
        if not file_path.exists(): continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source)
        except SyntaxError as e:
            print(f"❌ SYNTAX ERROR in {file_path.name}: Line {e.lineno}")
            print(f"   {e.msg}")
            print(f"   {e.text.strip() if e.text else ''}")
            error_count += 1
        except Exception as e:
            print(f"❌ ERROR processing {file_path.name}: {e}")
            error_count += 1

    if error_count == 0:
        print("\n✅ SUCCESS: All files parsed correctly.")
        sys.exit(0)
    else:
        print(f"\n❌ FAILURE: Found {error_count} syntax errors.")
        sys.exit(1)

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    verify_syntax(root)