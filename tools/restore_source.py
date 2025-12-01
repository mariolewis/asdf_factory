import shutil
import os
from pathlib import Path

def restore_source():
    root = Path(__file__).parent.parent
    backups_dir = root / "backups"

    # Find latest backup
    if not backups_dir.exists():
        print("Error: No backups found.")
        return

    backups = sorted(backups_dir.iterdir(), key=os.path.getmtime, reverse=True)
    if not backups:
        print("Error: Backup directory empty.")
        return

    latest = backups[0]
    print(f"Restoring from {latest.name}...")

    # Restore Root Modules
    for mod in ["master_orchestrator.py", "klyve_db_manager.py", "llm_service.py"]:
        src = latest / mod
        if src.exists():
            shutil.copy2(src, root / mod)
            print(f"  Restored {mod}")

    # Restore Agents
    agent_src_dir = latest / "agents"
    if agent_src_dir.exists():
        for f in agent_src_dir.glob("*.py"):
            shutil.copy2(f, root / "agents" / f.name)
            print(f"  Restored agents/{f.name}")

if __name__ == "__main__":
    restore_source()