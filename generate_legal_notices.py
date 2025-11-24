import importlib.metadata
import sys
import pathlib
import re
from datetime import datetime

# Configuration
REQUIREMENTS_FILE = "requirements.txt"
OUTPUT_FILE = "Third_Party_Notices.txt"

# Licenses to look for (case-insensitive partial match)
LICENSE_FILENAMES = ["LICENSE", "COPYING", "NOTICE", "LICENCE"]

def read_requirements_file(filepath):
    """
    Attempts to read requirements.txt using multiple encodings to handle
    Windows PowerShell (UTF-16) vs Standard (UTF-8) outputs.
    """
    encodings_to_try = ['utf-8-sig', 'utf-16', 'cp1252', 'latin-1']

    for enc in encodings_to_try:
        try:
            with open(filepath, "r", encoding=enc) as f:
                lines = [line.strip() for line in f.readlines()]

            # Heuristic check: If we read lines but they look like garbage (null bytes),
            # or if it's a single massive line, this encoding is wrong.
            if len(lines) > 0:
                # If we successfully read readable text that looks like a package
                if any(re.match(r"^[a-zA-Z]", line) for line in lines[:5]):
                    print(f"[DEBUG] Successfully read {filepath} using encoding: {enc}")
                    return lines
        except UnicodeError:
            continue
        except Exception as e:
            print(f"[DEBUG] Failed to read with {enc}: {e}")

    print("[ERROR] Could not read requirements.txt with any standard encoding.")
    return []

def get_transitive_dependencies(root_packages):
    """
    Given a list of root packages, recursively find all their dependencies
    installed in the current environment.
    """
    dependencies = set()
    queue = list(root_packages)
    processed = set()

    print(f"[DEBUG] Resolving dependencies for {len(root_packages)} root packages...")

    while queue:
        raw_name = queue.pop(0)
        # Normalize package name (replace . and _ with -)
        pkg_name = raw_name.lower().replace("_", "-").replace(".", "-")

        if pkg_name in processed:
            continue

        processed.add(pkg_name)
        dependencies.add(pkg_name)

        try:
            # Get dependencies for this package
            requires = importlib.metadata.requires(pkg_name)
            if requires:
                for req_str in requires:
                    # Simple parsing to get just the package name from strings like "requests (>=2.0)"
                    # We split by space, semicolon, or comparison operators
                    match = re.match(r"^([a-zA-Z0-9_\-\.]+)", req_str)
                    if match:
                        dep_name = match.group(1)
                        # Basic marker check: skip if it's for a different OS or python version
                        if ";" in req_str and ("extra =" in req_str or "sys_platform" in req_str):
                            # Very basic skip for optional extras to keep it simple without 'packaging' lib
                            continue
                        queue.append(dep_name)

        except importlib.metadata.PackageNotFoundError:
            # Only warn if it's a root package; otherwise it might be an optional dep we don't have
            if raw_name in root_packages:
                print(f"[WARNING] Root package '{raw_name}' not found in current environment.")

    return sorted(list(dependencies))

def generate_scoped_notices():
    if not pathlib.Path(REQUIREMENTS_FILE).exists():
        print(f"[ERROR] {REQUIREMENTS_FILE} not found in {pathlib.Path.cwd()}")
        return

    # 1. Robust Read of Requirements
    lines = read_requirements_file(REQUIREMENTS_FILE)
    root_packages = []

    print(f"[DEBUG] First 3 lines read from file:")
    for i, l in enumerate(lines[:3]):
        print(f"  {i+1}: {l}")

    for line in lines:
        # Clean comments and whitespace
        line = line.split('#')[0].strip()
        if not line:
            continue

        # Regex to grab the package name (stops at ==, >=, etc)
        match = re.match(r"^([a-zA-Z0-9_\-\.]+)", line)
        if match:
            root_packages.append(match.group(1))

    if not root_packages:
        print("[ERROR] Could not parse any package names from requirements.txt.")
        return

    # 2. Resolve full dependency tree
    all_packages = get_transitive_dependencies(root_packages)
    print(f"[INFO] Resolved {len(all_packages)} total packages (roots + dependencies).")

    # 3. Generate License Text
    timestamp = datetime.now().strftime("%Y-%m-%d")
    full_text = [
        "THIRD-PARTY SOFTWARE NOTICES AND INFORMATION",
        f"Generated: {timestamp}",
        "=========================================================================",
        "This software includes components developed by third parties.",
        "The following are the license notices and copyright information for these components.",
        "=========================================================================",
        ""
    ]

    success_count = 0
    missing_licenses = []

    for pkg_name in all_packages:
        try:
            dist = importlib.metadata.distribution(pkg_name)
            meta = dist.metadata

            name = meta.get('Name', pkg_name)
            version = dist.version
            home_page = meta.get('Home-page', 'N/A')
            license_summary = meta.get('License', 'See full text below')

            header = (
                f"\n"
                f"-------------------------------------------------------------------------\n"
                f"COMPONENT: {name} ({version})\n"
                f"URL: {home_page}\n"
                f"LICENSE SUMMARY: {license_summary}\n"
                f"-------------------------------------------------------------------------\n"
            )
            full_text.append(header)

            # Try to find license text files
            license_content = None
            if dist.files:
                for file_path in dist.files:
                    # Search for license-like files in the distribution info
                    if any(marker in file_path.name.upper() for marker in LICENSE_FILENAMES):
                        # Ensure we don't pick up binary files by accident
                        if file_path.suffix.lower() not in ['.py', '.pyc', '.pyd', '.dll', '.so']:
                            full_path = dist.locate_file(file_path)
                            if full_path.is_file():
                                try:
                                    license_content = full_path.read_text(encoding='utf-8', errors='replace')
                                    break
                                except Exception:
                                    pass

            if license_content:
                full_text.append(license_content)
                full_text.append("\n")
                success_count += 1
            else:
                full_text.append(f"License file not automatically found.\n")
                full_text.append(f"Please refer to the project homepage for license terms: {home_page}\n")
                missing_licenses.append(name)

        except importlib.metadata.PackageNotFoundError:
            pass

    # 4. Write Output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(full_text))

    print("-" * 60)
    print(f"[SUCCESS] Output saved to: {OUTPUT_FILE}")
    print(f"Licenses found: {success_count}")
    print(f"Licenses MISSING: {len(missing_licenses)}")

    if missing_licenses:
        print("\n[ACTION REQUIRED] The following packages need manual license verification:")
        print(", ".join(missing_licenses))

if __name__ == "__main__":
    generate_scoped_notices()