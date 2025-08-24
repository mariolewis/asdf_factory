# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'documents_page.ui'
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

class Ui_DocumentsPage(object):
    def setupUi(self, DocumentsPage):
        if not DocumentsPage.objectName():
            DocumentsPage.setObjectName(u"DocumentsPage")
        DocumentsPage.resize(700, 500)
        self.verticalLayout = QVBoxLayout(DocumentsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(DocumentsPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(DocumentsPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(DocumentsPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.documentsTableView = QTableView(DocumentsPage)
        self.documentsTableView.setObjectName(u"documentsTableView")

        self.verticalLayout.addWidget(self.documentsTableView)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.backButton = QPushButton(DocumentsPage)
        self.backButton.setObjectName(u"backButton")

        self.horizontalLayout.addWidget(self.backButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.viewButton = QPushButton(DocumentsPage)
        self.viewButton.setObjectName(u"viewButton")

        self.horizontalLayout.addWidget(self.viewButton)

        self.exportButton = QPushButton(DocumentsPage)
        self.exportButton.setObjectName(u"exportButton")

        self.horizontalLayout.addWidget(self.exportButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(DocumentsPage)

        QMetaObject.connectSlotsByName(DocumentsPage)
    # setupUi

    def retranslateUi(self, DocumentsPage):
        DocumentsPage.setWindowTitle(QCoreApplication.translate("DocumentsPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("DocumentsPage", u"Project Documents", None))
        self.instructionLabel.setText(QCoreApplication.translate("DocumentsPage", u"View and export version-controlled documents for the active project.", None))
        self.backButton.setText(QCoreApplication.translate("DocumentsPage", u"<-- Back to Main Workflow", None))
        self.viewButton.setText(QCoreApplication.translate("DocumentsPage", u"View Selected Document", None))
        self.exportButton.setText(QCoreApplication.translate("DocumentsPage", u"Export Document", None))
    # retranslateUi

