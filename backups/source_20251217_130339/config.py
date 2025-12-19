# config.py

import base64
import sys
import os
from pathlib import Path

def is_dev_mode() -> bool:
    """
    Checks for the existence of the .dev_mode flag file in the project root.
    Returns:
        bool: True if the file exists (Developer Mode), False otherwise (User Mode).
    """
    # In frozen mode, we look in the same folder as the executable
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent

    return (base_dir / ".dev_mode").exists()

def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for Nuitka/PyInstaller frozen builds.

    Args:
        relative_path (str): The path relative to the project root (e.g., "gui/icons/logo.ico").
    """
    if getattr(sys, 'frozen', False):
        # Production Mode: Resources are in the same folder as the executable (Sidecar pattern)
        base_path = Path(sys.executable).parent
    else:
        # Development Mode: Resources are relative to this config file (project root)
        base_path = Path(__file__).parent

    return str(base_path / relative_path)

def get_graphviz_binary() -> str:
    """
    Returns the absolute path to the Graphviz 'dot' executable.
    Handles the 'Sidecar' deployment strategy for production.
    """
    # Windows executable name
    bin_name = "dot.exe" if sys.platform == "win32" else "dot"

    # Check the sidecar location first (dist/dependencies/graphviz/bin/dot.exe)
    sidecar_path = get_resource_path(f"dependencies/graphviz/bin/{bin_name}")

    if Path(sidecar_path).exists():
        return sidecar_path

    # Fallback: Check system PATH (Development convenience)
    import shutil
    system_path = shutil.which("dot")
    if system_path:
        return system_path

    return "dot" # Hope it's in the path if all else fails

def get_db_key() -> str:
    """
    Retrieves the database encryption key.
    Uses simple obfuscation to prevent the key from being easily readable in plain text
    if the source file is inspected.
    """
    # Obfuscated segments of the key "Klyve-Secure-Core-2025"
    # Segment 1: "Klyve-"
    s1 = b'S2x5dmUt'
    # Segment 2: "Secure-"
    s2 = b'U2VjdXJlLQ=='
    # Segment 3: "Core-"
    s3 = b'Q29yZS0='
    # Segment 4: "2025"
    s4 = b'MjAyNQ=='

    # Reconstruct the key at runtime
    key = (base64.b64decode(s1) +
           base64.b64decode(s2) +
           base64.b64decode(s3) +
           base64.b64decode(s4)).decode('utf-8')

    return key