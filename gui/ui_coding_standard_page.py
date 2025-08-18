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
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget)

class Ui_CodingStandardPage(object):
    def setupUi(self, CodingStandardPage):
        if not CodingStandardPage.objectName():
            CodingStandardPage.setObjectName(u"CodingStandardPage")
        CodingStandardPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(CodingStandardPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(CodingStandardPage)
        self.headerLabel.setObjectName(u"headerLabel")
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(CodingStandardPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(CodingStandardPage)
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

        self.standardTextEdit = QTextEdit(self.reviewPage)
        self.standardTextEdit.setObjectName(u"standardTextEdit")

        self.verticalLayout_3.addWidget(self.standardTextEdit)

        self.feedbackLabel = QLabel(self.reviewPage)
        self.feedbackLabel.setObjectName(u"feedbackLabel")

        self.verticalLayout_3.addWidget(self.feedbackLabel)

        self.feedbackTextEdit = QPlainTextEdit(self.reviewPage)
        self.feedbackTextEdit.setObjectName(u"feedbackTextEdit")
        self.feedbackTextEdit.setMaximumSize(QSize(16777215, 100))

        self.verticalLayout_3.addWidget(self.feedbackTextEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

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


        self.retranslateUi(CodingStandardPage)

        QMetaObject.connectSlotsByName(CodingStandardPage)
    # setupUi

    def retranslateUi(self, CodingStandardPage):
        CodingStandardPage.setWindowTitle(QCoreApplication.translate("CodingStandardPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Coding Standard Generation", None))
        self.instructionLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Generate a project-specific coding standard based on the technical specification. This standard will be enforced by all code-generating agents.", None))
        self.generateButton.setText(QCoreApplication.translate("CodingStandardPage", u"Generate Coding Standard Draft", None))
        self.reviewHeaderLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Review Coding Standard", None))
        self.feedbackLabel.setText(QCoreApplication.translate("CodingStandardPage", u"Provide feedback for refinement (optional):", None))
        self.refineButton.setText(QCoreApplication.translate("CodingStandardPage", u"Submit Feedback & Refine", None))
        self.approveButton.setText(QCoreApplication.translate("CodingStandardPage", u"Approve Coding Standard", None))
    # retranslateUi

