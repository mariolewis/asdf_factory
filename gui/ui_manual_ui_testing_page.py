# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'manual_ui_testing_page.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_ManualUITestingPage(object):
    def setupUi(self, ManualUITestingPage):
        if not ManualUITestingPage.objectName():
            ManualUITestingPage.setObjectName(u"ManualUITestingPage")
        ManualUITestingPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(ManualUITestingPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(ManualUITestingPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(ManualUITestingPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(ManualUITestingPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)
        self.instructionLabel.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.goToDocumentsButton = QPushButton(ManualUITestingPage)
        self.goToDocumentsButton.setObjectName(u"goToDocumentsButton")

        self.verticalLayout.addWidget(self.goToDocumentsButton)

        self.line_2 = QFrame(ManualUITestingPage)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        self.uploadLabel = QLabel(ManualUITestingPage)
        self.uploadLabel.setObjectName(u"uploadLabel")

        self.verticalLayout.addWidget(self.uploadLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.filePathLineEdit = QLineEdit(ManualUITestingPage)
        self.filePathLineEdit.setObjectName(u"filePathLineEdit")
        self.filePathLineEdit.setReadOnly(True)

        self.horizontalLayout.addWidget(self.filePathLineEdit)

        self.browseButton = QPushButton(ManualUITestingPage)
        self.browseButton.setObjectName(u"browseButton")

        self.horizontalLayout.addWidget(self.browseButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.processResultsButton = QPushButton(ManualUITestingPage)
        self.processResultsButton.setObjectName(u"processResultsButton")

        self.verticalLayout.addWidget(self.processResultsButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(ManualUITestingPage)

        QMetaObject.connectSlotsByName(ManualUITestingPage)
    # setupUi

    def retranslateUi(self, ManualUITestingPage):
        ManualUITestingPage.setWindowTitle(QCoreApplication.translate("ManualUITestingPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("ManualUITestingPage", u"Testing && Validation", None))
        self.instructionLabel.setText(QCoreApplication.translate("ManualUITestingPage", u"<b>Your action is required to complete manual testing:</b>\n"
"<ol>\n"
"<li>The system has just generated a new <b>Manual UI Test Plan</b> for this sprint.</li>\n"
"<li>Click the <b>'Go to Documents Page'</b> button to view and download the <code>manual_ui_test_plan.docx</code> file.</li>\n"
"<li>Execute the tests as described in the document, record the results, and save the file.</li>\n"
"<li>Return to this page and upload your completed results document below to finalize the sprint.</li>\n"
"</ol>", None))
        self.goToDocumentsButton.setText(QCoreApplication.translate("ManualUITestingPage", u"Go to Documents Page", None))
        self.uploadLabel.setText(QCoreApplication.translate("ManualUITestingPage", u"<b>Upload Completed Test Plan Results:</b>", None))
        self.browseButton.setText(QCoreApplication.translate("ManualUITestingPage", u"Browse...", None))
        self.processResultsButton.setText(QCoreApplication.translate("ManualUITestingPage", u"Process Test Results", None))
    # retranslateUi

