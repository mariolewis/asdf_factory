# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'delivery_assessment_page.ui'
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
    QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QSizePolicy, QSpacerItem, QTextEdit, QVBoxLayout,
    QWidget)

class Ui_DeliveryAssessmentPage(object):
    def setupUi(self, DeliveryAssessmentPage):
        if not DeliveryAssessmentPage.objectName():
            DeliveryAssessmentPage.setObjectName(u"DeliveryAssessmentPage")
        DeliveryAssessmentPage.resize(800, 600)
        self.verticalLayout = QVBoxLayout(DeliveryAssessmentPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.headerLabel = QLabel(DeliveryAssessmentPage)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.line = QFrame(DeliveryAssessmentPage)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.instructionLabel = QLabel(DeliveryAssessmentPage)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.assessmentGroupBox = QGroupBox(DeliveryAssessmentPage)
        self.assessmentGroupBox.setObjectName(u"assessmentGroupBox")
        self.verticalLayout_2 = QVBoxLayout(self.assessmentGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.automationConfidenceLabel = QLabel(self.assessmentGroupBox)
        self.automationConfidenceLabel.setObjectName(u"automationConfidenceLabel")
        self.automationConfidenceLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.automationConfidenceLabel)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.featureScopeLabel = QLabel(self.assessmentGroupBox)
        self.featureScopeLabel.setObjectName(u"featureScopeLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.featureScopeLabel)

        self.featureScopeGauge = QProgressBar(self.assessmentGroupBox)
        self.featureScopeGauge.setObjectName(u"featureScopeGauge")
        self.featureScopeGauge.setValue(0)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.featureScopeGauge)

        self.dataSchemaLabel = QLabel(self.assessmentGroupBox)
        self.dataSchemaLabel.setObjectName(u"dataSchemaLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.dataSchemaLabel)

        self.dataSchemaGauge = QProgressBar(self.assessmentGroupBox)
        self.dataSchemaGauge.setObjectName(u"dataSchemaGauge")
        self.dataSchemaGauge.setValue(0)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.dataSchemaGauge)

        self.uiuxLabel = QLabel(self.assessmentGroupBox)
        self.uiuxLabel.setObjectName(u"uiuxLabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.uiuxLabel)

        self.uiuxGauge = QProgressBar(self.assessmentGroupBox)
        self.uiuxGauge.setObjectName(u"uiuxGauge")
        self.uiuxGauge.setValue(0)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.uiuxGauge)

        self.integrationsLabel = QLabel(self.assessmentGroupBox)
        self.integrationsLabel.setObjectName(u"integrationsLabel")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.integrationsLabel)

        self.integrationsGauge = QProgressBar(self.assessmentGroupBox)
        self.integrationsGauge.setObjectName(u"integrationsGauge")
        self.integrationsGauge.setValue(0)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.integrationsGauge)


        self.verticalLayout_2.addLayout(self.formLayout)


        self.verticalLayout.addWidget(self.assessmentGroupBox)

        self.detailsTextEdit = QTextEdit(DeliveryAssessmentPage)
        self.detailsTextEdit.setObjectName(u"detailsTextEdit")
        self.detailsTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.detailsTextEdit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.cancelButton = QPushButton(DeliveryAssessmentPage)
        self.cancelButton.setObjectName(u"cancelButton")

        self.horizontalLayout.addWidget(self.cancelButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.approveButton = QPushButton(DeliveryAssessmentPage)
        self.approveButton.setObjectName(u"approveButton")

        self.horizontalLayout.addWidget(self.approveButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout.setStretch(4, 1)

        self.retranslateUi(DeliveryAssessmentPage)

        QMetaObject.connectSlotsByName(DeliveryAssessmentPage)
    # setupUi

    def retranslateUi(self, DeliveryAssessmentPage):
        DeliveryAssessmentPage.setWindowTitle(QCoreApplication.translate("DeliveryAssessmentPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("DeliveryAssessmentPage", u"Delivery Automation Risk Assessment", None))
        self.instructionLabel.setText(QCoreApplication.translate("DeliveryAssessmentPage", u"The system has analyzed the project's complexity. The 'Automation Confidence Level' indicates how well-suited the project is for AI-driven development. Review the assessment and approve to proceed.", None))
        self.assessmentGroupBox.setTitle("")
        self.automationConfidenceLabel.setText(QCoreApplication.translate("DeliveryAssessmentPage", u"Automation Confidence Level:", None))
        self.featureScopeLabel.setText(QCoreApplication.translate("DeliveryAssessmentPage", u"Feature Scope:", None))
        self.dataSchemaLabel.setText(QCoreApplication.translate("DeliveryAssessmentPage", u"Data Schema:", None))
        self.uiuxLabel.setText(QCoreApplication.translate("DeliveryAssessmentPage", u"UI/UX:", None))
        self.integrationsLabel.setText(QCoreApplication.translate("DeliveryAssessmentPage", u"Integrations:", None))
        self.cancelButton.setText(QCoreApplication.translate("DeliveryAssessmentPage", u"Cancel Project", None))
        self.approveButton.setText(QCoreApplication.translate("DeliveryAssessmentPage", u"Acknowledge & Proceed to Spec Review", None))
    # retranslateUi

