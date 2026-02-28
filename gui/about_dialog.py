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

        # FORCE the width here
        self.setMinimumWidth(700)
        # OR just resize it initially (can be shrunk by user later)
        self.resize(700, 600)

        self._setup_branding()
        self._setup_credits()
        self._load_legal_text()

        self.ui.buttonBox.rejected.connect(self.accept) # Close button acts as accept/close

    def _setup_branding(self):
        """Sets the HTML content for the main About tab."""
        version = "1.1 Beta"
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
                <p style="font-size: 11pt;">The Automated Software Factory</p><br>
                <p class="version">Version: {version}</p>

                <hr style="border-top: 1px solid #4A4A4A;" width="50%">

                <p class="footer">&copy; 2025 Mario J. Lewis. Licensed under the MIT License.</p>
                <p class="sub">Use is subject to the End User License Agreement.</p>
            </center>
        </body>
        </html>
        """
        self.ui.brandingLabel.setText(about_html)

    def _setup_credits(self):
        """Populates the Credits tab."""
        credits_html = """
        <html>
        <head>
            <style>
                /* Match the QSS font settings exactly to ensure uniformity */
                body {
                    color: #F0F0F0;
                    font-family: "Inter", "Segoe UI", sans-serif;
                    font-size: 10pt;
                    font-weight: 400;
                }
                h3 {
                    color: #007ACC;
                    font-family: "Inter", "Segoe UI", sans-serif;
                    margin-bottom: 5px;
                    font-weight: 700;
                }
                ul {
                    margin-top: 0px;
                    -qt-list-indent: 1;
                }
                li {
                    margin-bottom: 8px;
                }
            </style>
        </head>
        <body>
            <h3>Special Thanks & Acknowledgments</h3>
            <p>Klyve is built in part upon the excellent work of the open-source community.</p>
            <ul>
                <li><b>The Qt Company:</b><br>This application uses the Qt framework licensed under the GNU LGPL v3. (www.qt.io)</li>
                <li><b>FreeType Project:</b><br>Portions of this software are copyright &copy; 1996-2000 The FreeType Project (www.freetype.org). All rights reserved.</li>
                <li><b>Independent JPEG Group:</b><br>This software is based in part on the work of the Independent JPEG Group (ijg.org).</li>
                <li><b>Jordan Russell's Software:</b><br>Inno Setup installation builder provided by Jordan Russell. Copyright &copy; 1997-2025 Jordan Russell. Portions Copyright &copy; 2000-2025 Martijn Laan. (jrsoftware.org)</li>
                </ul>
        </body>
        </html>
        """
        self.ui.creditsTextEdit.setHtml(credits_html)

    def _load_legal_text(self):
        """Loads secure text resources into the tabs."""
        self.ui.eulaTextEdit.setPlainText(resources.EULA_TEXT)
        self.ui.privacyTextEdit.setPlainText(resources.PRIVACY_POLICY_TEXT)
        self.ui.noticesTextEdit.setPlainText(resources.THIRD_PARTY_NOTICES_TEXT)