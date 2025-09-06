# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'output.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
    QPlainTextEdit, QSizePolicy, QVBoxLayout, QWidget)

class Output(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(693, 429)
        self.central_widget = QWidget(MainWindow)
        self.central_widget.setObjectName(u"central_widget")
        self.horizontalLayout = QHBoxLayout(self.central_widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.stdout_layout = QVBoxLayout()
        self.stdout_layout.setObjectName(u"stdout_layout")
        self.stdout_label = QLabel(self.central_widget)
        self.stdout_label.setObjectName(u"stdout_label")

        self.stdout_layout.addWidget(self.stdout_label)

        self.stdout_text = QPlainTextEdit(self.central_widget)
        self.stdout_text.setObjectName(u"stdout_text")
        self.stdout_text.setReadOnly(True)

        self.stdout_layout.addWidget(self.stdout_text)


        self.horizontalLayout.addLayout(self.stdout_layout)

        self.stderr_layout = QVBoxLayout()
        self.stderr_layout.setObjectName(u"stderr_layout")
        self.stderr_label = QLabel(self.central_widget)
        self.stderr_label.setObjectName(u"stderr_label")

        self.stderr_layout.addWidget(self.stderr_label)

        self.stderr_text = QPlainTextEdit(self.central_widget)
        self.stderr_text.setObjectName(u"stderr_text")
        self.stderr_text.setReadOnly(True)

        self.stderr_layout.addWidget(self.stderr_text)


        self.horizontalLayout.addLayout(self.stderr_layout)

        MainWindow.setCentralWidget(self.central_widget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Olfactory Controller", None))
        self.stdout_label.setText(QCoreApplication.translate("MainWindow", u"Standard Output", None))
        self.stderr_label.setText(QCoreApplication.translate("MainWindow", u"Standard Error", None))
    # retranslateUi

