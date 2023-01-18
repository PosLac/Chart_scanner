from shutil import copyfile

import cv2
import numpy as np
from pyqt5_plugins.examplebuttonplugin import QtGui

import image_detectations as detects
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

        self.export_button_png.setEnabled(False)
        self.export_button_pdf.setEnabled(False)
        self.edit_button.setEnabled(False)

        self.title_pos = 0
        self.above = self.findChild(QRadioButton, "above")
        self.below = self.findChild(QRadioButton, "below")

        self.xBar = self.findChild(QPushButton, "xBar")
        self.yBar = self.findChild(QPushButton, "yBar")

        self.spinner = QMovie("Spin-1s-200px.gif")

        self.export_button_pdf.clicked.connect(lambda: self.export("pdf"))
        self.export_button_png.clicked.connect(lambda: self.export("png"))
        self.edit_button.clicked.connect(self.open_edit_window)
        self.openFiles.clicked.connect(self.clicker)
        self.scanButton.clicked.connect(self.scanChart)
        self.closeButton.clicked.connect(self.closeWin)
        # self.xBar.clicked.connect(self.xBar_scan)
        # self.yBar.clicked.connect(self.yBar_scan)

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
        if self.above.isChecked():
            self.title_pos = 1
        elif self.below.isChecked():
            self.title_pos = -1

        self.work_requested.emit(fname)
        self.spinner.start()

    def closeWin(self):
        self.close()

    def export(self, type):
        input_file = "tikzdraw." + type
        dst = QFileDialog.getSaveFileName(self, 'Save File', 'tikzdraw.' + type, "*." + type)[0]
        if dst:
            copyfile(input_file, dst)
        print("copy done")

    def open_edit_window(self):
        print("Edit")
        self.edit_window = EditWindow()
        print("Edit2")

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
        self.error_label = self.findChild(QLabel, "error_label")

        self.export_button_pdf = self.findChild(QPushButton, "export_button_pdf")
        self.export_button_png = self.findChild(QPushButton, "export_button_png")
        print(self.export_button_png)
        print(self.export_button_pdf)
        self.export_button_pdf.clicked.connect(lambda: UIWindow.export("pdf"))
        self.export_button_png.clicked.connect(lambda: UIWindow.export("png"))

        self.title.setText(detects.chart_title)
        input_chart = QPixmap("tikzdraw.png")
        input_chart = input_chart.scaledToWidth(700)
        self.loaded_chart.setPixmap(input_chart)

        self.update_bool = False
        self.orientation = detects.orientation
        self.ratios = detects.ratios

        self.xMin_check = self.findChild(QCheckBox, "xMin_check")
        self.xMax_check = self.findChild(QCheckBox, "xMax_check")
        self.yMin_check = self.findChild(QCheckBox, "yMin_check")
        self.yMax_check = self.findChild(QCheckBox, "yMax_check")

        self.xMin = self.findChild(QSpinBox, "xMin")
        self.xMax = self.findChild(QSpinBox, "xMax")
        self.yMin = self.findChild(QSpinBox, "yMin")
        self.yMax = self.findChild(QSpinBox, "yMax")

        self.xMin_en = self.xMin_check.isChecked()
        self.xMax_en = self.xMax_check.isChecked()
        self.yMin_en = self.yMin_check.isChecked()
        self.yMax_en = self.yMax_check.isChecked()

        self.xMin_check.stateChanged.connect(lambda: self.minMax_toggle("xMin"))
        self.xMax_check.stateChanged.connect(lambda: self.minMax_toggle("xMax"))
        self.yMin_check.stateChanged.connect(lambda: self.minMax_toggle("yMin"))
        self.yMax_check.stateChanged.connect(lambda: self.minMax_toggle("yMax"))

        self.above.toggled.connect(self.above_title)
        self.above.setChecked(False)
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
        self.title_pos = 1

    def below_title(self):
        self.title_pos = -1

    def minMax_toggle(self, val):
        minMax = self.findChild(QSpinBox, val)
        minMax.setEnabled(not minMax.isEnabled())
        if not minMax.isEnabled():
            spinbox = self.findChild(QSpinBox, val)
            spinbox.setValue(0)

    def update_chart(self):
        print("Update start")
        self.update_bool = True
        self.xMin_en = self.xMin_check.isChecked()
        self.xMax_en = self.xMax_check.isChecked()
        self.yMin_en = self.yMin_check.isChecked()
        self.yMax_en = self.yMax_check.isChecked()

        self.work_requested.emit("")
        self.spinner.start()

        title_str = ""
        if self.title.text():
            title_str = self.title.text()
            print(title_str)

        if (self.xMin_en and self.xMax_en and self.xMin.value() > self.xMax.value()) or \
                (self.yMin_en and self.yMin_en and self.yMin.value() > self.yMax.value()):
            # todo popup ablak vagy vmi
            self.error_label.setText("A max értéke nagyobb kell, legyen, mint a min.")
            print("A maximum értéke nagyobb kell, legyen, mint a minimum.")

        else:
            minMax_array = [("xmin", self.xMin.value(), self.xMin_en), ("xmax", self.xMax.value(), self.xMax_en),
                            ("ymin", self.yMin.value(), self.yMin_en), ("ymax", self.yMax.value(), self.yMax_en)]
            print(self.orientation, self.ratios, minMax_array, title_str, self.title_pos)
            to_latex.latex(self.update_bool, self.orientation, self.ratios, minMax_array, title_str, self.title_pos)

            os.system('pdf2png.bat tikzdraw 300')
            input_chart = QPixmap("tikzdraw.png")
            input_chart = input_chart.scaledToWidth(700)
            self.loaded_chart.setPixmap(input_chart)


class Worker(QObject):
    fname = Signal(str)
    completed = Signal()
    chart = Signal(QPixmap)

    @Slot(str)
    def do_work(self, name):
        print("do_work")
        if name:
            print("mainw")
            UIWindow.outputChart.setMovie(UIWindow.spinner)
            self.fname.emit(name)
        else:
            print("editw")
            UIWindow.edit_window.loaded_chart.setMovie(UIWindow.edit_window.spinner)
            self.fname.emit("")
        if name:
            print("main")
            # print("UIWindow.title_pos: ", UIWindow.title_pos)
            main.main(name, UIWindow.title_pos)

        os.system('pdf2png.bat tikzdraw 300')
        output_chart = QPixmap("tikzdraw.png")
        output_chart = output_chart.scaledToWidth(700)
        print("worker done")
        self.completed.emit()
        if name:
            UIWindow.outputChart.setPixmap(output_chart)
            UIWindow.export_button_png.setEnabled(True)
            UIWindow.export_button_pdf.setEnabled(True)
            UIWindow.edit_button.setEnabled(True)
            print("MainWindow")
        else:
            print("1")

            UIWindow.edit_window.loaded_chart.setPixmap(output_chart)
            print("2")

            # UIWindow.edit_window.export_button_png.setEnabled(True)
            # UIWindow.edit_window.export_button_pdf.setEnabled(True)
            print("EditWindow")


app = QApplication(sys.argv)
UIWindow = MainWindow()
# editWindow = EditWindow()
app.exec_()
