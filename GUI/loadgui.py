from shutil import copyfile
import main.image_detectations as detects
import main
import os
import sys
import main.to_latex

from PyQt5 import uic
from PyQt5.QtCore import QObject, QThread
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QPushButton, QLabel, QApplication, QRadioButton, QLineEdit, \
    QCheckBox, QSpinBox, QGroupBox, QGridLayout


class MainWindow(QMainWindow):
    work_requested = Signal(str, bool)

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("../GUI/MainWindow.ui", self)
        self.edit_window = None
        self.back_button = self.findChild(QPushButton, "back_button")
        self.crop_image_button = self.findChild(QPushButton, "crop_image")
        self.scanButton = self.findChild(QPushButton, "scan")
        self.export_button_pdf = self.findChild(QPushButton, "export_button_pdf")
        self.export_button_png = self.findChild(QPushButton, "export_button_png")
        self.edit_button = self.findChild(QPushButton, "edit_button")
        self.title_group = self.findChild(QGroupBox, "title_group")
        self.label = self.findChild(QLabel, "file_name")
        self.input_image = self.findChild(QLabel, "input_image")
        self.output_chart = self.findChild(QLabel, "output_chart")
        # self.export_name = self.findChild(QTextEdit, "export_name")

        # self.title_group.setHidden(True) #todo set hidden layout
        self.scanButton.setHidden(True)
        self.export_button_png.setHidden(True)
        self.export_button_pdf.setHidden(True)
        self.edit_button.setHidden(True)

        self.title_pos = 0
        self.above = self.findChild(QRadioButton, "above")
        self.above.setChecked(False)
        self.below = self.findChild(QRadioButton, "below")
        self.below.setChecked(False)
        self.no_title = self.findChild(QRadioButton, "no_title")
        self.no_title.setChecked(True)

        self.xBar = self.findChild(QPushButton, "xBar")
        self.yBar = self.findChild(QPushButton, "yBar")

        self.spinner = QMovie("Spin-1s-200px.gif")

        self.export_button_pdf.clicked.connect(lambda: self.export("pdf"))
        self.export_button_png.clicked.connect(lambda: self.export("png"))
        self.edit_button.clicked.connect(self.open_edit_window)
        # self.open_files_button.clicked.connect(self.clicker)
        # self.crop_image_button.clicked.connect(self.crop_picture)
        self.scanButton.clicked.connect(self.scan_chart)

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
        fname = QFileDialog.getOpenFileName(None, "Open file", "")[0]  # todo replaced with fix filename
        # fname = "chart_ybar.png"
        if fname:
            self.scanButton.setHidden(False)
            self.title_group.setHidden(False)

            self.label.setText(fname)
            input_chart = QPixmap(fname)
            input_chart = input_chart.scaledToWidth(700)
            self.input_image.setPixmap(input_chart)

        # self.scan_chart()  # todo delete

    def update(self):
        print("update")

    def complete(self):
        print("complete")

    def scan_chart(self):
        global fname
        if self.above.isChecked():
            self.title_pos = 1
        elif self.below.isChecked():
            self.title_pos = -1
        elif self.no_title.isChecked():
            self.title_pos = 0

        self.work_requested.emit(fname, False)
        self.spinner.start()

    def export(self, type):
        input_file = "tikzdraw." + type
        dst = QFileDialog.getSaveFileName(self, 'Save File', 'tikzdraw.' + type, "*." + type)[0]
        if dst:
            copyfile(input_file, dst)
        print("copy done")

    def open_edit_window(self):
        self.edit_window = EditWindow()


class EditWindow(QMainWindow):
    work_requested = Signal(str, bool)

    def __init__(self):
        super(EditWindow, self).__init__()
        self.minMax_array = None
        uic.loadUi("EditWindow.ui", self)

        self.title_pos = 0
        self.above = self.findChild(QRadioButton, "above")
        self.below = self.findChild(QRadioButton, "below")
        self.no_title = self.findChild(QRadioButton, "no_title")
        self.title = self.findChild(QLineEdit, "title_text")
        self.update_button = self.findChild(QPushButton, "update_button")
        self.back_button = self.findChild(QPushButton, "back")
        self.loaded_chart = self.findChild(QLabel, "chart")
        self.error_label = self.findChild(QLabel, "error_label")

        self.export_button_pdf = self.findChild(QPushButton, "export_button_pdf")
        self.export_button_png = self.findChild(QPushButton, "export_button_png")
        print(self.export_button_png)
        print(self.export_button_pdf)
        self.export_button_pdf.clicked.connect(lambda: UIWindow.export("pdf"))
        self.export_button_png.clicked.connect(lambda: UIWindow.export("png"))
        self.back_button.clicked.connect(lambda: self.close())

        self.title_str = ""
        self.title.setText(detects.chart_title)
        input_chart = QPixmap("../tikzdraw.png")
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

        self.above.setChecked(UIWindow.above.isChecked())
        self.below.setChecked(UIWindow.below.isChecked())
        self.no_title.setChecked(UIWindow.no_title.isChecked())

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

    def minMax_toggle(self, val):
        min_max = self.findChild(QSpinBox, val)
        min_max.setEnabled(not min_max.isEnabled())
        if not min_max.isEnabled():
            spinbox = self.findChild(QSpinBox, val)
            spinbox.setValue(0)

    def update_chart(self):
        print("Update start")
        error_list = ""
        self.update_bool = True
        self.xMin_en = self.xMin_check.isChecked()
        self.xMax_en = self.xMax_check.isChecked()
        self.yMin_en = self.yMin_check.isChecked()
        self.yMax_en = self.yMax_check.isChecked()

        if self.above.isChecked():
            self.title_pos = 1
        elif self.below.isChecked():
            self.title_pos = -1
        elif self.no_title.isChecked():
            self.title_pos = 0

        if self.title.text() == "" and self.title_pos != 0:
            error_list = error_list + "\n Amennyiben nem szeretne címet megadni, válassza ki a 'Nincs cím' opciót."
            self.error_label.setText(error_list)

        if self.title.text():
            self.title_str = self.title.text()
            print(self.title_str)

        if (self.xMin_en and self.xMax_en and self.xMin.value() > self.xMax.value()) or \
                (self.yMin_en and self.yMin_en and self.yMin.value() > self.yMax.value()):
            error_list = error_list + "\n A maximum értéke nagyobb kell, hogy legyen, mint a minimum."
            self.error_label.setText(error_list)

        else:
            self.loaded_chart.setPixmap(QPixmap())
            self.loaded_chart.setMovie(self.spinner)
            self.spinner.start()
            self.minMax_array = [("xmin", self.xMin.value(), self.xMin_en), ("xmax", self.xMax.value(), self.xMax_en),
                                 ("ymin", self.yMin.value(), self.yMin_en), ("ymax", self.yMax.value(), self.yMax_en)]
            self.work_requested.emit("", True)


class Worker(QObject):
    fname = Signal(str)
    completed = Signal()
    chart = Signal(QPixmap)

    @Slot(str, bool)
    def do_work(self, name, update):
        print("do_work")
        if name:
            print("mainw")
            print(name)
            UIWindow.output_chart.setPixmap(QPixmap())
            UIWindow.output_chart.setMovie(UIWindow.spinner)
            self.fname.emit(name)
            main.main(name, UIWindow.title_pos)

        if update:
            main.to_latex.latex(UIWindow.edit_window.update_bool, UIWindow.edit_window.orientation,
                           UIWindow.edit_window.ratios, UIWindow.edit_window.minMax_array,
                           UIWindow.edit_window.title_str, UIWindow.edit_window.title_pos)
            print("latex")

        os.system('pdf2png.bat tikzdraw 300')
        output_chart = QPixmap("../tikzdraw.png")
        output_chart = output_chart.scaledToWidth(700)
        print("worker done")
        if name:
            UIWindow.output_chart.setPixmap(output_chart)
            UIWindow.export_button_png.setHidden(False)
            UIWindow.export_button_pdf.setHidden(False)
            UIWindow.edit_button.setHidden(False)
            print("MainWindow")
        else:
            UIWindow.edit_window.loaded_chart.setPixmap(output_chart)
            print("EditWindow")
        self.completed.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    UIWindow = MainWindow()
    sys.exit(app.exec_())
