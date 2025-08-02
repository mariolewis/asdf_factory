# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'test_env_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QStackedWidget, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_TestEnvPage(object):
    def setupUi(self, TestEnvPage):
        if not TestEnvPage.objectName():
            TestEnvPage.setObjectName(u"TestEnvPage")
        TestEnvPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(TestEnvPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(TestEnvPage)
        self.headerLabel.setObjectName(u"headerLabel")
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(TestEnvPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(TestEnvPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.checklistPage = QWidget()
        self.checklistPage.setObjectName(u"checklistPage")
        self.verticalLayout_2 = QVBoxLayout(self.checklistPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.instructionLabel = QLabel(self.checklistPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.instructionLabel)

        self.taskGroupBox = QGroupBox(self.checklistPage)
        self.taskGroupBox.setObjectName(u"taskGroupBox")
        self.verticalLayout_3 = QVBoxLayout(self.taskGroupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.taskInstructionsTextEdit = QTextEdit(self.taskGroupBox)
        self.taskInstructionsTextEdit.setObjectName(u"taskInstructionsTextEdit")
        self.taskInstructionsTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.taskInstructionsTextEdit)

        self.helpTextEdit = QTextEdit(self.taskGroupBox)
        self.helpTextEdit.setObjectName(u"helpTextEdit")
        self.helpTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.helpTextEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.doneButton = QPushButton(self.taskGroupBox)
        self.doneButton.setObjectName(u"doneButton")

        self.horizontalLayout.addWidget(self.doneButton)

        self.helpButton = QPushButton(self.taskGroupBox)
        self.helpButton.setObjectName(u"helpButton")

        self.horizontalLayout.addWidget(self.helpButton)

        self.ignoreButton = QPushButton(self.taskGroupBox)
        self.ignoreButton.setObjectName(u"ignoreButton")

        self.horizontalLayout.addWidget(self.ignoreButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.verticalLayout_3.setStretch(0, 1)

        self.verticalLayout_2.addWidget(self.taskGroupBox)

        self.stackedWidget.addWidget(self.checklistPage)
        self.finalConfirmPage = QWidget()
        self.finalConfirmPage.setObjectName(u"finalConfirmPage")
        self.verticalLayout_4 = QVBoxLayout(self.finalConfirmPage)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.successLabel = QLabel(self.finalConfirmPage)
        self.successLabel.setObjectName(u"successLabel")
        self.successLabel.setStyleSheet(u"font-size: 14pt;")

        self.verticalLayout_4.addWidget(self.successLabel)

        self.finalInstructionLabel = QLabel(self.finalConfirmPage)
        self.finalInstructionLabel.setObjectName(u"finalInstructionLabel")
        self.finalInstructionLabel.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.finalInstructionLabel)

        self.testCommandLineEdit = QLineEdit(self.finalConfirmPage)
        self.testCommandLineEdit.setObjectName(u"testCommandLineEdit")

        self.verticalLayout_4.addWidget(self.testCommandLineEdit)

        self.finalizeButton = QPushButton(self.finalConfirmPage)
        self.finalizeButton.setObjectName(u"finalizeButton")

        self.verticalLayout_4.addWidget(self.finalizeButton)

        self.verticalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.stackedWidget.addWidget(self.finalConfirmPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(TestEnvPage)

        QMetaObject.connectSlotsByName(TestEnvPage)
    # setupUi

    def retranslateUi(self, TestEnvPage):
        TestEnvPage.setWindowTitle(QCoreApplication.translate("TestEnvPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("TestEnvPage", u"Test Environment Setup", None))
        self.instructionLabel.setText(QCoreApplication.translate("TestEnvPage", u"Please follow the steps below to set up the necessary testing frameworks for your project's technology stack.", None))
        self.taskGroupBox.setTitle(QCoreApplication.translate("TestEnvPage", u"Step X of Y: Task Name", None))
        self.doneButton.setText(QCoreApplication.translate("TestEnvPage", u"Done, Next Step", None))
        self.helpButton.setText(QCoreApplication.translate("TestEnvPage", u"I Need Help", None))
        self.ignoreButton.setText(QCoreApplication.translate("TestEnvPage", u"Ignore & Continue", None))
        self.successLabel.setText(QCoreApplication.translate("TestEnvPage", u"All setup steps have been actioned.", None))
        self.finalInstructionLabel.setText(QCoreApplication.translate("TestEnvPage", u"Please confirm the final command that should be used to run all automated tests for this project (e.g., 'pytest', 'mvn test').", None))
        self.finalizeButton.setText(QCoreApplication.translate("TestEnvPage", u"Finalize Test Environment Setup", None))
    # retranslateUi

