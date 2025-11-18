# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'project_settings_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QSizePolicy, QStackedWidget, QTabWidget, QVBoxLayout,
    QWidget)

class Ui_ProjectSettingsDialog(object):
    def setupUi(self, ProjectSettingsDialog):
        if not ProjectSettingsDialog.objectName():
            ProjectSettingsDialog.setObjectName(u"ProjectSettingsDialog")
        ProjectSettingsDialog.resize(550, 400)
        ProjectSettingsDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(ProjectSettingsDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(ProjectSettingsDialog)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.tabWidget = QTabWidget(ProjectSettingsDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.integrationsTab = QWidget()
        self.integrationsTab.setObjectName(u"integrationsTab")
        self.verticalLayout_2 = QVBoxLayout(self.integrationsTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.providerLabel = QLabel(self.integrationsTab)
        self.providerLabel.setObjectName(u"providerLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.providerLabel)

        self.providerComboBox = QComboBox(self.integrationsTab)
        self.providerComboBox.addItem("")
        self.providerComboBox.addItem("")
        self.providerComboBox.setObjectName(u"providerComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.providerComboBox)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.providerStackedWidget = QStackedWidget(self.integrationsTab)
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

        self.tabWidget.addTab(self.integrationsTab, "")
        self.commandsTab = QWidget()
        self.commandsTab.setObjectName(u"commandsTab")
        self.formLayout_3 = QFormLayout(self.commandsTab)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.backendTestCommandLabel = QLabel(self.commandsTab)
        self.backendTestCommandLabel.setObjectName(u"backendTestCommandLabel")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.backendTestCommandLabel)

        self.backendTestCommandLineEdit = QLineEdit(self.commandsTab)
        self.backendTestCommandLineEdit.setObjectName(u"backendTestCommandLineEdit")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.backendTestCommandLineEdit)

        self.integrationTestCommandLabel = QLabel(self.commandsTab)
        self.integrationTestCommandLabel.setObjectName(u"integrationTestCommandLabel")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.integrationTestCommandLabel)

        self.integrationTestCommandLineEdit = QLineEdit(self.commandsTab)
        self.integrationTestCommandLineEdit.setObjectName(u"integrationTestCommandLineEdit")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.integrationTestCommandLineEdit)

        self.uiTestCommandLabel = QLabel(self.commandsTab)
        self.uiTestCommandLabel.setObjectName(u"uiTestCommandLabel")

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.LabelRole, self.uiTestCommandLabel)

        self.uiTestCommandLineEdit = QLineEdit(self.commandsTab)
        self.uiTestCommandLineEdit.setObjectName(u"uiTestCommandLineEdit")

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.FieldRole, self.uiTestCommandLineEdit)

        self.tabWidget.addTab(self.commandsTab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.buttonBox = QDialogButtonBox(ProjectSettingsDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(ProjectSettingsDialog)
        self.buttonBox.accepted.connect(ProjectSettingsDialog.accept)
        self.buttonBox.rejected.connect(ProjectSettingsDialog.reject)

        self.tabWidget.setCurrentIndex(0)
        self.providerStackedWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(ProjectSettingsDialog)
    # setupUi

    def retranslateUi(self, ProjectSettingsDialog):
        ProjectSettingsDialog.setWindowTitle(QCoreApplication.translate("ProjectSettingsDialog", u"Project Settings", None))
        self.headerLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Project-Specific Settings", None))
        self.providerLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Integration Provider:", None))
        self.providerComboBox.setItemText(0, QCoreApplication.translate("ProjectSettingsDialog", u"None", None))
        self.providerComboBox.setItemText(1, QCoreApplication.translate("ProjectSettingsDialog", u"Jira", None))

        self.noProviderLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"No integration provider selected for this project.", None))
        self.projectKeyLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Project Key:", None))
#if QT_CONFIG(tooltip)
        self.projectKeyLineEdit.setToolTip(QCoreApplication.translate("ProjectSettingsDialog", u"The short code for your project in Jira (e.g., Klyve, PROJ).", None))
#endif // QT_CONFIG(tooltip)
        self.epicTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Epic Type ID:", None))
        self.storyTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Story Type ID:", None))
        self.taskTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Task Type ID:", None))
        self.bugTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Bug Type ID:", None))
        self.changeRequestTypeIdLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Jira Change Request Type ID:", None))
#if QT_CONFIG(tooltip)
        self.changeRequestTypeIdLineEdit.setToolTip(QCoreApplication.translate("ProjectSettingsDialog", u"Optional: The ID for a custom 'Change Request' issue type.", None))
#endif // QT_CONFIG(tooltip)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.integrationsTab), QCoreApplication.translate("ProjectSettingsDialog", u"Integrations", None))
        self.backendTestCommandLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Backend Regression Test Command:", None))
        self.integrationTestCommandLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Backend Integration Test Command (Optional):", None))
        self.uiTestCommandLabel.setText(QCoreApplication.translate("ProjectSettingsDialog", u"Automated UI Test Command (Optional):", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commandsTab), QCoreApplication.translate("ProjectSettingsDialog", u"Test Commands", None))
    # retranslateUi

