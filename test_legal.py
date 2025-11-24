# test_legal.py
import sys
from PySide6.QtWidgets import QApplication
from gui.legal_dialog import LegalDialog

app = QApplication(sys.argv)

# Apply a basic dark theme to match the app style roughly for this test
app.setStyleSheet("QWidget { background-color: #2b2b2b; color: #f0f0f0; } QTextEdit { background-color: #1e1e1e; }")

dialog = LegalDialog()
result = dialog.exec()

if result == 1:
    print("User ACCEPTED the terms.")
else:
    print("User DECLINED the terms.")