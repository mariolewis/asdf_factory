# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preflight_check_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QSpacerItem, QStackedWidget, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_PreflightCheckPage(object):
    def setupUi(self, PreflightCheckPage):
        if not PreflightCheckPage.objectName():
            PreflightCheckPage.setObjectName(u"PreflightCheckPage")
        PreflightCheckPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(PreflightCheckPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(PreflightCheckPage)
        self.headerLabel.setObjectName(u"headerLabel")
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(PreflightCheckPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(PreflightCheckPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.loadingPage = QWidget()
        self.loadingPage.setObjectName(u"loadingPage")
        self.verticalLayout_2 = QVBoxLayout(self.loadingPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.loadingLabel = QLabel(self.loadingPage)
        self.loadingLabel.setObjectName(u"loadingLabel")
        self.loadingLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.loadingLabel)

        self.stackedWidget.addWidget(self.loadingPage)
        self.resultsPage = QWidget()
        self.resultsPage.setObjectName(u"resultsPage")
        self.verticalLayout_3 = QVBoxLayout(self.resultsPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.statusLabel = QLabel(self.resultsPage)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setStyleSheet(u"font-size: 14pt;")

        self.verticalLayout_3.addWidget(self.statusLabel)

        self.messageTextEdit = QTextEdit(self.resultsPage)
        self.messageTextEdit.setObjectName(u"messageTextEdit")
        self.messageTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.messageTextEdit)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")

        self.verticalLayout_3.addLayout(self.buttonLayout)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.stackedWidget.addWidget(self.resultsPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(PreflightCheckPage)

        QMetaObject.connectSlotsByName(PreflightCheckPage)
    # setupUi

    def retranslateUi(self, PreflightCheckPage):
        PreflightCheckPage.setWindowTitle(QCoreApplication.translate("PreflightCheckPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("PreflightCheckPage", u"Pre-flight Check Resolution", None))
        self.loadingLabel.setText(QCoreApplication.translate("PreflightCheckPage", u"Running pre-flight checks...", None))
        self.statusLabel.setText(QCoreApplication.translate("PreflightCheckPage", u"Status: All Checks Passed", None))
    # retranslateUi

