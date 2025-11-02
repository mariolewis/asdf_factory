# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dockerization_page.ui'
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
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_DockerizationPage(object):
    def setupUi(self, DockerizationPage):
        if not DockerizationPage.objectName():
            DockerizationPage.setObjectName(u"DockerizationPage")
        DockerizationPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(DockerizationPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(DockerizationPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(DockerizationPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(DockerizationPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.autoGenerateButton = QPushButton(DockerizationPage)
        self.autoGenerateButton.setObjectName(u"autoGenerateButton")

        self.horizontalLayout.addWidget(self.autoGenerateButton)

        self.skipButton = QPushButton(DockerizationPage)
        self.skipButton.setObjectName(u"skipButton")

        self.horizontalLayout.addWidget(self.skipButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(DockerizationPage)

        QMetaObject.connectSlotsByName(DockerizationPage)
    # setupUi

    def retranslateUi(self, DockerizationPage):
        DockerizationPage.setWindowTitle(QCoreApplication.translate("DockerizationPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("DockerizationPage", u"Dockerization", None))
        self.instructionLabel.setText(QCoreApplication.translate("DockerizationPage", u"A Dockerfile defines a consistent, portable environment for the application. Choose whether to generate a Dockerfile for this project.", None))
        self.autoGenerateButton.setText(QCoreApplication.translate("DockerizationPage", u"Auto-Generate Dockerfile", None))
        self.skipButton.setText(QCoreApplication.translate("DockerizationPage", u"Skip Dockerization", None))
    # retranslateUi

