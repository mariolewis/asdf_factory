# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'reports_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_ReportsPage(object):
    def setupUi(self, ReportsPage):
        if not ReportsPage.objectName():
            ReportsPage.setObjectName(u"ReportsPage")
        ReportsPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(ReportsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(ReportsPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(ReportsPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(ReportsPage)
        self.instructionLabel.setObjectName(u"instructionLabel")

        self.verticalLayout.addWidget(self.instructionLabel)

        self.reportsGrid = QGridLayout()
        self.reportsGrid.setObjectName(u"reportsGrid")
        self.healthSnapshotCard = QGroupBox(ReportsPage)
        self.healthSnapshotCard.setObjectName(u"healthSnapshotCard")
        self.verticalLayout_2 = QVBoxLayout(self.healthSnapshotCard)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_2 = QLabel(self.healthSnapshotCard)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.label_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.generateHealthSnapshotButton = QPushButton(self.healthSnapshotCard)
        self.generateHealthSnapshotButton.setObjectName(u"generateHealthSnapshotButton")

        self.verticalLayout_2.addWidget(self.generateHealthSnapshotButton)


        self.reportsGrid.addWidget(self.healthSnapshotCard, 0, 0, 1, 1)

        self.traceabilityCard = QGroupBox(ReportsPage)
        self.traceabilityCard.setObjectName(u"traceabilityCard")
        self.verticalLayout_3 = QVBoxLayout(self.traceabilityCard)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_3 = QLabel(self.traceabilityCard)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.label_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)

        self.generateTraceabilityMatrixButton = QPushButton(self.traceabilityCard)
        self.generateTraceabilityMatrixButton.setObjectName(u"generateTraceabilityMatrixButton")

        self.verticalLayout_3.addWidget(self.generateTraceabilityMatrixButton)


        self.reportsGrid.addWidget(self.traceabilityCard, 0, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.reportsGrid.addItem(self.horizontalSpacer, 0, 2, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.reportsGrid.addItem(self.verticalSpacer_3, 1, 0, 1, 1)


        self.verticalLayout.addLayout(self.reportsGrid)

        self.mainVerticalSpacer = QSpacerItem(20, 179, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.mainVerticalSpacer)

        self.horizontalLayout_back = QHBoxLayout()
        self.horizontalLayout_back.setObjectName(u"horizontalLayout_back")
        self.backButton = QPushButton(ReportsPage)
        self.backButton.setObjectName(u"backButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.backButton.sizePolicy().hasHeightForWidth())
        self.backButton.setSizePolicy(sizePolicy)

        self.horizontalLayout_back.addWidget(self.backButton)

        self.horizontalSpacer_back = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_back.addItem(self.horizontalSpacer_back)


        self.verticalLayout.addLayout(self.horizontalLayout_back)


        self.retranslateUi(ReportsPage)

        QMetaObject.connectSlotsByName(ReportsPage)
    # setupUi

    def retranslateUi(self, ReportsPage):
        ReportsPage.setWindowTitle(QCoreApplication.translate("ReportsPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("ReportsPage", u"Reports Hub", None))
        self.instructionLabel.setText(QCoreApplication.translate("ReportsPage", u"Generate high-level reports for project analysis and stakeholder updates.", None))
        self.healthSnapshotCard.setTitle(QCoreApplication.translate("ReportsPage", u"Project Health Snapshot", None))
        self.label_2.setText(QCoreApplication.translate("ReportsPage", u"A one-page visual summary of backlog completion and code quality. Ideal for stakeholder updates.", None))
        self.generateHealthSnapshotButton.setText(QCoreApplication.translate("ReportsPage", u"Generate .docx", None))
        self.traceabilityCard.setTitle(QCoreApplication.translate("ReportsPage", u"Traceability Matrix", None))
        self.label_3.setText(QCoreApplication.translate("ReportsPage", u"An end-to-end report mapping backlog items to their implemented code artifacts.", None))
        self.generateTraceabilityMatrixButton.setText(QCoreApplication.translate("ReportsPage", u"Generate .xlsx", None))
        self.backButton.setText(QCoreApplication.translate("ReportsPage", u"< Back", None))
    # retranslateUi

