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
    QLabel, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QStackedWidget, QTextEdit, QVBoxLayout,
    QWidget)

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
        self.osLabel = QLabel(self.initialChoicePage)
        self.osLabel.setObjectName(u"osLabel")

        self.verticalLayout_2.addWidget(self.osLabel)

        self.osComboBox = QComboBox(self.initialChoicePage)
        self.osComboBox.addItem("")
        self.osComboBox.addItem("")
        self.osComboBox.addItem("")
        self.osComboBox.setObjectName(u"osComboBox")

        self.verticalLayout_2.addWidget(self.osComboBox)

        self.line_2 = QFrame(self.initialChoicePage)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line_2)

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

        self.infoLabel = QLabel(self.reviewPage)
        self.infoLabel.setObjectName(u"infoLabel")
        self.infoLabel.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.infoLabel)

        self.techSpecTextEdit = QTextEdit(self.reviewPage)
        self.techSpecTextEdit.setObjectName(u"techSpecTextEdit")

        self.verticalLayout_3.addWidget(self.techSpecTextEdit)

        self.feedbackLabel = QLabel(self.reviewPage)
        self.feedbackLabel.setObjectName(u"feedbackLabel")

        self.verticalLayout_3.addWidget(self.feedbackLabel)

        self.feedbackTextEdit = QPlainTextEdit(self.reviewPage)
        self.feedbackTextEdit.setObjectName(u"feedbackTextEdit")
        self.feedbackTextEdit.setMaximumSize(QSize(16777215, 100))

        self.verticalLayout_3.addWidget(self.feedbackTextEdit)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.refineButton = QPushButton(self.reviewPage)
        self.refineButton.setObjectName(u"refineButton")

        self.horizontalLayout_2.addWidget(self.refineButton)

        self.approveButton = QPushButton(self.reviewPage)
        self.approveButton.setObjectName(u"approveButton")

        self.horizontalLayout_2.addWidget(self.approveButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.stackedWidget.addWidget(self.reviewPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(TechSpecPage)

        QMetaObject.connectSlotsByName(TechSpecPage)
    # setupUi

    def retranslateUi(self, TechSpecPage):
        TechSpecPage.setWindowTitle(QCoreApplication.translate("TechSpecPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("TechSpecPage", u"Technical Specification & Architecture", None))
        self.osLabel.setText(QCoreApplication.translate("TechSpecPage", u"First, select the target Operating System for the application.", None))
        self.osComboBox.setItemText(0, QCoreApplication.translate("TechSpecPage", u"Windows", None))
        self.osComboBox.setItemText(1, QCoreApplication.translate("TechSpecPage", u"Linux", None))
        self.osComboBox.setItemText(2, QCoreApplication.translate("TechSpecPage", u"macOS", None))

        self.instructionLabel.setText(QCoreApplication.translate("TechSpecPage", u"Next, choose how to create the Technical Specification document.", None))
        self.proposeStackButton.setText(QCoreApplication.translate("TechSpecPage", u"Let ASDF Propose a Tech Stack", None))
        self.pmDefineButton.setText(QCoreApplication.translate("TechSpecPage", u"I Will Provide Technology Guidelines", None))
        self.pmDefineHeaderLabel.setText(QCoreApplication.translate("TechSpecPage", u"Define Technology Guidelines", None))
        self.pmDefineInstructionLabel.setText(QCoreApplication.translate("TechSpecPage", u"Provide your key technology choices or guidelines below (e.g., 'Use Python with a Flask backend and a SQLite database'). The AI will use your input to generate the full technical specification document.", None))
        self.generateFromGuidelinesButton.setText(QCoreApplication.translate("TechSpecPage", u"Generate Full Specification from My Input", None))
        self.reviewHeaderLabel.setText(QCoreApplication.translate("TechSpecPage", u"Review Technical Specification", None))
        self.infoLabel.setText(QCoreApplication.translate("TechSpecPage", u"Tip: You can edit this draft directly. Please apply final modifications here. For general feedback or questions that require an AI response, please enter your input in the box below the draft.", None))
        self.feedbackLabel.setText(QCoreApplication.translate("TechSpecPage", u"Provide feedback for refinement (optional):", None))
        self.refineButton.setText(QCoreApplication.translate("TechSpecPage", u"Submit Feedback & Refine", None))
        self.approveButton.setText(QCoreApplication.translate("TechSpecPage", u"Approve Technical Specification", None))
    # retranslateUi

