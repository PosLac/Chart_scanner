from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtWidgets import QMainWindow, QRadioButton, QLineEdit, QPushButton, QLabel, QCheckBox, QSpinBox

from functions import image_detectations as detects
from functions.worker import Worker


class EditWindow(QMainWindow):
    work_requested = pyqtSignal(str, bool)

    def __init__(self, parent_window):
        super(EditWindow, self).__init__()
        self.parent_window = parent_window
        self.minMax_array = None
        uic.loadUi("editWindow.ui", self)

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
        self.export_button_pdf.clicked.connect(lambda: self.parent_window.export("pdf"))
        self.export_button_png.clicked.connect(lambda: self.parent_window.export("png"))
        self.back_button.clicked.connect(self.back_to_main)

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

        self.above.setChecked(self.parent_window.above.isChecked())
        self.below.setChecked(self.parent_window.below.isChecked())
        self.no_title.setChecked(self.parent_window.no_title.isChecked())

        self.update_button.clicked.connect(self.update_chart)

        self.worker = Worker(self)
        self.worker_thread = QThread()
        self.worker.fname.connect(self.update)
        self.worker.completed.connect(self.complete)
        self.work_requested.connect(self.worker.do_work)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()


        print("inited")
        self.spinner = QMovie("Spin-1s-200px.gif")
        self.showMaximized()

    def minMax_toggle(self, val):
        min_max = self.findChild(QSpinBox, val)
        min_max.setEnabled(not min_max.isEnabled())
        if not min_max.isEnabled():
            spinbox = self.findChild(QSpinBox, val)
            spinbox.setValue(0)

    def update(self):
        print("update")

    def complete(self):
        print("complete")

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
                (self.yMin_en and self.yMax_en and self.yMin.value() > self.yMax.value()):
            error_list = error_list + "\n A maximum értéke nagyobb kell, hogy legyen, mint a minimum."
            self.error_label.setText(error_list)

        else:
            self.loaded_chart.setPixmap(QPixmap())
            self.loaded_chart.setMovie(self.spinner)
            self.spinner.start()
            self.minMax_array = [("xmin", self.xMin.value(), self.xMin_en), ("xmax", self.xMax.value(), self.xMax_en),
                                 ("ymin", self.yMin.value(), self.yMin_en), ("ymax", self.yMax.value(), self.yMax_en)]
            self.work_requested.emit("", True)

    def back_to_main(self):
        self.close()
        self.parent_window.showMaximized()
