# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'codebase_analysis_page.ui'
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
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_CodebaseAnalysisPage(object):
    def setupUi(self, CodebaseAnalysisPage):
        if not CodebaseAnalysisPage.objectName():
            CodebaseAnalysisPage.setObjectName(u"CodebaseAnalysisPage")
        CodebaseAnalysisPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(CodebaseAnalysisPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(CodebaseAnalysisPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(CodebaseAnalysisPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.statusLabel = QLabel(CodebaseAnalysisPage)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.statusLabel)

        self.progressBar = QProgressBar(CodebaseAnalysisPage)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        self.verticalLayout.addWidget(self.progressBar)

        self.logOutputTextEdit = QTextEdit(CodebaseAnalysisPage)
        self.logOutputTextEdit.setObjectName(u"logOutputTextEdit")
        self.logOutputTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.logOutputTextEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.cancelButton = QPushButton(CodebaseAnalysisPage)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)

        self.pauseButton = QPushButton(CodebaseAnalysisPage)
        self.pauseButton.setObjectName(u"pauseButton")

        self.horizontalLayout.addWidget(self.pauseButton)

        self.resumeButton = QPushButton(CodebaseAnalysisPage)
        self.resumeButton.setObjectName(u"resumeButton")

        self.horizontalLayout.addWidget(self.resumeButton)

        self.continueButton = QPushButton(CodebaseAnalysisPage)
        self.continueButton.setObjectName(u"continueButton")

        self.horizontalLayout.addWidget(self.continueButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(CodebaseAnalysisPage)

        QMetaObject.connectSlotsByName(CodebaseAnalysisPage)
    # setupUi

    def retranslateUi(self, CodebaseAnalysisPage):
        CodebaseAnalysisPage.setWindowTitle(QCoreApplication.translate("CodebaseAnalysisPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("CodebaseAnalysisPage", u"Project Archeology: Analyzing Codebase", None))
        self.statusLabel.setText(QCoreApplication.translate("CodebaseAnalysisPage", u"Status: Initializing scan...", None))
        self.cancelButton.setText(QCoreApplication.translate("CodebaseAnalysisPage", u"Cancel Analysis", None))
        self.pauseButton.setText(QCoreApplication.translate("CodebaseAnalysisPage", u"Pause", None))
        self.resumeButton.setText(QCoreApplication.translate("CodebaseAnalysisPage", u"Resume", None))
        self.continueButton.setText(QCoreApplication.translate("CodebaseAnalysisPage", u"Continue", None))
    # retranslateUi

