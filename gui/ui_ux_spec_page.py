# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ux_spec_page.ui'
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
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget)

class Ui_UXSpecPage(object):
    def setupUi(self, UXSpecPage):
        if not UXSpecPage.objectName():
            UXSpecPage.setObjectName(u"UXSpecPage")
        UXSpecPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(UXSpecPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(UXSpecPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(UXSpecPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(UXSpecPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.reviewPage = QWidget()
        self.reviewPage.setObjectName(u"reviewPage")
        self.verticalLayout_2 = QVBoxLayout(self.reviewPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.reviewInstructionLabel = QLabel(self.reviewPage)
        self.reviewInstructionLabel.setObjectName(u"reviewInstructionLabel")
        self.reviewInstructionLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.reviewInstructionLabel)

        self.infoLabel = QLabel(self.reviewPage)
        self.infoLabel.setObjectName(u"infoLabel")
        self.infoLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.infoLabel)

        self.specTextEdit = QTextEdit(self.reviewPage)
        self.specTextEdit.setObjectName(u"specTextEdit")

        self.verticalLayout_2.addWidget(self.specTextEdit)

        self.feedbackLabel = QLabel(self.reviewPage)
        self.feedbackLabel.setObjectName(u"feedbackLabel")

        self.verticalLayout_2.addWidget(self.feedbackLabel)

        self.feedbackTextEdit = QPlainTextEdit(self.reviewPage)
        self.feedbackTextEdit.setObjectName(u"feedbackTextEdit")
        self.feedbackTextEdit.setMaximumSize(QSize(16777215, 100))

        self.verticalLayout_2.addWidget(self.feedbackTextEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.pauseProjectButton = QPushButton(self.reviewPage)
        self.pauseProjectButton.setObjectName(u"pauseProjectButton")

        self.horizontalLayout.addWidget(self.pauseProjectButton)

        self.refineButton = QPushButton(self.reviewPage)
        self.refineButton.setObjectName(u"refineButton")

        self.horizontalLayout.addWidget(self.refineButton)

        self.approveButton = QPushButton(self.reviewPage)
        self.approveButton.setObjectName(u"approveButton")

        self.horizontalLayout.addWidget(self.approveButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.stackedWidget.addWidget(self.reviewPage)
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

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(UXSpecPage)

        QMetaObject.connectSlotsByName(UXSpecPage)
    # setupUi

    def retranslateUi(self, UXSpecPage):
        UXSpecPage.setWindowTitle(QCoreApplication.translate("UXSpecPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("UXSpecPage", u"User Experience && Interface Design", None))
        self.reviewInstructionLabel.setText(QCoreApplication.translate("UXSpecPage", u"Below is the consolidated UX/UI Specification draft, including personas, user journeys, and a style guide. Please review it, make any direct edits, and provide general feedback for refinement below.", None))
        self.infoLabel.setText(QCoreApplication.translate("UXSpecPage", u"Tip: You can edit this draft directly. Please apply final modifications here. For general feedback or questions that require an AI response, please use the text box below.", None))
        self.feedbackLabel.setText(QCoreApplication.translate("UXSpecPage", u"Feedback for Refinement (Optional):", None))
        self.pauseProjectButton.setText(QCoreApplication.translate("UXSpecPage", u"Pause Project", None))
        self.refineButton.setText(QCoreApplication.translate("UXSpecPage", u"Submit Feedback &&&& Refine", None))
        self.approveButton.setText(QCoreApplication.translate("UXSpecPage", u"Approve Specification", None))
        self.processingLabel.setText(QCoreApplication.translate("UXSpecPage", u"Processing... Please wait.", None))
    # retranslateUi

