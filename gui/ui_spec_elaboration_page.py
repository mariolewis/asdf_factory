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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QSplitter, QStackedWidget, QTabWidget,
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
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

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

        self.processFilesButton = QPushButton(self.uploadTab)
        self.processFilesButton.setObjectName(u"processFilesButton")

        self.verticalLayout_3.addWidget(self.processFilesButton)

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

        self.processTextButton = QPushButton(self.textInputTab)
        self.processTextButton.setObjectName(u"processTextButton")

        self.verticalLayout_4.addWidget(self.processTextButton)

        self.inputTabWidget.addTab(self.textInputTab, "")

        self.verticalLayout_2.addWidget(self.inputTabWidget)

        self.stackedWidget.addWidget(self.initialInputPage)
        self.complexityReviewPage = QWidget()
        self.complexityReviewPage.setObjectName(u"complexityReviewPage")
        self.verticalLayout_5 = QVBoxLayout(self.complexityReviewPage)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.reviewHeaderLabel = QLabel(self.complexityReviewPage)
        self.reviewHeaderLabel.setObjectName(u"reviewHeaderLabel")
        self.reviewHeaderLabel.setStyleSheet(u"font-size: 14pt;")

        self.verticalLayout_5.addWidget(self.reviewHeaderLabel)

        self.analysisResultTextEdit = QTextEdit(self.complexityReviewPage)
        self.analysisResultTextEdit.setObjectName(u"analysisResultTextEdit")
        self.analysisResultTextEdit.setReadOnly(True)

        self.verticalLayout_5.addWidget(self.analysisResultTextEdit)

        self.confirmAnalysisButton = QPushButton(self.complexityReviewPage)
        self.confirmAnalysisButton.setObjectName(u"confirmAnalysisButton")

        self.verticalLayout_5.addWidget(self.confirmAnalysisButton)

        self.stackedWidget.addWidget(self.complexityReviewPage)
        self.finalReviewPage = QWidget()
        self.finalReviewPage.setObjectName(u"finalReviewPage")
        self.verticalLayout_6 = QVBoxLayout(self.finalReviewPage)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.finalReviewHeaderLabel = QLabel(self.finalReviewPage)
        self.finalReviewHeaderLabel.setObjectName(u"finalReviewHeaderLabel")
        self.finalReviewHeaderLabel.setStyleSheet(u"font-size: 14pt;")

        self.verticalLayout_6.addWidget(self.finalReviewHeaderLabel)

        self.splitter = QSplitter(self.finalReviewPage)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Horizontal)
        self.widget = QWidget(self.splitter)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_7 = QVBoxLayout(self.widget)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.specDraftLabel = QLabel(self.widget)
        self.specDraftLabel.setObjectName(u"specDraftLabel")

        self.verticalLayout_7.addWidget(self.specDraftLabel)

        self.specDraftTextEdit = QTextEdit(self.widget)
        self.specDraftTextEdit.setObjectName(u"specDraftTextEdit")

        self.verticalLayout_7.addWidget(self.specDraftTextEdit)

        self.splitter.addWidget(self.widget)
        self.widget1 = QWidget(self.splitter)
        self.widget1.setObjectName(u"widget1")
        self.verticalLayout_8 = QVBoxLayout(self.widget1)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.aiIssuesLabel = QLabel(self.widget1)
        self.aiIssuesLabel.setObjectName(u"aiIssuesLabel")

        self.verticalLayout_8.addWidget(self.aiIssuesLabel)

        self.aiIssuesTextEdit = QTextEdit(self.widget1)
        self.aiIssuesTextEdit.setObjectName(u"aiIssuesTextEdit")
        self.aiIssuesTextEdit.setReadOnly(True)

        self.verticalLayout_8.addWidget(self.aiIssuesTextEdit)

        self.splitter.addWidget(self.widget1)

        self.verticalLayout_6.addWidget(self.splitter)

        self.feedbackLabel = QLabel(self.finalReviewPage)
        self.feedbackLabel.setObjectName(u"feedbackLabel")

        self.verticalLayout_6.addWidget(self.feedbackLabel)

        self.feedbackTextEdit = QPlainTextEdit(self.finalReviewPage)
        self.feedbackTextEdit.setObjectName(u"feedbackTextEdit")

        self.verticalLayout_6.addWidget(self.feedbackTextEdit)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
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
        self.headerLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Application Specification", None))
        self.instructionLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Please provide the initial specification for your target application.", None))
        self.browseFilesButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Browse...", None))
        self.processFilesButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Process Uploaded Document(s)", None))
        self.inputTabWidget.setTabText(self.inputTabWidget.indexOf(self.uploadTab), QCoreApplication.translate("SpecElaborationPage", u"Upload Specification Document(s)", None))
        self.processTextButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Process Brief Description", None))
        self.inputTabWidget.setTabText(self.inputTabWidget.indexOf(self.textInputTab), QCoreApplication.translate("SpecElaborationPage", u"Enter Brief Description", None))
        self.reviewHeaderLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Project Complexity & Risk Assessment", None))
        self.confirmAnalysisButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Confirm Assessment & Proceed to Final Review", None))
        self.finalReviewHeaderLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Final Specification Review", None))
        self.specDraftLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Specification Draft (Editable)", None))
        self.aiIssuesLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"AI Analysis & Potential Issues", None))
        self.feedbackLabel.setText(QCoreApplication.translate("SpecElaborationPage", u"Your Feedback & Clarifications (Optional):", None))
        self.submitFeedbackButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Submit Feedback & Refine Draft", None))
        self.approveSpecButton.setText(QCoreApplication.translate("SpecElaborationPage", u"Approve Specification & Proceed", None))
    # retranslateUi

