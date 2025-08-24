# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'raise_request_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QRadioButton, QSizePolicy, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_RaiseRequestDialog(object):
    def setupUi(self, RaiseRequestDialog):
        if not RaiseRequestDialog.objectName():
            RaiseRequestDialog.setObjectName(u"RaiseRequestDialog")
        RaiseRequestDialog.resize(500, 400)
        RaiseRequestDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(RaiseRequestDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(RaiseRequestDialog)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.typeGroupBox = QGroupBox(RaiseRequestDialog)
        self.typeGroupBox.setObjectName(u"typeGroupBox")
        self.horizontalLayout = QHBoxLayout(self.typeGroupBox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.crRadioButton = QRadioButton(self.typeGroupBox)
        self.crRadioButton.setObjectName(u"crRadioButton")
        self.crRadioButton.setChecked(True)

        self.horizontalLayout.addWidget(self.crRadioButton)

        self.bugRadioButton = QRadioButton(self.typeGroupBox)
        self.bugRadioButton.setObjectName(u"bugRadioButton")

        self.horizontalLayout.addWidget(self.bugRadioButton)


        self.verticalLayout.addWidget(self.typeGroupBox)

        self.descriptionLabel = QLabel(RaiseRequestDialog)
        self.descriptionLabel.setObjectName(u"descriptionLabel")

        self.verticalLayout.addWidget(self.descriptionLabel)

        self.descriptionTextEdit = QTextEdit(RaiseRequestDialog)
        self.descriptionTextEdit.setObjectName(u"descriptionTextEdit")

        self.verticalLayout.addWidget(self.descriptionTextEdit)

        self.severityWidget = QWidget(RaiseRequestDialog)
        self.severityWidget.setObjectName(u"severityWidget")
        self.formLayout = QFormLayout(self.severityWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.severityLabel = QLabel(self.severityWidget)
        self.severityLabel.setObjectName(u"severityLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.severityLabel)

        self.severityComboBox = QComboBox(self.severityWidget)
        self.severityComboBox.addItem("")
        self.severityComboBox.addItem("")
        self.severityComboBox.addItem("")
        self.severityComboBox.setObjectName(u"severityComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.severityComboBox)


        self.verticalLayout.addWidget(self.severityWidget)

        self.buttonBox = QDialogButtonBox(RaiseRequestDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(RaiseRequestDialog)

        QMetaObject.connectSlotsByName(RaiseRequestDialog)
    # setupUi

    def retranslateUi(self, RaiseRequestDialog):
        RaiseRequestDialog.setWindowTitle(QCoreApplication.translate("RaiseRequestDialog", u"Create New Request", None))
        self.headerLabel.setText(QCoreApplication.translate("RaiseRequestDialog", u"Create New Request", None))
        self.typeGroupBox.setTitle(QCoreApplication.translate("RaiseRequestDialog", u"Request Type", None))
        self.crRadioButton.setText(QCoreApplication.translate("RaiseRequestDialog", u"Change Request", None))
        self.bugRadioButton.setText(QCoreApplication.translate("RaiseRequestDialog", u"Bug Report", None))
        self.descriptionLabel.setText(QCoreApplication.translate("RaiseRequestDialog", u"Description:", None))
        self.severityLabel.setText(QCoreApplication.translate("RaiseRequestDialog", u"Severity:", None))
        self.severityComboBox.setItemText(0, QCoreApplication.translate("RaiseRequestDialog", u"Minor", None))
        self.severityComboBox.setItemText(1, QCoreApplication.translate("RaiseRequestDialog", u"Medium", None))
        self.severityComboBox.setItemText(2, QCoreApplication.translate("RaiseRequestDialog", u"Major", None))

    # retranslateUi

