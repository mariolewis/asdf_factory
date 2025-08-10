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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget)

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

        self.statusLabel = QLabel(PreflightCheckPage)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.statusLabel)

        self.detailsTextEdit = QTextEdit(PreflightCheckPage)
        self.detailsTextEdit.setObjectName(u"detailsTextEdit")
        self.detailsTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.detailsTextEdit)

        self.actionStackedWidget = QStackedWidget(PreflightCheckPage)
        self.actionStackedWidget.setObjectName(u"actionStackedWidget")
        self.loadingPage = QWidget()
        self.loadingPage.setObjectName(u"loadingPage")
        self.actionStackedWidget.addWidget(self.loadingPage)
        self.successPage = QWidget()
        self.successPage.setObjectName(u"successPage")
        self.horizontalLayout = QHBoxLayout(self.successPage)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.proceedButton = QPushButton(self.successPage)
        self.proceedButton.setObjectName(u"proceedButton")

        self.horizontalLayout.addWidget(self.proceedButton)

        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.actionStackedWidget.addWidget(self.successPage)
        self.stateDriftPage = QWidget()
        self.stateDriftPage.setObjectName(u"stateDriftPage")
        self.verticalLayout_2 = QVBoxLayout(self.stateDriftPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.stateDriftLabel = QLabel(self.stateDriftPage)
        self.stateDriftLabel.setObjectName(u"stateDriftLabel")
        self.stateDriftLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.stateDriftLabel)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.manualResolveButton = QPushButton(self.stateDriftPage)
        self.manualResolveButton.setObjectName(u"manualResolveButton")

        self.gridLayout.addWidget(self.manualResolveButton, 0, 0, 1, 1)

        self.manualResolveLabel = QLabel(self.stateDriftPage)
        self.manualResolveLabel.setObjectName(u"manualResolveLabel")
        self.manualResolveLabel.setWordWrap(True)

        self.gridLayout.addWidget(self.manualResolveLabel, 0, 1, 1, 1)

        self.discardButton = QPushButton(self.stateDriftPage)
        self.discardButton.setObjectName(u"discardButton")

        self.gridLayout.addWidget(self.discardButton, 1, 0, 1, 1)

        self.discardLabel = QLabel(self.stateDriftPage)
        self.discardLabel.setObjectName(u"discardLabel")
        self.discardLabel.setWordWrap(True)

        self.gridLayout.addWidget(self.discardLabel, 1, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)

        self.actionStackedWidget.addWidget(self.stateDriftPage)
        self.errorPage = QWidget()
        self.errorPage.setObjectName(u"errorPage")
        self.horizontalLayout_3 = QHBoxLayout(self.errorPage)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.backButton = QPushButton(self.errorPage)
        self.backButton.setObjectName(u"backButton")

        self.horizontalLayout_3.addWidget(self.backButton)

        self.horizontalSpacer_2 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.actionStackedWidget.addWidget(self.errorPage)

        self.verticalLayout.addWidget(self.actionStackedWidget)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(PreflightCheckPage)

        QMetaObject.connectSlotsByName(PreflightCheckPage)
    # setupUi

    def retranslateUi(self, PreflightCheckPage):
        PreflightCheckPage.setWindowTitle(QCoreApplication.translate("PreflightCheckPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("PreflightCheckPage", u"Continue Project", None))
        self.statusLabel.setText(QCoreApplication.translate("PreflightCheckPage", u"Status: Running checks...", None))
        self.proceedButton.setText(QCoreApplication.translate("PreflightCheckPage", u"Proceed to Project", None))
        self.stateDriftLabel.setText(QCoreApplication.translate("PreflightCheckPage", u"<b>Action Required:</b> To prevent conflicts, please resolve the state of the repository.", None))
        self.manualResolveButton.setText(QCoreApplication.translate("PreflightCheckPage", u"I Will Resolve Manually", None))
        self.manualResolveLabel.setText(QCoreApplication.translate("PreflightCheckPage", u"(Closes the project and returns to the main screen. You can then use external tools like 'git commit' before reloading.)", None))
        self.discardButton.setText(QCoreApplication.translate("PreflightCheckPage", u"Discard All Uncommitted Changes", None))
        self.discardLabel.setText(QCoreApplication.translate("PreflightCheckPage", u"(Deletes all local changes that have not been committed to Git. This action cannot be undone.)", None))
        self.backButton.setText(QCoreApplication.translate("PreflightCheckPage", u"<-- Back to Project List", None))
    # retranslateUi

