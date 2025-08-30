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
    QSpacerItem, QStackedWidget, QTableView, QVBoxLayout,
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

        self.crTableView = QTableView(CRManagementPage)
        self.crTableView.setObjectName(u"crTableView")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.crTableView.sizePolicy().hasHeightForWidth())
        self.crTableView.setSizePolicy(sizePolicy)
        self.crTableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.crTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.crTableView.setSortingEnabled(True)

        self.verticalLayout.addWidget(self.crTableView)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.backButton = QPushButton(CRManagementPage)
        self.backButton.setObjectName(u"backButton")

        self.horizontalLayout.addWidget(self.backButton)

        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

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

        self.reorderButton = QPushButton(self.normalModePage)
        self.reorderButton.setObjectName(u"reorderButton")

        self.horizontalLayout_2.addWidget(self.reorderButton)

        self.clearSelectionButton = QPushButton(self.normalModePage)
        self.clearSelectionButton.setObjectName(u"clearSelectionButton")

        self.horizontalLayout_2.addWidget(self.clearSelectionButton)

        self.proceedToTechSpecButton = QPushButton(self.normalModePage)
        self.proceedToTechSpecButton.setObjectName(u"proceedToTechSpecButton")

        self.horizontalLayout_2.addWidget(self.proceedToTechSpecButton)

        self.moreActionsButton = QPushButton(self.normalModePage)
        self.moreActionsButton.setObjectName(u"moreActionsButton")

        self.horizontalLayout_2.addWidget(self.moreActionsButton)

        self.actionButtonStackedWidget.addWidget(self.normalModePage)
        self.reorderModePage = QWidget()
        self.reorderModePage.setObjectName(u"reorderModePage")
        self.horizontalLayout_3 = QHBoxLayout(self.reorderModePage)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.moveUpButton = QPushButton(self.reorderModePage)
        self.moveUpButton.setObjectName(u"moveUpButton")

        self.horizontalLayout_3.addWidget(self.moveUpButton)

        self.moveDownButton = QPushButton(self.reorderModePage)
        self.moveDownButton.setObjectName(u"moveDownButton")

        self.horizontalLayout_3.addWidget(self.moveDownButton)

        self.cancelReorderButton = QPushButton(self.reorderModePage)
        self.cancelReorderButton.setObjectName(u"cancelReorderButton")

        self.horizontalLayout_3.addWidget(self.cancelReorderButton)

        self.saveOrderButton = QPushButton(self.reorderModePage)
        self.saveOrderButton.setObjectName(u"saveOrderButton")

        self.horizontalLayout_3.addWidget(self.saveOrderButton)

        self.actionButtonStackedWidget.addWidget(self.reorderModePage)

        self.horizontalLayout.addWidget(self.actionButtonStackedWidget)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(CRManagementPage)

        QMetaObject.connectSlotsByName(CRManagementPage)
    # setupUi

    def retranslateUi(self, CRManagementPage):
        CRManagementPage.setWindowTitle(QCoreApplication.translate("CRManagementPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("CRManagementPage", u"Project Backlog", None))
        self.instructionLabel.setText(QCoreApplication.translate("CRManagementPage", u"Select an item from the register to view available actions. Implementation is enabled for items with an 'IMPACT_ANALYZED' status after the main development plan is complete.", None))
        self.backButton.setText(QCoreApplication.translate("CRManagementPage", u"< Back", None))
        self.addNewItemButton.setText(QCoreApplication.translate("CRManagementPage", u"Add New Item...", None))
        self.reorderButton.setText(QCoreApplication.translate("CRManagementPage", u"Reorder Backlog", None))
        self.clearSelectionButton.setText(QCoreApplication.translate("CRManagementPage", u"Clear Selection", None))
        self.proceedToTechSpecButton.setText(QCoreApplication.translate("CRManagementPage", u"Proceed to Technical Specification", None))
        self.moreActionsButton.setText(QCoreApplication.translate("CRManagementPage", u"More Actions...", None))
        self.moveUpButton.setText(QCoreApplication.translate("CRManagementPage", u"Move Up", None))
        self.moveDownButton.setText(QCoreApplication.translate("CRManagementPage", u"Move Down", None))
        self.cancelReorderButton.setText(QCoreApplication.translate("CRManagementPage", u"Cancel", None))
        self.saveOrderButton.setText(QCoreApplication.translate("CRManagementPage", u"Save Order", None))
    # retranslateUi

