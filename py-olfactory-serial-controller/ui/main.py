# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QFrame,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Main(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(578, 372)
        self.central_widget = QWidget(MainWindow)
        self.central_widget.setObjectName(u"central_widget")
        self.horizontalLayout = QHBoxLayout(self.central_widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.relays_layout = QVBoxLayout()
        self.relays_layout.setObjectName(u"relays_layout")
        self.relays_label = QLabel(self.central_widget)
        self.relays_label.setObjectName(u"relays_label")
        font = QFont()
        font.setPointSize(16)
        self.relays_label.setFont(font)

        self.relays_layout.addWidget(self.relays_label)

        self.relays_list = QListWidget(self.central_widget)
        self.relays_list.setObjectName(u"relays_list")
        self.relays_list.setFocusPolicy(Qt.NoFocus)
        self.relays_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.relays_layout.addWidget(self.relays_list)

        self.relays_button_layout = QHBoxLayout()
        self.relays_button_layout.setObjectName(u"relays_button_layout")
        self.enable_button = QPushButton(self.central_widget)
        self.enable_button.setObjectName(u"enable_button")
        self.enable_button.setMinimumSize(QSize(0, 41))
        self.enable_button.setFocusPolicy(Qt.NoFocus)

        self.relays_button_layout.addWidget(self.enable_button)

        self.disable_button = QPushButton(self.central_widget)
        self.disable_button.setObjectName(u"disable_button")
        self.disable_button.setMinimumSize(QSize(0, 41))
        self.disable_button.setFocusPolicy(Qt.NoFocus)

        self.relays_button_layout.addWidget(self.disable_button)


        self.relays_layout.addLayout(self.relays_button_layout)


        self.horizontalLayout.addLayout(self.relays_layout)

        self.actions_layout = QVBoxLayout()
        self.actions_layout.setObjectName(u"actions_layout")
        self.actions_label = QLabel(self.central_widget)
        self.actions_label.setObjectName(u"actions_label")
        self.actions_label.setMinimumSize(QSize(231, 0))
        self.actions_label.setMaximumSize(QSize(16777215, 31))
        self.actions_label.setFont(font)

        self.actions_layout.addWidget(self.actions_label)

        self.start_csv_button = QPushButton(self.central_widget)
        self.start_csv_button.setObjectName(u"start_csv_button")
        self.start_csv_button.setMinimumSize(QSize(231, 41))
        self.start_csv_button.setFocusPolicy(Qt.NoFocus)

        self.actions_layout.addWidget(self.start_csv_button)

        self.pause_csv_button = QPushButton(self.central_widget)
        self.pause_csv_button.setObjectName(u"pause_csv_button")
        self.pause_csv_button.setEnabled(False)
        self.pause_csv_button.setMinimumSize(QSize(231, 41))
        self.pause_csv_button.setFocusPolicy(Qt.NoFocus)

        self.actions_layout.addWidget(self.pause_csv_button)

        self.stop_csv_button = QPushButton(self.central_widget)
        self.stop_csv_button.setObjectName(u"stop_csv_button")
        self.stop_csv_button.setEnabled(False)
        self.stop_csv_button.setMinimumSize(QSize(231, 41))
        self.stop_csv_button.setFocusPolicy(Qt.NoFocus)

        self.actions_layout.addWidget(self.stop_csv_button)

        self.actions_separator = QFrame(self.central_widget)
        self.actions_separator.setObjectName(u"actions_separator")
        self.actions_separator.setFrameShape(QFrame.Shape.HLine)
        self.actions_separator.setFrameShadow(QFrame.Shadow.Sunken)

        self.actions_layout.addWidget(self.actions_separator)

        self.running_csv_checkbox = QCheckBox(self.central_widget)
        self.running_csv_checkbox.setObjectName(u"running_csv_checkbox")
        self.running_csv_checkbox.setEnabled(True)
        self.running_csv_checkbox.setMinimumSize(QSize(231, 31))
        self.running_csv_checkbox.setFocusPolicy(Qt.NoFocus)
        self.running_csv_checkbox.setCheckable(True)
        self.running_csv_checkbox.setChecked(False)

        self.actions_layout.addWidget(self.running_csv_checkbox)

        self.show_csv_button = QPushButton(self.central_widget)
        self.show_csv_button.setObjectName(u"show_csv_button")
        self.show_csv_button.setEnabled(True)
        self.show_csv_button.setMinimumSize(QSize(231, 41))
        self.show_csv_button.setFocusPolicy(Qt.NoFocus)

        self.actions_layout.addWidget(self.show_csv_button)

        self.show_output_button = QPushButton(self.central_widget)
        self.show_output_button.setObjectName(u"show_output_button")
        self.show_output_button.setMinimumSize(QSize(231, 41))
        self.show_output_button.setFocusPolicy(Qt.NoFocus)

        self.actions_layout.addWidget(self.show_output_button)

        self.actions_layout_stretch = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.actions_layout.addItem(self.actions_layout_stretch)


        self.horizontalLayout.addLayout(self.actions_layout)

        MainWindow.setCentralWidget(self.central_widget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Olfactory Controller", None))
        self.relays_label.setText(QCoreApplication.translate("MainWindow", u"Relays", None))
        self.enable_button.setText(QCoreApplication.translate("MainWindow", u"Enable", None))
        self.disable_button.setText(QCoreApplication.translate("MainWindow", u"Disable", None))
        self.actions_label.setText(QCoreApplication.translate("MainWindow", u"Actions", None))
        self.start_csv_button.setText(QCoreApplication.translate("MainWindow", u"Start CSV", None))
        self.pause_csv_button.setText(QCoreApplication.translate("MainWindow", u"PLACEHOLDER", None))
        self.stop_csv_button.setText(QCoreApplication.translate("MainWindow", u"Stop CSV", None))
        self.running_csv_checkbox.setText(QCoreApplication.translate("MainWindow", u"Running CSV", None))
        self.show_csv_button.setText(QCoreApplication.translate("MainWindow", u"Show CSV", None))
        self.show_output_button.setText(QCoreApplication.translate("MainWindow", u"Show Output", None))
    # retranslateUi

