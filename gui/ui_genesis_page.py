# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'genesis_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QProgressBar, QPushButton, QSizePolicy,
    QSpacerItem, QStackedWidget, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_GenesisPage(object):
    def setupUi(self, GenesisPage):
        if not GenesisPage.objectName():
            GenesisPage.setObjectName(u"GenesisPage")
        GenesisPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(GenesisPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(GenesisPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(GenesisPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(GenesisPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.checkpointPage = QWidget()
        self.checkpointPage.setObjectName(u"checkpointPage")
        self.verticalLayout_2 = QVBoxLayout(self.checkpointPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.sprintGoalLabel = QLabel(self.checkpointPage)
        self.sprintGoalLabel.setObjectName(u"sprintGoalLabel")
        self.sprintGoalLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.sprintGoalLabel)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.checkpointPage)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.progressBar = QProgressBar(self.checkpointPage)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.progressBar)

        self.aiConfidenceLabel = QLabel(self.checkpointPage)
        self.aiConfidenceLabel.setObjectName(u"aiConfidenceLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.aiConfidenceLabel)

        self.aiConfidenceGauge = QProgressBar(self.checkpointPage)
        self.aiConfidenceGauge.setObjectName(u"aiConfidenceGauge")
        self.aiConfidenceGauge.setValue(0)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.aiConfidenceGauge)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.nextTaskLabel = QLabel(self.checkpointPage)
        self.nextTaskLabel.setObjectName(u"nextTaskLabel")
        self.nextTaskLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.nextTaskLabel)

        self.actionButtonStackedWidget = QStackedWidget(self.checkpointPage)
        self.actionButtonStackedWidget.setObjectName(u"actionButtonStackedWidget")
        self.normalModePage = QWidget()
        self.normalModePage.setObjectName(u"normalModePage")
        self.horizontalLayout = QHBoxLayout(self.normalModePage)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.proceedButton = QPushButton(self.normalModePage)
        self.proceedButton.setObjectName(u"proceedButton")

        self.horizontalLayout.addWidget(self.proceedButton)

        self.actionButtonStackedWidget.addWidget(self.normalModePage)
        self.manualFixModePage = QWidget()
        self.manualFixModePage.setObjectName(u"manualFixModePage")
        self.horizontalLayout_manual = QHBoxLayout(self.manualFixModePage)
        self.horizontalLayout_manual.setObjectName(u"horizontalLayout_manual")
        self.horizontalSpacer_manual = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_manual.addItem(self.horizontalSpacer_manual)

        self.acknowledgeButton = QPushButton(self.manualFixModePage)
        self.acknowledgeButton.setObjectName(u"acknowledgeButton")

        self.horizontalLayout_manual.addWidget(self.acknowledgeButton)

        self.retryButton = QPushButton(self.manualFixModePage)
        self.retryButton.setObjectName(u"retryButton")

        self.horizontalLayout_manual.addWidget(self.retryButton)

        self.skipButton = QPushButton(self.manualFixModePage)
        self.skipButton.setObjectName(u"skipButton")

        self.horizontalLayout_manual.addWidget(self.skipButton)

        self.actionButtonStackedWidget.addWidget(self.manualFixModePage)

        self.verticalLayout_2.addWidget(self.actionButtonStackedWidget)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.verticalLayout_2.setStretch(4, 1)
        self.stackedWidget.addWidget(self.checkpointPage)
        self.processingPage = QWidget()
        self.processingPage.setObjectName(u"processingPage")
        self.verticalLayout_3 = QVBoxLayout(self.processingPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.statusLabel = QLabel(self.processingPage)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.statusLabel)

        self.contextLabel = QLabel(self.processingPage)
        self.contextLabel.setObjectName(u"contextLabel")
        self.contextLabel.setAlignment(Qt.AlignCenter)
        self.contextLabel.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.contextLabel)

        self.logOutputTextEdit = QTextEdit(self.processingPage)
        self.logOutputTextEdit.setObjectName(u"logOutputTextEdit")
        self.logOutputTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.logOutputTextEdit)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.continueButton = QPushButton(self.processingPage)
        self.continueButton.setObjectName(u"continueButton")

        self.horizontalLayout_2.addWidget(self.continueButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.verticalLayout_3.setStretch(2, 1)
        self.stackedWidget.addWidget(self.processingPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(GenesisPage)

        self.actionButtonStackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(GenesisPage)
    # setupUi

    def retranslateUi(self, GenesisPage):
        GenesisPage.setWindowTitle(QCoreApplication.translate("GenesisPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("GenesisPage", u"Sprint Progress Dashboard", None))
        self.sprintGoalLabel.setText(QCoreApplication.translate("GenesisPage", u"Sprint Goal: ...", None))
        self.label.setText(QCoreApplication.translate("GenesisPage", u"Sprint Completion:", None))
        self.aiConfidenceLabel.setText(QCoreApplication.translate("GenesisPage", u"AI Context Quality:", None))
        self.nextTaskLabel.setText(QCoreApplication.translate("GenesisPage", u"Next component in the plan is: '...'", None))
        self.proceedButton.setText(QCoreApplication.translate("GenesisPage", u"\u25b6\ufe0f Proceed with Next Step", None))
        self.acknowledgeButton.setText(QCoreApplication.translate("GenesisPage", u"Proceed to Next Task", None))
        self.retryButton.setText(QCoreApplication.translate("GenesisPage", u"Retry Automated Fix", None))
        self.skipButton.setText(QCoreApplication.translate("GenesisPage", u"Skip Last Task and Log Bug", None))
        self.statusLabel.setText(QCoreApplication.translate("GenesisPage", u"Status: Initializing...", None))
        self.contextLabel.setText(QCoreApplication.translate("GenesisPage", u"Context: ...", None))
        self.continueButton.setText(QCoreApplication.translate("GenesisPage", u"Continue", None))
    # retranslateUi

