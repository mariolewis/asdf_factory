# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tech_spec_page.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QStackedWidget, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_TechSpecPage(object):
    def setupUi(self, TechSpecPage):
        if not TechSpecPage.objectName():
            TechSpecPage.setObjectName(u"TechSpecPage")
        TechSpecPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(TechSpecPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(TechSpecPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(TechSpecPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(TechSpecPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.initialChoicePage = QWidget()
        self.initialChoicePage.setObjectName(u"initialChoicePage")
        self.verticalLayout_2 = QVBoxLayout(self.initialChoicePage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.instructionLabel = QLabel(self.initialChoicePage)
        self.instructionLabel.setObjectName(u"instructionLabel")

        self.verticalLayout_2.addWidget(self.instructionLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.proposeStackButton = QPushButton(self.initialChoicePage)
        self.proposeStackButton.setObjectName(u"proposeStackButton")

        self.horizontalLayout.addWidget(self.proposeStackButton)

        self.pmDefineButton = QPushButton(self.initialChoicePage)
        self.pmDefineButton.setObjectName(u"pmDefineButton")

        self.horizontalLayout.addWidget(self.pmDefineButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.stackedWidget.addWidget(self.initialChoicePage)
        self.pmDefinePage = QWidget()
        self.pmDefinePage.setObjectName(u"pmDefinePage")
        self.verticalLayout_4 = QVBoxLayout(self.pmDefinePage)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.pmDefineHeaderLabel = QLabel(self.pmDefinePage)
        self.pmDefineHeaderLabel.setObjectName(u"pmDefineHeaderLabel")

        self.verticalLayout_4.addWidget(self.pmDefineHeaderLabel)

        self.pmDefineInstructionLabel = QLabel(self.pmDefinePage)
        self.pmDefineInstructionLabel.setObjectName(u"pmDefineInstructionLabel")
        self.pmDefineInstructionLabel.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.pmDefineInstructionLabel)

        self.pmGuidelinesTextEdit = QPlainTextEdit(self.pmDefinePage)
        self.pmGuidelinesTextEdit.setObjectName(u"pmGuidelinesTextEdit")

        self.verticalLayout_4.addWidget(self.pmGuidelinesTextEdit)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.uploadLabel = QLabel(self.pmDefinePage)
        self.uploadLabel.setObjectName(u"uploadLabel")

        self.horizontalLayout_5.addWidget(self.uploadLabel)

        self.uploadPathLineEdit = QLineEdit(self.pmDefinePage)
        self.uploadPathLineEdit.setObjectName(u"uploadPathLineEdit")
        self.uploadPathLineEdit.setReadOnly(True)

        self.horizontalLayout_5.addWidget(self.uploadPathLineEdit)

        self.browseFilesButton = QPushButton(self.pmDefinePage)
        self.browseFilesButton.setObjectName(u"browseFilesButton")

        self.horizontalLayout_5.addWidget(self.browseFilesButton)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

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
        self.techSpecTextEdit = QTextEdit(self.specDraftTab)
        self.techSpecTextEdit.setObjectName(u"techSpecTextEdit")

        self.verticalLayout_7.addWidget(self.techSpecTextEdit)

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

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.pauseProjectButton = QPushButton(self.reviewPage)
        self.pauseProjectButton.setObjectName(u"pauseProjectButton")

        self.horizontalLayout_2.addWidget(self.pauseProjectButton)

        self.refineButton = QPushButton(self.reviewPage)
        self.refineButton.setObjectName(u"refineButton")

        self.horizontalLayout_2.addWidget(self.refineButton)

        self.approveButton = QPushButton(self.reviewPage)
        self.approveButton.setObjectName(u"approveButton")

        self.horizontalLayout_2.addWidget(self.approveButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.stackedWidget.addWidget(self.reviewPage)
        self.processingPage = QWidget()
        self.processingPage.setObjectName(u"processingPage")
        self.verticalLayout_5 = QVBoxLayout(self.processingPage)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_2)

        self.processingLabel = QLabel(self.processingPage)
        self.processingLabel.setObjectName(u"processingLabel")
        self.processingLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_5.addWidget(self.processingLabel)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer_3)

        self.stackedWidget.addWidget(self.processingPage)
        self.osSelectionPage = QWidget()
        self.osSelectionPage.setObjectName(u"osSelectionPage")
        self.verticalLayout_6 = QVBoxLayout(self.osSelectionPage)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.osLabel = QLabel(self.osSelectionPage)
        self.osLabel.setObjectName(u"osLabel")

        self.verticalLayout_6.addWidget(self.osLabel)

        self.osComboBox = QComboBox(self.osSelectionPage)
        self.osComboBox.addItem("")
        self.osComboBox.addItem("")
        self.osComboBox.addItem("")
        self.osComboBox.addItem("")
        self.osComboBox.addItem("")
        self.osComboBox.addItem("")
        self.osComboBox.setObjectName(u"osComboBox")

        self.verticalLayout_6.addWidget(self.osComboBox)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalSpacer_4 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)

        self.generateProposalButton = QPushButton(self.osSelectionPage)
        self.generateProposalButton.setObjectName(u"generateProposalButton")

        self.horizontalLayout_4.addWidget(self.generateProposalButton)


        self.verticalLayout_6.addLayout(self.horizontalLayout_4)

        self.verticalSpacer_4 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_4)

        self.stackedWidget.addWidget(self.osSelectionPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(TechSpecPage)

        QMetaObject.connectSlotsByName(TechSpecPage)
    # setupUi

    def retranslateUi(self, TechSpecPage):
        TechSpecPage.setWindowTitle(QCoreApplication.translate("TechSpecPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("TechSpecPage", u"Technical Specification & Architecture", None))
        self.instructionLabel.setText(QCoreApplication.translate("TechSpecPage", u"First, choose how to create the Technical Specification document.", None))
        self.proposeStackButton.setText(QCoreApplication.translate("TechSpecPage", u"Let ASDF Propose a Tech Stack", None))
        self.pmDefineButton.setText(QCoreApplication.translate("TechSpecPage", u"I Will Provide Technology Guidelines", None))
        self.pmDefineHeaderLabel.setText(QCoreApplication.translate("TechSpecPage", u"Define Technology Guidelines", None))
        self.pmDefineInstructionLabel.setText(QCoreApplication.translate("TechSpecPage", u"Provide your key technology choices or guidelines below (e.g., 'Use Python with a Flask backend and a SQLite database'). You can also upload supporting documents. The AI will use your input to generate the full technical specification document.", None))
        self.uploadLabel.setText(QCoreApplication.translate("TechSpecPage", u"Supporting Documents (Optional):", None))
        self.browseFilesButton.setText(QCoreApplication.translate("TechSpecPage", u"Browse...", None))
        self.generateFromGuidelinesButton.setText(QCoreApplication.translate("TechSpecPage", u"Analyze && Generate Draft", None))
        self.reviewHeaderLabel.setText(QCoreApplication.translate("TechSpecPage", u"Review Technical Specification", None))
        self.reviewTabWidget.setTabText(self.reviewTabWidget.indexOf(self.specDraftTab), QCoreApplication.translate("TechSpecPage", u"Specification Draft", None))
        self.reviewTabWidget.setTabText(self.reviewTabWidget.indexOf(self.aiAnalysisTab), QCoreApplication.translate("TechSpecPage", u"AI Analysis & Suggestions", None))
        self.feedbackLabel.setText(QCoreApplication.translate("TechSpecPage", u"Provide feedback and clarifications below to have the AI generate a new version of the draft.", None))
        self.reviewTabWidget.setTabText(self.reviewTabWidget.indexOf(self.feedbackTab), QCoreApplication.translate("TechSpecPage", u"Your Feedback & Refinements", None))
        self.pauseProjectButton.setText(QCoreApplication.translate("TechSpecPage", u"Pause Project", None))
        self.refineButton.setText(QCoreApplication.translate("TechSpecPage", u"Submit Feedback && Refine", None))
        self.approveButton.setText(QCoreApplication.translate("TechSpecPage", u"Approve Technical Specification", None))
        self.processingLabel.setText(QCoreApplication.translate("TechSpecPage", u"Processing... Please wait.", None))
        self.osLabel.setText(QCoreApplication.translate("TechSpecPage", u"Please select the target Operating System for the application.", None))
        self.osComboBox.setItemText(0, QCoreApplication.translate("TechSpecPage", u"Windows", None))
        self.osComboBox.setItemText(1, QCoreApplication.translate("TechSpecPage", u"Linux", None))
        self.osComboBox.setItemText(2, QCoreApplication.translate("TechSpecPage", u"macOS", None))
        self.osComboBox.setItemText(3, QCoreApplication.translate("TechSpecPage", u"Android and iOS", None))
        self.osComboBox.setItemText(4, QCoreApplication.translate("TechSpecPage", u"Windows and iOS", None))
        self.osComboBox.setItemText(5, QCoreApplication.translate("TechSpecPage", u"Linux and Windows", None))

        self.generateProposalButton.setText(QCoreApplication.translate("TechSpecPage", u"Generate Proposal", None))
    # retranslateUi

