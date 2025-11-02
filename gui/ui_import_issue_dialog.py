# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'import_issue_dialog.ui'
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
    QFormLayout, QLabel, QLineEdit, QPlainTextEdit,
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

class Ui_ImportIssueDialog(object):
    def setupUi(self, ImportIssueDialog):
        if not ImportIssueDialog.objectName():
            ImportIssueDialog.setObjectName(u"ImportIssueDialog")
        ImportIssueDialog.resize(500, 250)
        ImportIssueDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(ImportIssueDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.headerLabel = QLabel(ImportIssueDialog)
        self.headerLabel.setObjectName(u"headerLabel")

        self.verticalLayout.addWidget(self.headerLabel)

        self.tabWidget = QTabWidget(ImportIssueDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.byIdTab = QWidget()
        self.byIdTab.setObjectName(u"byIdTab")
        self.formLayout = QFormLayout(self.byIdTab)
        self.formLayout.setObjectName(u"formLayout")
        self.idInstructionLabel = QLabel(self.byIdTab)
        self.idInstructionLabel.setObjectName(u"idInstructionLabel")
        self.idInstructionLabel.setWordWrap(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.SpanningRole, self.idInstructionLabel)

        self.issueIdLabel = QLabel(self.byIdTab)
        self.issueIdLabel.setObjectName(u"issueIdLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.issueIdLabel)

        self.issueIdLineEdit = QLineEdit(self.byIdTab)
        self.issueIdLineEdit.setObjectName(u"issueIdLineEdit")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.issueIdLineEdit)

        self.tabWidget.addTab(self.byIdTab, "")
        self.byQueryTab = QWidget()
        self.byQueryTab.setObjectName(u"byQueryTab")
        self.verticalLayout_2 = QVBoxLayout(self.byQueryTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.queryInstructionLabel = QLabel(self.byQueryTab)
        self.queryInstructionLabel.setObjectName(u"queryInstructionLabel")

        self.verticalLayout_2.addWidget(self.queryInstructionLabel)

        self.queryTextEdit = QPlainTextEdit(self.byQueryTab)
        self.queryTextEdit.setObjectName(u"queryTextEdit")

        self.verticalLayout_2.addWidget(self.queryTextEdit)

        self.tabWidget.addTab(self.byQueryTab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.buttonBox = QDialogButtonBox(ImportIssueDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(ImportIssueDialog)
        self.buttonBox.accepted.connect(ImportIssueDialog.accept)
        self.buttonBox.rejected.connect(ImportIssueDialog.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ImportIssueDialog)
    # setupUi

    def retranslateUi(self, ImportIssueDialog):
        ImportIssueDialog.setWindowTitle(QCoreApplication.translate("ImportIssueDialog", u"Import from External Tool", None))
        self.headerLabel.setText(QCoreApplication.translate("ImportIssueDialog", u"Import Backlog Item(s)", None))
        self.idInstructionLabel.setText(QCoreApplication.translate("ImportIssueDialog", u"Enter the exact Issue ID or Key from the external tool (e.g., PROJ-123).", None))
        self.issueIdLabel.setText(QCoreApplication.translate("ImportIssueDialog", u"Issue ID:", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.byIdTab), QCoreApplication.translate("ImportIssueDialog", u"Import by ID", None))
        self.queryInstructionLabel.setText(QCoreApplication.translate("ImportIssueDialog", u"Enter the query string or filter to find issues to import (e.g., JQL for Jira).", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.byQueryTab), QCoreApplication.translate("ImportIssueDialog", u"Import by Query", None))
    # retranslateUi

