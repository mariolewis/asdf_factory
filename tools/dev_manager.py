import sys
import shutil
import os
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
BACKUPS_DIR = PROJECT_ROOT / "backups"
AGENTS_DIR = PROJECT_ROOT / "agents"

ROOT_MODULES = ["master_orchestrator", "klyve_db_manager", "llm_service"]

def get_latest_backup():
    if not BACKUPS_DIR.exists(): return None
    backups = sorted(BACKUPS_DIR.iterdir(), key=os.path.getmtime, reverse=True)
    return backups[0] if backups else None

def status():
    """Checks if the project is in Source Mode or Binary Mode."""
    print(f"--- Project Status ({PROJECT_ROOT}) ---")

    # Check Master Orchestrator
    mo_py = PROJECT_ROOT / "master_orchestrator.py"
    mo_pyd = list(PROJECT_ROOT.glob("master_orchestrator*.pyd")) + list(PROJECT_ROOT.glob("master_orchestrator*.so"))

    if mo_py.exists():
        print("✅ Core Logic: SOURCE CODE (Editable)")
    elif mo_pyd:
        print("🔒 Core Logic: COMPILED BINARY (Locked)")
    else:
        print("❌ Core Logic: MISSING (Invalid State)")

    # Check Agents
    py_count = len(list(AGENTS_DIR.glob("*.py")))
    pyd_count = len(list(AGENTS_DIR.glob("*.pyd"))) + len(list(AGENTS_DIR.glob("*.so")))

    print(f"   Agents: {py_count} Source files | {pyd_count} Compiled files")
    print("-" * 30)

def switch_to_dev_mode():
    """Restores .py files from the latest backup."""
    print("\n🔓 SWITCHING TO DEV MODE (Restoring Source)...")

    backup = get_latest_backup()
    if not backup:
        print("❌ Error: No backups found. Cannot restore source.")
        return

    print(f"Restoring from: {backup.name}")

    # Restore Root Modules
    for mod in ROOT_MODULES:
        src = backup / f"{mod}.py"
        dst = PROJECT_ROOT / f"{mod}.py"
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Restored {mod}.py")

    # Restore Agents
    backup_agents = backup / "agents"
    if backup_agents.exists():
        count = 0
        for f in backup_agents.glob("*.py"):
            shutil.copy2(f, AGENTS_DIR / f.name)
            count += 1
        print(f"  Restored {count} agents.")

    # Restore Config (if it was sanitized)
    src_config = backup / "config.py"
    if src_config.exists():
        shutil.copy2(src_config, PROJECT_ROOT / "config.py")
        print("  Restored config.py")

    # Clean up binaries to avoid confusion
    print("Cleaning up root binaries...")
    for ext in ["*.pyd", "*.so", "*.c"]:
        for f in PROJECT_ROOT.glob(ext):
            f.unlink()
        for f in AGENTS_DIR.glob(ext):
            f.unlink()

    print("✅ Project is now in DEV MODE. You can edit code.")

def switch_to_prod_mode():
    """Compiles source and moves .py files to backup."""
    print("\n🔒 SWITCHING TO PROD MODE (Compiling & Locking)...")

    # 1. Create Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUPS_DIR / f"source_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=True)

    # Backup Root Modules & Config
    for mod in ROOT_MODULES + ["config"]:
        src = PROJECT_ROOT / f"{mod}.py"
        if src.exists():
            shutil.copy2(src, backup_path / f"{mod}.py")

    # Backup Agents
    (backup_path / "agents").mkdir()
    for f in AGENTS_DIR.glob("*.py"):
        shutil.copy2(f, backup_path / "agents" / f.name)

    print(f"Backup created: {backup_path.name}")

    # 2. Compile (Invokes your existing setup_cython)
    print("Compiling...")
    try:
        subprocess.run([sys.executable, "setup_cython.py", "build_ext", "--inplace"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Compilation Failed. Aborting lock.")
        return

    # 3. Remove Source Files
    print("Removing source files...")
    for mod in ROOT_MODULES:
        src = PROJECT_ROOT / f"{mod}.py"
        if src.exists(): src.unlink()

    for f in AGENTS_DIR.glob("*.py"):
        if f.name != "__init__.py":
            f.unlink()

    print("✅ Project is now in PROD MODE. Source code hidden.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        status()
        print("\nUsage: python tools/dev_manager.py [unlock | lock | status]")
    elif sys.argv[1] == "unlock":
        switch_to_dev_mode()
    elif sys.argv[1] == "lock":
        switch_to_prod_mode()
    else:
        status()