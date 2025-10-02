# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'new_project_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_NewProjectDialog(object):
    def setupUi(self, NewProjectDialog):
        if not NewProjectDialog.objectName():
            NewProjectDialog.setObjectName(u"NewProjectDialog")
        NewProjectDialog.resize(400, 200)
        NewProjectDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(NewProjectDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.instructionLabel = QLabel(NewProjectDialog)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.fromSpecButton = QPushButton(NewProjectDialog)
        self.fromSpecButton.setObjectName(u"fromSpecButton")

        self.horizontalLayout.addWidget(self.fromSpecButton)

        self.fromCodebaseButton = QPushButton(NewProjectDialog)
        self.fromCodebaseButton.setObjectName(u"fromCodebaseButton")

        self.horizontalLayout.addWidget(self.fromCodebaseButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.buttonBox = QDialogButtonBox(NewProjectDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel)
        self.buttonBox.setCenterButtons(True)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(NewProjectDialog)

        QMetaObject.connectSlotsByName(NewProjectDialog)
    # setupUi

    def retranslateUi(self, NewProjectDialog):
        NewProjectDialog.setWindowTitle(QCoreApplication.translate("NewProjectDialog", u"Create New Project", None))
        self.instructionLabel.setText(QCoreApplication.translate("NewProjectDialog", u"How would you like to create the new project?", None))
        self.fromSpecButton.setText(QCoreApplication.translate("NewProjectDialog", u"Create from a New Specification", None))
        self.fromCodebaseButton.setText(QCoreApplication.translate("NewProjectDialog", u"Work with an Existing Codebase", None))
    # retranslateUi

