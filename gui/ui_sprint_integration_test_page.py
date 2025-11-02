# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sprint_integration_test_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_SprintIntegrationTestPage(object):
    def setupUi(self, SprintIntegrationTestPage):
        if not SprintIntegrationTestPage.objectName():
            SprintIntegrationTestPage.setObjectName(u"SprintIntegrationTestPage")
        SprintIntegrationTestPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(SprintIntegrationTestPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(SprintIntegrationTestPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(SprintIntegrationTestPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(SprintIntegrationTestPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.detailsGroupBox = QGroupBox(SprintIntegrationTestPage)
        self.detailsGroupBox.setObjectName(u"detailsGroupBox")
        self.formLayout = QFormLayout(self.detailsGroupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.filePathLabel = QLabel(self.detailsGroupBox)
        self.filePathLabel.setObjectName(u"filePathLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.filePathLabel)

        self.filePathLineEdit = QLineEdit(self.detailsGroupBox)
        self.filePathLineEdit.setObjectName(u"filePathLineEdit")
        self.filePathLineEdit.setReadOnly(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.filePathLineEdit)

        self.commandLabel = QLabel(self.detailsGroupBox)
        self.commandLabel.setObjectName(u"commandLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.commandLabel)

        self.commandLineEdit = QLineEdit(self.detailsGroupBox)
        self.commandLineEdit.setObjectName(u"commandLineEdit")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.commandLineEdit)


        self.verticalLayout.addWidget(self.detailsGroupBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pauseButton = QPushButton(SprintIntegrationTestPage)
        self.pauseButton.setObjectName(u"pauseButton")

        self.horizontalLayout.addWidget(self.pauseButton)

        self.skipButton = QPushButton(SprintIntegrationTestPage)
        self.skipButton.setObjectName(u"skipButton")

        self.horizontalLayout.addWidget(self.skipButton)

        self.runButton = QPushButton(SprintIntegrationTestPage)
        self.runButton.setObjectName(u"runButton")

        self.horizontalLayout.addWidget(self.runButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(SprintIntegrationTestPage)

        QMetaObject.connectSlotsByName(SprintIntegrationTestPage)
    # setupUi

    def retranslateUi(self, SprintIntegrationTestPage):
        SprintIntegrationTestPage.setWindowTitle(QCoreApplication.translate("SprintIntegrationTestPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("SprintIntegrationTestPage", u"Sprint Integration Test", None))
        self.instructionLabel.setText(QCoreApplication.translate("SprintIntegrationTestPage", u"The system has generated a temporary integration test script for this sprint's components. Please review the proposed command and choose how to proceed.", None))
        self.detailsGroupBox.setTitle("")
        self.filePathLabel.setText(QCoreApplication.translate("SprintIntegrationTestPage", u"Generated Test File:", None))
        self.commandLabel.setText(QCoreApplication.translate("SprintIntegrationTestPage", u"Suggested Command:", None))
        self.pauseButton.setText(QCoreApplication.translate("SprintIntegrationTestPage", u"Pause for Manual Fix", None))
        self.skipButton.setText(QCoreApplication.translate("SprintIntegrationTestPage", u"Skip Integration Test", None))
        self.runButton.setText(QCoreApplication.translate("SprintIntegrationTestPage", u"Run Test", None))
    # retranslateUi

