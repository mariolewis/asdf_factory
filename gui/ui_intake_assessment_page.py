# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'intake_assessment_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_IntakeAssessmentPage(object):
    def setupUi(self, IntakeAssessmentPage):
        if not IntakeAssessmentPage.objectName():
            IntakeAssessmentPage.setObjectName(u"IntakeAssessmentPage")
        IntakeAssessmentPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(IntakeAssessmentPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(IntakeAssessmentPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(IntakeAssessmentPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(IntakeAssessmentPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.summaryGroupBox = QGroupBox(IntakeAssessmentPage)
        self.summaryGroupBox.setObjectName(u"summaryGroupBox")
        self.verticalLayout_2 = QVBoxLayout(self.summaryGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.summaryTextEdit = QTextEdit(self.summaryGroupBox)
        self.summaryTextEdit.setObjectName(u"summaryTextEdit")
        self.summaryTextEdit.setReadOnly(True)

        self.verticalLayout_2.addWidget(self.summaryTextEdit)


        self.verticalLayout.addWidget(self.summaryGroupBox)

        self.planGroupBox = QGroupBox(IntakeAssessmentPage)
        self.planGroupBox.setObjectName(u"planGroupBox")
        self.verticalLayout_3 = QVBoxLayout(self.planGroupBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.scrollArea = QScrollArea(self.planGroupBox)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 742, 123))
        self.verticalLayout_4 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.planFormLayout = QFormLayout()
        self.planFormLayout.setObjectName(u"planFormLayout")

        self.verticalLayout_4.addLayout(self.planFormLayout)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_3.addWidget(self.scrollArea)


        self.verticalLayout.addWidget(self.planGroupBox)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.overrideButton = QPushButton(IntakeAssessmentPage)
        self.overrideButton.setObjectName(u"overrideButton")

        self.horizontalLayout.addWidget(self.overrideButton)

        self.acceptProposalButton = QPushButton(IntakeAssessmentPage)
        self.acceptProposalButton.setObjectName(u"acceptProposalButton")

        self.horizontalLayout.addWidget(self.acceptProposalButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout.setStretch(4, 1)

        self.retranslateUi(IntakeAssessmentPage)

        QMetaObject.connectSlotsByName(IntakeAssessmentPage)
    # setupUi

    def retranslateUi(self, IntakeAssessmentPage):
        IntakeAssessmentPage.setWindowTitle(QCoreApplication.translate("IntakeAssessmentPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("IntakeAssessmentPage", u"Intelligent Intake Assessment", None))
        self.instructionLabel.setText(QCoreApplication.translate("IntakeAssessmentPage", u"The AI has analyzed the project brief and proposes the following workflow. You can accept this proportional plan or override it to run the full, standard workflow.", None))
        self.summaryGroupBox.setTitle(QCoreApplication.translate("IntakeAssessmentPage", u"Assessment Summary", None))
        self.planGroupBox.setTitle(QCoreApplication.translate("IntakeAssessmentPage", u"Proposed Plan", None))
        self.overrideButton.setText(QCoreApplication.translate("IntakeAssessmentPage", u"Override & Run Full Workflow", None))
        self.acceptProposalButton.setText(QCoreApplication.translate("IntakeAssessmentPage", u"Accept Proposal & Proceed", None))
    # retranslateUi

