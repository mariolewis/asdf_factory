# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cr_management_page.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QStackedWidget, QTreeView, QVBoxLayout,
    QWidget)

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

        self.crTreeView = QTreeView(CRManagementPage)
        self.crTreeView.setObjectName(u"crTreeView")
        self.crTreeView.setDragDropMode(QAbstractItemView.InternalMove)

        self.verticalLayout.addWidget(self.crTreeView)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.backButton = QPushButton(CRManagementPage)
        self.backButton.setObjectName(u"backButton")

        self.horizontalLayout.addWidget(self.backButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.actionButtonStackedWidget = QStackedWidget(CRManagementPage)
        self.actionButtonStackedWidget.setObjectName(u"actionButtonStackedWidget")
        self.normalModePage = QWidget()
        self.normalModePage.setObjectName(u"normalModePage")
        self.horizontalLayout_2 = QHBoxLayout(self.normalModePage)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.addNewItemButton = QPushButton(self.normalModePage)
        self.addNewItemButton.setObjectName(u"addNewItemButton")

        self.horizontalLayout_2.addWidget(self.addNewItemButton)

        self.saveBacklogButton = QPushButton(self.normalModePage)
        self.saveBacklogButton.setObjectName(u"saveBacklogButton")

        self.horizontalLayout_2.addWidget(self.saveBacklogButton)

        self.primaryActionButton = QPushButton(self.normalModePage)
        self.primaryActionButton.setObjectName(u"primaryActionButton")

        self.horizontalLayout_2.addWidget(self.primaryActionButton)

        self.moreActionsButton = QPushButton(self.normalModePage)
        self.moreActionsButton.setObjectName(u"moreActionsButton")

        self.horizontalLayout_2.addWidget(self.moreActionsButton)

        self.actionButtonStackedWidget.addWidget(self.normalModePage)

        self.horizontalLayout.addWidget(self.actionButtonStackedWidget)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout.setStretch(3, 1)

        self.retranslateUi(CRManagementPage)

        QMetaObject.connectSlotsByName(CRManagementPage)
    # setupUi

    def retranslateUi(self, CRManagementPage):
        CRManagementPage.setWindowTitle(QCoreApplication.translate("CRManagementPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("CRManagementPage", u"Project Backlog", None))
        self.instructionLabel.setText(QCoreApplication.translate("CRManagementPage", u"Manage the project hierarchy. Double-click to edit an item. Right-click an item to add children or delete.", None))
        self.backButton.setText(QCoreApplication.translate("CRManagementPage", u"< Back", None))
        self.addNewItemButton.setText(QCoreApplication.translate("CRManagementPage", u"Add New Item...", None))
        self.saveBacklogButton.setText(QCoreApplication.translate("CRManagementPage", u"Export Backlog to .xlsx...", None))
        self.primaryActionButton.setText(QCoreApplication.translate("CRManagementPage", u"Plan Sprint", None))
        self.moreActionsButton.setText(QCoreApplication.translate("CRManagementPage", u"More Actions...", None))
    # retranslateUi

