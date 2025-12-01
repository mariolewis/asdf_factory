import shutil
import sys
import os
from pathlib import Path

def unlock_source(project_root):
    backups_dir = project_root / "backups"
    if not backups_dir.exists():
        print("Error: No backups directory found.")
        return

    # Find the most recent backup folder
    all_backups = sorted(backups_dir.iterdir(), key=os.path.getmtime, reverse=True)
    if not all_backups:
        print("Error: No backup snapshots found.")
        return

    latest_backup = all_backups[0]
    print(f"Restoring source from: {latest_backup.name}")

    # 1. Restore Root Modules
    root_modules = ["master_orchestrator.py", "klyve_db_manager.py", "llm_service.py"]
    for mod in root_modules:
        src = latest_backup / mod
        dest = project_root / mod
        if src.exists():
            shutil.copy2(src, dest)
            print(f"  Restored {mod}")

    # 2. Restore Agents
    backup_agents = latest_backup / "agents"
    dest_agents = project_root / "agents"
    if backup_agents.exists():
        for py_file in backup_agents.glob("*.py"):
            shutil.copy2(py_file, dest_agents / py_file.name)
            print(f"  Restored agents/{py_file.name}")

    print("Unlock complete. Source code is ready for patching.")

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    unlock_source(root)