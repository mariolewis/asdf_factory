# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'on_demand_task_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_OnDemandTaskPage(object):
    def setupUi(self, OnDemandTaskPage):
        if not OnDemandTaskPage.objectName():
            OnDemandTaskPage.setObjectName(u"OnDemandTaskPage")
        OnDemandTaskPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(OnDemandTaskPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(OnDemandTaskPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(OnDemandTaskPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.logOutputTextEdit = QTextEdit(OnDemandTaskPage)
        self.logOutputTextEdit.setObjectName(u"logOutputTextEdit")
        self.logOutputTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.logOutputTextEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.returnButton = QPushButton(OnDemandTaskPage)
        self.returnButton.setObjectName(u"returnButton")

        self.horizontalLayout.addWidget(self.returnButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(OnDemandTaskPage)

        QMetaObject.connectSlotsByName(OnDemandTaskPage)
    # setupUi

    def retranslateUi(self, OnDemandTaskPage):
        OnDemandTaskPage.setWindowTitle(QCoreApplication.translate("OnDemandTaskPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("OnDemandTaskPage", u"On-Demand Task", None))
        self.returnButton.setText(QCoreApplication.translate("OnDemandTaskPage", u"Return", None))
    # retranslateUi

