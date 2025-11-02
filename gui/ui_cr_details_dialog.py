# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cr_details_dialog.ui'
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
    QLabel, QSizePolicy, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_CRDetailsDialog(object):
    def setupUi(self, CRDetailsDialog):
        if not CRDetailsDialog.objectName():
            CRDetailsDialog.setObjectName(u"CRDetailsDialog")
        CRDetailsDialog.resize(600, 450)
        CRDetailsDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(CRDetailsDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(CRDetailsDialog)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.detailsTextEdit = QTextEdit(CRDetailsDialog)
        self.detailsTextEdit.setObjectName(u"detailsTextEdit")
        self.detailsTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.detailsTextEdit)

        self.buttonBox = QDialogButtonBox(CRDetailsDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(CRDetailsDialog)

        QMetaObject.connectSlotsByName(CRDetailsDialog)
    # setupUi

    def retranslateUi(self, CRDetailsDialog):
        CRDetailsDialog.setWindowTitle(QCoreApplication.translate("CRDetailsDialog", u"Request Details", None))
        self.headerLabel.setText(QCoreApplication.translate("CRDetailsDialog", u"CR-ID: Type", None))
    # retranslateUi

