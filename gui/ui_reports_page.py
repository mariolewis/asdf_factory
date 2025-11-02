# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'reports_page.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QFrame,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTreeView,
    QVBoxLayout, QWidget)

class Ui_ReportsPage(object):
    def setupUi(self, ReportsPage):
        if not ReportsPage.objectName():
            ReportsPage.setObjectName(u"ReportsPage")
        ReportsPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(ReportsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(ReportsPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(ReportsPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(ReportsPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.mainHorizontalLayout = QHBoxLayout()
        self.mainHorizontalLayout.setObjectName(u"mainHorizontalLayout")
        self.reportTreeView = QTreeView(ReportsPage)
        self.reportTreeView.setObjectName(u"reportTreeView")
        self.reportTreeView.setMinimumSize(QSize(250, 0))
        self.reportTreeView.setHeaderHidden(True)

        self.mainHorizontalLayout.addWidget(self.reportTreeView)

        self.detailsPanelWidget = QWidget(ReportsPage)
        self.detailsPanelWidget.setObjectName(u"detailsPanelWidget")
        self.detailsPanelLayout = QVBoxLayout(self.detailsPanelWidget)
        self.detailsPanelLayout.setObjectName(u"detailsPanelLayout")
        self.reportTitleLabel = QLabel(self.detailsPanelWidget)
        self.reportTitleLabel.setObjectName(u"reportTitleLabel")

        self.detailsPanelLayout.addWidget(self.reportTitleLabel)

        self.reportDescriptionLabel = QLabel(self.detailsPanelWidget)
        self.reportDescriptionLabel.setObjectName(u"reportDescriptionLabel")
        self.reportDescriptionLabel.setWordWrap(True)
        self.reportDescriptionLabel.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.detailsPanelLayout.addWidget(self.reportDescriptionLabel)

        self.filterGroupBox = QGroupBox(self.detailsPanelWidget)
        self.filterGroupBox.setObjectName(u"filterGroupBox")
        self.filterGroupBox.setVisible(False)
        self.filterFormLayout = QFormLayout(self.filterGroupBox)
        self.filterFormLayout.setObjectName(u"filterFormLayout")
        self.statusFilterLabel = QLabel(self.filterGroupBox)
        self.statusFilterLabel.setObjectName(u"statusFilterLabel")
        self.statusFilterLabel.setVisible(False)

        self.filterFormLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.statusFilterLabel)

        self.statusFilterComboBox = QComboBox(self.filterGroupBox)
        self.statusFilterComboBox.setObjectName(u"statusFilterComboBox")
        self.statusFilterComboBox.setVisible(False)

        self.filterFormLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.statusFilterComboBox)

        self.typeFilterLabel = QLabel(self.filterGroupBox)
        self.typeFilterLabel.setObjectName(u"typeFilterLabel")
        self.typeFilterLabel.setVisible(False)

        self.filterFormLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.typeFilterLabel)

        self.typeFilterComboBox = QComboBox(self.filterGroupBox)
        self.typeFilterComboBox.setObjectName(u"typeFilterComboBox")
        self.typeFilterComboBox.setVisible(False)

        self.filterFormLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.typeFilterComboBox)

        self.sprintFilterLabel = QLabel(self.filterGroupBox)
        self.sprintFilterLabel.setObjectName(u"sprintFilterLabel")
        self.sprintFilterLabel.setVisible(False)

        self.filterFormLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.sprintFilterLabel)

        self.sprintFilterComboBox = QComboBox(self.filterGroupBox)
        self.sprintFilterComboBox.setObjectName(u"sprintFilterComboBox")
        self.sprintFilterComboBox.setVisible(False)

        self.filterFormLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.sprintFilterComboBox)


        self.detailsPanelLayout.addWidget(self.filterGroupBox)

        self.detailsVerticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.detailsPanelLayout.addItem(self.detailsVerticalSpacer)

        self.lastGeneratedLabel = QLabel(self.detailsPanelWidget)
        self.lastGeneratedLabel.setObjectName(u"lastGeneratedLabel")
        self.lastGeneratedLabel.setVisible(False)

        self.detailsPanelLayout.addWidget(self.lastGeneratedLabel)

        self.detailsButtonLayout = QHBoxLayout()
        self.detailsButtonLayout.setObjectName(u"detailsButtonLayout")
        self.detailsHorizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.detailsButtonLayout.addItem(self.detailsHorizontalSpacer)

        self.generateReportButton = QPushButton(self.detailsPanelWidget)
        self.generateReportButton.setObjectName(u"generateReportButton")
        self.generateReportButton.setEnabled(False)

        self.detailsButtonLayout.addWidget(self.generateReportButton)


        self.detailsPanelLayout.addLayout(self.detailsButtonLayout)


        self.mainHorizontalLayout.addWidget(self.detailsPanelWidget)

        self.mainHorizontalLayout.setStretch(1, 1)

        self.verticalLayout.addLayout(self.mainHorizontalLayout)

        self.horizontalLayout_back = QHBoxLayout()
        self.horizontalLayout_back.setObjectName(u"horizontalLayout_back")
        self.backButton = QPushButton(ReportsPage)
        self.backButton.setObjectName(u"backButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.backButton.sizePolicy().hasHeightForWidth())
        self.backButton.setSizePolicy(sizePolicy)

        self.horizontalLayout_back.addWidget(self.backButton)

        self.horizontalSpacer_back = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_back.addItem(self.horizontalSpacer_back)


        self.verticalLayout.addLayout(self.horizontalLayout_back)


        self.retranslateUi(ReportsPage)

        QMetaObject.connectSlotsByName(ReportsPage)
    # setupUi

    def retranslateUi(self, ReportsPage):
        ReportsPage.setWindowTitle(QCoreApplication.translate("ReportsPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("ReportsPage", u"Reports Hub", None))
        self.instructionLabel.setText(QCoreApplication.translate("ReportsPage", u"Select a report from the list to view details and generate it.", None))
        self.reportTitleLabel.setText(QCoreApplication.translate("ReportsPage", u"Select a Report", None))
        self.reportTitleLabel.setObjectName(QCoreApplication.translate("ReportsPage", u"reportTitleLabel", None))
        self.reportDescriptionLabel.setText(QCoreApplication.translate("ReportsPage", u"Report description will appear here.", None))
        self.filterGroupBox.setTitle(QCoreApplication.translate("ReportsPage", u"Options", None))
        self.statusFilterLabel.setText(QCoreApplication.translate("ReportsPage", u"Filter by Status:", None))
        self.typeFilterLabel.setText(QCoreApplication.translate("ReportsPage", u"Filter by Type:", None))
        self.sprintFilterLabel.setText(QCoreApplication.translate("ReportsPage", u"Select Sprint:", None))
        self.lastGeneratedLabel.setText(QCoreApplication.translate("ReportsPage", u"Last generated: N/A", None))
        self.generateReportButton.setText(QCoreApplication.translate("ReportsPage", u"Generate Report", None))
        self.backButton.setText(QCoreApplication.translate("ReportsPage", u"< Back", None))
    # retranslateUi

