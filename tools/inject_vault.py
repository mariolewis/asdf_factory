import json
import sys
import os
import re
from pathlib import Path

def make_safe_placeholder(expr):
    """
    Converts any Python expression into a valid alphanumeric identifier.
    Must MATCH the logic in extract_prompts.py exactly.
    """
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', expr)
    clean = re.sub(r'_+', '_', clean)
    clean = clean.strip('_')
    if clean and clean[0].isdigit():
        clean = "v_" + clean
    if not clean:
        clean = "expr"
    return clean

def inject_vault_calls(project_root):
    manifest_path = project_root / "data" / "prompts_manifest.json"
    if not manifest_path.exists():
        print("Error: Manifest not found.")
        return

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    files_to_process = {}
    for key, entry in manifest.items():
        file_path = entry['source_file']
        if file_path not in files_to_process:
            files_to_process[file_path] = []
        files_to_process[file_path].append(entry)

    print(f"Ready to inject Vault calls into {len(files_to_process)} files.")

    for rel_path, entries in files_to_process.items():
        full_path = project_root / rel_path

        if not full_path.exists():
            print(f"Skipping missing file: {rel_path}")
            continue

        print(f"Processing {rel_path}...")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            entries.sort(key=lambda x: x['line_start'], reverse=True)
            modified = False

            has_import = any("import vault" in line for line in lines) or \
                         any("from vault import" in line for line in lines)

            for entry in entries:
                start_idx = entry['line_start'] - 1
                end_idx = entry['line_end']

                target_line = lines[start_idx]
                if entry['variable_name'] not in target_line:
                    print(f"  [WARNING] Variable mismatch at line {entry['line_start']}. Skipping.")
                    continue

                indentation = target_line[:len(target_line) - len(target_line.lstrip())]
                var_name = entry['variable_name']
                vault_key = entry['vault_key']

                if entry['is_fstring']:
                    fmt_args = []
                    seen_keys = set() # FIX: Track added keys to prevent duplicates

                    for raw_var in entry['original_variables']:
                        safe_key = make_safe_placeholder(raw_var)

                        # Only add unique keys
                        if safe_key not in seen_keys:
                            fmt_args.append(f"{safe_key}={raw_var}")
                            seen_keys.add(safe_key)

                    fmt_str = ", ".join(fmt_args)
                    new_line = f'{indentation}{var_name} = vault.get_prompt("{vault_key}").format({fmt_str})\n'
                else:
                    new_line = f'{indentation}{var_name} = vault.get_prompt("{vault_key}")\n'

                lines[start_idx:end_idx] = [new_line]
                modified = True

            if modified and not has_import:
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        insert_pos = i + 1

                if insert_pos == 0:
                    if len(lines) > 0 and (lines[0].startswith("#") or lines[0].startswith('"""')):
                        insert_pos = 1

                lines.insert(insert_pos, "import vault\n")

            if modified:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print(f"  -> Successfully patched {rel_path}")

        except Exception as e:
            print(f"  [ERROR] Failed to process {rel_path}: {e}")

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    inject_vault_calls(root)