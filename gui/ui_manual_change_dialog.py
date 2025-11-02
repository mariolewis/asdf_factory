# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'manual_change_dialog.ui'
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
    QLabel, QListWidget, QListWidgetItem, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_ManualChangeDialog(object):
    def setupUi(self, ManualChangeDialog):
        if not ManualChangeDialog.objectName():
            ManualChangeDialog.setObjectName(u"ManualChangeDialog")
        ManualChangeDialog.resize(600, 450)
        ManualChangeDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(ManualChangeDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.instructionLabel = QLabel(ManualChangeDialog)
        self.instructionLabel.setObjectName(u"instructionLabel")
        self.instructionLabel.setWordWrap(True)

        self.verticalLayout.addWidget(self.instructionLabel)

        self.tasksListWidget = QListWidget(ManualChangeDialog)
        self.tasksListWidget.setObjectName(u"tasksListWidget")

        self.verticalLayout.addWidget(self.tasksListWidget)

        self.buttonBox = QDialogButtonBox(ManualChangeDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(ManualChangeDialog)
        self.buttonBox.accepted.connect(ManualChangeDialog.accept)
        self.buttonBox.rejected.connect(ManualChangeDialog.reject)

        QMetaObject.connectSlotsByName(ManualChangeDialog)
    # setupUi

    def retranslateUi(self, ManualChangeDialog):
        ManualChangeDialog.setWindowTitle(QCoreApplication.translate("ManualChangeDialog", u"Confirm Manual Changes", None))
        self.instructionLabel.setText(QCoreApplication.translate("ManualChangeDialog", u"Your manual fix will now be committed. Please check the box next to every development task that your fix has completed. This will update the project's internal state.", None))
    # retranslateUi

