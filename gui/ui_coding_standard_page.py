# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'coding_standard_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QStackedWidget,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget)

class Ui_CodingStandardPage(object):
    def setupUi(self, CodingStandardPage):
        if not CodingStandardPage.objectName():
            CodingStandardPage.setObjectName(u"CodingStandardPage")
        CodingStandardPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(CodingStandardPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(CodingStandardPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(CodingStandardPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(CodingStandardPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.initialChoicePage = QWidget()
        self.initialChoicePage.setObjectName(u"initialChoicePage")
        self.verticalLayout_2 = QVBoxLayout(self.initialChoicePage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.instructionLabel = QLabel(self.initialChoicePage)
        self.instructionLabel.setObjectName(u"instructionLabel")

        self.verticalLayout_2.addWidget(self.instructionLabel)

        self.techListWidget = QListWidget(self.initialChoicePage)
        self.techListWidget.setObjectName(u"techListWidget")

        self.verticalLayout_2.addWidget(self.techListWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.skipStandardButton = QPushButton(self.initialChoicePage)
        self.skipStandardButton.setObjectName(u"skipStandardButton")
        self.skipStandardButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.horizontalLayout.addWidget(self.skipStandardButton)

        self.horizontalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.aiProposedButton = QPushButton(self.initialChoicePage)
        self.aiProposedButton.setObjectName(u"aiProposedButton")

        self.horizontalLayout.addWidget(self.aiProposedButton)

        self.pmGuidedButton = QPushButton(self.initialChoicePage)
        self.pmGuidedButton.setObjectName(u"pmGuidedButton")

        self.horizontalLayout.addWidget(self.pmGuidedButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.stackedWidget.addWidget(self.initialChoicePage)
        self.pmDefinePage = QWidget()
        self.pmDefinePage.setObjectName(u"pmDefinePage")
        self.verticalLayout_4 = QVBoxLayout(self.pmDefinePage)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.pmDefineHeaderLabel = QLabel(self.pmDefinePage)
        self.pmDefineHeaderLabel.setObjectName(u"pmDefineHeaderLabel")

        self.verticalLayout_4.addWidget(self.pmDefineHeaderLabel)

        self.pmInputTabWidget = QTabWidget(self.pmDefinePage)
        self.pmInputTabWidget.setObjectName(u"pmInputTabWidget")
        self.textInputTab = QWidget()
        self.textInputTab.setObjectName(u"textInputTab")
        self.verticalLayout_text = QVBoxLayout(self.textInputTab)
        self.verticalLayout_text.setObjectName(u"verticalLayout_text")
        self.pmGuidelinesTextEdit = QPlainTextEdit(self.textInputTab)
        self.pmGuidelinesTextEdit.setObjectName(u"pmGuidelinesTextEdit")

        self.verticalLayout_text.addWidget(self.pmGuidelinesTextEdit)

        self.pmInputTabWidget.addTab(self.textInputTab, "")
        self.uploadTab = QWidget()
        self.uploadTab.setObjectName(u"uploadTab")
        self.verticalLayout_upload = QVBoxLayout(self.uploadTab)
        self.verticalLayout_upload.setObjectName(u"verticalLayout_upload")
        self.horizontalLayout_upload = QHBoxLayout()
        self.horizontalLayout_upload.setObjectName(u"horizontalLayout_upload")
        self.uploadPathLineEdit = QLineEdit(self.uploadTab)
        self.uploadPathLineEdit.setObjectName(u"uploadPathLineEdit")
        self.uploadPathLineEdit.setReadOnly(True)

        self.horizontalLayout_upload.addWidget(self.uploadPathLineEdit)

        self.browseFilesButton = QPushButton(self.uploadTab)
        self.browseFilesButton.setObjectName(u"browseFilesButton")

        self.horizontalLayout_upload.addWidget(self.browseFilesButton)


        self.verticalLayout_upload.addLayout(self.horizontalLayout_upload)

        self.verticalSpacer_upload = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_upload.addItem(self.verticalSpacer_upload)

        self.pmInputTabWidget.addTab(self.uploadTab, "")

        self.verticalLayout_4.addWidget(self.pmInputTabWidget)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.cancelButton_1 = QPushButton(self.pmDefinePage)
        self.cancelButton_1.setObjectName(u"cancelButton_1")

        self.horizontalLayout_3.addWidget(self.cancelButton_1)

        self.horizontalSpacer_3 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.generateFromGuidelinesButton = QPushButton(self.pmDefinePage)
        self.generateFromGuidelinesButton.setObjectName(u"generateFromGuidelinesButton")

        self.horizontalLayout_3.addWidget(self.generateFromGuidelinesButton)


        self.verticalLayout_4.addLayout(self.horizontalLayout_3)

        self.stackedWidget.addWidget(self.pmDefinePage)
        self.reviewPage = QWidget()
        self.reviewPage.setObjectName(u"reviewPage")
        self.verticalLayout_3 = QVBoxLayout(self.reviewPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.reviewHeaderLabel = QLabel(self.reviewPage)
        self.reviewHeaderLabel.setObjectName(u"reviewHeaderLabel")

        self.verticalLayout_3.addWidget(self.reviewHeaderLabel)

        self.reviewTabWidget = QTabWidget(self.reviewPage)
        self.reviewTabWidget.setObjectName(u"reviewTabWidget")
        self.specDraftTab = QWidget()
        self.specDraftTab.setObjectName(u"specDraftTab")
        self.verticalLayout_7 = QVBoxLayout(self.specDraftTab)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.standardTextEdit = QTextEdit(self.specDraftTab)
        self.standardTextEdit.setObjectName(u"standardTextEdit")

        self.verticalLayout_7.addWidget(self.standardTextEdit)

        self.reviewTabWidget.addTab(self.specDraftTab, "")
        self.aiAnalysisTab = QWidget()
        self.aiAnalysisTab.setObjectName(u"aiAnalysisTab")
        self.verticalLayout_8 = QVBoxLayout(self.aiAnalysisTab)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.aiAnalysisTextEdit = QTextEdit(self.aiAnalysisTab)
        self.aiAnalysisTextEdit.setObjectName(u"aiAnalysisTextEdit")
        self.aiAnalysisTextEdit.setReadOnly(True)

        self.verticalLayout_8.addWidget(self.aiAnalysisTextEdit)

        self.reviewTabWidget.addTab(self.aiAnalysisTab, "")
        self.feedbackTab = QWidget()
        self.feedbackTab.setObjectName(u"feedbackTab")
        self.verticalLayout_10 = QVBoxLayout(self.feedbackTab)
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.feedbackLabel = QLabel(self.feedbackTab)
        self.feedbackLabel.setObjectName(u"feedbackLabel")
        self.feedbackLabel.setWordWrap(True)

        self.verticalLayout_10.addWidget(self.feedbackLabel)

        self.feedbackTextEdit = QPlainTextEdit(self.feedbackTab)
        self.feedbackTextEdit.setObjectName(u"feedbackTextEdit")

        self.verticalLayout_10.addWidget(self.feedbackTextEdit)

        self.reviewTabWidget.addTab(self.feedbackTab, "")

        self.verticalLayout_3.addWidget(self.reviewTabWidget)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.cancelButton_2 = QPushButton(self.reviewPage)
        self.cancelButton_2.setObjectName(u"cancelButton_2")

        self.horizontalLayout_4.addWidget(self.cancelButton_2)

        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)

        self.refineButton = QPushButton(self.reviewPage)
        self.refineButton.setObjectName(u"refineButton")

        self.horizontalLayout_4.addWidget(self.refineButton)

        self.approveButton = QPushButton(self.reviewPage)
        self.approveButton.setObjectName(u"approveButton")

        self.horizontalLayout_4.addWidget(self.approveButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_4)

        self.stackedWidget.addWidget(self.reviewPage)
        self.processingPage = QWidget()
        self.processingPage.setObjectName(u"processingPage")
        self.verticalLayout_5 = QVBoxLayout(self.processingPage)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_2)

        self.processingLabel = QLabel(self.processingPage)
        self.processingLabel.setObjectName(u"processingLabel")
        self.processingLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_5.addWidget(self.processingLabel)

        self.verticalSpacer_3 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)

        self.stackedWidget.addWidget(self.processingPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(CodingStandardPage)

        QMetaObject.connectSlotsByName(CodingStandardPage)
    # setupUi

    def retranslateUi(self, CodingStandardPage):
        CodingStandardPage.setWindowTitle(QCoreApplication.translate("CodingStandardPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Coding Standard Generation", None))
        self.instructionLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Choose how to create the Coding Standard document(s) for the detected technologies.", None))
        self.skipStandardButton.setText(QCoreApplication.translate("CodingStandardPage", u"Skip this Technology", None))
        self.aiProposedButton.setText(QCoreApplication.translate("CodingStandardPage", u"Generate with AI Proposal", None))
        self.pmGuidedButton.setText(QCoreApplication.translate("CodingStandardPage", u"Generate with PM Guidelines", None))
        self.pmDefineHeaderLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Define Guidelines for [Technology]", None))
        self.pmInputTabWidget.setTabText(self.pmInputTabWidget.indexOf(self.textInputTab), QCoreApplication.translate("CodingStandardPage", u"Enter Text Guidelines", None))
        self.browseFilesButton.setText(QCoreApplication.translate("CodingStandardPage", u"Browse...", None))
        self.pmInputTabWidget.setTabText(self.pmInputTabWidget.indexOf(self.uploadTab), QCoreApplication.translate("CodingStandardPage", u"Upload Guideline Documents", None))
        self.cancelButton_1.setText(QCoreApplication.translate("CodingStandardPage", u"Cancel", None))
        self.generateFromGuidelinesButton.setText(QCoreApplication.translate("CodingStandardPage", u"Analyze Guidelines && Generate Draft", None))
        self.reviewHeaderLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Review Coding Standard for [Technology]", None))
        self.reviewTabWidget.setTabText(self.reviewTabWidget.indexOf(self.specDraftTab), QCoreApplication.translate("CodingStandardPage", u"Standard Draft", None))
        self.reviewTabWidget.setTabText(self.reviewTabWidget.indexOf(self.aiAnalysisTab), QCoreApplication.translate("CodingStandardPage", u"AI Analysis & Suggestions", None))
        self.feedbackLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Provide feedback and clarifications below to have the AI generate a new version.", None))
        self.reviewTabWidget.setTabText(self.reviewTabWidget.indexOf(self.feedbackTab), QCoreApplication.translate("CodingStandardPage", u"Your Feedback", None))
        self.cancelButton_2.setText(QCoreApplication.translate("CodingStandardPage", u"Cancel", None))
        self.refineButton.setText(QCoreApplication.translate("CodingStandardPage", u"Submit Feedback && Refine", None))
        self.approveButton.setText(QCoreApplication.translate("CodingStandardPage", u"Approve Standard", None))
        self.processingLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Processing... Please wait.", None))
    # retranslateUi

