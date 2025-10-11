# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'decision_page.ui'
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
    QPushButton, QSizePolicy, QSpacerItem, QTextEdit,
    QVBoxLayout, QWidget)

class Ui_DecisionPage(object):
    def setupUi(self, DecisionPage):
        if not DecisionPage.objectName():
            DecisionPage.setObjectName(u"DecisionPage")
        DecisionPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(DecisionPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(DecisionPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(DecisionPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(DecisionPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.detailsTextEdit = QTextEdit(DecisionPage)
        self.detailsTextEdit.setObjectName(u"detailsTextEdit")
        self.detailsTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.detailsTextEdit)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.buttonLayout.addItem(self.horizontalSpacer)

        self.option1Button = QPushButton(DecisionPage)
        self.option1Button.setObjectName(u"option1Button")

        self.buttonLayout.addWidget(self.option1Button)

        self.option2Button = QPushButton(DecisionPage)
        self.option2Button.setObjectName(u"option2Button")

        self.buttonLayout.addWidget(self.option2Button)

        self.option3Button = QPushButton(DecisionPage)
        self.option3Button.setObjectName(u"option3Button")

        self.buttonLayout.addWidget(self.option3Button)


        self.verticalLayout.addLayout(self.buttonLayout)

        self.verticalLayout.setStretch(3, 1)

        self.retranslateUi(DecisionPage)

        QMetaObject.connectSlotsByName(DecisionPage)
    # setupUi

    def retranslateUi(self, DecisionPage):
        DecisionPage.setWindowTitle(QCoreApplication.translate("DecisionPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("DecisionPage", u"Action Required", None))
        self.instructionLabel.setText(QCoreApplication.translate("DecisionPage", u"Instructions for the decision will be displayed here.", None))
        self.option1Button.setText(QCoreApplication.translate("DecisionPage", u"Option 1", None))
        self.option2Button.setText(QCoreApplication.translate("DecisionPage", u"Option 2", None))
        self.option3Button.setText(QCoreApplication.translate("DecisionPage", u"Option 3", None))
    # retranslateUi

