# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'reports_page.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QFrame,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTableView,
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
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(ReportsPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(ReportsPage)
        self.instructionLabel.setObjectName(u"instructionLabel")

        self.verticalLayout.addWidget(self.instructionLabel)

        self.progressSummaryGroupBox = QGroupBox(ReportsPage)
        self.progressSummaryGroupBox.setObjectName(u"progressSummaryGroupBox")
        self.verticalLayout_2 = QVBoxLayout(self.progressSummaryGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.progressFormLayout = QFormLayout()
        self.progressFormLayout.setObjectName(u"progressFormLayout")

        self.verticalLayout_2.addLayout(self.progressFormLayout)

        self.exportProgressButton = QPushButton(self.progressSummaryGroupBox)
        self.exportProgressButton.setObjectName(u"exportProgressButton")

        self.verticalLayout_2.addWidget(self.exportProgressButton)


        self.verticalLayout.addWidget(self.progressSummaryGroupBox)

        self.crBugGroupBox = QGroupBox(ReportsPage)
        self.crBugGroupBox.setObjectName(u"crBugGroupBox")
        self.verticalLayout_3 = QVBoxLayout(self.crBugGroupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.filterLabel = QLabel(self.crBugGroupBox)
        self.filterLabel.setObjectName(u"filterLabel")

        self.horizontalLayout.addWidget(self.filterLabel)

        self.crFilterComboBox = QComboBox(self.crBugGroupBox)
        self.crFilterComboBox.addItem("")
        self.crFilterComboBox.addItem("")
        self.crFilterComboBox.addItem("")
        self.crFilterComboBox.setObjectName(u"crFilterComboBox")

        self.horizontalLayout.addWidget(self.crFilterComboBox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.crTableView = QTableView(self.crBugGroupBox)
        self.crTableView.setObjectName(u"crTableView")

        self.verticalLayout_3.addWidget(self.crTableView)

        self.exportCrButton = QPushButton(self.crBugGroupBox)
        self.exportCrButton.setObjectName(u"exportCrButton")

        self.verticalLayout_3.addWidget(self.exportCrButton)


        self.verticalLayout.addWidget(self.crBugGroupBox)

        self.backButton = QPushButton(ReportsPage)
        self.backButton.setObjectName(u"backButton")

        self.verticalLayout.addWidget(self.backButton)


        self.retranslateUi(ReportsPage)

        QMetaObject.connectSlotsByName(ReportsPage)
    # setupUi

    def retranslateUi(self, ReportsPage):
        ReportsPage.setWindowTitle(QCoreApplication.translate("ReportsPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("ReportsPage", u"Project Status Reports", None))
        self.instructionLabel.setText(QCoreApplication.translate("ReportsPage", u"Showing all available reports for the currently active project.", None))
        self.progressSummaryGroupBox.setTitle(QCoreApplication.translate("ReportsPage", u"Development Progress Summary", None))
        self.exportProgressButton.setText(QCoreApplication.translate("ReportsPage", u"Export Summary to .docx", None))
        self.crBugGroupBox.setTitle(QCoreApplication.translate("ReportsPage", u"Change Requests & Bug Fixes", None))
        self.filterLabel.setText(QCoreApplication.translate("ReportsPage", u"Filter by Status:", None))
        self.crFilterComboBox.setItemText(0, QCoreApplication.translate("ReportsPage", u"Pending", None))
        self.crFilterComboBox.setItemText(1, QCoreApplication.translate("ReportsPage", u"Closed", None))
        self.crFilterComboBox.setItemText(2, QCoreApplication.translate("ReportsPage", u"All", None))

        self.exportCrButton.setText(QCoreApplication.translate("ReportsPage", u"Export This View to .docx", None))
        self.backButton.setText(QCoreApplication.translate("ReportsPage", u"<-- Back to Main Workflow", None))
    # retranslateUi

