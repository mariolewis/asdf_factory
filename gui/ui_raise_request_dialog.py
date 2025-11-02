# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'raise_request_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QLabel, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget)

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

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        self.typeLabel = QLabel(RaiseRequestDialog)
        self.typeLabel.setObjectName(u"typeLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.typeLabel)

        self.typeComboBox = QComboBox(RaiseRequestDialog)
        self.typeComboBox.addItem("")
        self.typeComboBox.addItem("")
        self.typeComboBox.addItem("")
        self.typeComboBox.addItem("")
        self.typeComboBox.addItem("")
        self.typeComboBox.setObjectName(u"typeComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.typeComboBox)

        self.parentLabel = QLabel(RaiseRequestDialog)
        self.parentLabel.setObjectName(u"parentLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.parentLabel)

        self.parentComboBox = QComboBox(RaiseRequestDialog)
        self.parentComboBox.setObjectName(u"parentComboBox")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.parentComboBox)

        self.descriptionLabel = QLabel(RaiseRequestDialog)
        self.descriptionLabel.setObjectName(u"descriptionLabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.descriptionLabel)

        self.descriptionTextEdit = QTextEdit(RaiseRequestDialog)
        self.descriptionTextEdit.setObjectName(u"descriptionTextEdit")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.descriptionTextEdit)

        self.priorityLabel = QLabel(RaiseRequestDialog)
        self.priorityLabel.setObjectName(u"priorityLabel")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.priorityLabel)

        self.priorityComboBox = QComboBox(RaiseRequestDialog)
        self.priorityComboBox.addItem("")
        self.priorityComboBox.addItem("")
        self.priorityComboBox.addItem("")
        self.priorityComboBox.setObjectName(u"priorityComboBox")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.priorityComboBox)

        self.complexityLabel = QLabel(RaiseRequestDialog)
        self.complexityLabel.setObjectName(u"complexityLabel")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.complexityLabel)

        self.complexityComboBox = QComboBox(RaiseRequestDialog)
        self.complexityComboBox.addItem("")
        self.complexityComboBox.addItem("")
        self.complexityComboBox.addItem("")
        self.complexityComboBox.setObjectName(u"complexityComboBox")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.complexityComboBox)


        self.verticalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(RaiseRequestDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(RaiseRequestDialog)

        QMetaObject.connectSlotsByName(RaiseRequestDialog)
    # setupUi

    def retranslateUi(self, RaiseRequestDialog):
        RaiseRequestDialog.setWindowTitle(QCoreApplication.translate("RaiseRequestDialog", u"Add New Backlog Item", None))
        self.headerLabel.setText(QCoreApplication.translate("RaiseRequestDialog", u"Add New Backlog Item", None))
        self.typeLabel.setText(QCoreApplication.translate("RaiseRequestDialog", u"Request Type:", None))
        self.typeComboBox.setItemText(0, QCoreApplication.translate("RaiseRequestDialog", u"Backlog Item", None))
        self.typeComboBox.setItemText(1, QCoreApplication.translate("RaiseRequestDialog", u"Change Request", None))
        self.typeComboBox.setItemText(2, QCoreApplication.translate("RaiseRequestDialog", u"Bug Report", None))
        self.typeComboBox.setItemText(3, QCoreApplication.translate("RaiseRequestDialog", u"Feature", None))
        self.typeComboBox.setItemText(4, QCoreApplication.translate("RaiseRequestDialog", u"Epic", None))

        self.parentLabel.setText(QCoreApplication.translate("RaiseRequestDialog", u"Parent:", None))
        self.descriptionLabel.setText(QCoreApplication.translate("RaiseRequestDialog", u"Description:", None))
        self.priorityLabel.setText(QCoreApplication.translate("RaiseRequestDialog", u"Priority:", None))
        self.priorityComboBox.setItemText(0, QCoreApplication.translate("RaiseRequestDialog", u"Low", None))
        self.priorityComboBox.setItemText(1, QCoreApplication.translate("RaiseRequestDialog", u"Medium", None))
        self.priorityComboBox.setItemText(2, QCoreApplication.translate("RaiseRequestDialog", u"High", None))

        self.complexityLabel.setText(QCoreApplication.translate("RaiseRequestDialog", u"Complexity:", None))
        self.complexityComboBox.setItemText(0, QCoreApplication.translate("RaiseRequestDialog", u"Small", None))
        self.complexityComboBox.setItemText(1, QCoreApplication.translate("RaiseRequestDialog", u"Medium", None))
        self.complexityComboBox.setItemText(2, QCoreApplication.translate("RaiseRequestDialog", u"Large", None))

    # retranslateUi

