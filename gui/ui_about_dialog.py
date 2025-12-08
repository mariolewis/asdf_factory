# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QLabel, QSizePolicy, QSpacerItem, QTabWidget,
    QTextEdit, QVBoxLayout, QWidget)

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        if not AboutDialog.objectName():
            AboutDialog.setObjectName(u"AboutDialog")
        AboutDialog.resize(700, 550)
        self.verticalLayout = QVBoxLayout(AboutDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(AboutDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.aboutTab = QWidget()
        self.aboutTab.setObjectName(u"aboutTab")
        self.verticalLayout_2 = QVBoxLayout(self.aboutTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer_top = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_top)

        self.brandingLabel = QLabel(self.aboutTab)
        self.brandingLabel.setObjectName(u"brandingLabel")
        self.brandingLabel.setAlignment(Qt.AlignCenter)
        self.brandingLabel.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.brandingLabel)

        self.verticalSpacer_bottom = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_bottom)

        self.tabWidget.addTab(self.aboutTab, "")
        self.eulaTab = QWidget()
        self.eulaTab.setObjectName(u"eulaTab")
        self.verticalLayout_3 = QVBoxLayout(self.eulaTab)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.eulaTextEdit = QTextEdit(self.eulaTab)
        self.eulaTextEdit.setObjectName(u"eulaTextEdit")
        self.eulaTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.eulaTextEdit)

        self.tabWidget.addTab(self.eulaTab, "")
        self.privacyTab = QWidget()
        self.privacyTab.setObjectName(u"privacyTab")
        self.verticalLayout_4 = QVBoxLayout(self.privacyTab)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.privacyTextEdit = QTextEdit(self.privacyTab)
        self.privacyTextEdit.setObjectName(u"privacyTextEdit")
        self.privacyTextEdit.setReadOnly(True)

        self.verticalLayout_4.addWidget(self.privacyTextEdit)

        self.tabWidget.addTab(self.privacyTab, "")
        self.noticesTab = QWidget()
        self.noticesTab.setObjectName(u"noticesTab")
        self.verticalLayout_5 = QVBoxLayout(self.noticesTab)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.noticesTextEdit = QTextEdit(self.noticesTab)
        self.noticesTextEdit.setObjectName(u"noticesTextEdit")
        self.noticesTextEdit.setReadOnly(True)
        self.noticesTextEdit.setLineWrapMode(QTextEdit.NoWrap)

        self.verticalLayout_5.addWidget(self.noticesTextEdit)

        self.tabWidget.addTab(self.noticesTab, "")
        self.creditsTab = QWidget()
        self.creditsTab.setObjectName(u"creditsTab")
        self.verticalLayout_credits = QVBoxLayout(self.creditsTab)
        self.verticalLayout_credits.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_credits.setObjectName(u"verticalLayout_credits")
        self.creditsTextEdit = QTextEdit(self.creditsTab)
        self.creditsTextEdit.setObjectName(u"creditsTextEdit")
        self.creditsTextEdit.setReadOnly(True)

        self.verticalLayout_credits.addWidget(self.creditsTextEdit)

        self.tabWidget.addTab(self.creditsTab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.buttonBox = QDialogButtonBox(AboutDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(AboutDialog)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AboutDialog)
    # setupUi

    def retranslateUi(self, AboutDialog):
        AboutDialog.setWindowTitle(QCoreApplication.translate("AboutDialog", u"About Klyve", None))
        self.brandingLabel.setText(QCoreApplication.translate("AboutDialog", u"Branding Text", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.aboutTab), QCoreApplication.translate("AboutDialog", u"About Klyve", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.eulaTab), QCoreApplication.translate("AboutDialog", u"EULA", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.privacyTab), QCoreApplication.translate("AboutDialog", u"Privacy Policy", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.noticesTab), QCoreApplication.translate("AboutDialog", u"Third-Party Notices", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.creditsTab), QCoreApplication.translate("AboutDialog", u"Credits", None))
    # retranslateUi

