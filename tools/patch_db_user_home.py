import sys
from pathlib import Path

def patch_db_location(project_root):
    target = project_root / "klyve.py"
    print(f"Patching {target.name} for User Home DB storage...")

    content = target.read_text(encoding='utf-8')

    # We need to find the DB path definitions we added previously.
    # We look for the block that sets up 'db_path' using 'config.get_resource_path'

    old_logic_signature = 'db_path_str = config.get_resource_path("data/klyve.db")'

    new_logic = """        # [FIX] Store DB in User Home to support Read-Only AppImages/Program Files
        user_data_dir = Path.home() / ".klyve" / "data"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        db_path = user_data_dir / "klyve.db"

        # Copy default DB if it exists in resources but not in user home (Optional bootstrapping)
        # For now, we just let the app create a new one."""

    if old_logic_signature in content:
        # We replace the specific line and the following path creation lines
        # This regex replaces the block we added in the previous 'patch_db_path.py'
        import re
        # Pattern matches the get_resource_path line and the next 2 lines (Path object + mkdir)
        pattern = r'db_path_str = config\.get_resource_path\("data/klyve\.db"\)\s+db_path = Path\(db_path_str\)\s+db_path\.parent\.mkdir\(parents=True, exist_ok=True\)'

        if re.search(pattern, content):
            content = re.sub(pattern, new_logic, content)
            target.write_text(content, encoding='utf-8')
            print("✅ SUCCESS: klyve.py patched to use ~/.klyve/data/")
        else:
            print("❌ ERROR: Found signature but regex match failed. Manual check required.")
    else:
        print("❌ ERROR: Could not find previous DB path logic.")

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    patch_db_location(root)