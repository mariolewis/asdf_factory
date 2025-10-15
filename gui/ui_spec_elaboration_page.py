# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'spec_elaboration_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QStackedWidget, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_SpecElaborationPage(object):
    def setupUi(self, SpecElaborationPage):
        if not SpecElaborationPage.objectName():
            SpecElaborationPage.setObjectName(u"SpecElaborationPage")
        SpecElaborationPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(SpecElaborationPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(SpecElaborationPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(SpecElaborationPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(SpecElaborationPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.initialInputPage = QWidget()
        self.initialInputPage.setObjectName(u"initialInputPage")
        self.verticalLayout_2 = QVBoxLayout(self.initialInputPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.instructionLabel = QLabel(self.initialInputPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.instructionLabel)

        self.inputTabWidget = QTabWidget(self.initialInputPage)
        self.inputTabWidget.setObjectName(u"inputTabWidget")
        self.uploadTab = QWidget()
        self.uploadTab.setObjectName(u"uploadTab")
        self.verticalLayout_3 = QVBoxLayout(self.uploadTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.uploadPathLineEdit = QLineEdit(self.uploadTab)
        self.uploadPathLineEdit.setObjectName(u"uploadPathLineEdit")

        self.horizontalLayout.addWidget(self.uploadPathLineEdit)

        self.browseFilesButton = QPushButton(self.uploadTab)
        self.browseFilesButton.setObjectName(u"browseFilesButton")

        self.horizontalLayout.addWidget(self.browseFilesButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_4)

        self.processFilesButton = QPushButton(self.uploadTab)
        self.processFilesButton.setObjectName(u"processFilesButton")

        self.horizontalLayout_6.addWidget(self.processFilesButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_6)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.inputTabWidget.addTab(self.uploadTab, "")
        self.textInputTab = QWidget()
        self.textInputTab.setObjectName(u"textInputTab")
        self.verticalLayout_4 = QVBoxLayout(self.textInputTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.briefDescriptionTextEdit = QPlainTextEdit(self.textInputTab)
        self.briefDescriptionTextEdit.setObjectName(u"briefDescriptionTextEdit")

        self.verticalLayout_4.addWidget(self.briefDescriptionTextEdit)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_5)

        self.processTextButton = QPushButton(self.textInputTab)
        self.processTextButton.setObjectName(u"processTextButton")

        self.horizontalLayout_7.addWidget(self.processTextButton)


        self.verticalLayout_4.addLayout(self.horizontalLayout_7)

        self.inputTabWidget.addTab(self.textInputTab, "")

        self.verticalLayout_2.addWidget(self.inputTabWidget)

        self.stackedWidget.addWidget(self.initialInputPage)
        self.processingPage = QWidget()
        self.processingPage.setObjectName(u"processingPage")
        self.verticalLayout_11 = QVBoxLayout(self.processingPage)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer_2)

        self.processingLabel = QLabel(self.processingPage)
        self.processingLabel.setObjectName(u"processingLabel")
        self.processingLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_11.addWidget(self.processingLabel)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_11.addItem(self.verticalSpacer_3)

        self.stackedWidget.addWidget(self.processingPage)
        self.complexityReviewPage = QWidget()
        self.complexityReviewPage.setObjectName(u"complexityReviewPage")
        self.gridLayout = QGridLayout(self.complexityReviewPage)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.cancelProjectButton = QPushButton(self.complexityReviewPage)
        self.cancelProjectButton.setObjectName(u"cancelProjectButton")

        self.horizontalLayout_3.addWidget(self.cancelProjectButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.confirmAnalysisButton = QPushButton(self.complexityReviewPage)
        self.confirmAnalysisButton.setObjectName(u"confirmAnalysisButton")

        self.horizontalLayout_3.addWidget(self.confirmAnalysisButton)


        self.gridLayout.addLayout(self.horizontalLayout_3, 1, 0, 1, 1)

        self.analysisResultTextEdit = QTextEdit(self.complexityReviewPage)
        self.analysisResultTextEdit.setObjectName(u"analysisResultTextEdit")
        self.analysisResultTextEdit.setReadOnly(True)

        self.gridLayout.addWidget(self.analysisResultTextEdit, 0, 0, 1, 1)

        self.gridLayout.setRowStretch(0, 1)
        self.stackedWidget.addWidget(self.complexityReviewPage)
        self.pmFirstReviewPage = QWidget()
        self.pmFirstReviewPage.setObjectName(u"pmFirstReviewPage")
        self.verticalLayout_9 = QVBoxLayout(self.pmFirstReviewPage)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.pmReviewInstructionLabel = QLabel(self.pmFirstReviewPage)
        self.pmReviewInstructionLabel.setObjectName(u"pmReviewInstructionLabel")
        self.pmReviewInstructionLabel.setWordWrap(True)

        self.verticalLayout_9.addWidget(self.pmReviewInstructionLabel)

        self.pmReviewTextEdit = QTextEdit(self.pmFirstReviewPage)
        self.pmReviewTextEdit.setObjectName(u"pmReviewTextEdit")

        self.verticalLayout_9.addWidget(self.pmReviewTextEdit)

        self.pmFeedbackLabel = QLabel(self.pmFirstReviewPage)
        self.pmFeedbackLabel.setObjectName(u"pmFeedbackLabel")

        self.verticalLayout_9.addWidget(self.pmFeedbackLabel)

        self.pmFeedbackTextEdit = QPlainTextEdit(self.pmFirstReviewPage)
        self.pmFeedbackTextEdit.setObjectName(u"pmFeedbackTextEdit")
        self.pmFeedbackTextEdit.setMaximumSize(QSize(16777215, 100))

        self.verticalLayout_9.addWidget(self.pmFeedbackTextEdit)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.submitForAnalysisButton = QPushButton(self.pmFirstReviewPage)
        self.submitForAnalysisButton.setObjectName(u"submitForAnalysisButton")

        self.horizontalLayout_4.addWidget(self.submitForAnalysisButton)


        self.verticalLayout_9.addLayout(self.horizontalLayout_4)

        self.stackedWidget.addWidget(self.pmFirstReviewPage)
        self.finalReviewPage = QWidget()
        self.finalReviewPage.setObjectName(u"finalReviewPage")
        self.verticalLayout_6 = QVBoxLayout(self.finalReviewPage)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.reviewTabWidget = QTabWidget(self.finalReviewPage)
        self.reviewTabWidget.setObjectName(u"reviewTabWidget")
        self.specDraftTab = QWidget()
        self.specDraftTab.setObjectName(u"specDraftTab")
        self.verticalLayout_7 = QVBoxLayout(self.specDraftTab)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.specDraftTextEdit = QTextEdit(self.specDraftTab)
        self.specDraftTextEdit.setObjectName(u"specDraftTextEdit")

        self.verticalLayout_7.addWidget(self.specDraftTextEdit)

        self.reviewTabWidget.addTab(self.specDraftTab, "")
        self.aiIssuesTab = QWidget()
        self.aiIssuesTab.setObjectName(u"aiIssuesTab")
        self.verticalLayout_8 = QVBoxLayout(self.aiIssuesTab)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.aiIssuesTextEdit = QTextEdit(self.aiIssuesTab)
        self.aiIssuesTextEdit.setObjectName(u"aiIssuesTextEdit")
        self.aiIssuesTextEdit.setReadOnly(True)

        self.verticalLayout_8.addWidget(self.aiIssuesTextEdit)

        self.reviewTabWidget.addTab(self.aiIssuesTab, "")
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

        self.verticalLayout_6.addWidget(self.reviewTabWidget)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_3 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.submitFeedbackButton = QPushButton(self.finalReviewPage)
        self.submitFeedbackButton.setObjectName(u"submitFeedbackButton")

        self.horizontalLayout_2.addWidget(self.submitFeedbackButton)

        self.approveSpecButton = QPushButton(self.finalReviewPage)
        self.approveSpecButton.setObjectName(u"approveSpecButton")

        self.horizontalLayout_2.addWidget(self.approveSpecButton)


        self.verticalLayout_6.addLayout(self.horizontalLayout_2)

        self.stackedWidget.addWidget(self.finalReviewPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(SpecElaborationPage)

        QMetaObject.connectSlotsByName(SpecElaborationPage)
    # setupUi

    def retranslateUi(self, SpecElaborationPage):
        SpecElaborationPage.setWindowTitle(QCoreApplication.translate("SpecElaborationPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Your Requirement", None))
        self.instructionLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Please enter a brief description of the application you want, or upload a requirement document and any additional technical specifications and/or standards that it must comply with.", None))
        self.browseFilesButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Browse...", None))
        self.processFilesButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Process Uploaded Document(s)", None))
        self.inputTabWidget.setTabText(self.inputTabWidget.indexOf(self.uploadTab), QCoreApplication.translate("SpecElaborationPage", u"Upload Specification Document(s)", None))
        self.processTextButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Process Brief Description", None))
        self.inputTabWidget.setTabText(self.inputTabWidget.indexOf(self.textInputTab), QCoreApplication.translate("SpecElaborationPage", u"Enter Brief Description", None))
        self.processingLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Processing... Please wait.", None))
        self.cancelProjectButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Cancel Project", None))
        self.confirmAnalysisButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Confirm Assessment && Proceed", None))
        self.pmReviewInstructionLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"This is the first specification draft generated by the AI. Review it and make any direct edits. You can also provide general feedback for refinement in the box at the bottom before submitting for a final AI analysis.", None))
        self.pmFeedbackLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Feedback for Refinement (Optional):", None))
        self.submitForAnalysisButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Submit for AI Analysis", None))
        self.reviewTabWidget.setTabText(self.reviewTabWidget.indexOf(self.specDraftTab), QCoreApplication.translate("SpecElaborationPage", u"Specification Draft", None))
        self.reviewTabWidget.setTabText(self.reviewTabWidget.indexOf(self.aiIssuesTab), QCoreApplication.translate("SpecElaborationPage", u"AI Analysis & Issues", None))
        self.feedbackLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Provide feedback and clarifications below to have the AI generate a new version of the draft.", None))
        self.reviewTabWidget.setTabText(self.reviewTabWidget.indexOf(self.feedbackTab), QCoreApplication.translate("SpecElaborationPage", u"Your Feedback & Refinements", None))
        self.submitFeedbackButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Submit Feedback && Refine Draft", None))
        self.approveSpecButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Approve Specification && Proceed", None))
    # retranslateUi

