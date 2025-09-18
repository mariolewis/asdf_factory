# gui/utils.py

import logging
from PySide6.QtCore import QDateTime, QLocale, Qt

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