# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'backlog_ratification_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTableView, QVBoxLayout, QWidget)

class Ui_BacklogRatificationPage(object):
    def setupUi(self, BacklogRatificationPage):
        if not BacklogRatificationPage.objectName():
            BacklogRatificationPage.setObjectName(u"BacklogRatificationPage")
        BacklogRatificationPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(BacklogRatificationPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(BacklogRatificationPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(BacklogRatificationPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(BacklogRatificationPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.backlogTableView = QTableView(BacklogRatificationPage)
        self.backlogTableView.setObjectName(u"backlogTableView")

        self.verticalLayout.addWidget(self.backlogTableView)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.addItemButton = QPushButton(BacklogRatificationPage)
        self.addItemButton.setObjectName(u"addItemButton")

        self.horizontalLayout.addWidget(self.addItemButton)

        self.deleteItemButton = QPushButton(BacklogRatificationPage)
        self.deleteItemButton.setObjectName(u"deleteItemButton")

        self.horizontalLayout.addWidget(self.deleteItemButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.ratifyButton = QPushButton(BacklogRatificationPage)
        self.ratifyButton.setObjectName(u"ratifyButton")

        self.horizontalLayout.addWidget(self.ratifyButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(BacklogRatificationPage)

        QMetaObject.connectSlotsByName(BacklogRatificationPage)
    # setupUi

    def retranslateUi(self, BacklogRatificationPage):
        BacklogRatificationPage.setWindowTitle(QCoreApplication.translate("BacklogRatificationPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("BacklogRatificationPage", u"Backlog Ratification", None))
        self.instructionLabel.setText(QCoreApplication.translate("BacklogRatificationPage", u"The AI has generated the following backlog items. Review them below. You can edit any item by double-clicking its cell. Use the buttons to add new items or delete selected ones before ratifying the final backlog.", None))
        self.addItemButton.setText(QCoreApplication.translate("BacklogRatificationPage", u"Add New Item", None))
        self.deleteItemButton.setText(QCoreApplication.translate("BacklogRatificationPage", u"Delete Selected Item", None))
        self.ratifyButton.setText(QCoreApplication.translate("BacklogRatificationPage", u"Ratify Backlog", None))
    # retranslateUi

