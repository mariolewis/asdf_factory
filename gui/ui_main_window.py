# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QHeaderView, QLabel, QMainWindow,
    QMenu, QMenuBar, QSizePolicy, QSplitter,
    QStackedWidget, QStatusBar, QTabWidget, QTableView,
    QToolBar, QTreeView, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 800)
        self.actionNew_Project = QAction(MainWindow)
        self.actionNew_Project.setObjectName(u"actionNew_Project")
        self.actionLoad_Archived_Project = QAction(MainWindow)
        self.actionLoad_Archived_Project.setObjectName(u"actionLoad_Archived_Project")
        self.actionStop_Export_Project = QAction(MainWindow)
        self.actionStop_Export_Project.setObjectName(u"actionStop_Export_Project")
        self.actionSettings = QAction(MainWindow)
        self.actionSettings.setObjectName(u"actionSettings")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.mainSplitter = QSplitter(self.centralwidget)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Horizontal)
        self.mainSplitter.setHandleWidth(1)
        self.leftPanelWidget = QWidget(self.mainSplitter)
        self.leftPanelWidget.setObjectName(u"leftPanelWidget")
        self.leftPanelWidget.setMinimumSize(QSize(250, 0))
        self.leftPanelWidget.setMaximumSize(QSize(400, 16777215))
        self.leftPanelLayout = QVBoxLayout(self.leftPanelWidget)
        self.leftPanelLayout.setObjectName(u"leftPanelLayout")
        self.projectNavigationTabs = QTabWidget(self.leftPanelWidget)
        self.projectNavigationTabs.setObjectName(u"projectNavigationTabs")
        self.filesTab = QWidget()
        self.filesTab.setObjectName(u"filesTab")
        self.verticalLayout_2 = QVBoxLayout(self.filesTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.projectFilesTreeView = QTreeView(self.filesTab)
        self.projectFilesTreeView.setObjectName(u"projectFilesTreeView")

        self.verticalLayout_2.addWidget(self.projectFilesTreeView)

        self.projectNavigationTabs.addTab(self.filesTab, "")
        self.changesTab = QWidget()
        self.changesTab.setObjectName(u"changesTab")
        self.verticalLayout_3 = QVBoxLayout(self.changesTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.crTableView = QTableView(self.changesTab)
        self.crTableView.setObjectName(u"crTableView")

        self.verticalLayout_3.addWidget(self.crTableView)

        self.projectNavigationTabs.addTab(self.changesTab, "")

        self.leftPanelLayout.addWidget(self.projectNavigationTabs)

        self.mainSplitter.addWidget(self.leftPanelWidget)
        self.mainContentArea = QStackedWidget(self.mainSplitter)
        self.mainContentArea.setObjectName(u"mainContentArea")
        self.welcomePage = QWidget()
        self.welcomePage.setObjectName(u"welcomePage")
        self.verticalLayout_4 = QVBoxLayout(self.welcomePage)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.welcomeLabel = QLabel(self.welcomePage)
        self.welcomeLabel.setObjectName(u"welcomeLabel")
        self.welcomeLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.welcomeLabel)

        self.mainContentArea.addWidget(self.welcomePage)
        self.phasePage = QWidget()
        self.phasePage.setObjectName(u"phasePage")
        self.verticalLayout_5 = QVBoxLayout(self.phasePage)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.phaseLabel = QLabel(self.phasePage)
        self.phaseLabel.setObjectName(u"phaseLabel")

        self.verticalLayout_5.addWidget(self.phaseLabel)

        self.mainContentArea.addWidget(self.phasePage)
        self.mainSplitter.addWidget(self.mainContentArea)

        self.verticalLayout.addWidget(self.mainSplitter)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1200, 21))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName(u"menuView")
        self.menuProject = QMenu(self.menubar)
        self.menuProject.setObjectName(u"menuProject")
        self.menuRun = QMenu(self.menubar)
        self.menuRun.setObjectName(u"menuRun")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuDebug = QMenu(self.menubar)
        self.menuDebug.setObjectName(u"menuDebug")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(MainWindow)
        self.toolBar.setObjectName(u"toolBar")
        MainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuProject.menuAction())
        self.menubar.addAction(self.menuRun.menuAction())
        self.menubar.addAction(self.menuDebug.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionNew_Project)
        self.menuFile.addAction(self.actionLoad_Archived_Project)
        self.menuFile.addAction(self.actionStop_Export_Project)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSettings)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"ASDF - Autonomous Software Development Factory", None))
        self.actionNew_Project.setText(QCoreApplication.translate("MainWindow", u"New Project...", None))
        self.actionLoad_Archived_Project.setText(QCoreApplication.translate("MainWindow", u"Load Archived Project...", None))
        self.actionStop_Export_Project.setText(QCoreApplication.translate("MainWindow", u"Stop & Export Project...", None))
        self.actionSettings.setText(QCoreApplication.translate("MainWindow", u"Settings...", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.projectNavigationTabs.setTabText(self.projectNavigationTabs.indexOf(self.filesTab), QCoreApplication.translate("MainWindow", u"Files", None))
        self.projectNavigationTabs.setTabText(self.projectNavigationTabs.indexOf(self.changesTab), QCoreApplication.translate("MainWindow", u"Changes", None))
        self.welcomeLabel.setText(QCoreApplication.translate("MainWindow", u"Welcome to ASDF. Please create a New Project or Load an Archived Project to begin.", None))
        self.phaseLabel.setText(QCoreApplication.translate("MainWindow", u"This is where the UI for a specific project phase will be rendered.", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", u"Edit", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
        self.menuProject.setTitle(QCoreApplication.translate("MainWindow", u"Project", None))
        self.menuRun.setTitle(QCoreApplication.translate("MainWindow", u"Run", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.menuDebug.setTitle(QCoreApplication.translate("MainWindow", u"Debug", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
    # retranslateUi

