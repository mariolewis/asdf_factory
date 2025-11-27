# config.py

from pathlib import Path

def is_dev_mode() -> bool:
    """
    Checks for the existence of the .dev_mode flag file in the project root.

    Returns:
        bool: True if the file exists (Developer Mode), False otherwise (User Mode).
    """
    return Path(".dev_mode").exists()