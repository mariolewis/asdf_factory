# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sprint_planning_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton,
    QSizePolicy, QSpacerItem, QSplitter, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_SprintPlanningPage(object):
    def setupUi(self, SprintPlanningPage):
        if not SprintPlanningPage.objectName():
            SprintPlanningPage.setObjectName(u"SprintPlanningPage")
        SprintPlanningPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(SprintPlanningPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(SprintPlanningPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(SprintPlanningPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.mainSplitter = QSplitter(SprintPlanningPage)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Horizontal)
        self.sprintScopeWidget = QWidget(self.mainSplitter)
        self.sprintScopeWidget.setObjectName(u"sprintScopeWidget")
        self.verticalLayout_2 = QVBoxLayout(self.sprintScopeWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.sprintScopeLabel = QLabel(self.sprintScopeWidget)
        self.sprintScopeLabel.setObjectName(u"sprintScopeLabel")

        self.verticalLayout_2.addWidget(self.sprintScopeLabel)

        self.sprintScopeListWidget = QListWidget(self.sprintScopeWidget)
        self.sprintScopeListWidget.setObjectName(u"sprintScopeListWidget")
        self.sprintScopeListWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.verticalLayout_2.addWidget(self.sprintScopeListWidget)

        self.mainSplitter.addWidget(self.sprintScopeWidget)
        self.implementationPlanWidget = QWidget(self.mainSplitter)
        self.implementationPlanWidget.setObjectName(u"implementationPlanWidget")
        self.verticalLayout_3 = QVBoxLayout(self.implementationPlanWidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.planTabWidget = QTabWidget(self.implementationPlanWidget)
        self.planTabWidget.setObjectName(u"planTabWidget")
        self.planTab = QWidget()
        self.planTab.setObjectName(u"planTab")
        self.verticalLayout_4 = QVBoxLayout(self.planTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.implementationPlanTextEdit = QTextEdit(self.planTab)
        self.implementationPlanTextEdit.setObjectName(u"implementationPlanTextEdit")
        self.implementationPlanTextEdit.setReadOnly(True)

        self.verticalLayout_4.addWidget(self.implementationPlanTextEdit)

        self.planTabWidget.addTab(self.planTab, "")
        self.advisoryTab = QWidget()
        self.advisoryTab.setObjectName(u"advisoryTab")
        self.verticalLayout_5 = QVBoxLayout(self.advisoryTab)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.advisoryGroupBox = QGroupBox(self.advisoryTab)
        self.advisoryGroupBox.setObjectName(u"advisoryGroupBox")
        self.verticalLayout_6 = QVBoxLayout(self.advisoryGroupBox)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, 5, -1, 5)
        self.advisoryInstructionLabel = QLabel(self.advisoryGroupBox)
        self.advisoryInstructionLabel.setObjectName(u"advisoryInstructionLabel")
        self.advisoryInstructionLabel.setWordWrap(True)

        self.verticalLayout_6.addWidget(self.advisoryInstructionLabel)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.runAuditButton = QPushButton(self.advisoryGroupBox)
        self.runAuditButton.setObjectName(u"runAuditButton")

        self.horizontalLayout_2.addWidget(self.runAuditButton)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)


        self.verticalLayout_6.addLayout(self.horizontalLayout_2)

        self.auditResultTextEdit = QTextEdit(self.advisoryGroupBox)
        self.auditResultTextEdit.setObjectName(u"auditResultTextEdit")
        self.auditResultTextEdit.setReadOnly(True)

        self.verticalLayout_6.addWidget(self.auditResultTextEdit)

        self.verticalLayout_6.setStretch(2, 1)

        self.verticalLayout_5.addWidget(self.advisoryGroupBox)

        self.planTabWidget.addTab(self.advisoryTab, "")

        self.verticalLayout_3.addWidget(self.planTabWidget)

        self.mainSplitter.addWidget(self.implementationPlanWidget)

        self.verticalLayout.addWidget(self.mainSplitter)

        self.metricsLabel = QLabel(SprintPlanningPage)
        self.metricsLabel.setObjectName(u"metricsLabel")

        self.verticalLayout.addWidget(self.metricsLabel)

        self.complexityLegendLabel = QLabel(SprintPlanningPage)
        self.complexityLegendLabel.setObjectName(u"complexityLegendLabel")

        self.verticalLayout.addWidget(self.complexityLegendLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.removeFromSprintButton = QPushButton(SprintPlanningPage)
        self.removeFromSprintButton.setObjectName(u"removeFromSprintButton")

        self.horizontalLayout.addWidget(self.removeFromSprintButton)

        self.cancelSprintButton = QPushButton(SprintPlanningPage)
        self.cancelSprintButton.setObjectName(u"cancelSprintButton")

        self.horizontalLayout.addWidget(self.cancelSprintButton)

        self.refinePlanButton = QPushButton(SprintPlanningPage)
        self.refinePlanButton.setObjectName(u"refinePlanButton")

        self.horizontalLayout.addWidget(self.refinePlanButton)

        self.savePlanButton = QPushButton(SprintPlanningPage)
        self.savePlanButton.setObjectName(u"savePlanButton")

        self.horizontalLayout.addWidget(self.savePlanButton)

        self.startSprintButton = QPushButton(SprintPlanningPage)
        self.startSprintButton.setObjectName(u"startSprintButton")

        self.horizontalLayout.addWidget(self.startSprintButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout.setStretch(2, 1)

        self.retranslateUi(SprintPlanningPage)

        self.planTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(SprintPlanningPage)
    # setupUi

    def retranslateUi(self, SprintPlanningPage):
        SprintPlanningPage.setWindowTitle(QCoreApplication.translate("SprintPlanningPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("SprintPlanningPage", u"Sprint Planning", None))
        self.sprintScopeLabel.setText(QCoreApplication.translate("SprintPlanningPage", u"Sprint Scope", None))
        self.planTabWidget.setTabText(self.planTabWidget.indexOf(self.planTab), QCoreApplication.translate("SprintPlanningPage", u"Implementation Plan", None))
        self.advisoryGroupBox.setTitle("")
        self.advisoryInstructionLabel.setText(QCoreApplication.translate("SprintPlanningPage", u"Audit the plan to ensure the generated code will meet project specifications:", None))
        self.runAuditButton.setText(QCoreApplication.translate("SprintPlanningPage", u"Run Audit...", None))
        self.planTabWidget.setTabText(self.planTabWidget.indexOf(self.advisoryTab), QCoreApplication.translate("SprintPlanningPage", u"AI Advisory Panel", None))
        self.metricsLabel.setText(QCoreApplication.translate("SprintPlanningPage", u"Items: 0 | Total Complexity: 0 story points | Development Tasks: 0", None))
        self.complexityLegendLabel.setText(QCoreApplication.translate("SprintPlanningPage", u"<b>Complexity Estimation:</b> Small = 1 story point, Medium = 3 story points, Large = 5 story points", None))
        self.removeFromSprintButton.setText(QCoreApplication.translate("SprintPlanningPage", u"Remove from Sprint", None))
        self.cancelSprintButton.setText(QCoreApplication.translate("SprintPlanningPage", u"Cancel Sprint", None))
        self.refinePlanButton.setText(QCoreApplication.translate("SprintPlanningPage", u"Refine Plan...", None))
        self.savePlanButton.setText(QCoreApplication.translate("SprintPlanningPage", u"Save Plan...", None))
        self.startSprintButton.setText(QCoreApplication.translate("SprintPlanningPage", u"Start Sprint", None))
    # retranslateUi

