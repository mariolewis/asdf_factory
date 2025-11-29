import sys
from pathlib import Path

def patch_db_manager(project_root):
    target_file = project_root / "klyve_db_manager.py"

    if not target_file.exists():
        print(f"Error: Could not find {target_file}")
        sys.exit(1)

    print(f"Patching {target_file.name} to use Iron Vault...")

    with open(target_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    has_vault_import = any("import vault" in line for line in lines)

    new_lines = []
    for line in lines:
        # 1. Inject Import if missing (put it after 'import config')
        if "import config" in line and not has_vault_import:
            new_lines.append(line)
            new_lines.append("import vault\n")
            has_vault_import = True
            continue

        # 2. Swap the Key Retrieval Logic
        if "key = config.get_db_key()" in line:
            # Preserve indentation
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}# [SECURED] Key retrieved from Iron Vault\n")
            new_lines.append(f"{indent}key = vault.get_db_key()\n")
            modified = True
            print("  -> Replaced config.get_db_key() with vault.get_db_key()")
        else:
            new_lines.append(line)

    if modified:
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("SUCCESS: klyve_db_manager.py patched.")
    else:
        print("WARNING: No changes made. Was the file already patched?")

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    patch_db_manager(root)