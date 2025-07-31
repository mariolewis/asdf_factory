# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings_page.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialogButtonBox,
    QFormLayout, QLabel, QSizePolicy, QSpinBox,
    QTabWidget, QVBoxLayout, QWidget)

class Ui_SettingsPage(object):
    def setupUi(self, SettingsPage):
        if not SettingsPage.objectName():
            SettingsPage.setObjectName(u"SettingsPage")
        SettingsPage.resize(600, 500)
        self.verticalLayout = QVBoxLayout(SettingsPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(SettingsPage)
        self.headerLabel.setObjectName(u"headerLabel")
        self.headerLabel.setStyleSheet(u"font-size: 18pt; font-weight: bold;")

        self.verticalLayout.addWidget(self.headerLabel)

        self.mainTabWidget = QTabWidget(SettingsPage)
        self.mainTabWidget.setObjectName(u"mainTabWidget")
        self.llmProvidersTab = QWidget()
        self.llmProvidersTab.setObjectName(u"llmProvidersTab")
        self.formLayout = QFormLayout(self.llmProvidersTab)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.llmProvidersTab)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.providerComboBox = QComboBox(self.llmProvidersTab)
        self.providerComboBox.setObjectName(u"providerComboBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.providerComboBox)

        self.mainTabWidget.addTab(self.llmProvidersTab, "")
        self.factoryBehaviorTab = QWidget()
        self.factoryBehaviorTab.setObjectName(u"factoryBehaviorTab")
        self.formLayout_factory = QFormLayout(self.factoryBehaviorTab)
        self.formLayout_factory.setObjectName(u"formLayout_factory")
        self.label_6 = QLabel(self.factoryBehaviorTab)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_factory.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.maxDebugSpinBox = QSpinBox(self.factoryBehaviorTab)
        self.maxDebugSpinBox.setObjectName(u"maxDebugSpinBox")

        self.formLayout_factory.setWidget(0, QFormLayout.ItemRole.FieldRole, self.maxDebugSpinBox)

        self.mainTabWidget.addTab(self.factoryBehaviorTab, "")

        self.verticalLayout.addWidget(self.mainTabWidget)

        self.buttonBox = QDialogButtonBox(SettingsPage)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel|QDialogButtonBox.RestoreDefaults)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(SettingsPage)

        self.mainTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(SettingsPage)
    # setupUi

    def retranslateUi(self, SettingsPage):
        SettingsPage.setWindowTitle(QCoreApplication.translate("SettingsPage", u"Form", None))
        self.headerLabel.setText(QCoreApplication.translate("SettingsPage", u"Factory Settings", None))
        self.label.setText(QCoreApplication.translate("SettingsPage", u"Select LLM Provider:", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.llmProvidersTab), QCoreApplication.translate("SettingsPage", u"LLM Providers", None))
        self.label_6.setText(QCoreApplication.translate("SettingsPage", u"Max Debug Attempts:", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.factoryBehaviorTab), QCoreApplication.translate("SettingsPage", u"Factory Behavior", None))
    # retranslateUi

