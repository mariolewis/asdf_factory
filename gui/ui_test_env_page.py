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
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

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

        self.startButton = QPushButton(self.standbyPage)
        self.startButton.setObjectName(u"startButton")

        self.verticalLayout_2.addWidget(self.startButton)

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

        self.finalizeButton = QPushButton(self.finalizePage)
        self.finalizeButton.setObjectName(u"finalizeButton")

        self.verticalLayout_4.addWidget(self.finalizeButton)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_2)

        self.stackedWidget.addWidget(self.finalizePage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(TestEnvPage)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(TestEnvPage)
    # setupUi

    def retranslateUi(self, TestEnvPage):
        TestEnvPage.setWindowTitle(QCoreApplication.translate("TestEnvPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("TestEnvPage", u"Test Environment Setup", None))
        self.standbyLabel.setText(QCoreApplication.translate("TestEnvPage", u"The system will now analyze the project's Technical Specification to generate a step-by-step guide for setting up the required testing environment.\n"
"\n"
"Click 'Start Analysis' to proceed.", None))
        self.startButton.setText(QCoreApplication.translate("TestEnvPage", u"Start Analysis", None))
        self.checklistHeaderLabel.setText(QCoreApplication.translate("TestEnvPage", u"Please follow the steps below to set up the testing environment:", None))
        self.doneButton.setText(QCoreApplication.translate("TestEnvPage", u"Done, Next Step", None))
        self.helpButton.setText(QCoreApplication.translate("TestEnvPage", u"I Need Help", None))
        self.ignoreButton.setText(QCoreApplication.translate("TestEnvPage", u"Ignore & Continue", None))
        self.finalizeLabel.setText(QCoreApplication.translate("TestEnvPage", u"All setup steps have been actioned.\n"
"\n"
"Please confirm the final command that should be used to run all automated tests for this project (e.g., 'pytest', 'mvn test').", None))
        self.finalizeButton.setText(QCoreApplication.translate("TestEnvPage", u"Finalize Test Environment Setup", None))
    # retranslateUi

