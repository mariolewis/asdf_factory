# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sprint_validation_page.ui'
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
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget)

class Ui_SprintValidationPage(object):
    def setupUi(self, SprintValidationPage):
        if not SprintValidationPage.objectName():
            SprintValidationPage.setObjectName(u"SprintValidationPage")
        SprintValidationPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(SprintValidationPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(SprintValidationPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(SprintValidationPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(SprintValidationPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.reportStackedWidget = QStackedWidget(SprintValidationPage)
        self.reportStackedWidget.setObjectName(u"reportStackedWidget")
        self.processingPage = QWidget()
        self.processingPage.setObjectName(u"processingPage")
        self.verticalLayout_proc = QVBoxLayout(self.processingPage)
        self.verticalLayout_proc.setObjectName(u"verticalLayout_proc")
        self.verticalSpacer_1 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_proc.addItem(self.verticalSpacer_1)

        self.processingLabel = QLabel(self.processingPage)
        self.processingLabel.setObjectName(u"processingLabel")
        self.processingLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_proc.addWidget(self.processingLabel)

        self.verticalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_proc.addItem(self.verticalSpacer_2)

        self.reportStackedWidget.addWidget(self.processingPage)
        self.reportPage = QWidget()
        self.reportPage.setObjectName(u"reportPage")
        self.verticalLayout_report = QVBoxLayout(self.reportPage)
        self.verticalLayout_report.setObjectName(u"verticalLayout_report")
        self.scrollArea = QScrollArea(self.reportPage)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 742, 405))
        self.scrollAreaLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollAreaLayout.setObjectName(u"scrollAreaLayout")
        self.scopeHeaderLabel = QLabel(self.scrollAreaWidgetContents)
        self.scopeHeaderLabel.setObjectName(u"scopeHeaderLabel")

        self.scrollAreaLayout.addWidget(self.scopeHeaderLabel)

        self.scopeDetailsTextEdit = QTextEdit(self.scrollAreaWidgetContents)
        self.scopeDetailsTextEdit.setObjectName(u"scopeDetailsTextEdit")
        self.scopeDetailsTextEdit.setReadOnly(True)

        self.scrollAreaLayout.addWidget(self.scopeDetailsTextEdit)

        self.staleHeaderLabel = QLabel(self.scrollAreaWidgetContents)
        self.staleHeaderLabel.setObjectName(u"staleHeaderLabel")

        self.scrollAreaLayout.addWidget(self.staleHeaderLabel)

        self.staleDetailsTextEdit = QTextEdit(self.scrollAreaWidgetContents)
        self.staleDetailsTextEdit.setObjectName(u"staleDetailsTextEdit")
        self.staleDetailsTextEdit.setReadOnly(True)

        self.scrollAreaLayout.addWidget(self.staleDetailsTextEdit)

        self.riskHeaderLabel = QLabel(self.scrollAreaWidgetContents)
        self.riskHeaderLabel.setObjectName(u"riskHeaderLabel")

        self.scrollAreaLayout.addWidget(self.riskHeaderLabel)

        self.riskDetailsTextEdit = QTextEdit(self.scrollAreaWidgetContents)
        self.riskDetailsTextEdit.setObjectName(u"riskDetailsTextEdit")
        self.riskDetailsTextEdit.setReadOnly(True)

        self.scrollAreaLayout.addWidget(self.riskDetailsTextEdit)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_report.addWidget(self.scrollArea)

        self.reportStackedWidget.addWidget(self.reportPage)

        self.verticalLayout.addWidget(self.reportStackedWidget)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonLayout.addItem(self.horizontalSpacer)

        self.returnToBacklogButton = QPushButton(SprintValidationPage)
        self.returnToBacklogButton.setObjectName(u"returnToBacklogButton")

        self.buttonLayout.addWidget(self.returnToBacklogButton)

        self.proceedButton = QPushButton(SprintValidationPage)
        self.proceedButton.setObjectName(u"proceedButton")

        self.buttonLayout.addWidget(self.proceedButton)


        self.verticalLayout.addLayout(self.buttonLayout)


        self.retranslateUi(SprintValidationPage)

        QMetaObject.connectSlotsByName(SprintValidationPage)
    # setupUi

    def retranslateUi(self, SprintValidationPage):
        SprintValidationPage.setWindowTitle(QCoreApplication.translate("SprintValidationPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("SprintValidationPage", u"Sprint Pre-Execution Check", None))
        self.instructionLabel.setText(QCoreApplication.translate("SprintValidationPage", u"The system has analyzed the selected sprint items. Please review the report below before proceeding.", None))
        self.processingLabel.setText(QCoreApplication.translate("SprintValidationPage", u"Running validation checks...", None))
        self.scopeHeaderLabel.setText(QCoreApplication.translate("SprintValidationPage", u"Scope Guardrail Check Status:", None))
        self.staleHeaderLabel.setText(QCoreApplication.translate("SprintValidationPage", u"Stale Analysis Check Status:", None))
        self.riskHeaderLabel.setText(QCoreApplication.translate("SprintValidationPage", u"Technical Risk Check Status:", None))
        self.returnToBacklogButton.setText(QCoreApplication.translate("SprintValidationPage", u"Return to Backlog", None))
        self.proceedButton.setText(QCoreApplication.translate("SprintValidationPage", u"Proceed to Plan Generation", None))
    # retranslateUi

