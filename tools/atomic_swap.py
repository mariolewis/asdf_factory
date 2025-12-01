import shutil
import sys
import os
from pathlib import Path
from datetime import datetime

def atomic_swap(project_root):
    print(f"Initiating Atomic Swap in: {project_root}")

    # 1. Setup Backup Directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / "backups" / f"source_code_snapshot_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    print(f"Backup location: {backup_dir}")

    # 2. Define Targets (Must match setup_cython.py logic)
    # Root modules
    root_targets = ["master_orchestrator", "klyve_db_manager", "llm_service"]

    # Agent modules (scan directory)
    agents_dir = project_root / "agents"
    agent_targets = []
    if agents_dir.exists():
        for f in agents_dir.glob("*.py"):
            if f.name != "__init__.py":
                agent_targets.append(f.stem) # filename without extension

    moved_count = 0

    # 3. Process Root Targets
    for module_name in root_targets:
        if _move_source_if_compiled(project_root, module_name, backup_dir):
            moved_count += 1

    # 4. Process Agent Targets
    for agent_name in agent_targets:
        if _move_source_if_compiled(agents_dir, agent_name, backup_dir / "agents"):
            moved_count += 1

    print(f"\nAtomic Swap Complete.")
    print(f"Secured {moved_count} modules. Source files moved to backup.")
    print("You may now run the application to verify binary execution.")

def _move_source_if_compiled(base_path, module_name, backup_dest):
    """
    Moves .py and .c files to backup IF AND ONLY IF a valid .pyd/.so exists.
    """
    py_file = base_path / f"{module_name}.py"
    c_file = base_path / f"{module_name}.c"

    # Find the compiled extension. Naming varies by OS/Compiler.
    # We look for any file starting with module_name and ending in .pyd or .so
    candidates = list(base_path.glob(f"{module_name}*.pyd")) + \
                 list(base_path.glob(f"{module_name}*.so"))

    if not candidates:
        print(f"  [SKIP] {module_name}: No compiled extension found.")
        return False

    if not py_file.exists():
        print(f"  [SKIP] {module_name}: Source .py already missing.")
        return False

    # Ensure backup destination exists
    backup_dest.mkdir(parents=True, exist_ok=True)

    try:
        # Move .py
        shutil.move(str(py_file), str(backup_dest / py_file.name))

        # Move .c (if it exists)
        if c_file.exists():
            shutil.move(str(c_file), str(backup_dest / c_file.name))

        print(f"  [SECURED] {module_name}")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to move {module_name}: {e}")
        return False

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    atomic_swap(root)