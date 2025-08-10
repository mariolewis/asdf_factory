# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cr_management_page.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QTableView, QVBoxLayout, QWidget)

class Ui_CRManagementPage(object):
    def setupUi(self, CRManagementPage):
        if not CRManagementPage.objectName():
            CRManagementPage.setObjectName(u"CRManagementPage")
        CRManagementPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(CRManagementPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(CRManagementPage)
        self.headerLabel.setObjectName(u"headerLabel")
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(CRManagementPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(CRManagementPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.crTableView = QTableView(CRManagementPage)
        self.crTableView.setObjectName(u"crTableView")
        self.crTableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.crTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.crTableView.setSortingEnabled(True)

        self.verticalLayout.addWidget(self.crTableView)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.backButton = QPushButton(CRManagementPage)
        self.backButton.setObjectName(u"backButton")

        self.horizontalLayout.addWidget(self.backButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.editButton = QPushButton(CRManagementPage)
        self.editButton.setObjectName(u"editButton")

        self.horizontalLayout.addWidget(self.editButton)

        self.deleteButton = QPushButton(CRManagementPage)
        self.deleteButton.setObjectName(u"deleteButton")

        self.horizontalLayout.addWidget(self.deleteButton)

        self.analyzeButton = QPushButton(CRManagementPage)
        self.analyzeButton.setObjectName(u"analyzeButton")

        self.horizontalLayout.addWidget(self.analyzeButton)

        self.implementButton = QPushButton(CRManagementPage)
        self.implementButton.setObjectName(u"implementButton")

        self.horizontalLayout.addWidget(self.implementButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(CRManagementPage)

        QMetaObject.connectSlotsByName(CRManagementPage)
    # setupUi

    def retranslateUi(self, CRManagementPage):
        CRManagementPage.setWindowTitle(QCoreApplication.translate("CRManagementPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("CRManagementPage", u"Change & Bug Management", None))
        self.instructionLabel.setText(QCoreApplication.translate("CRManagementPage", u"Select an item from the register below to view available actions. Implementation of any item is only enabled after the main development plan is fully complete.", None))
        self.backButton.setText(QCoreApplication.translate("CRManagementPage", u"<-- Back to Main Workflow", None))
        self.editButton.setText(QCoreApplication.translate("CRManagementPage", u"Edit Item", None))
        self.deleteButton.setText(QCoreApplication.translate("CRManagementPage", u"Delete Item", None))
        self.analyzeButton.setText(QCoreApplication.translate("CRManagementPage", u"Run Impact Analysis", None))
        self.implementButton.setText(QCoreApplication.translate("CRManagementPage", u"Implement Item", None))
    # retranslateUi

