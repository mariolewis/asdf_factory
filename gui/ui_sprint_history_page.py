# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sprint_history_page.ui'
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

class Ui_SprintHistoryPage(object):
    def setupUi(self, SprintHistoryPage):
        if not SprintHistoryPage.objectName():
            SprintHistoryPage.setObjectName(u"SprintHistoryPage")
        SprintHistoryPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(SprintHistoryPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(SprintHistoryPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(SprintHistoryPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(SprintHistoryPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.sprintsTableView = QTableView(SprintHistoryPage)
        self.sprintsTableView.setObjectName(u"sprintsTableView")

        self.verticalLayout.addWidget(self.sprintsTableView)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.backButton = QPushButton(SprintHistoryPage)
        self.backButton.setObjectName(u"backButton")

        self.horizontalLayout.addWidget(self.backButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.viewDetailsButton = QPushButton(SprintHistoryPage)
        self.viewDetailsButton.setObjectName(u"viewDetailsButton")

        self.horizontalLayout.addWidget(self.viewDetailsButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(SprintHistoryPage)

        QMetaObject.connectSlotsByName(SprintHistoryPage)
    # setupUi

    def retranslateUi(self, SprintHistoryPage):
        SprintHistoryPage.setWindowTitle(QCoreApplication.translate("SprintHistoryPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("SprintHistoryPage", u"Sprint History", None))
        self.instructionLabel.setText(QCoreApplication.translate("SprintHistoryPage", u"Review a summary of all completed and paused sprints for this project. Select a sprint and click 'View Details' to see the full implementation plan.", None))
        self.backButton.setText(QCoreApplication.translate("SprintHistoryPage", u"< Back", None))
        self.viewDetailsButton.setText(QCoreApplication.translate("SprintHistoryPage", u"View Development Plan", None))
    # retranslateUi

