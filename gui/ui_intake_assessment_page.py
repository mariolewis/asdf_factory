# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'intake_assessment_page.ui'
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

        self.summaryHeaderLabel = QLabel(IntakeAssessmentPage)
        self.summaryHeaderLabel.setObjectName(u"summaryHeaderLabel")

        self.verticalLayout.addWidget(self.summaryHeaderLabel)

        self.summaryTextEdit = QTextEdit(IntakeAssessmentPage)
        self.summaryTextEdit.setObjectName(u"summaryTextEdit")
        self.summaryTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.summaryTextEdit)

        self.assessmentHeaderLabel = QLabel(IntakeAssessmentPage)
        self.assessmentHeaderLabel.setObjectName(u"assessmentHeaderLabel")

        self.verticalLayout.addWidget(self.assessmentHeaderLabel)

        self.completenessAssessmentLabel = QLabel(IntakeAssessmentPage)
        self.completenessAssessmentLabel.setObjectName(u"completenessAssessmentLabel")
        self.completenessAssessmentLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.completenessAssessmentLabel)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.backButton = QPushButton(IntakeAssessmentPage)
        self.backButton.setObjectName(u"backButton")

        self.horizontalLayout.addWidget(self.backButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.fullLifecycleButton = QPushButton(IntakeAssessmentPage)
        self.fullLifecycleButton.setObjectName(u"fullLifecycleButton")

        self.horizontalLayout.addWidget(self.fullLifecycleButton)

        self.directToDevelopmentButton = QPushButton(IntakeAssessmentPage)
        self.directToDevelopmentButton.setObjectName(u"directToDevelopmentButton")

        self.horizontalLayout.addWidget(self.directToDevelopmentButton)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(IntakeAssessmentPage)

        QMetaObject.connectSlotsByName(IntakeAssessmentPage)
    # setupUi

    def retranslateUi(self, IntakeAssessmentPage):
        IntakeAssessmentPage.setWindowTitle(QCoreApplication.translate("IntakeAssessmentPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("IntakeAssessmentPage", u"Project Input Analysis & Recommendation", None))
        self.instructionLabel.setText(QCoreApplication.translate("IntakeAssessmentPage", u"The system has analyzed your project brief. Review the summary and assessment below, then choose the desired workflow for this project.", None))
        self.summaryHeaderLabel.setText(QCoreApplication.translate("IntakeAssessmentPage", u"<b>AI Summary of Inputs</b>", None))
        self.assessmentHeaderLabel.setText(QCoreApplication.translate("IntakeAssessmentPage", u"<b>Completeness Assessment</b>", None))
        self.completenessAssessmentLabel.setText(QCoreApplication.translate("IntakeAssessmentPage", u"Assessment text will appear here...", None))
        self.backButton.setText(QCoreApplication.translate("IntakeAssessmentPage", u"Cancel", None))
        self.fullLifecycleButton.setText(QCoreApplication.translate("IntakeAssessmentPage", u"Proceed with Spec Elaboration and Development", None))
        self.directToDevelopmentButton.setText(QCoreApplication.translate("IntakeAssessmentPage", u"Proceed Directly to Development", None))
    # retranslateUi

