# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'project_dashboard_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QGridLayout,
    QGroupBox, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_ProjectDashboardPage(object):
    def setupUi(self, ProjectDashboardPage):
        if not ProjectDashboardPage.objectName():
            ProjectDashboardPage.setObjectName(u"ProjectDashboardPage")
        ProjectDashboardPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(ProjectDashboardPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(ProjectDashboardPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(ProjectDashboardPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(ProjectDashboardPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.metricsGroupBox = QGroupBox(ProjectDashboardPage)
        self.metricsGroupBox.setObjectName(u"metricsGroupBox")
        self.formLayout = QFormLayout(self.metricsGroupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.languagesLabel = QLabel(self.metricsGroupBox)
        self.languagesLabel.setObjectName(u"languagesLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.languagesLabel)

        self.languagesValueLabel = QLabel(self.metricsGroupBox)
        self.languagesValueLabel.setObjectName(u"languagesValueLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.languagesValueLabel)

        self.filesLabel = QLabel(self.metricsGroupBox)
        self.filesLabel.setObjectName(u"filesLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.filesLabel)

        self.filesValueLabel = QLabel(self.metricsGroupBox)
        self.filesValueLabel.setObjectName(u"filesValueLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.filesValueLabel)


        self.verticalLayout.addWidget(self.metricsGroupBox)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.pathGroupBox = QGroupBox(ProjectDashboardPage)
        self.pathGroupBox.setObjectName(u"pathGroupBox")
        self.gridLayout = QGridLayout(self.pathGroupBox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.maintainButton = QPushButton(self.pathGroupBox)
        self.maintainButton.setObjectName(u"maintainButton")

        self.gridLayout.addWidget(self.maintainButton, 0, 0, 1, 1)

        self.maintainGuidanceLabel = QLabel(self.pathGroupBox)
        self.maintainGuidanceLabel.setObjectName(u"maintainGuidanceLabel")
        self.maintainGuidanceLabel.setWordWrap(True)

        self.gridLayout.addWidget(self.maintainGuidanceLabel, 0, 1, 1, 1)

        self.quickFixButton = QPushButton(self.pathGroupBox)
        self.quickFixButton.setObjectName(u"quickFixButton")

        self.gridLayout.addWidget(self.quickFixButton, 1, 0, 1, 1)

        self.quickFixGuidanceLabel = QLabel(self.pathGroupBox)
        self.quickFixGuidanceLabel.setObjectName(u"quickFixGuidanceLabel")
        self.quickFixGuidanceLabel.setWordWrap(True)

        self.gridLayout.addWidget(self.quickFixGuidanceLabel, 1, 1, 1, 1)


        self.verticalLayout.addWidget(self.pathGroupBox)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)


        self.retranslateUi(ProjectDashboardPage)

        QMetaObject.connectSlotsByName(ProjectDashboardPage)
    # setupUi

    def retranslateUi(self, ProjectDashboardPage):
        ProjectDashboardPage.setWindowTitle(QCoreApplication.translate("ProjectDashboardPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("ProjectDashboardPage", u"Project Archeology Complete", None))
        self.instructionLabel.setText(QCoreApplication.translate("ProjectDashboardPage", u"The system has completed its analysis of the codebase. Review the summary below and choose the strategic path for this project.", None))
        self.metricsGroupBox.setTitle(QCoreApplication.translate("ProjectDashboardPage", u"Analysis Summary", None))
        self.languagesLabel.setText(QCoreApplication.translate("ProjectDashboardPage", u"Languages Detected:", None))
        self.languagesValueLabel.setText(QCoreApplication.translate("ProjectDashboardPage", u"Calculating...", None))
        self.filesLabel.setText(QCoreApplication.translate("ProjectDashboardPage", u"Source Files Scanned:", None))
        self.filesValueLabel.setText(QCoreApplication.translate("ProjectDashboardPage", u"Calculating...", None))
        self.pathGroupBox.setTitle(QCoreApplication.translate("ProjectDashboardPage", u"Choose Your Path", None))
        self.maintainButton.setText(QCoreApplication.translate("ProjectDashboardPage", u"Maintain && Enhance", None))
        self.maintainGuidanceLabel.setText(QCoreApplication.translate("ProjectDashboardPage", u"Choose this path to manage the project using a formal backlog. This is best for tracking features, planning future sprints, and maintaining a structured overview of all work. You will be taken to the backlog view where you can add new user stories and bug reports.", None))
        self.quickFixButton.setText(QCoreApplication.translate("ProjectDashboardPage", u"Add to Backlog / Quick Fix", None))
        self.quickFixGuidanceLabel.setText(QCoreApplication.translate("ProjectDashboardPage", u"Choose this path to go to the Project Backlog. This is the standard path for adding new bug reports, features, or other work items before planning a new sprint.", None))
    # retranslateUi

