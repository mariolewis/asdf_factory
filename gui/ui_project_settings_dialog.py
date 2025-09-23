# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'project_settings_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QSizePolicy, QSpacerItem, QStackedWidget,
    QVBoxLayout, QWidget)

class Ui_ProjectSettingsDialog(object):
    def setupUi(self, ProjectSettingsDialog):
        if not ProjectSettingsDialog.objectName():
            ProjectSettingsDialog.setObjectName(u"ProjectSettingsDialog")
        ProjectSettingsDialog.resize(500, 250)
        ProjectSettingsDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(ProjectSettingsDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(ProjectSettingsDialog)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.integrationsGroupBox = QGroupBox(ProjectSettingsDialog)
        self.integrationsGroupBox.setObjectName(u"integrationsGroupBox")
        self.verticalLayout_2 = QVBoxLayout(self.integrationsGroupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.providerLabel = QLabel(self.integrationsGroupBox)
        self.providerLabel.setObjectName(u"providerLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.providerLabel)

        self.providerComboBox = QComboBox(self.integrationsGroupBox)
        self.providerComboBox.addItem("")
        self.providerComboBox.addItem("")
        self.providerComboBox.setObjectName(u"providerComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.providerComboBox)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.providerStackedWidget = QStackedWidget(self.integrationsGroupBox)
        self.providerStackedWidget.setObjectName(u"providerStackedWidget")
        self.noProviderPage = QWidget()
        self.noProviderPage.setObjectName(u"noProviderPage")
        self.verticalLayout_3 = QVBoxLayout(self.noProviderPage)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.noProviderLabel = QLabel(self.noProviderPage)
        self.noProviderLabel.setObjectName(u"noProviderLabel")

        self.verticalLayout_3.addWidget(self.noProviderLabel)

        self.providerStackedWidget.addWidget(self.noProviderPage)
        self.jiraPage = QWidget()
        self.jiraPage.setObjectName(u"jiraPage")
        self.formLayout_2 = QFormLayout(self.jiraPage)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.projectKeyLabel = QLabel(self.jiraPage)
        self.projectKeyLabel.setObjectName(u"projectKeyLabel")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.projectKeyLabel)

        self.projectKeyLineEdit = QLineEdit(self.jiraPage)
        self.projectKeyLineEdit.setObjectName(u"projectKeyLineEdit")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.projectKeyLineEdit)

        self.epicTypeIdLabel = QLabel(self.jiraPage)
        self.epicTypeIdLabel.setObjectName(u"epicTypeIdLabel")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.epicTypeIdLabel)

        self.epicTypeIdLineEdit = QLineEdit(self.jiraPage)
        self.epicTypeIdLineEdit.setObjectName(u"epicTypeIdLineEdit")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.epicTypeIdLineEdit)

        self.storyTypeIdLabel = QLabel(self.jiraPage)
        self.storyTypeIdLabel.setObjectName(u"storyTypeIdLabel")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.storyTypeIdLabel)

        self.storyTypeIdLineEdit = QLineEdit(self.jiraPage)
        self.storyTypeIdLineEdit.setObjectName(u"storyTypeIdLineEdit")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.storyTypeIdLineEdit)

        self.taskTypeIdLabel = QLabel(self.jiraPage)
        self.taskTypeIdLabel.setObjectName(u"taskTypeIdLabel")

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.taskTypeIdLabel)

        self.bugTypeIdLabel = QLabel(self.jiraPage)
        self.bugTypeIdLabel.setObjectName(u"bugTypeIdLabel")

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.LabelRole, self.bugTypeIdLabel)

        self.bugTypeIdLineEdit = QLineEdit(self.jiraPage)
        self.bugTypeIdLineEdit.setObjectName(u"bugTypeIdLineEdit")

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.FieldRole, self.bugTypeIdLineEdit)

        self.changeRequestTypeIdLabel = QLabel(self.jiraPage)
        self.changeRequestTypeIdLabel.setObjectName(u"changeRequestTypeIdLabel")

        self.formLayout_2.setWidget(5, QFormLayout.ItemRole.LabelRole, self.changeRequestTypeIdLabel)

        self.changeRequestTypeIdLineEdit = QLineEdit(self.jiraPage)
        self.changeRequestTypeIdLineEdit.setObjectName(u"changeRequestTypeIdLineEdit")

        self.formLayout_2.setWidget(5, QFormLayout.ItemRole.FieldRole, self.changeRequestTypeIdLineEdit)

        self.taskTypeIdLineEdit = QLineEdit(self.jiraPage)
        self.taskTypeIdLineEdit.setObjectName(u"taskTypeIdLineEdit")

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.taskTypeIdLineEdit)

        self.providerStackedWidget.addWidget(self.jiraPage)

        self.verticalLayout_2.addWidget(self.providerStackedWidget)


        self.verticalLayout.addWidget(self.integrationsGroupBox)

        self.testCommandsGroupBox = QGroupBox(ProjectSettingsDialog)
        self.testCommandsGroupBox.setObjectName(u"testCommandsGroupBox")
        self.formLayout_3 = QFormLayout(self.testCommandsGroupBox)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.backendTestCommandLabel = QLabel(self.testCommandsGroupBox)
        self.backendTestCommandLabel.setObjectName(u"backendTestCommandLabel")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.backendTestCommandLabel)

        self.backendTestCommandLineEdit = QLineEdit(self.testCommandsGroupBox)
        self.backendTestCommandLineEdit.setObjectName(u"backendTestCommandLineEdit")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.backendTestCommandLineEdit)

        self.uiTestCommandLabel = QLabel(self.testCommandsGroupBox)
        self.uiTestCommandLabel.setObjectName(u"uiTestCommandLabel")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.uiTestCommandLabel)

        self.uiTestCommandLineEdit = QLineEdit(self.testCommandsGroupBox)
        self.uiTestCommandLineEdit.setObjectName(u"uiTestCommandLineEdit")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.uiTestCommandLineEdit)


        self.verticalLayout.addWidget(self.testCommandsGroupBox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(ProjectSettingsDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(ProjectSettingsDialog)
        self.buttonBox.accepted.connect(ProjectSettingsDialog.accept)
        self.buttonBox.rejected.connect(ProjectSettingsDialog.reject)

        self.providerStackedWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(ProjectSettingsDialog)
    # setupUi

    def retranslateUi(self, ProjectSettingsDialog):
        ProjectSettingsDialog.setWindowTitle(QCoreApplication.translate("ProjectSettingsDialog", u"Project Settings", None))
        self.headerLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Project-Specific Settings", None))
        self.integrationsGroupBox.setTitle(QCoreApplication.translate("ProjectSettingsDialog", u"Integrations", None))
        self.providerLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Integration Provider:", None))
        self.providerComboBox.setItemText(0, QCoreApplication.translate("ProjectSettingsDialog", u"None", None))
        self.providerComboBox.setItemText(1, QCoreApplication.translate("ProjectSettingsDialog", u"Jira", None))

        self.noProviderLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"No integration provider selected for this project.", None))
        self.projectKeyLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Project Key:", None))
#if QT_CONFIG(tooltip)
        self.projectKeyLineEdit.setToolTip(QCoreApplication.translate("ProjectSettingsDialog", u"The short code for your project in Jira (e.g., ASDF, PROJ).", None))
#endif // QT_CONFIG(tooltip)
        self.epicTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Epic Type ID:", None))
        self.storyTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Story Type ID:", None))
        self.taskTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Task Type ID:", None))
        self.bugTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Bug Type ID:", None))
        self.changeRequestTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Change Request Type ID:", None))
#if QT_CONFIG(tooltip)
        self.changeRequestTypeIdLineEdit.setToolTip(QCoreApplication.translate("ProjectSettingsDialog", u"Optional: The ID for a custom 'Change Request' issue type.", None))
#endif // QT_CONFIG(tooltip)
        self.testCommandsGroupBox.setTitle(QCoreApplication.translate("ProjectSettingsDialog", u"Test Command Configuration", None))
        self.backendTestCommandLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Backend Test Command:", None))
        self.uiTestCommandLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Automated UI Test Command:", None))
    # retranslateUi

