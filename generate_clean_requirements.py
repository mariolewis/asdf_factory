import ast
import os
import sys
import importlib.metadata
from pathlib import Path

# --- CONFIGURATION ---
PROJECT_ROOT = "."
OUTPUT_FILE = "requirements.new.txt"

# 1. FORCE INCLUDE: Packages that are NOT explicitly imported in code
#    but are required for the application to run (binaries, plugins, etc.)
FORCE_INCLUDE = [
    "PySide6",           # The main wrapper package
    "PySide6_Addons",    # Qt Addons
    "PySide6_Essentials",# Qt Essentials
    "shiboken6",         # C++ Binding generator
    "kaleido",           # Required by Plotly for image export
    "openpyxl",          # Required by Pandas for Excel export
    "htmldocx",          # Used for converting HTML to Docx
    "deepseek",          # Explicitly requested
]

# 2. FORCE EXCLUDE: Packages to ignore even if imported
#    (e.g., local modules that look like packages, or dev tools)
FORCE_EXCLUDE = [
    "klyve_db_manager", "master_orchestrator", "gui", "agents", "llm_service",
    "config", "utils", "tests", "stubs"
]

def get_stdlib_module_names():
    """Returns a set of standard library module names."""
    if sys.version_info >= (3, 10):
        return sys.stdlib_module_names
    else:
        return {
            'os', 'sys', 'json', 're', 'math', 'datetime', 'time', 'logging',
            'pathlib', 'shutil', 'subprocess', 'textwrap', 'io', 'typing',
            'threading', 'traceback', 'ast', 'unittest', 'html', 'uuid',
            'base64', 'hashlib', 'sqlite3', 'tempfile', 'atexit', 'contextlib',
            'random', 'enum', 'abc'
        }

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
        pass
    return imports

def map_imports_to_packages():
    """
    Creates a mapping of {top_level_module: package_name}.
    """
    mapping = {}
    try:
        packages = list(importlib.metadata.distributions())
    except Exception:
        return {}

    for dist in packages:
        try:
            pkg_name = dist.metadata['Name']
            # 1. Check top_level.txt (standard way)
            top_level = dist.read_text('top_level.txt')
            if top_level:
                for module in top_level.splitlines():
                    module = module.strip()
                    if module:
                        mapping[module.lower()] = pkg_name

            # 2. Fallback: If package name is very similar to module name
            # (e.g. "GitPython" -> "git")
            mapping[pkg_name.lower()] = pkg_name

        except Exception:
            pass

    return mapping

def generate():
    print(f"Scanning project at '{PROJECT_ROOT}'...")

    # 1. Harvest all imports
    all_imports = set()
    for dirpath, _, filenames in os.walk(PROJECT_ROOT):
        if any(part.startswith('.') for part in Path(dirpath).parts) or "venv" in dirpath or "__pycache__" in dirpath:
            continue

        for filename in filenames:
            if filename.endswith(".py"):
                full_path = os.path.join(dirpath, filename)
                all_imports.update(get_imports_from_file(full_path))

    print(f"Found {len(all_imports)} unique imports in source code.")

    # 2. Filter
    stdlib = get_stdlib_module_names()
    filtered_imports = {
        imp for imp in all_imports
        if imp not in stdlib
        and imp not in FORCE_EXCLUDE
        and imp.lower() not in [x.lower() for x in FORCE_EXCLUDE]
    }

    # 3. Map to Packages
    import_map = map_imports_to_packages()
    final_requirements = {}

    # A. Process Imports
    for module in filtered_imports:
        pkg_name = import_map.get(module.lower())

        if not pkg_name:
            # Fallback: assume package name = module name
            pkg_name = module

        # Get Version
        try:
            version = importlib.metadata.version(pkg_name)
            final_requirements[pkg_name] = version
        except importlib.metadata.PackageNotFoundError:
            # Only warn if it's not in our exclusions
            if module not in FORCE_EXCLUDE:
                print(f"[WARNING] Could not find installed package for import: '{module}'")

    # B. Process Force Includes
    print("Adding forced dependencies...")
    for force_pkg in FORCE_INCLUDE:
        try:
            version = importlib.metadata.version(force_pkg)
            final_requirements[force_pkg] = version
        except importlib.metadata.PackageNotFoundError:
            # If deepseek is not actually installed, this will catch it
            print(f"[WARNING] Forced package '{force_pkg}' is not installed in your environment. Skipping.")

    # 4. Write Output
    sorted_reqs = sorted(final_requirements.items(), key=lambda x: x[0].lower())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for pkg, ver in sorted_reqs:
            f.write(f"{pkg}=={ver}\n")

    print("-" * 60)
    print(f"[SUCCESS] Identified {len(final_requirements)} packages.")
    print(f"Check '{OUTPUT_FILE}'")
    print("-" * 60)

if __name__ == "__main__":
    generate()