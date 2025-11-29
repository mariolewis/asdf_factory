# config.py

import base64
from pathlib import Path

def is_dev_mode() -> bool:
    """
    Checks for the existence of the .dev_mode flag file in the project root.

    Returns:
        bool: True if the file exists (Developer Mode), False otherwise (User Mode).
    """
    return Path(".dev_mode").exists()

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