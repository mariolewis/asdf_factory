# gui/about_dialog.py

from PySide6.QtWidgets import QDialog
import resources
from gui.ui_about_dialog import Ui_AboutDialog

class AboutDialog(QDialog):
    """
    A centralized dialog for application info and legal documentation.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AboutDialog()
        self.ui.setupUi(self)

        self._setup_branding()
        self._load_legal_text()

        self.ui.buttonBox.rejected.connect(self.accept) # Close button acts as accept/close

    def _setup_branding(self):
        """Sets the HTML content for the main About tab."""
        version = "1.0 Beta"
        about_html = f"""
        <html>
        <head>
            <style>
                body {{ color: #F0F0F0; font-family: sans-serif; }}
                h3 {{ margin-bottom: 8px; color: #007ACC; font-weight: bold; font-size: 16pt; }}
                p {{ margin: 0 0 5px 0; }}
                .version {{ font-weight: bold; color: #FFC66D; font-size: 11pt; }}
                .footer {{ font-size: 10pt; color: #CCCCCC; }}
                .sub {{ font-size: 8pt; color: #888888; }}
            </style>
        </head>
        <body>
            <center>
                <h3>KLYVE: Your Expertise. Scaled.</h3>
                <p style="font-size: 11pt;">The Orchestrated Software Development Assistant</p><br>
                <p class="version">Version: {version}</p>

                <hr style="border-top: 1px solid #4A4A4A;" width="50%">

                <p class="footer">&copy; 2025 Mario J. Lewis. All Rights Reserved.</p>
                <p class="sub">Use is subject to the End User License Agreement.</p>
            </center>
        </body>
        </html>
        """
        self.ui.brandingLabel.setText(about_html)

    def _load_legal_text(self):
        """Loads secure text resources into the tabs."""
        self.ui.eulaTextEdit.setPlainText(resources.EULA_TEXT)
        self.ui.privacyTextEdit.setPlainText(resources.PRIVACY_POLICY_TEXT)
        self.ui.noticesTextEdit.setPlainText(resources.THIRD_PARTY_NOTICES_TEXT)