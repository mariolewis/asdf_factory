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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

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

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.confirmPathButton = QPushButton(EnvSetupPage)
        self.confirmPathButton.setObjectName(u"confirmPathButton")

        self.horizontalLayout_2.addWidget(self.confirmPathButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.vcsLine = QFrame(EnvSetupPage)
        self.vcsLine.setObjectName(u"vcsLine")
        self.vcsLine.setFrameShape(QFrame.Shape.HLine)
        self.vcsLine.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.vcsLine)

        self.vcsChoiceWidget = QWidget(EnvSetupPage)
        self.vcsChoiceWidget.setObjectName(u"vcsChoiceWidget")
        self.verticalLayout_2 = QVBoxLayout(self.vcsChoiceWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.vcsInstructionLabel = QLabel(self.vcsChoiceWidget)
        self.vcsInstructionLabel.setObjectName(u"vcsInstructionLabel")

        self.verticalLayout_2.addWidget(self.vcsInstructionLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.localWorkspaceButton = QPushButton(self.vcsChoiceWidget)
        self.localWorkspaceButton.setObjectName(u"localWorkspaceButton")

        self.horizontalLayout.addWidget(self.localWorkspaceButton)

        self.initGitButton = QPushButton(self.vcsChoiceWidget)
        self.initGitButton.setObjectName(u"initGitButton")

        self.horizontalLayout.addWidget(self.initGitButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout.addWidget(self.vcsChoiceWidget)

        self.bottomVerticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.bottomVerticalSpacer)


        self.retranslateUi(EnvSetupPage)

        QMetaObject.connectSlotsByName(EnvSetupPage)
    # setupUi

    def retranslateUi(self, EnvSetupPage):
        EnvSetupPage.setWindowTitle(QCoreApplication.translate("EnvSetupPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("EnvSetupPage", u"New Application Setup", None))
        self.instructionLabel.setText(QCoreApplication.translate("EnvSetupPage", u"Define the root folder for the new target application.", None))
        self.pathLabel.setText(QCoreApplication.translate("EnvSetupPage", u"Target Project Root Folder:", None))
        self.confirmPathButton.setText(QCoreApplication.translate("EnvSetupPage", u"Confirm Project Folder", None))
        self.vcsInstructionLabel.setText(QCoreApplication.translate("EnvSetupPage", u"Next, choose how to manage your project's source code.", None))
        self.localWorkspaceButton.setText(QCoreApplication.translate("EnvSetupPage", u"Use Local Workspace && Proceed", None))
        self.initGitButton.setText(QCoreApplication.translate("EnvSetupPage", u"Initialize Git Repository && Proceed", None))
    # retranslateUi

