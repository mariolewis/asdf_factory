# gui/utils.py

import logging
import markdown
import html
import re
from PySide6.QtCore import QDateTime, QLocale, Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox
from .rendering_utils import preprocess_markdown_for_display

def format_timestamp_for_display(timestamp_str: str) -> str:
    """
    Parses an ISO 8601 timestamp string and formats it using the user's
    local system settings via Qt. This is the central utility for all
    user-facing timestamps.
    """
    if not timestamp_str:
        return "N/A"
    try:
        # Manually replace 'Z' with UTC offset for robust parsing
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + "+00:00"

        utc_dt = QDateTime.fromString(timestamp_str, Qt.DateFormat.ISODateWithMs)
        if not utc_dt.isValid():
            # Try parsing without milliseconds if the first attempt fails
            utc_dt = QDateTime.fromString(timestamp_str, Qt.DateFormat.ISODate)
            if not utc_dt.isValid():
                return timestamp_str # Return original if parsing fails

        # Convert to the user's local time zone
        local_dt = utc_dt.toLocalTime()

        # Format using the system's default short date and time format
        return QLocale.system().toString(local_dt, QLocale.FormatType.ShortFormat)
    except Exception as e:
        logging.warning(f"Could not format timestamp '{timestamp_str}': {e}")
        # Fallback for any unexpected error
        return timestamp_str

def show_status_message(window: QMainWindow, message: str, level: str = "info", duration: int = 5000):
    """
    Displays a temporary message in the main window's status bar.

    Args:
        window (QMainWindow): The main window instance.
        message (str): The message to display.
        level (str): 'info', 'success', 'warning', or 'error'. Affects potential styling (optional).
        duration (int): How long the message should stay (in milliseconds). 0 means persistent until cleared.
    """
    if not window or not hasattr(window, 'statusBar'):
        logging.warning(f"Cannot show status message: Invalid window object. Message: {message}")
        return

    # Optional: Add styling based on level later if needed
    # For now, just display the message
    window.statusBar().showMessage(message, duration)

    # Log the message as well
    if level == "error":
        logging.error(f"Status Bar: {message}")
    elif level == "warning":
        logging.warning(f"Status Bar: {message}")
    else:
        logging.info(f"Status Bar: {message}")

def render_markdown_to_html(markdown_text: str) -> str:
    """
    Renders markdown content to HTML, robustly fixing common LLM list errors.
    Includes extensions for tables and fenced code blocks.
    """
    if not markdown_text:
        return ""
    try:
        # First, preprocess the text to convert Mermaid blocks to <img> tags
        text_with_images = preprocess_markdown_for_display(markdown_text)
        # Unescape any remaining HTML entities
        text = html.unescape(text_with_images)

        # Use regex to insert a newline before a list item if it's not already preceded by one.
        text = re.sub(r'([^\n])\n([ \t]*[\*\-]\s)', r'\1\n\n\2', text) # For bulleted lists
        text = re.sub(r'([^\n])\n([ \t]*\d+\.\s)', r'\1\n\n\2', text) # For numbered lists

        # Render to HTML using the standard extensions (merged from both versions)
        html_content = markdown.markdown(
            text,
            extensions=['fenced_code', 'tables', 'extra', 'codehilite']
        )
        return html_content

    except Exception as e:
        # --- ORIGINAL ERROR HANDLING ---
        logging.error(f"Failed to render markdown: {e}", exc_info=True)
        # Fallback to plain text, escaped
        escaped_content = html.escape(markdown_text) # Use original text for fallback
        return f"<h3 style='color:red;'>Markdown Rendering Error</h3><pre>{escaped_content}</pre>"

def center_window(widget):
    """
    Centers a top-level widget on the screen.
    This explicit centering is required for consistent behavior across platforms
    (Windows, Linux/WSL), as some window managers default to random placement.
    """
    from PySide6.QtGui import QGuiApplication

    screen = QGuiApplication.primaryScreen()
    if not screen:
        return

    screen_geometry = screen.availableGeometry()
    # Force the widget to calculate its layout size first
    widget.adjustSize()
    widget_geometry = widget.frameGeometry()

    center_point = screen_geometry.center()
    widget_geometry.moveCenter(center_point)
    widget.move(widget_geometry.topLeft())

def validate_security_input(parent_widget, input_text: str, input_type: str = "NAME") -> bool:
    """
    Validates user input against common security vulnerabilities (SQLi, OS Injection).

    Args:
        parent_widget: The widget to parent the blocking dialog to.
        input_text (str): The raw string entered by the user.
        input_type (str): 'NAME' (Strict), 'PATH' (Allow separators), or 'COMMAND' (Allow shell chars).

    Returns:
        bool: True if input is safe, False if potentially malicious.
    """
    if not input_text:
        return True # Empty input is handled by specific form logic, not security validation

    # 1. SQL Injection Patterns (Common to ALL inputs)
    # Checks for dangerous SQL keywords or structural manipulation characters
    sql_patterns = [
        r"';\s*DROP\s+TABLE", r"--;", r"'\s+OR\s+'1'='1",
        r"UNION\s+SELECT", r"exec\(\s*'"
    ]
    for pattern in sql_patterns:
        if re.search(pattern, input_text, re.IGNORECASE):
            QMessageBox.warning(parent_widget, "Security Alert",
                "Potentially insecure input detected (SQL Injection Risk).\n"
                "Please enter a valid input.")
            return False

    # 2. Strict Name Validation (Project Names, etc.)
    if input_type == "NAME":
        # Block: Quotes, Semicolons, Slashes, Shell Operators, Wildcards
        if re.search(r"['\";/\\&\|\$><`*?]", input_text):
            QMessageBox.warning(parent_widget, "Invalid Input",
                "Project names cannot contain special characters, paths, or shell operators.\n"
                "Allowed: Alphanumeric, underscores, hyphens.")
            return False

    # 3. Path Validation (File System Paths)
    elif input_type == "PATH":
        # Block: Quotes, Semicolons, Shell Operators
        # Allow: Slashes (/ \), Colons (:) for drive letters
        if re.search(r"['\";&\|\$><`]", input_text):
            QMessageBox.warning(parent_widget, "Invalid Path",
                "Paths cannot contain shell operators or injection characters.\n"
                "Please use standard file system paths.")
            return False

    # 4. Command Validation (Test Commands)
    elif input_type == "COMMAND":
        # We ALLOW shell operators (e.g., &&, |) as they are valid in commands.
        # We only strictly block the SQL injection patterns checked in Step 1.
        pass

    return True