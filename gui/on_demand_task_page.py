# gui/on_demand_task_page.py

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal, QTimer
from PySide6.QtGui import QColor

from gui.ui_on_demand_task_page import Ui_OnDemandTaskPage

class OnDemandTaskPage(QWidget):
    """
    A simple, dedicated page for displaying the progress of a single,
    long-running on-demand task.
    """
    return_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_OnDemandTaskPage()
        self.ui.setupUi(self)
        self.ui.returnButton.setEnabled(False)
        self.ui.returnButton.clicked.connect(self.return_requested.emit)

    def on_progress_update(self, log_data):
        """Appends a log message to the text area with color."""
        try:
            if isinstance(log_data, tuple) and len(log_data) == 2:
                status, message = log_data
            else:
                status, message = "INFO", str(log_data)

            color_map = {
                "SUCCESS": "#6A8759",
                "INFO": "#A9B7C6",
                "WARNING": "#FFC66D",
                "ERROR": "#CC7832"
            }
            color = color_map.get(status, "#A9B7C6")
            escaped_message = message.replace('<', '&lt;').replace('>', '&gt;')
            html_message = f'<font color="{color}">{escaped_message}</font>'
            QTimer.singleShot(0, lambda: self.ui.logOutputTextEdit.append(html_message))
        except Exception:
             QTimer.singleShot(0, lambda: self.ui.logOutputTextEdit.append(str(log_data)))

    def on_task_finished(self):
        """Enables the return button when the task is complete."""
        self.ui.logOutputTextEdit.append("\n<b>--- TASK COMPLETE ---</b>")
        self.ui.returnButton.setEnabled(True)

    def reset_display(self, title, button_text="Return"):
        """Resets the UI for a new task run."""
        self.ui.headerLabel.setText(title)
        self.ui.logOutputTextEdit.clear()
        self.ui.returnButton.setText(button_text)
        self.ui.returnButton.setEnabled(False)