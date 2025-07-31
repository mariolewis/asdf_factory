# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'env_setup_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_EnvSetupPage(object):
    def setupUi(self, EnvSetupPage):
        if not EnvSetupPage.objectName():
            EnvSetupPage.setObjectName(u"EnvSetupPage")
        EnvSetupPage.resize(600, 400)
        self.verticalLayout = QVBoxLayout(EnvSetupPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(EnvSetupPage)
        self.headerLabel.setObjectName(u"headerLabel")
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(EnvSetupPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(EnvSetupPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.pathLabel = QLabel(EnvSetupPage)
        self.pathLabel.setObjectName(u"pathLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.pathLabel)

        self.projectPathLineEdit = QLineEdit(EnvSetupPage)
        self.projectPathLineEdit.setObjectName(u"projectPathLineEdit")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.projectPathLineEdit)


        self.verticalLayout.addLayout(self.formLayout)

        self.confirmPathButton = QPushButton(EnvSetupPage)
        self.confirmPathButton.setObjectName(u"confirmPathButton")

        self.verticalLayout.addWidget(self.confirmPathButton)

        self.gitLabel = QLabel(EnvSetupPage)
        self.gitLabel.setObjectName(u"gitLabel")
        self.gitLabel.setStyleSheet(u"color: orange;")

        self.verticalLayout.addWidget(self.gitLabel)

        self.initGitButton = QPushButton(EnvSetupPage)
        self.initGitButton.setObjectName(u"initGitButton")

        self.verticalLayout.addWidget(self.initGitButton)

        self.proceedButton = QPushButton(EnvSetupPage)
        self.proceedButton.setObjectName(u"proceedButton")

        self.verticalLayout.addWidget(self.proceedButton)

        self.bottomVerticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.bottomVerticalSpacer)


        self.retranslateUi(EnvSetupPage)

        QMetaObject.connectSlotsByName(EnvSetupPage)
    # setupUi

    def retranslateUi(self, EnvSetupPage):
        EnvSetupPage.setWindowTitle(QCoreApplication.translate("EnvSetupPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("EnvSetupPage", u"New Application Setup", None))
        self.instructionLabel.setText(QCoreApplication.translate("EnvSetupPage", u"Define the root folder and initialize a Git repository for the new target application.", None))
        self.pathLabel.setText(QCoreApplication.translate("EnvSetupPage", u"Target Project Root Folder:", None))
        self.confirmPathButton.setText(QCoreApplication.translate("EnvSetupPage", u"Confirm Project Folder", None))
        self.gitLabel.setText(QCoreApplication.translate("EnvSetupPage", u"Git repository not initialized.", None))
        self.initGitButton.setText(QCoreApplication.translate("EnvSetupPage", u"Initialize Git Repository", None))
        self.proceedButton.setText(QCoreApplication.translate("EnvSetupPage", u"Confirm Setup & Proceed to Specification", None))
    # retranslateUi

