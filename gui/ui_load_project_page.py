# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'load_project_page.ui'
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

class Ui_LoadProjectPage(object):
    def setupUi(self, LoadProjectPage):
        if not LoadProjectPage.objectName():
            LoadProjectPage.setObjectName(u"LoadProjectPage")
        LoadProjectPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(LoadProjectPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(LoadProjectPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(LoadProjectPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(LoadProjectPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.projectsTableView = QTableView(LoadProjectPage)
        self.projectsTableView.setObjectName(u"projectsTableView")

        self.verticalLayout.addWidget(self.projectsTableView)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.backButton = QPushButton(LoadProjectPage)
        self.backButton.setObjectName(u"backButton")

        self.horizontalLayout.addWidget(self.backButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.deleteButton = QPushButton(LoadProjectPage)
        self.deleteButton.setObjectName(u"deleteButton")

        self.horizontalLayout.addWidget(self.deleteButton)

        self.loadButton = QPushButton(LoadProjectPage)
        self.loadButton.setObjectName(u"loadButton")

        self.horizontalLayout.addWidget(self.loadButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(LoadProjectPage)

        QMetaObject.connectSlotsByName(LoadProjectPage)
    # setupUi

    def retranslateUi(self, LoadProjectPage):
        LoadProjectPage.setWindowTitle(QCoreApplication.translate("LoadProjectPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("LoadProjectPage", u"Load an Exported Project", None))
        self.instructionLabel.setText(QCoreApplication.translate("LoadProjectPage", u"Select a project from the history below to load it into the factory. Loading a project will archive any currently active work.", None))
        self.backButton.setText(QCoreApplication.translate("LoadProjectPage", u"Back to Main Page", None))
        self.deleteButton.setText(QCoreApplication.translate("LoadProjectPage", u"Delete Selected Project", None))
        self.loadButton.setText(QCoreApplication.translate("LoadProjectPage", u"Load Selected Project", None))
    # retranslateUi

