# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'legal_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget)

class Ui_LegalDialog(object):
    def setupUi(self, LegalDialog):
        if not LegalDialog.objectName():
            LegalDialog.setObjectName(u"LegalDialog")
        LegalDialog.resize(700, 600)
        LegalDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(LegalDialog)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(LegalDialog)
        self.headerLabel.setObjectName(u"headerLabel")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.headerLabel.setFont(font)
        self.headerLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.headerLabel)

        self.instructionLabel = QLabel(LegalDialog)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.tabWidget = QTabWidget(LegalDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.eulaTab = QWidget()
        self.eulaTab.setObjectName(u"eulaTab")
        self.verticalLayout_2 = QVBoxLayout(self.eulaTab)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.eulaTextEdit = QTextEdit(self.eulaTab)
        self.eulaTextEdit.setObjectName(u"eulaTextEdit")
        self.eulaTextEdit.setReadOnly(True)

        self.verticalLayout_2.addWidget(self.eulaTextEdit)

        self.tabWidget.addTab(self.eulaTab, "")
        self.privacyTab = QWidget()
        self.privacyTab.setObjectName(u"privacyTab")
        self.verticalLayout_3 = QVBoxLayout(self.privacyTab)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.privacyTextEdit = QTextEdit(self.privacyTab)
        self.privacyTextEdit.setObjectName(u"privacyTextEdit")
        self.privacyTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.privacyTextEdit)

        self.tabWidget.addTab(self.privacyTab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.validationLabel = QLabel(LegalDialog)
        self.validationLabel.setObjectName(u"validationLabel")
        font1 = QFont()
        font1.setItalic(True)
        self.validationLabel.setFont(font1)
        self.validationLabel.setStyleSheet(u"color: #FFC66D;")
        self.validationLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.validationLabel)

        self.consentCheckBox = QCheckBox(LegalDialog)
        self.consentCheckBox.setObjectName(u"consentCheckBox")
        self.consentCheckBox.setEnabled(False)
        font2 = QFont()
        font2.setBold(True)
        self.consentCheckBox.setFont(font2)

        self.verticalLayout.addWidget(self.consentCheckBox)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.exitButton = QPushButton(LegalDialog)
        self.exitButton.setObjectName(u"exitButton")

        self.horizontalLayout.addWidget(self.exitButton)

        self.acceptButton = QPushButton(LegalDialog)
        self.acceptButton.setObjectName(u"acceptButton")
        self.acceptButton.setEnabled(False)

        self.horizontalLayout.addWidget(self.acceptButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(LegalDialog)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(LegalDialog)
    # setupUi

    def retranslateUi(self, LegalDialog):
        LegalDialog.setWindowTitle(QCoreApplication.translate("LegalDialog", u"Klyve - License Agreement & Privacy Policy", None))
        self.headerLabel.setText(QCoreApplication.translate("LegalDialog", u"Welcome to Klyve", None))
        self.instructionLabel.setText(QCoreApplication.translate("LegalDialog", u"Please carefully review the End User License Agreement and Privacy Policy. You must accept these terms to use the software.", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.eulaTab), QCoreApplication.translate("LegalDialog", u"End User License Agreement", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.privacyTab), QCoreApplication.translate("LegalDialog", u"Privacy Policy", None))
        self.validationLabel.setText(QCoreApplication.translate("LegalDialog", u"Please review BOTH tabs above to proceed.", None))
        self.consentCheckBox.setText(QCoreApplication.translate("LegalDialog", u"I have read and agree to the EULA and Privacy Policy. I grant permission for Klyve to transmit project data to my configured AI provider.", None))
        self.exitButton.setText(QCoreApplication.translate("LegalDialog", u"Decline && Exit", None))
        self.acceptButton.setText(QCoreApplication.translate("LegalDialog", u"Accept && Start", None))
    # retranslateUi

