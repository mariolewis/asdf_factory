# gui/manual_change_dialog.py

from PySide6.QtWidgets import QDialog, QListWidgetItem
from PySide6.QtCore import Qt

# This import will work once the .ui file is compiled
from gui.ui_manual_change_dialog import Ui_ManualChangeDialog

class ManualChangeDialog(QDialog):
    """
    The logic handler for the Manual Change Confirmation dialog.
    """
    def __init__(self, uncompleted_tasks: list, parent=None):
        super().__init__(parent)
        self.ui = Ui_ManualChangeDialog()
        self.ui.setupUi(self)
        self.populate_tasks(uncompleted_tasks)
        self.connect_signals()

    def connect_signals(self):
        """Connects the dialog's buttons."""
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

    def populate_tasks(self, tasks: list):
        """
        Populates the list widget with checkable tasks.

        Args:
            tasks (list): A list of task dictionaries from the development plan.
        """
        self.ui.tasksListWidget.clear()
        if not tasks:
            item = QListWidgetItem("No uncompleted tasks found in the plan.")
            self.ui.tasksListWidget.addItem(item)
            return

        for task in tasks:
            task_id = task.get("micro_spec_id", "N/A")
            task_desc = task.get("task_description", "No description.")

            # Use f-string for clear formatting
            display_text = f"[{task_id}] {task_desc}"

            item = QListWidgetItem(display_text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            # Store the raw task ID in the item for later retrieval
            item.setData(Qt.UserRole, task_id)
            self.ui.tasksListWidget.addItem(item)

    def get_selected_task_ids(self) -> list[str]:
        """
        Retrieves the micro_spec_ids of all tasks checked by the user.

        Returns:
            A list of strings, where each string is a selected task ID.
        """
        selected_ids = []
        for i in range(self.ui.tasksListWidget.count()):
            item = self.ui.tasksListWidget.item(i)
            if item.checkState() == Qt.Checked:
                task_id = item.data(Qt.UserRole)
                if task_id:
                    selected_ids.append(task_id)
        return selected_ids