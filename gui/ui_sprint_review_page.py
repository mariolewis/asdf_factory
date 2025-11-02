# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sprint_review_page.ui'
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

class Ui_SprintReviewPage(object):
    def setupUi(self, SprintReviewPage):
        if not SprintReviewPage.objectName():
            SprintReviewPage.setObjectName(u"SprintReviewPage")
        SprintReviewPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(SprintReviewPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(SprintReviewPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(SprintReviewPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(SprintReviewPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.summaryTextEdit = QTextEdit(SprintReviewPage)
        self.summaryTextEdit.setObjectName(u"summaryTextEdit")
        self.summaryTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.summaryTextEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.exportSummaryButton = QPushButton(SprintReviewPage)
        self.exportSummaryButton.setObjectName(u"exportSummaryButton")

        self.horizontalLayout.addWidget(self.exportSummaryButton)

        self.returnToBacklogButton = QPushButton(SprintReviewPage)
        self.returnToBacklogButton.setObjectName(u"returnToBacklogButton")

        self.horizontalLayout.addWidget(self.returnToBacklogButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(SprintReviewPage)

        QMetaObject.connectSlotsByName(SprintReviewPage)
    # setupUi

    def retranslateUi(self, SprintReviewPage):
        SprintReviewPage.setWindowTitle(QCoreApplication.translate("SprintReviewPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("SprintReviewPage", u"Sprint Review", None))
        self.instructionLabel.setText(QCoreApplication.translate("SprintReviewPage", u"The sprint is complete and all regression tests have passed. Review the summary below. You can export a detailed report or return to the backlog to plan the next sprint.", None))
        self.exportSummaryButton.setText(QCoreApplication.translate("SprintReviewPage", u"Export Sprint Summary...", None))
        self.returnToBacklogButton.setText(QCoreApplication.translate("SprintReviewPage", u"Return to Backlog", None))
    # retranslateUi

