# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'project_complete_page.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_ProjectCompletePage(object):
    def setupUi(self, ProjectCompletePage):
        if not ProjectCompletePage.objectName():
            ProjectCompletePage.setObjectName(u"ProjectCompletePage")
        ProjectCompletePage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(ProjectCompletePage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.headerLabel = QLabel(ProjectCompletePage)
        self.headerLabel.setObjectName(u"headerLabel")
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")
        self.headerLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.headerLabel)

        self.projectNameLabel = QLabel(ProjectCompletePage)
        self.projectNameLabel.setObjectName(u"projectNameLabel")
        self.projectNameLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.projectNameLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.backButton = QPushButton(ProjectCompletePage)
        self.backButton.setObjectName(u"backButton")

        self.horizontalLayout.addWidget(self.backButton)

        self.exportButton = QPushButton(ProjectCompletePage)
        self.exportButton.setObjectName(u"exportButton")

        self.horizontalLayout.addWidget(self.exportButton)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(ProjectCompletePage)

        QMetaObject.connectSlotsByName(ProjectCompletePage)
    # setupUi

    def retranslateUi(self, ProjectCompletePage):
        ProjectCompletePage.setWindowTitle(QCoreApplication.translate("ProjectCompletePage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("ProjectCompletePage", u"Project Complete", None))
        self.projectNameLabel.setText(QCoreApplication.translate("ProjectCompletePage", u"Project 'Project Name' has been completed successfully.", None))
        self.backButton.setText(QCoreApplication.translate("ProjectCompletePage", u"<-- Back to Main Window", None))
        self.exportButton.setText(QCoreApplication.translate("ProjectCompletePage", u"Close & Export Project", None))
    # retranslateUi

