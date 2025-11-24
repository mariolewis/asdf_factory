import ast
import os
import re
import importlib.metadata
from pathlib import Path

# Configuration
REQUIREMENTS_FILE = "requirements.txt"
PROJECT_ROOT = "."
# Packages to ignore (known implicit dependencies or tools)
# We keep PySide6 addons here because they are often loaded dynamically by Qt
WHITELIST = ["pip", "setuptools", "wheel", "graphviz", "PySide6_Addons", "PySide6_Essentials"]

def get_imports_from_file(filepath):
    """Parses a Python file and returns a set of imported module names."""
    imports = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            root = ast.parse(f.read(), filename=filepath)

        for node in ast.walk(root):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception:
        # Fallback for files with syntax errors or encoding issues
        pass
    return imports

def get_all_project_imports(root_dir):
    """Scans all .py files in the project and aggregates imports."""
    all_imports = set()
    for dirpath, _, filenames in os.walk(root_dir):
        if "venv" in dirpath or ".git" in dirpath or "__pycache__" in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(".py"):
                full_path = os.path.join(dirpath, filename)
                all_imports.update(get_imports_from_file(full_path))
    return all_imports

def get_package_import_names(package_name):
    """
    Uses metadata to find the top-level import names for a package.
    Example: 'PyYAML' -> ['yaml'], 'beautifulsoup4' -> ['bs4']
    """
    try:
        dist = importlib.metadata.distribution(package_name)
        # method 1: check top_level.txt
        top_level = dist.read_text('top_level.txt')
        if top_level:
            return [name.strip() for name in top_level.splitlines() if name.strip()]

        # method 2: fallback to iterating files (slower, less accurate)
        # usually top_level.txt exists for compliant packages.
    except Exception:
        pass

    # Fallback: assume package name is the import name (normalized)
    return [package_name.replace('-', '_').lower()]

def audit_requirements():
    if not Path(REQUIREMENTS_FILE).exists():
        print(f"Error: {REQUIREMENTS_FILE} not found.")
        return

    print("Scanning codebase for imports...")
    codebase_imports = get_all_project_imports(PROJECT_ROOT)
    print(f"Found {len(codebase_imports)} unique imported modules in source code.")

    print(f"Reading {REQUIREMENTS_FILE}...")

    unused_packages = []
    used_packages = []

    with open(REQUIREMENTS_FILE, "r", encoding="utf-16") as f: # Using UTF-16 based on your previous success
        for line in f:
            line = line.split('#')[0].strip()
            if not line: continue

            # Extract package name
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)", line)
            if not match: continue
            pkg_name = match.group(1)

            if pkg_name in WHITELIST:
                continue

            # Resolve what this package provides (e.g. 'pandas' -> 'pandas')
            provides_modules = get_package_import_names(pkg_name)

            is_used = False
            for mod in provides_modules:
                if mod in codebase_imports:
                    is_used = True
                    break

            if is_used:
                used_packages.append(pkg_name)
            else:
                # Special Check: formatting specific logic
                # Sometimes imports are case sensitive or mapped weirdly.
                # We do a secondary check.
                unused_packages.append((pkg_name, provides_modules))

    print("\n" + "="*60)
    print("POTENTIALLY UNUSED DEPENDENCIES")
    print("============================================================")
    if not unused_packages:
        print("No obvious unused packages found.")
    else:
        print(f"Found {len(unused_packages)} packages that do not appear to be imported.")
        print("REVIEW THESE CAREFULLY BEFORE DELETING:\n")
        for pkg, modules in unused_packages:
            print(f"[?] {pkg} (Provides: {modules})")

    print("\n" + "="*60)
    print("VERIFIED USED DEPENDENCIES")
    print("============================================================")
    print(", ".join(used_packages))

if __name__ == "__main__":
    audit_requirements()