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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QVBoxLayout, QWidget)

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

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(TestEnvPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(TestEnvPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.standbyPage = QWidget()
        self.standbyPage.setObjectName(u"standbyPage")
        self.verticalLayout_2 = QVBoxLayout(self.standbyPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.standbyLabel = QLabel(self.standbyPage)
        self.standbyLabel.setObjectName(u"standbyLabel")
        self.standbyLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.standbyLabel)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.startButton = QPushButton(self.standbyPage)
        self.startButton.setObjectName(u"startButton")

        self.horizontalLayout_2.addWidget(self.startButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.stackedWidget.addWidget(self.standbyPage)
        self.checklistPage = QWidget()
        self.checklistPage.setObjectName(u"checklistPage")
        self.verticalLayout_3 = QVBoxLayout(self.checklistPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.checklistHeaderLabel = QLabel(self.checklistPage)
        self.checklistHeaderLabel.setObjectName(u"checklistHeaderLabel")

        self.verticalLayout_3.addWidget(self.checklistHeaderLabel)

        self.stepsStackedWidget = QStackedWidget(self.checklistPage)
        self.stepsStackedWidget.setObjectName(u"stepsStackedWidget")

        self.verticalLayout_3.addWidget(self.stepsStackedWidget)

        self.line_2 = QFrame(self.checklistPage)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.line_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.doneButton = QPushButton(self.checklistPage)
        self.doneButton.setObjectName(u"doneButton")

        self.horizontalLayout.addWidget(self.doneButton)

        self.helpButton = QPushButton(self.checklistPage)
        self.helpButton.setObjectName(u"helpButton")

        self.horizontalLayout.addWidget(self.helpButton)

        self.ignoreButton = QPushButton(self.checklistPage)
        self.ignoreButton.setObjectName(u"ignoreButton")

        self.horizontalLayout.addWidget(self.ignoreButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.stackedWidget.addWidget(self.checklistPage)
        self.finalizePage = QWidget()
        self.finalizePage.setObjectName(u"finalizePage")
        self.verticalLayout_4 = QVBoxLayout(self.finalizePage)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.finalizeLabel = QLabel(self.finalizePage)
        self.finalizeLabel.setObjectName(u"finalizeLabel")
        self.finalizeLabel.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.finalizeLabel)

        self.testCommandLineEdit = QLineEdit(self.finalizePage)
        self.testCommandLineEdit.setObjectName(u"testCommandLineEdit")

        self.verticalLayout_4.addWidget(self.testCommandLineEdit)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.finalizeButton = QPushButton(self.finalizePage)
        self.finalizeButton.setObjectName(u"finalizeButton")

        self.horizontalLayout_3.addWidget(self.finalizeButton)


        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.stackedWidget.addWidget(self.finalizePage)
        self.manualBuildScriptPage = QWidget()
        self.manualBuildScriptPage.setObjectName(u"manualBuildScriptPage")
        self.verticalLayout_5 = QVBoxLayout(self.manualBuildScriptPage)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.manualBuildScriptLabel = QLabel(self.manualBuildScriptPage)
        self.manualBuildScriptLabel.setObjectName(u"manualBuildScriptLabel")
        self.manualBuildScriptLabel.setWordWrap(True)

        self.verticalLayout_5.addWidget(self.manualBuildScriptLabel)

        self.manualBuildScriptLineEdit = QLineEdit(self.manualBuildScriptPage)
        self.manualBuildScriptLineEdit.setObjectName(u"manualBuildScriptLineEdit")

        self.verticalLayout_5.addWidget(self.manualBuildScriptLineEdit)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)

        self.confirmBuildScriptButton = QPushButton(self.manualBuildScriptPage)
        self.confirmBuildScriptButton.setObjectName(u"confirmBuildScriptButton")

        self.horizontalLayout_5.addWidget(self.confirmBuildScriptButton)


        self.verticalLayout_5.addLayout(self.horizontalLayout_5)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)

        self.stackedWidget.addWidget(self.manualBuildScriptPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(TestEnvPage)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(TestEnvPage)
    # setupUi

    def retranslateUi(self, TestEnvPage):
        TestEnvPage.setWindowTitle(QCoreApplication.translate("TestEnvPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("TestEnvPage", u"Test Environment Setup", None))
        self.standbyLabel.setText(QCoreApplication.translate("TestEnvPage", u"This step generates a setup guide for the project's testing environment based on the technical specification. Click 'Start Analysis' to begin.", None))
        self.startButton.setText(QCoreApplication.translate("TestEnvPage", u"Start Analysis", None))
        self.checklistHeaderLabel.setText(QCoreApplication.translate("TestEnvPage", u"Please follow the steps below to set up the testing environment:", None))
        self.doneButton.setText(QCoreApplication.translate("TestEnvPage", u"Done, Next Step", None))
        self.helpButton.setText(QCoreApplication.translate("TestEnvPage", u"I Need Help", None))
        self.ignoreButton.setText(QCoreApplication.translate("TestEnvPage", u"Ignore & Continue", None))
        self.finalizeLabel.setText(QCoreApplication.translate("TestEnvPage", u"All setup steps have been actioned.\n"
"\n"
"Please confirm the final command that should be used to run all automated tests for this project (e.g., 'pytest', 'mvn test').", None))
        self.finalizeButton.setText(QCoreApplication.translate("TestEnvPage", u"Finalize Test Environment Setup", None))
        self.manualBuildScriptLabel.setText(QCoreApplication.translate("TestEnvPage", u"<b>Action Required</b><br>You previously chose to create the build script manually. Please enter the exact filename of the script you created (e.g., requirements.txt, build.gradle). This is required for the test environment setup.", None))
        self.confirmBuildScriptButton.setText(QCoreApplication.translate("TestEnvPage", u"Confirm Filename and Continue", None))
    # retranslateUi

