# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'planning_page.ui'
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

class Ui_PlanningPage(object):
    def setupUi(self, PlanningPage):
        if not PlanningPage.objectName():
            PlanningPage.setObjectName(u"PlanningPage")
        PlanningPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(PlanningPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(PlanningPage)
        self.headerLabel.setObjectName(u"headerLabel")
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(PlanningPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(PlanningPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.generatePage = QWidget()
        self.generatePage.setObjectName(u"generatePage")
        self.verticalLayout_2 = QVBoxLayout(self.generatePage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.instructionLabel = QLabel(self.generatePage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.instructionLabel)

        self.generateButton = QPushButton(self.generatePage)
        self.generateButton.setObjectName(u"generateButton")

        self.verticalLayout_2.addWidget(self.generateButton)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.stackedWidget.addWidget(self.generatePage)
        self.reviewPage = QWidget()
        self.reviewPage.setObjectName(u"reviewPage")
        self.verticalLayout_3 = QVBoxLayout(self.reviewPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.reviewHeaderLabel = QLabel(self.reviewPage)
        self.reviewHeaderLabel.setObjectName(u"reviewHeaderLabel")
        self.reviewHeaderLabel.setStyleSheet(u"font-size: 14pt;")

        self.verticalLayout_3.addWidget(self.reviewHeaderLabel)

        self.planTextEdit = QTextEdit(self.reviewPage)
        self.planTextEdit.setObjectName(u"planTextEdit")
        self.planTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.planTextEdit)

        self.feedbackLabel = QLabel(self.reviewPage)
        self.feedbackLabel.setObjectName(u"feedbackLabel")

        self.verticalLayout_3.addWidget(self.feedbackLabel)

        self.feedbackTextEdit = QPlainTextEdit(self.reviewPage)
        self.feedbackTextEdit.setObjectName(u"feedbackTextEdit")
        self.feedbackTextEdit.setMaximumSize(QSize(16777215, 100))

        self.verticalLayout_3.addWidget(self.feedbackTextEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.refineButton = QPushButton(self.reviewPage)
        self.refineButton.setObjectName(u"refineButton")

        self.horizontalLayout.addWidget(self.refineButton)

        self.approveButton = QPushButton(self.reviewPage)
        self.approveButton.setObjectName(u"approveButton")

        self.horizontalLayout.addWidget(self.approveButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.stackedWidget.addWidget(self.reviewPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(PlanningPage)

        QMetaObject.connectSlotsByName(PlanningPage)
    # setupUi

    def retranslateUi(self, PlanningPage):
        PlanningPage.setWindowTitle(QCoreApplication.translate("PlanningPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("PlanningPage", u"Strategic Development Planning", None))
        self.instructionLabel.setText(QCoreApplication.translate("PlanningPage", u"Click the button below to generate a detailed, sequential development plan based on the finalized specifications.", None))
        self.generateButton.setText(QCoreApplication.translate("PlanningPage", u"Generate Development Plan", None))
        self.reviewHeaderLabel.setText(QCoreApplication.translate("PlanningPage", u"Review Development Plan", None))
        self.feedbackLabel.setText(QCoreApplication.translate("PlanningPage", u"Provide feedback for refinement (optional):", None))
        self.refineButton.setText(QCoreApplication.translate("PlanningPage", u"Submit Feedback & Refine", None))
        self.approveButton.setText(QCoreApplication.translate("PlanningPage", u"Approve Plan & Proceed to Development", None))
    # retranslateUi

