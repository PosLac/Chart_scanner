from shutil import copyfile

import cv2
import numpy as np
from pyqt5_plugins.examplebuttonplugin import QtGui

import main
import os
import sys

from PyQt5 import uic
from PyQt5.QtCore import QObject, QThread
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QLabel, QApplication, QTextEdit, QWidget, \
    QRadioButton, QLineEdit, QCheckBox, QSpinBox

import to_latex


class MainWindow(QMainWindow):
    work_requested = Signal(str)

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("MainWindow.ui", self)
        self.edit_window = None
        self.openFiles = self.findChild(QPushButton, "openFiles")
        self.scanButton = self.findChild(QPushButton, "scan")
        self.closeButton = self.findChild(QPushButton, "closeButton")
        self.export_button_pdf = self.findChild(QPushButton, "export_button_pdf")
        self.export_button_png = self.findChild(QPushButton, "export_button_png")
        self.edit_button = self.findChild(QPushButton, "edit_button")
        self.label = self.findChild(QLabel, "fileName")
        self.inputChart = self.findChild(QLabel, "inputChart")
        self.outputChart = self.findChild(QLabel, "outputChart")
        self.export_name = self.findChild(QTextEdit, "export_name")

        self.xBar = self.findChild(QPushButton, "xBar")
        self.yBar = self.findChild(QPushButton, "yBar")

        self.spinner = QMovie("Spin-1s-200px.gif")

        self.export_button_pdf.clicked.connect(lambda: self.export("pdf"))
        self.export_button_png.clicked.connect(lambda: self.export("png"))
        self.edit_button.clicked.connect(self.open_edit_window)
        self.openFiles.clicked.connect(self.clicker)
        self.scanButton.clicked.connect(self.scanChart)
        self.closeButton.clicked.connect(self.closeWin)
        self.xBar.clicked.connect(self.xBar_scan)
        self.yBar.clicked.connect(self.yBar_scan)

        self.worker = Worker()
        self.worker_thread = QThread()

        self.worker.fname.connect(self.update)
        self.worker.completed.connect(self.complete)
        self.work_requested.connect(self.worker.do_work)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.showMaximized()

    def clicker(self):
        global fname
        fname = QFileDialog.getOpenFileName(None, "Open file", "")[0]
        if fname:
            self.scanButton.setEnabled(True)
            self.label.setText(fname)
            input_chart = QPixmap(fname)
            input_chart = input_chart.scaledToWidth(700)
            self.inputChart.setPixmap(input_chart)

    def update(self):
        print("update")

    def complete(self):
        print("complete")

    def scanChart(self):
        global fname
        print("1")
        self.work_requested.emit(fname)
        print("2")
        self.spinner.start()
        print("3")

    def closeWin(self):
        self.close()

    def export(self, type):
        input_file = "tikzdraw."+type
        dst = QFileDialog.getSaveFileName(self, 'Save File', 'tikzdraw.'+type, "*."+type)[0]
        if dst:
            copyfile(input_file, dst)
        print("copy done")

    def open_edit_window(self):
        self.edit_window = EditWindow()

    def xBar_scan(self):
        self.spinner.start()
        x_bar = "D:/SZTE/Szakdoga/Let's_Scan/chart_xbar.png"

        self.label.setText(x_bar)
        input_chart = QPixmap(x_bar)
        input_chart = input_chart.scaledToWidth(700)
        self.inputChart.setPixmap(input_chart)

        self.work_requested.emit(x_bar)

    def yBar_scan(self):

        self.spinner.start()
        y_bar = "D:/SZTE/Szakdoga/Let's_Scan/chart_ybar.png"

        self.label.setText(y_bar)
        input_chart = QPixmap(y_bar)
        input_chart = input_chart.scaledToWidth(700)
        self.inputChart.setPixmap(input_chart)

        self.work_requested.emit(y_bar)


class EditWindow(QMainWindow):
    work_requested = Signal(str)

    def __init__(self):
        super(EditWindow, self).__init__()
        uic.loadUi("EditWindow.ui", self)

        self.title_pos = ""
        self.above = self.findChild(QRadioButton, "above")
        self.below = self.findChild(QRadioButton, "below")
        self.title = self.findChild(QLineEdit, "title_text")
        self.update_button = self.findChild(QPushButton, "update_button")
        self.loaded_chart = self.findChild(QLabel, "chart")
        input_chart = QPixmap("tikzdraw.png")
        input_chart = input_chart.scaledToWidth(700)
        self.loaded_chart.setPixmap(input_chart)

        self.xMin_check = self.findChild(QCheckBox, "xMin_check")
        self.xMax_check = self.findChild(QCheckBox, "xMax_check")
        self.yMin_check = self.findChild(QCheckBox, "yMin_check")
        self.yMax_check = self.findChild(QCheckBox, "yMax_check")

        self.xMin = self.findChild(QSpinBox, "xMin")
        self.xMax = self.findChild(QSpinBox, "xMax")
        self.yMin = self.findChild(QSpinBox, "yMin")
        self.yMax = self.findChild(QSpinBox, "yMax")

        self.xMin_check.stateChanged.connect(lambda: self.minMax_toggle("xMin"))
        self.xMax_check.stateChanged.connect(lambda: self.minMax_toggle("xMax"))
        self.yMin_check.stateChanged.connect(lambda: self.minMax_toggle("yMin"))
        self.yMax_check.stateChanged.connect(lambda: self.minMax_toggle("yMax"))

        self.above.toggled.connect(self.above_title)
        self.above.setChecked(True)
        self.below.toggled.connect(self.below_title)
        self.below.setChecked(False)

        self.update_button.clicked.connect(self.update_chart)

        self.worker = Worker()
        self.worker_thread = QThread()
        self.worker.fname.connect(self.update)
        self.worker.completed.connect(self.complete)
        self.work_requested.connect(self.worker.do_work)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        print("inited")
        self.spinner = QMovie("Spin-1s-200px.gif")
        self.showMaximized()

    def update(self):
        print("update")

    def complete(self):
        print("complete")

    def above_title(self):
        self.title_pos = "above"

    def below_title(self):
        self.title_pos = "below"

    def minMax_toggle(self, val):
        minMax = self.findChild(QSpinBox, val)
        minMax.setEnabled(not minMax.isEnabled())

    def update_chart(self):
        orientation, ratios, chart_title, title_below =\
            to_latex.orientation, to_latex.ratios, to_latex.chart_title, to_latex.title_below
        print("1")
        self.work_requested.emit("")
        print("2")
        self.spinner.start()

        if self.title_pos == "above":
            print("above")
        elif self.title_pos == "below":
            print("below")

        if self.title.text():
            pass

        print(self.title.text())


class Worker(QObject):
    fname = Signal(str)
    completed = Signal()
    chart = Signal(QPixmap)

    @Slot(str)
    def do_work(self, name):
        print("do_work")
        if name:
            UIWindow.outputChart.setMovie(UIWindow.spinner)
        else:
            UIWindow.edit_window.loaded_chart.setMovie(UIWindow.edit_window.spinner)
        self.fname.emit(name)
        print(name)
        if name:
            main.main(name)
        os.system('pdf2png.bat tikzdraw 300')
        output_chart = QPixmap("tikzdraw.png")
        output_chart = output_chart.scaledToWidth(700)
        print("worker done")
        self.completed.emit()
        if name:
            UIWindow.outputChart.setPixmap(output_chart)
        else:
            UIWindow.edit_window.loaded_chart.setPixmap(output_chart)

app = QApplication(sys.argv)
UIWindow = MainWindow()
# editWindow = EditWindow()
app.exec_()
