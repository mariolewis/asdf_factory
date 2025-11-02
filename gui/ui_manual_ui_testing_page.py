# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'manual_ui_testing_page.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
    QTextEdit, QVBoxLayout, QWidget)

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

        self.instructionTextEdit = QTextEdit(ManualUITestingPage)
        self.instructionTextEdit.setObjectName(u"instructionTextEdit")
        self.instructionTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.instructionTextEdit)

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

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.goToDocumentsButton = QPushButton(ManualUITestingPage)
        self.goToDocumentsButton.setObjectName(u"goToDocumentsButton")

        self.horizontalLayout_2.addWidget(self.goToDocumentsButton)

        self.processResultsButton = QPushButton(ManualUITestingPage)
        self.processResultsButton.setObjectName(u"processResultsButton")

        self.horizontalLayout_2.addWidget(self.processResultsButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(ManualUITestingPage)

        QMetaObject.connectSlotsByName(ManualUITestingPage)
    # setupUi

    def retranslateUi(self, ManualUITestingPage):
        ManualUITestingPage.setWindowTitle(QCoreApplication.translate("ManualUITestingPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("ManualUITestingPage", u"Manual UI Testing", None))
        self.instructionTextEdit.setHtml(QCoreApplication.translate("ManualUITestingPage", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"    <html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"    p, li { white-space: pre-wrap; }\n"
"    </style></head><body>\n"
"    <p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Your action is required to complete manual testing:</span></p>\n"
"    <ol style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\">\n"
"    <li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The system has just generated a new <span style=\" font-weight:600;\">Manual UI Test Plan</span> for this sprint.</li>\n"
"    <li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Click the <span style=\" font-weight:600;\">'"
                        "Go to Documents Page'</span> button to view and download the <code>manual_ui_test_plan.docx</code> file.</li>\n"
"    <li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Execute the tests as described in the document, record the results, and save the file.</li>\n"
"    <li style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Return to this page and upload your completed results document below to finalize the sprint.</li></ol></body></html>", None))
        self.uploadLabel.setText(QCoreApplication.translate("ManualUITestingPage", u"<b>Upload Completed Test Plan Results:</b>", None))
        self.browseButton.setText(QCoreApplication.translate("ManualUITestingPage", u"Browse...", None))
        self.goToDocumentsButton.setText(QCoreApplication.translate("ManualUITestingPage", u"Go to Documents Page", None))
        self.processResultsButton.setText(QCoreApplication.translate("ManualUITestingPage", u"Process Test Results", None))
    # retranslateUi

