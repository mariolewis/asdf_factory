# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'build_script_page.ui'
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
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_BuildScriptPage(object):
    def setupUi(self, BuildScriptPage):
        if not BuildScriptPage.objectName():
            BuildScriptPage.setObjectName(u"BuildScriptPage")
        BuildScriptPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(BuildScriptPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(BuildScriptPage)
        self.headerLabel.setObjectName(u"headerLabel")
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(BuildScriptPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(BuildScriptPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.autoGenerateButton = QPushButton(BuildScriptPage)
        self.autoGenerateButton.setObjectName(u"autoGenerateButton")

        self.horizontalLayout.addWidget(self.autoGenerateButton)

        self.manualCreateButton = QPushButton(BuildScriptPage)
        self.manualCreateButton.setObjectName(u"manualCreateButton")

        self.horizontalLayout.addWidget(self.manualCreateButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(BuildScriptPage)

        QMetaObject.connectSlotsByName(BuildScriptPage)
    # setupUi

    def retranslateUi(self, BuildScriptPage):
        BuildScriptPage.setWindowTitle(QCoreApplication.translate("BuildScriptPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("BuildScriptPage", u"Build Script Generation", None))
        self.instructionLabel.setText(QCoreApplication.translate("BuildScriptPage", u"The technical specification is complete. Now, let's establish the build script for the project. This script (e.g., requirements.txt, pom.xml) manages project dependencies and how the application is built.", None))
        self.autoGenerateButton.setText(QCoreApplication.translate("BuildScriptPage", u"Auto-Generate Build Script", None))
        self.manualCreateButton.setText(QCoreApplication.translate("BuildScriptPage", u"I Will Create It Manually", None))
    # retranslateUi

