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
    QGroupBox, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_NewProjectDialog(object):
    def setupUi(self, NewProjectDialog):
        if not NewProjectDialog.objectName():
            NewProjectDialog.setObjectName(u"NewProjectDialog")
        NewProjectDialog.resize(450, 200)
        NewProjectDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(NewProjectDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.instructionLabel = QLabel(NewProjectDialog)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.groupBox = QGroupBox(NewProjectDialog)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.fromSpecButton = QPushButton(self.groupBox)
        self.fromSpecButton.setObjectName(u"fromSpecButton")

        self.verticalLayout_2.addWidget(self.fromSpecButton)

        self.fromCodebaseButton = QPushButton(self.groupBox)
        self.fromCodebaseButton.setObjectName(u"fromCodebaseButton")

        self.verticalLayout_2.addWidget(self.fromCodebaseButton)


        self.verticalLayout.addWidget(self.groupBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(NewProjectDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(NewProjectDialog)
        self.buttonBox.accepted.connect(NewProjectDialog.accept)
        self.buttonBox.rejected.connect(NewProjectDialog.reject)

        QMetaObject.connectSlotsByName(NewProjectDialog)
    # setupUi

    def retranslateUi(self, NewProjectDialog):
        NewProjectDialog.setWindowTitle(QCoreApplication.translate("NewProjectDialog", u"Create New Project", None))
        self.instructionLabel.setText(QCoreApplication.translate("NewProjectDialog", u"How would you like to start this project?", None))
        self.groupBox.setTitle("")
        self.fromSpecButton.setText(QCoreApplication.translate("NewProjectDialog", u"From a New Specification or Project Brief", None))
        self.fromCodebaseButton.setText(QCoreApplication.translate("NewProjectDialog", u"Work with an existing Application Codebase", None))
    # retranslateUi

