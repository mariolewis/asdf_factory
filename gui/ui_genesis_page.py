# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'genesis_page.ui'
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
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget)

class Ui_GenesisPage(object):
    def setupUi(self, GenesisPage):
        if not GenesisPage.objectName():
            GenesisPage.setObjectName(u"GenesisPage")
        GenesisPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(GenesisPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(GenesisPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(GenesisPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.stackedWidget = QStackedWidget(GenesisPage)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.checkpointPage = QWidget()
        self.checkpointPage.setObjectName(u"checkpointPage")
        self.verticalLayout_2 = QVBoxLayout(self.checkpointPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.checkpointHeaderLabel = QLabel(self.checkpointPage)
        self.checkpointHeaderLabel.setObjectName(u"checkpointHeaderLabel")

        self.verticalLayout_2.addWidget(self.checkpointHeaderLabel)

        self.progressBar = QProgressBar(self.checkpointPage)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(24)
        self.progressBar.setTextVisible(True)

        self.verticalLayout_2.addWidget(self.progressBar)

        self.nextTaskLabel = QLabel(self.checkpointPage)
        self.nextTaskLabel.setObjectName(u"nextTaskLabel")
        self.nextTaskLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.nextTaskLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.proceedButton = QPushButton(self.checkpointPage)
        self.proceedButton.setObjectName(u"proceedButton")

        self.horizontalLayout.addWidget(self.proceedButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.stackedWidget.addWidget(self.checkpointPage)
        self.processingPage = QWidget()
        self.processingPage.setObjectName(u"processingPage")
        self.verticalLayout_3 = QVBoxLayout(self.processingPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.processingLabel = QLabel(self.processingPage)
        self.processingLabel.setObjectName(u"processingLabel")
        self.processingLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.processingLabel)

        self.logOutputTextEdit = QTextEdit(self.processingPage)
        self.logOutputTextEdit.setObjectName(u"logOutputTextEdit")
        self.logOutputTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.logOutputTextEdit)

        self.stackedWidget.addWidget(self.processingPage)

        self.verticalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(GenesisPage)

        QMetaObject.connectSlotsByName(GenesisPage)
    # setupUi

    def retranslateUi(self, GenesisPage):
        GenesisPage.setWindowTitle(QCoreApplication.translate("GenesisPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("GenesisPage", u"Component Development", None))
        self.checkpointHeaderLabel.setText(QCoreApplication.translate("GenesisPage", u"Development Checkpoint", None))
        self.nextTaskLabel.setText(QCoreApplication.translate("GenesisPage", u"Next component in the plan is: '...'", None))
        self.proceedButton.setText(QCoreApplication.translate("GenesisPage", u"\u25b6\ufe0f Proceed with Next Step", None))
        self.processingLabel.setText(QCoreApplication.translate("GenesisPage", u"Executing Development Step...", None))
    # retranslateUi

