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