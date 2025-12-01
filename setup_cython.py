import sys
import os
import shutil
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize

def get_extensions_and_inventory():
    """
    Scans the project to build a list of Extension objects for Cython.
    Also returns a list of file paths for the audit report.
    """
    project_root = Path(__file__).parent
    extensions = []
    inventory = []

    # 1. Root-level targets (The Core Systems)
    root_targets = [
        "master_orchestrator",
        "klyve_db_manager",
        "llm_service"
    ]

    for target in root_targets:
        py_file = project_root / f"{target}.py"
        if py_file.exists():
            extensions.append(Extension(target, [str(py_file)]))
            inventory.append(str(py_file))
        else:
            print(f"WARNING: Root target not found: {py_file}")

    # 2. Agent Swarm (The Intelligence)
    agents_dir = project_root / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.py"):
            # Skip __init__.py to maintain package structure safely
            if agent_file.name == "__init__.py":
                continue

            # Module name must be dotted path: agents.agent_name
            module_name = f"agents.{agent_file.stem}"
            extensions.append(Extension(module_name, [str(agent_file)]))
            inventory.append(str(agent_file))

    return extensions, inventory

if __name__ == "__main__":
    # --- AUDIT MODE ---
    # If run without arguments, just print what WOULD happen.
    if len(sys.argv) == 1:
        exts, inventory = get_extensions_and_inventory()
        print(f"\n--- CYTHON COMPILATION AUDIT ---")
        print(f"Targeting {len(inventory)} files for hardening:")
        for f in inventory:
            print(f"  [TARGET] {f}")
        print(f"\nTo compile, run: python setup_cython.py build_ext --inplace")
        print(f"--------------------------------")
        sys.exit(0)

    # --- BUILD MODE ---
    # If run with arguments (like 'build_ext'), proceed with compilation.
    exts, _ = get_extensions_and_inventory()

    setup(
        name="Klyve Core",
        ext_modules=cythonize(
            exts,
            compiler_directives={
                'language_level': "3",       # Python 3 enforcement [cite: 2206]
                'always_allow_keywords': True # Robustness for kwargs
            },
            quiet=False
        ),
    )