# gui/utils.py

import logging
from PySide6.QtCore import QDateTime, QLocale, Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox

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