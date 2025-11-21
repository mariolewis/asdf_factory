# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'new_project_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_NewProjectDialog(object):
    def setupUi(self, NewProjectDialog):
        if not NewProjectDialog.objectName():
            NewProjectDialog.setObjectName(u"NewProjectDialog")
        NewProjectDialog.resize(650, 300)
        NewProjectDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(NewProjectDialog)
        self.verticalLayout.setSpacing(16)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(NewProjectDialog)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.instructionLabel = QLabel(NewProjectDialog)
        self.instructionLabel.setObjectName(u"instructionLabel")

        self.verticalLayout.addWidget(self.instructionLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(24)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.greenfieldCard = QGroupBox(NewProjectDialog)
        self.greenfieldCard.setObjectName(u"greenfieldCard")
        self.verticalLayout_2 = QVBoxLayout(self.greenfieldCard)
        self.verticalLayout_2.setSpacing(16)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.greenfieldTitleLabel = QLabel(self.greenfieldCard)
        self.greenfieldTitleLabel.setObjectName(u"greenfieldTitleLabel")

        self.verticalLayout_2.addWidget(self.greenfieldTitleLabel)

        self.greenfieldDescLabel = QLabel(self.greenfieldCard)
        self.greenfieldDescLabel.setObjectName(u"greenfieldDescLabel")
        self.greenfieldDescLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.greenfieldDescLabel)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.createGreenfieldButton = QPushButton(self.greenfieldCard)
        self.createGreenfieldButton.setObjectName(u"createGreenfieldButton")

        self.horizontalLayout_2.addWidget(self.createGreenfieldButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)


        self.horizontalLayout.addWidget(self.greenfieldCard)

        self.brownfieldCard = QGroupBox(NewProjectDialog)
        self.brownfieldCard.setObjectName(u"brownfieldCard")
        self.verticalLayout_3 = QVBoxLayout(self.brownfieldCard)
        self.verticalLayout_3.setSpacing(16)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.brownfieldTitleLabel = QLabel(self.brownfieldCard)
        self.brownfieldTitleLabel.setObjectName(u"brownfieldTitleLabel")

        self.verticalLayout_3.addWidget(self.brownfieldTitleLabel)

        self.brownfieldDescLabel = QLabel(self.brownfieldCard)
        self.brownfieldDescLabel.setObjectName(u"brownfieldDescLabel")
        self.brownfieldDescLabel.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.brownfieldDescLabel)

        self.verticalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.onboardBrownfieldButton = QPushButton(self.brownfieldCard)
        self.onboardBrownfieldButton.setObjectName(u"onboardBrownfieldButton")

        self.horizontalLayout_3.addWidget(self.onboardBrownfieldButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)


        self.horizontalLayout.addWidget(self.brownfieldCard)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(NewProjectDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel)
        self.buttonBox.setCenterButtons(False)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(NewProjectDialog)

        QMetaObject.connectSlotsByName(NewProjectDialog)
    # setupUi

    def retranslateUi(self, NewProjectDialog):
        NewProjectDialog.setWindowTitle(QCoreApplication.translate("NewProjectDialog", u"Create New Project", None))
        self.headerLabel.setText(QCoreApplication.translate("NewProjectDialog", u"Create New Project", None))
        self.instructionLabel.setText(QCoreApplication.translate("NewProjectDialog", u"Choose a workflow to begin your project.", None))
        self.greenfieldCard.setTitle("")
        self.greenfieldTitleLabel.setText(QCoreApplication.translate("NewProjectDialog", u"Develop New Application", None))
        self.greenfieldDescLabel.setText(QCoreApplication.translate("NewProjectDialog", u"Create a new software application from a textual brief or specification document.", None))
        self.createGreenfieldButton.setText(QCoreApplication.translate("NewProjectDialog", u"Create...", None))
        self.brownfieldCard.setTitle("")
        self.brownfieldTitleLabel.setText(QCoreApplication.translate("NewProjectDialog", u"Maintain Existing Application", None))
        self.brownfieldDescLabel.setText(QCoreApplication.translate("NewProjectDialog", u"Analyze an existing local codebase to reverse-engineer specifications and create a backlog.", None))
        self.onboardBrownfieldButton.setText(QCoreApplication.translate("NewProjectDialog", u"Onboard...", None))
    # retranslateUi

