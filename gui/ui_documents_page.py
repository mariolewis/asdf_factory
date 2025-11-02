# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'documents_page.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSplitter, QTextBrowser, QVBoxLayout,
    QWidget)

class Ui_DocumentsPage(object):
    def setupUi(self, DocumentsPage):
        if not DocumentsPage.objectName():
            DocumentsPage.setObjectName(u"DocumentsPage")
        DocumentsPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(DocumentsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(DocumentsPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(DocumentsPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.mainSplitter = QSplitter(DocumentsPage)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Vertical)
        self.topWidget = QWidget(self.mainSplitter)
        self.topWidget.setObjectName(u"topWidget")
        self.topRowLayout = QHBoxLayout(self.topWidget)
        self.topRowLayout.setSpacing(12)
        self.topRowLayout.setObjectName(u"topRowLayout")
        self.topRowLayout.setContentsMargins(0, 0, 0, 0)
        self.topLeftLayout = QVBoxLayout()
        self.topLeftLayout.setObjectName(u"topLeftLayout")
        self.specDocumentsHeaderLabel = QLabel(self.topWidget)
        self.specDocumentsHeaderLabel.setObjectName(u"specDocumentsHeaderLabel")

        self.topLeftLayout.addWidget(self.specDocumentsHeaderLabel)

        self.specDocumentsListWidget = QListWidget(self.topWidget)
        self.specDocumentsListWidget.setObjectName(u"specDocumentsListWidget")
        self.specDocumentsListWidget.setSelectionMode(QAbstractItemView.SingleSelection)

        self.topLeftLayout.addWidget(self.specDocumentsListWidget)


        self.topRowLayout.addLayout(self.topLeftLayout)

        self.topRightLayout = QVBoxLayout()
        self.topRightLayout.setObjectName(u"topRightLayout")
        self.reviewLogHeaderLabel = QLabel(self.topWidget)
        self.reviewLogHeaderLabel.setObjectName(u"reviewLogHeaderLabel")

        self.topRightLayout.addWidget(self.reviewLogHeaderLabel)

        self.reviewLogBrowser = QTextBrowser(self.topWidget)
        self.reviewLogBrowser.setObjectName(u"reviewLogBrowser")

        self.topRightLayout.addWidget(self.reviewLogBrowser)


        self.topRowLayout.addLayout(self.topRightLayout)

        self.topRowLayout.setStretch(0, 1)
        self.topRowLayout.setStretch(1, 2)
        self.mainSplitter.addWidget(self.topWidget)
        self.bottomWidget = QWidget(self.mainSplitter)
        self.bottomWidget.setObjectName(u"bottomWidget")
        self.bottomRowLayout = QHBoxLayout(self.bottomWidget)
        self.bottomRowLayout.setSpacing(12)
        self.bottomRowLayout.setObjectName(u"bottomRowLayout")
        self.bottomRowLayout.setContentsMargins(0, 0, 0, 0)
        self.bottomLeftLayout = QVBoxLayout()
        self.bottomLeftLayout.setObjectName(u"bottomLeftLayout")
        self.otherDocumentsHeaderLabel = QLabel(self.bottomWidget)
        self.otherDocumentsHeaderLabel.setObjectName(u"otherDocumentsHeaderLabel")

        self.bottomLeftLayout.addWidget(self.otherDocumentsHeaderLabel)

        self.otherDocumentsListWidget = QListWidget(self.bottomWidget)
        self.otherDocumentsListWidget.setObjectName(u"otherDocumentsListWidget")
        self.otherDocumentsListWidget.setSelectionMode(QAbstractItemView.SingleSelection)

        self.bottomLeftLayout.addWidget(self.otherDocumentsListWidget)


        self.bottomRowLayout.addLayout(self.bottomLeftLayout)

        self.reviewLogContentsWidget = QWidget(self.bottomWidget)
        self.reviewLogContentsWidget.setObjectName(u"reviewLogContentsWidget")
        self.verticalLayout_4 = QVBoxLayout(self.reviewLogContentsWidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.newLogEntryContentsWidget = QWidget(self.reviewLogContentsWidget)
        self.newLogEntryContentsWidget.setObjectName(u"newLogEntryContentsWidget")
        self.verticalLayout_5 = QVBoxLayout(self.newLogEntryContentsWidget)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.newLogEntryHeaderLabel = QLabel(self.newLogEntryContentsWidget)
        self.newLogEntryHeaderLabel.setObjectName(u"newLogEntryHeaderLabel")

        self.verticalLayout_5.addWidget(self.newLogEntryHeaderLabel)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.authorLabel = QLabel(self.newLogEntryContentsWidget)
        self.authorLabel.setObjectName(u"authorLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.authorLabel)

        self.authorComboBox = QComboBox(self.newLogEntryContentsWidget)
        self.authorComboBox.addItem("")
        self.authorComboBox.addItem("")
        self.authorComboBox.setObjectName(u"authorComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.authorComboBox)


        self.verticalLayout_5.addLayout(self.formLayout)

        self.logTextEdit = QPlainTextEdit(self.newLogEntryContentsWidget)
        self.logTextEdit.setObjectName(u"logTextEdit")

        self.verticalLayout_5.addWidget(self.logTextEdit)


        self.verticalLayout_4.addWidget(self.newLogEntryContentsWidget)


        self.bottomRowLayout.addWidget(self.reviewLogContentsWidget)

        self.bottomRowLayout.setStretch(0, 1)
        self.bottomRowLayout.setStretch(1, 2)
        self.mainSplitter.addWidget(self.bottomWidget)

        self.verticalLayout.addWidget(self.mainSplitter)

        self.bottomButtonRowLayout = QHBoxLayout()
        self.bottomButtonRowLayout.setSpacing(12)
        self.bottomButtonRowLayout.setObjectName(u"bottomButtonRowLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.uploadVersionButton = QPushButton(DocumentsPage)
        self.uploadVersionButton.setObjectName(u"uploadVersionButton")

        self.horizontalLayout_2.addWidget(self.uploadVersionButton)

        self.addOtherDocumentButton = QPushButton(DocumentsPage)
        self.addOtherDocumentButton.setObjectName(u"addOtherDocumentButton")

        self.horizontalLayout_2.addWidget(self.addOtherDocumentButton)


        self.bottomButtonRowLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.saveFeedbackButton = QPushButton(DocumentsPage)
        self.saveFeedbackButton.setObjectName(u"saveFeedbackButton")

        self.horizontalLayout_3.addWidget(self.saveFeedbackButton)

        self.markApprovedButton = QPushButton(DocumentsPage)
        self.markApprovedButton.setObjectName(u"markApprovedButton")

        self.horizontalLayout_3.addWidget(self.markApprovedButton)


        self.bottomButtonRowLayout.addLayout(self.horizontalLayout_3)

        self.bottomButtonRowLayout.setStretch(0, 1)
        self.bottomButtonRowLayout.setStretch(1, 2)

        self.verticalLayout.addLayout(self.bottomButtonRowLayout)

        self.bottomNavLayout = QHBoxLayout()
        self.bottomNavLayout.setObjectName(u"bottomNavLayout")
        self.backButton = QPushButton(DocumentsPage)
        self.backButton.setObjectName(u"backButton")

        self.bottomNavLayout.addWidget(self.backButton)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.bottomNavLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.bottomNavLayout)

        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(DocumentsPage)

        QMetaObject.connectSlotsByName(DocumentsPage)
    # setupUi

    def retranslateUi(self, DocumentsPage):
        DocumentsPage.setWindowTitle(QCoreApplication.translate("DocumentsPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("DocumentsPage", u"Document Hub", None))
        self.specDocumentsHeaderLabel.setText(QCoreApplication.translate("DocumentsPage", u"Project Specifications", None))
        self.reviewLogHeaderLabel.setText(QCoreApplication.translate("DocumentsPage", u"Review Log", None))
        self.otherDocumentsHeaderLabel.setText(QCoreApplication.translate("DocumentsPage", u"Other Documents", None))
        self.newLogEntryHeaderLabel.setText(QCoreApplication.translate("DocumentsPage", u"Add New Log Entry", None))
        self.authorLabel.setText(QCoreApplication.translate("DocumentsPage", u"Author:", None))
        self.authorComboBox.setItemText(0, QCoreApplication.translate("DocumentsPage", u"DEVELOPER", None))
        self.authorComboBox.setItemText(1, QCoreApplication.translate("DocumentsPage", u"CLIENT", None))

        self.uploadVersionButton.setText(QCoreApplication.translate("DocumentsPage", u"Upload New Version...", None))
        self.addOtherDocumentButton.setText(QCoreApplication.translate("DocumentsPage", u"Add Other Document...", None))
        self.saveFeedbackButton.setText(QCoreApplication.translate("DocumentsPage", u"Save Feedback", None))
        self.markApprovedButton.setText(QCoreApplication.translate("DocumentsPage", u"Mark as Approved", None))
        self.backButton.setText(QCoreApplication.translate("DocumentsPage", u" < Back ", None))
    # retranslateUi

