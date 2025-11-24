# test_about.py
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from gui.about_dialog import AboutDialog

app = QApplication(sys.argv)

# Load style for correct preview
style_file = Path("gui/style.qss")
if style_file.exists():
    with open(style_file, "r") as f:
        app.setStyleSheet(f.read())

dialog = AboutDialog()
dialog.exec()